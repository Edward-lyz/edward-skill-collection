from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

TOKEN_RE = re.compile(r"[a-zA-Z0-9_+.-]+")
TOKEN_SPLIT_RE = re.compile(r"[_+.-]+")
STOP_TOKENS = {
    "a",
    "an",
    "are",
    "by",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "include",
    "included",
    "information",
    "is",
    "it",
    "must",
    "of",
    "the",
    "to",
    "what",
    "with",
    "why",
    "would",
    "you",
}
ANCHOR_STOP_TOKENS = STOP_TOKENS | {"nvidia", "nsight", "nsys", "system", "systems", "recipe", "recipes"}
TITLE_TOKEN_SCORE = 20.0
KEYWORD_TOKEN_SCORE = 12.0
TEXT_TOKEN_BASE_SCORE = 4.0
TEXT_TOKEN_MAX_BONUS = 8.0
TEXT_TOKEN_LOG_SCALE = 2.0
EXACT_PHRASE_SCORE = 20.0
ALIAS_PHRASE_SCORE = 45.0
ALIAS_SUBSET_BASE_SCORE = 28.0
ALIAS_SUBSET_MAX_BONUS = 12.0
ALIAS_SUBSET_TOKEN_SCALE = 2.0
TOPIC_TOKEN_SCORE = 6.0
MAX_SEARCH_PRIORITY_MULTIPLIER = 4.0


def tokens(text: str) -> list[str]:
    """Return normalized lexical tokens for transparent local retrieval.

    The search layer is deliberately simple, but it should still behave like a
    token matcher rather than a substring matcher.  Expanding ``cuda_api_sum``
    into both the full token and its pieces preserves technical identifiers
    while avoiding false positives such as ``mode`` matching ``model``.
    """

    result: list[str] = []
    for raw in TOKEN_RE.findall(text):
        lowered = raw.lower()
        candidates = [lowered]
        candidates.extend(part for part in TOKEN_SPLIT_RE.split(lowered) if part and part != lowered)
        for candidate in candidates:
            result.extend(_token_variants(candidate))
    return [token for token in result if len(token) > 1 and token not in STOP_TOKENS]


def score_entry(query: str, entry: dict[str, Any]) -> float:
    query_tokens = tokens(query)
    if not query_tokens:
        return 0.0
    scoring_tokens = [token for token in query_tokens if token not in ANCHOR_STOP_TOKENS] or query_tokens
    title = " ".join(str(entry.get(k, "")) for k in ("title", "name", "display_name")).lower()
    title_tokens = set(tokens(title))
    keywords = set(tokens(" ".join(str(k) for k in entry.get("keywords", []))))
    text = str(entry.get("text", "")).lower()
    text_counts = Counter(tokens(text))
    score = 0.0
    for token in scoring_tokens:
        if token in title_tokens:
            score += TITLE_TOKEN_SCORE
        if token in keywords:
            score += KEYWORD_TOKEN_SCORE
        count = text_counts[token]
        if count:
            score += TEXT_TOKEN_BASE_SCORE + min(
                TEXT_TOKEN_MAX_BONUS,
                math.log(count + 1) * TEXT_TOKEN_LOG_SCALE,
            )
    phrase = query.strip().lower()
    if phrase and phrase in text:
        score += EXACT_PHRASE_SCORE
    score += _metadata_score(phrase, set(query_tokens), entry)
    return round(score, 2)


