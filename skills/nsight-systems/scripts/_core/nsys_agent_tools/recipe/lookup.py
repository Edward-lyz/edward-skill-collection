from __future__ import annotations

from typing import Any

from ..cli_tools import NsysCli
from ..search import has_explicit_match, make_snippet, score_entry
from ..skill_pack import SkillPack
from .capabilities import recipe_capability_summary
from .metadata import normalize_expected_outputs


def lookup_recipes(
    pack: SkillPack,
    query: str,
    nsys_path: str = "nsys",
    limit: int = 5,
    *,
    live_recipes: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Search packaged recipe metadata merged with live recipe names."""

    live = live_recipes if live_recipes is not None else NsysCli(nsys_path).recipes()
    entries = {str(e.get("name")): dict(e) for e in pack.recipes_index}
    for name, display in live.items():
        merged = dict(entries.get(name, {}))
        merged.update({"name": name, "display_name": display, "source": "live"})
        merged["text"] = f"{name} {display} {merged.get('text', '')}"
        entries[name] = merged
    matches = []
    for entry in entries.values():
        score = score_entry(query, entry)
        if score <= 0:
            continue
        text = str(entry.get("text", ""))
        if not has_explicit_match(query, entry, text, extra_fields=("options",)):
            continue
        outputs = expected_outputs(entry)
        matches.append(
            {
                "score": score,
                "name": entry.get("name"),
                "display_name": entry.get("display_name"),
                "source": entry.get("source", "packaged"),
                "reference_path": entry.get("reference_path"),
                "options": entry.get("options", [])[:40],
                "expected_outputs": outputs,
                "capability_summary": recipe_capability_summary(
                    {**entry, "expected_outputs": outputs},
                ),
                "snippet": make_snippet(str(entry.get("text", "")), query),
            }
        )
    matches.sort(key=lambda m: (-float(m["score"]), str(m.get("name", ""))))
    return matches[: max(0, limit)]


def recipe_match_summary(match: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return the compact fields an answer-producing agent should notice first."""

    if not match:
        return None
    return {
        "name": match.get("name"),
        "display_name": match.get("display_name"),
        "source": match.get("source"),
        "reference_path": match.get("reference_path"),
        "options": match.get("options", [])[:20],
        "expected_outputs": match.get("expected_outputs", [])[:12],
        "capability_summary": match.get("capability_summary"),
    }


def expected_outputs(entry: dict[str, Any]) -> list[dict[str, str]]:
    """Return output files declared by the generated recipe index."""

    return normalize_expected_outputs(entry.get("expected_outputs"))
