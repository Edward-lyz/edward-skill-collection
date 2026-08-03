from __future__ import annotations

import re
from dataclasses import dataclass

from .search import make_snippet, score_entry
from .skill_pack import SkillPack


@dataclass(frozen=True)
class SchemaMatch:
    score: float
    name: str
    description: str
    columns: list[dict[str, str]]
    snippet: str


def lookup_schema(pack: SkillPack, query: str, limit: int = 5) -> list[SchemaMatch]:
    entries = pack.sqlite_schema_index.get("tables", [])
    if not isinstance(entries, list):
        return []
    matches: list[SchemaMatch] = []
    exact_names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", ""))
        boost = _table_name_boost(query, name)
        score = score_entry(query, entry) + boost
        if score <= 0:
            continue
        if boost:
            exact_names.add(name)
        columns = entry.get("columns", [])
        if not isinstance(columns, list):
            columns = []
        matches.append(
            SchemaMatch(
                score=score,
                name=name,
                description=str(entry.get("description", "")),
                columns=[c for c in columns if isinstance(c, dict)][:80],
                snippet=make_snippet(str(entry.get("text", "")), query),
            )
        )
    matches.sort(key=lambda match: (-match.score, match.name))
    if exact_names:
        matches = [match for match in matches if match.name in exact_names]
    return matches[: max(0, limit)]


def _table_name_boost(query: str, table_name: str) -> float:
    if not table_name:
        return 0.0
    if re.search(rf"\b{re.escape(table_name.lower())}\b", query.lower()):
        return 100.0
    return 0.0
