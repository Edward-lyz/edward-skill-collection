from __future__ import annotations

import glob
import os
import re
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .process_utils import run_bounded_process
from .skill_pack import SkillPack

FLAG_RE = re.compile(r"(?<![\w-])(--[a-zA-Z0-9][a-zA-Z0-9-]*|-[A-Za-z0-9])")
TOKEN_RE = re.compile(r"^[a-zA-Z0-9_+-]+$")
RECIPE_RE = re.compile(r"^\s{2}([a-z0-9_]+)\s+--\s+(.+?)\s*$")


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    text: str
    error: str = ""
    returncode: int = 0


class NsysCli:
    def __init__(self, nsys_path: str | os.PathLike[str] = "nsys", timeout_s: int = 30) -> None:
        self.nsys_path = os.fspath(nsys_path)
        self.timeout_s = timeout_s

    def version(self) -> CommandResult:
        return self.run(["--version"], timeout_s=10)

    def help(self, target: str = "", max_chars: int = 16000) -> dict[str, Any]:
        version = self.version()
        if not version.ok:
            return {"ok": False, "source": "live", "error": version.error}
        target = target.strip()
        if target.startswith("-"):
            return self.find_flag(target, max_chars=max_chars, version=version.text.strip())
        parts = [p for p in target.split() if p] if target else []
        flag_parts = [part for part in parts if part.startswith("-")]
        for part in parts:
            if not part.startswith("-") and not TOKEN_RE.fullmatch(part):
                return {"ok": False, "source": "live", "nsys_version": version.text.strip(), "error": f"Invalid command word: {part!r}"}
        command_parts = [part for part in parts if not part.startswith("-")]
        if flag_parts and command_parts:
            payload = self._help_parts(command_parts, max_chars=max_chars, version=version.text.strip())
            flag = flag_parts[0]
            if payload.get("ok") and flag in payload.get("flags", []):
                payload["matched_flag"] = flag
                if excerpt := payload.get("flag_excerpts", {}).get(flag):
                    payload["matched_flag_excerpt"] = excerpt
                return payload
            if payload.get("ok"):
                payload["ok"] = False
                payload["error"] = f"Flag {flag} was not found in {' '.join(command_parts)!r} help for this nsys installation."
            return payload
        if flag_parts:
            return self.find_flag(flag_parts[0], max_chars=max_chars, version=version.text.strip())
        return self._help_parts(parts, max_chars=max_chars, version=version.text.strip())

    def find_flag(self, flag: str, *, max_chars: int = 16000, version: str | None = None) -> dict[str, Any]:
        version = version if version is not None else self.version().text.strip()
        scopes = [[]] + [[s] for s in self.subcommands()]
        searched = 0
        for scope in scopes:
            searched += 1
            payload = self._help_parts(scope, max_chars=max_chars, version=version)
            if payload.get("ok") and flag in payload.get("flags", []):
                payload["matched_flag"] = flag
                if excerpt := payload.get("flag_excerpts", {}).get(flag):
                    payload["matched_flag_excerpt"] = excerpt
                payload["searched_scopes"] = searched
                return payload
        for recipe_name in self.recipes():
            searched += 1
            payload = self._help_parts(["recipe", recipe_name], max_chars=max_chars, version=version)
            if payload.get("ok") and flag in payload.get("flags", []):
                payload["matched_flag"] = flag
                if excerpt := payload.get("flag_excerpts", {}).get(flag):
                    payload["matched_flag_excerpt"] = excerpt
                payload["matched_recipe"] = recipe_name
                payload["searched_scopes"] = searched
                return payload
        return {
            "ok": False,
            "source": "live",
            "nsys_version": version,
            "error": f"Flag {flag} was not found in this nsys installation after searching {searched} command and recipe scopes.",
        }

    def subcommands(self) -> list[str]:
        result = self.run(["--help"], timeout_s=10)
        if not result.ok:
            return []
        found: list[str] = []
        for line in result.text.splitlines():
            match = re.match(r"^\s{2,}([a-z][a-z0-9_-]+)\s", line)
            if match:
                found.append(match.group(1))
        return sorted(set(found))

    def recipes(self) -> dict[str, str]:
        result = self.run(["recipe", "--help"], timeout_s=20)
        if not result.ok:
            return {}
        recipes: dict[str, str] = {}
        for line in result.text.splitlines():
            match = RECIPE_RE.match(line)
            if match:
                recipes[match.group(1)] = match.group(2)
        return recipes

    def export_formats(self) -> dict[str, Any]:
        """Probe export formats from live help instead of guessing by version."""

        result = self.run(["export", "--help"], timeout_s=20)
        if not result.ok:
            return {"ok": False, "formats": [], "error": result.error}
        text = result.text.lower()
        formats = sorted(
            {
                name
                for name in ("sqlite", "parquet", "parquetdir")
                if re.search(rf"(?<![a-z0-9_]){name}(?![a-z0-9_])", text)
            }
        )
        return {
            "ok": True,
            "formats": formats,
            "preferred_report_cache_format": "parquetdir" if "parquetdir" in formats else None,
        }

    def recipe_dir(self) -> Path | None:
        path = Path(self.nsys_path).expanduser()
        resolved = path if path.is_absolute() else _which_path(self.nsys_path)
        if resolved is None:
            return None
        return resolved.parent / "python" / "packages" / "nsys_recipe"

    def resolved_path(self) -> Path | None:
        path = Path(self.nsys_path).expanduser()
        if path.is_absolute() or "/" in self.nsys_path or "\\" in self.nsys_path:
            return path.resolve() if path.exists() else None
        return _which_path(self.nsys_path)

    def run(self, args: list[str], timeout_s: int | None = None) -> CommandResult:
        timeout = int(timeout_s or self.timeout_s)
        return _run_cached(
            self.nsys_path,
            tuple(args),
            timeout,
            _binary_identity(self.nsys_path),
        )

    def _help_parts(self, parts: list[str], *, max_chars: int, version: str) -> dict[str, Any]:
        result = self.run(parts + ["--help"], timeout_s=_help_timeout_s(parts))
        command = " ".join([_display_binary(self.nsys_path)] + parts + ["--help"])
        if not result.ok:
            return {"ok": False, "source": "live", "nsys_version": version, "command": command, "error": result.error}
        full_text = result.text
        flags = sorted(set(FLAG_RE.findall(full_text)))
        flag_excerpts = {flag: _flag_excerpt(full_text, flag) for flag in flags}
        text = full_text
        truncated = len(text) > max_chars
        if truncated:
            text = text[:max_chars] + "\n... (truncated)"
        payload: dict[str, Any] = {
            "ok": True,
            "source": "live",
            "nsys_version": version,
            "command": command,
            "help_text": text,
            "flags": flags,
            "flag_excerpts": flag_excerpts,
            "truncated": truncated,
        }
        if parts == ["recipe"]:
            payload["recommended_shorthand"] = "nsys recipe <recipe-name> [recipe-args]"
            payload["note"] = (
                "Live help may show the generic parser shape. For user-facing examples, "
                "put the recipe name first, then recipe-specific arguments."
            )
        return payload