def has_explicit_match(query: str, entry: dict[str, Any], text: str, *, extra_fields: tuple[str, ...] = ()) -> bool:
    """Return whether a scored match has a concrete lexical/metadata overlap.

    `score_entry` intentionally knows about broad product anchors such as
    "nsys", "Nsight Systems", and "recipe" so canonical docs are still
    discoverable.  Callers that return top-k evidence use this guard to avoid
    surfacing a reference solely because of those anchors.  The rule remains
    generic: curated aliases/topics or real content tokens make an entry
    discoverable; Python code should not grow question-specific routing maps.
    """

    query_tokens = set(tokens(query))
    semantic_tokens = query_tokens - ANCHOR_STOP_TOKENS
    domain_tokens = {"nsys", "nsight", "systems", "system", "recipe", "recipes"}
    fields = [
        str(entry.get("title", "")),
        str(entry.get("name", "")),
        str(entry.get("display_name", "")),
        str(entry.get("source_path", "")),
        text,
        " ".join(str(item) for item in entry.get("aliases", []) or []),
        " ".join(str(item) for item in entry.get("topics", []) or []),
    ]
    fields.extend(str(entry.get(field, "")) for field in extra_fields)
    haystack = " ".join(fields).lower()
    haystack_tokens = set(tokens(haystack))
    if semantic_tokens:
        return any(token in haystack_tokens for token in semantic_tokens)
    if query_tokens & domain_tokens:
        return any(token in haystack_tokens for token in query_tokens & domain_tokens)
    phrase = query.strip().lower()
    return bool(phrase and phrase in haystack)


def _metadata_score(phrase: str, query_tokens: set[str], entry: dict[str, Any]) -> float:
    """Score generated metadata without embedding product question lists in code.

    Curated references can declare aliases/priority in their source markdown.
    Generated docs and recipes can also carry aliases later. The ranker only
    understands the generic metadata contract; it does not know about specific
    Nsight Systems support questions or eval prompts.
    """
    score = 0.0
    for alias in _string_list(entry.get("aliases")):
        alias_lower = alias.lower().strip()
        if not alias_lower:
            continue
        alias_tokens = set(tokens(alias_lower))
        alias_semantic_tokens = alias_tokens - ANCHOR_STOP_TOKENS
        query_semantic_tokens = query_tokens - ANCHOR_STOP_TOKENS
        if phrase and alias_lower in phrase:
            score += ALIAS_PHRASE_SCORE
        elif (
            alias_tokens
            and alias_tokens.issubset(query_tokens)
            and (alias_semantic_tokens or not query_semantic_tokens)
        ):
            score += ALIAS_SUBSET_BASE_SCORE + min(
                ALIAS_SUBSET_MAX_BONUS,
                ALIAS_SUBSET_TOKEN_SCALE * len(alias_tokens),
            )
    for topic in _string_list(entry.get("topics")):
        topic_tokens = set(tokens(topic))
        if topic_tokens and topic_tokens & query_tokens:
            score += TOPIC_TOKEN_SCORE
    try:
        priority = float(entry.get("search_priority", 1.0))
    except (TypeError, ValueError):
        priority = 1.0
    if priority > 1.0 and score > 0.0:
        score *= min(priority, MAX_SEARCH_PRIORITY_MULTIPLIER)
    return score


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _token_variants(token: str) -> list[str]:
    """Return conservative variants for plural/singular technical prose.

    This keeps lexical retrieval stable for pairs such as ``metric``/``metrics``
    and ``memory copy``/``memory copies`` without introducing stemming or a
    hidden semantic router.
    """

    variants = [token]
    if len(token) > 4 and token.endswith("ies"):
        variants.append(token[:-3] + "y")
    elif len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        variants.append(token[:-1])
    return variants


def make_snippet(text: str, query: str, limit: int = 1500) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    lower = compact.lower()
    phrase = query.strip().lower()
    if phrase and phrase in lower:
        start = max(0, lower.find(phrase) - 140)
        end = min(len(compact), start + limit)
        return ("..." if start else "") + compact[start:end] + ("..." if end < len(compact) else "")
    all_tokens = [t for t in tokens(query) if lower.find(t) >= 0]
    query_tokens = [t for t in all_tokens if t not in ANCHOR_STOP_TOKENS] or all_tokens
    # Anchor on the least-common matching token so broad words like "recipe"
    # do not hide the section that matched "custom", "metrics", etc.
    query_tokens.sort(key=lambda token: (lower.count(token), lower.find(token)))
    start = max(0, lower.find(query_tokens[0]) - 140) if query_tokens else 0
    end = min(len(compact), start + limit)
    return ("..." if start else "") + compact[start:end] + ("..." if end < len(compact) else "")
