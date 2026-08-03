"""Default locations for the bundled ``nsight-systems`` skill pack.

Release installers should place the prebuilt skill pack in one of these
locations so user-facing commands can stay short. Source checkouts can still
pass ``--skill-pack`` explicitly.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .defaults import NSYS_AGENT_SKILL_PACK_ENV

SKILL_PACK_NAME = "nsight-systems"
PROJECT_DIR_NAME = "nsys-agent-tools"


class SkillPackPathError(ValueError):
    """Raised when a command needs a skill pack but none is configured."""


def resolve_skill_pack_path(value: str | Path | None = None) -> Path:
    """Resolve an explicit or release-installed skill-pack path.

    The search order is intentionally small and predictable:

    1. the explicit ``--skill-pack`` value;
    2. ``NSYS_AGENT_SKILL_PACK`` for wrappers/test harnesses;
    3. user data dir installed by release bundles; and
    4. Python prefix ``share`` dir installed by packaged distributions.
    """

    if value:
        return _configured_skill_pack_path(value, "--skill-pack")
    env_value = os.environ.get(NSYS_AGENT_SKILL_PACK_ENV)
    if env_value:
        return _configured_skill_pack_path(env_value, NSYS_AGENT_SKILL_PACK_ENV)
    for candidate in default_skill_pack_candidates():
        if _looks_like_skill_pack(candidate):
            return candidate.resolve()
    raise SkillPackPathError(
        "No bundled nsight-systems skill pack was found. Install the "
        "nsys-agent-tools release package, or pass --skill-pack when running "
        "from source. nsys_skill_cli does not build skill packs at runtime."
    )


def default_skill_pack_candidates() -> tuple[Path, ...]:
    """Return release-install locations checked by ``nsys_skill_cli``.

    Paths are returned even when they do not exist; this keeps diagnostics and
    tests deterministic without probing unrelated directories.
    """

    candidates: list[Path] = []
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        candidates.append(_skill_path(Path(xdg_data_home).expanduser()))
    candidates.append(_skill_path(Path.home() / ".local" / "share"))
    candidates.append(_skill_path(Path(sys.prefix) / "share"))
    return tuple(_dedupe_paths(candidates))


def _skill_path(data_root: Path) -> Path:
    return data_root / PROJECT_DIR_NAME / "skills" / SKILL_PACK_NAME


def _configured_skill_pack_path(value: str | Path, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if _looks_like_skill_pack(path):
        return path
    raise SkillPackPathError(
        f"Invalid {label} path: {path}. Expected SKILL.md and skill-pack manifest metadata."
    )


def _looks_like_skill_pack(path: Path) -> bool:
    has_manifest = (path / "manifest.json").is_file() or (
        path / "assets" / "nsight-systems" / "manifest.json"
    ).is_file()
    return has_manifest and (path / "SKILL.md").is_file()


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path.expanduser())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(path)
    return deduped