def inspect_cli_help(
    cli: NsysCli,
    target: str = "",
    *,
    pack: SkillPack | None = None,
    max_chars: int = 18000,
) -> dict[str, Any]:
    """Return live CLI help for the installed Nsight Systems binary.

    Live `nsys --help` remains authoritative for exact installed syntax. When
    a flag-like target is not present in live help, packaged docs can provide
    related product context, but callers must preserve the live-help failure.
    """

    payload = cli.help(target, max_chars=max_chars)
    if pack is not None and target.strip().startswith("-") and not payload.get("ok"):
        from .docs import lookup_docs

        payload["related_docs"] = [match.__dict__ for match in lookup_docs(pack, target, limit=3)]
        payload["note"] = (
            "The flag was not found in live command help. If related packaged docs explain "
            "a recipe-framework or version-specific flag, use that evidence and say live help "
            "for a specific recipe/version should still be checked."
        )
    return payload


def _help_timeout_s(parts: list[str]) -> int:
    """Return a help timeout matched to the command's startup cost.

    Per-recipe help can bootstrap the installed recipe Python environment on a
    fresh machine.  That is still authoritative live help, so give it enough
    time instead of failing closed and nudging agents toward direct `nsys
    recipe` workarounds.
    """

    if len(parts) >= 2 and parts[0] == "recipe":
        return 120
    return 20


