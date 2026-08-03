from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .recipe.lookup import lookup_recipes
from .search import has_explicit_match, make_snippet, score_entry
from .skill_pack import SkillPack

DOC_SEARCH_HIGH_CONFIDENCE_SCORE = 35.0
DOC_SEARCH_LOW_CONFIDENCE_SCORE = 12.0


@dataclass(frozen=True)
class LookupMatch:
    score: float
    title: str
    source_path: str
    reference_path: str
    evidence_posture: str
    snippet: str


def lookup_docs(pack: SkillPack, query: str, limit: int = 5) -> list[LookupMatch]:
    matches: list[LookupMatch] = []
    for entry in pack.docs_index:
        score = score_entry(query, entry)
        if score <= 0:
            continue
        text = str(entry.get("text", ""))
        if not has_explicit_match(query, entry, text):
            continue
        matches.append(
            LookupMatch(
                score=score,
                title=str(entry.get("title", "")),
                source_path=str(entry.get("source_path", "")),
                reference_path=str(entry.get("reference_path", "")),
                evidence_posture=str(entry.get("evidence_posture", "unknown")),
                snippet=make_snippet(str(entry.get("text", "")), query),
            )
        )
    matches.sort(key=lambda m: (-m.score, m.title))
    return matches[: max(0, limit)]


def lookup_docs_and_recipes(
    pack: SkillPack,
    query: str,
    *,
    nsys_path: str = "nsys",
    limit: int = 5,
) -> dict[str, Any]:
    """Search all packaged product references with one stable result shape.

    The `nsys_skill_cli search-docs` CLI and packaged scripts both expose
    `nsys_search_docs`. Keep the behavior single-sourced here so both
    callers return the same confidence scores and result fields.
    """

    limit = max(0, limit)
    docs = [match.__dict__ for match in lookup_docs(pack, query, limit=limit)]
    recipes = lookup_recipes(pack, query, nsys_path, limit=limit)
    combined: list[dict[str, Any]] = []
    combined.extend({"kind": "docs", **item} for item in docs)
    combined.extend({"kind": "recipe", **item} for item in recipes)
    combined.sort(key=lambda item: (-float(item.get("score", 0)), item.get("title") or item.get("name") or ""))
    top_score = float(combined[0].get("score", 0)) if combined else 0.0
    return {
        "query": query,
        "confidence": retrieval_confidence(top_score),
        "docs_matches": docs[:limit],
        "recipe_matches": recipes[:limit],
        "matches": combined[: max(limit, 6)],
    }


def retrieval_confidence(top_score: float) -> str:
    """Map the local lexical score to a coarse retrieval confidence.

    These thresholds are calibration constants for the current shared scorer.
    When the scorer or indexed metadata changes materially, update the
    retrieval golden set before changing the thresholds.
    """

    if top_score >= DOC_SEARCH_HIGH_CONFIDENCE_SCORE:
        return "high"
    if top_score >= DOC_SEARCH_LOW_CONFIDENCE_SCORE:
        return "low"
    return "none"
