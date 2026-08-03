"""Runtime loader for the official Nsight Systems skill pack."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class SkillPackError(RuntimeError):
    """Raised when a runtime skill pack is invalid or unsupported."""


@dataclass(frozen=True)
class SkillPack:
    root: Path
    manifest: dict[str, Any]
    docs_index: list[dict[str, Any]]
    recipes_index: list[dict[str, Any]]
    sqlite_schema_index: dict[str, Any]

    @classmethod
    def load(cls, root: str | Path) -> SkillPack:
        path = Path(root).expanduser().resolve()
        manifest_path = _manifest_path(path)
        if not manifest_path.is_file():
            raise SkillPackError(f"manifest.json not found: {path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        _validate(path, manifest)
        resources = manifest["resources"]
        docs_index = json.loads((path / resources["docs_index"]).read_text(encoding="utf-8"))
        recipes_index = json.loads((path / resources["recipes_index"]).read_text(encoding="utf-8"))
        sqlite_schema_index: dict[str, Any] = {"tables": []}
        if "sqlite_schema_index" in resources:
            loaded = json.loads((path / resources["sqlite_schema_index"]).read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                sqlite_schema_index = loaded
        if not isinstance(docs_index, list) or not isinstance(recipes_index, list):
            raise SkillPackError("indexes must be JSON lists")
        return cls(path, manifest, docs_index, recipes_index, sqlite_schema_index)

    @property
    def package_version(self) -> str:
        return str(self.manifest.get("package_version", "unknown"))

    @property
    def build_nsys_version(self) -> str:
        return str(self.manifest.get("nsys", {}).get("build_nsys_version", "unknown"))


def _manifest_path(root: Path) -> Path:
    """Return the manifest for a product skill pack or NV-BASE export.

    Product builds keep `manifest.json` in the skill root. NV-BASE only
    considers `references/`, `scripts/`, `assets/`, and `evals/` expected
    top-level entries, so the generated NV-BASE export stores runtime
    metadata under `assets/nsight-systems/`. These are two current artifact
    layouts, not an old-version compatibility path.
    """

    for rel in (
        "manifest.json",
        "assets/nsight-systems/manifest.json",
    ):
        candidate = root / rel
        if candidate.is_file():
            return candidate
    return root / "manifest.json"


def _validate(root: Path, manifest: dict[str, Any]) -> None:
    name = manifest.get("name")
    aliases = manifest.get("runtime_aliases", [])
    if name != "nsight-systems":
        raise SkillPackError("manifest name must be nsight-systems")
    if "nsys" not in aliases:
        raise SkillPackError("manifest runtime_aliases must include nsys")
    for key in ("entry", "resources", "scripts", "content_hashes"):
        if key not in manifest:
            raise SkillPackError(f"manifest missing {key}")
    _path(root, manifest["entry"], file=True)
    for rel in manifest["resources"].values():
        _path(root, rel, file=None)
    for rel in manifest["scripts"].values():
        _path(root, rel, file=True)
    for rel, expected in manifest.get("content_hashes", {}).items():
        target = _path(root, rel, file=True)
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            raise SkillPackError(f"content hash mismatch: {rel}")


def _path(root: Path, rel: Any, *, file: bool | None) -> Path:
    if not isinstance(rel, str) or not rel:
        raise SkillPackError("manifest path must be a non-empty string")
    pure = PurePosixPath(rel)
    if pure.is_absolute() or ".." in pure.parts:
        raise SkillPackError(f"manifest path escapes pack: {rel}")
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise SkillPackError(f"manifest path escapes pack: {rel}") from exc
    if not path.exists():
        raise SkillPackError(f"manifest path not found: {rel}")
    if file is True and not path.is_file():
        raise SkillPackError(f"manifest path is not a file: {rel}")
    if file is False and not path.is_dir():
        raise SkillPackError(f"manifest path is not a directory: {rel}")
    return path