def doctor(nsys_path: str = "nsys") -> dict[str, Any]:
    cli = NsysCli(nsys_path)
    checks = []
    version = _check(cli, ["--version"], "nsys --version")
    checks.append(version)
    for args in (["--help"], ["profile", "--help"], ["stats", "--help"], ["recipe", "--help"]):
        checks.append(_check(cli, args, "nsys " + " ".join(args)))
    export_formats = cli.export_formats()
    export_detail = ", ".join(export_formats.get("formats", [])) or export_formats.get("error", "")
    checks.append(
        {
            "name": "nsys export formats",
            "status": "pass"
            if export_formats.get("ok") and export_formats.get("preferred_report_cache_format") == "parquetdir"
            else "fail",
            "detail": export_detail,
        }
    )
    recipe_dir = cli.recipe_dir()
    checks.append(
        {
            "name": "recipe directory",
            "status": "pass" if recipe_dir and recipe_dir.is_dir() else "warn",
            "detail": "<nsys-dir>/python/packages/nsys_recipe" if recipe_dir else "could not resolve nsys path",
        }
    )
    status_set = {c["status"] for c in checks}
    status = "fail" if "fail" in status_set else "warn" if "warn" in status_set else "pass"
    return {
        "status": status,
        "nsys_path": _display_binary(nsys_path),
        "paths_hidden": True,
        "nsys_version": version.get("detail", ""),
        "discovery": discover_nsys(nsys_path),
        "checks": checks,
    }


def discover_nsys(requested: str = "nsys") -> dict[str, Any]:
    """Find likely local nsys binaries without silently switching versions.

    The result is diagnostic only.  Callers still use the configured nsys path;
    candidates help users fix PATH/NSYS_PATH issues without exposing full local
    paths to the model.
    """

    requested_cli = NsysCli(requested)
    requested_path = requested_cli.resolved_path()
    candidates: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for source, candidate in _candidate_nsys_paths(requested):
        resolved = candidate.expanduser().resolve()
        if resolved in seen or not resolved.is_file():
            continue
        seen.add(resolved)
        version = NsysCli(str(resolved)).version()
        recipe_dir = resolved.parent / "python" / "packages" / "nsys_recipe"
        candidates.append(
            {
                "source": source,
                "display": _display_binary(resolved),
                "version": version.text.strip().splitlines()[0] if version.ok and version.text.strip() else "",
                "usable": bool(version.ok),
                "recipe_dir_present": recipe_dir.is_dir(),
            }
        )
    return {
        "requested": _display_binary(requested),
        "requested_resolved": requested_path is not None,
        "candidate_count": len(candidates),
        "candidates": candidates[:8],
        "note": "Diagnostics only; the runtime uses the explicitly configured nsys path and does not auto-switch.",
    }


def resolve_nsys(extra: tuple[Path, ...] = ()) -> Path | None:
    """Return the first existing Nsys binary, ``extra`` paths before the standard candidates.

    Unlike ``discover_nsys`` (diagnostic only), this picks one path for callers that must
    act on it, such as exporting ``NSYS_PATH``. Existence is the only test, as in the shell.
    """

    candidates = list(extra) + [path for _, path in _candidate_nsys_paths("nsys")]
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        if resolved.is_file():
            return resolved
    return None


def nsys_failure_hint(nsys_path: str | os.PathLike[str], error: object) -> str:
    """Return a redacted, actionable error for failed local `nsys` execution."""

    text = _redact_binary_path(f"{type(error).__name__}: {error}", nsys_path)
    lowered = text.lower()
    if "filenotfounderror" in lowered or "no such file or directory" in lowered:
        return (
            "nsys executable not found. Set NSYS_PATH or pass --nsys-path to the "
            "installed Nsight Systems `nsys` binary, then rerun `nsys_skill_cli doctor` "
            "for diagnostics."
        )
    return text


def _candidate_nsys_paths(requested: str) -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    requested_path = Path(requested).expanduser()
    if requested_path.is_absolute() or "/" in requested or "\\" in requested:
        candidates.append(("configured", requested_path))
    if env_path := os.environ.get("NSYS_PATH"):
        candidates.append(("NSYS_PATH", Path(env_path).expanduser()))
    if path_nsys := shutil.which("nsys"):
        candidates.append(("PATH", Path(path_nsys)))
    _append_candidate_globs(
        candidates,
        "common-linux",
        [
            "/opt/nvidia/nsight-systems/*/target-linux-x64/nsys",
            "/opt/nvidia/nsight-systems/*/host-linux-x64/nsys",
            "/usr/local/cuda-*/nsight-systems-*/target-linux-x64/nsys",
            "/usr/local/cuda-*/nsight-systems-*/host-linux-x64/nsys",
            "/usr/local/cuda/bin/nsys",
        ],
    )
    _append_candidate_globs(
        candidates,
        "common-wsl-windows",
        [
            "/mnt/c/Program Files/NVIDIA Corporation/Nsight Systems */target-linux-x64/nsys",
            "/mnt/c/Program Files/NVIDIA Corporation/Nsight Systems */host-linux-x64/nsys",
        ],
    )
    program_files_roots = [
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
    ]
    for root in [value for value in program_files_roots if value]:
        _append_candidate_globs(
            candidates,
            "common-windows",
            [
                str(Path(root) / "NVIDIA Corporation" / "Nsight Systems *" / "target-windows-x64" / "nsys.exe"),
                str(Path(root) / "NVIDIA Corporation" / "Nsight Systems *" / "host-windows-x64" / "nsys.exe"),
            ],
        )
    _append_candidate_globs(
        candidates,
        "common-macos",
        ["/Applications/NVIDIA Nsight Systems*.app/Contents/MacOS/nsys"],
    )
    return candidates


def _append_candidate_globs(
    candidates: list[tuple[str, Path]],
    source: str,
    patterns: list[str],
    *,
    max_per_pattern: int = 24,
) -> None:
    for pattern in patterns:
        for match in sorted(glob.glob(pattern))[:max_per_pattern]:
            path = Path(match)
            if path.is_file():
                candidates.append((source, path))


def _check(cli: NsysCli, args: list[str], name: str) -> dict[str, str]:
    result = cli.run(args, timeout_s=20)
    detail = (result.text or result.error).strip().splitlines()
    return {"name": name, "status": "pass" if result.ok else "fail", "detail": detail[0] if detail else result.error}


def _display_binary(nsys_path: str | os.PathLike[str]) -> str:
    """Return a non-sensitive binary label for model-facing evidence."""

    raw = os.fspath(nsys_path)
    if "/" in raw or "\\" in raw:
        return Path(raw).name or "nsys"
    return raw or "nsys"


def _redact_binary_path(text: str, nsys_path: str | os.PathLike[str]) -> str:
    raw = os.fspath(nsys_path)
    if not raw:
        return text
    return text.replace(raw, _display_binary(raw))


def _flag_excerpt(text: str, flag: str, *, radius: int = 600) -> str:
    index = text.find(flag)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + radius)
    return text[start:end].strip()


def _which_path(binary: str) -> Path | None:
    found = shutil.which(binary)
    return Path(found).resolve() if found else None


def _binary_identity(nsys_path: str | os.PathLike[str]) -> tuple[str, int, int, str]:
    """Return a cache key component for live help from one installed nsys.

    Help/version output is authoritative, but it is also repeatedly requested
    in one process by docs lookup, recipe lookup, guardrails, and local BYO developer tools.
    Key by resolved binary metadata and `NSYS_RECIPE_PATH` so live discovery
    stays version-aware without rerunning the same help commands every turn.
    """

    raw = os.fspath(nsys_path)
    path = Path(raw).expanduser()
    resolved = path.resolve() if path.is_absolute() or "/" in raw or "\\" in raw else _which_path(raw)
    recipe_path = os.environ.get("NSYS_RECIPE_PATH", "")
    if resolved is None:
        return raw, -1, -1, recipe_path
    try:
        stat = resolved.stat()
    except OSError:
        return str(resolved), -1, -1, recipe_path
    return str(resolved), int(stat.st_mtime_ns), int(stat.st_size), recipe_path


@lru_cache(maxsize=64)
def _run_cached(
    nsys_path: str,
    args: tuple[str, ...],
    timeout_s: int,
    _identity: tuple[str, int, int, str],
) -> CommandResult:
    """Run a live nsys help command with a small process-wide cache.

    The cached values include command help text, so keep the cache deliberately
    small. Correctness is protected by the binary identity component; this is a
    latency optimization, not a persistent product cache.
    """

    cmd = [nsys_path, *args]
    try:
        completed = run_bounded_process(cmd, timeout_s=timeout_s)
    except Exception as exc:
        return CommandResult(False, "", _redact_binary_path(f"{type(exc).__name__}: {exc}", nsys_path), -1)
    text = _redact_binary_path(completed.stdout or completed.stderr, nsys_path)
    if completed.returncode != 0:
        return CommandResult(False, text, text.strip() or f"exit {completed.returncode}", completed.returncode)
    return CommandResult(True, text, returncode=completed.returncode)
