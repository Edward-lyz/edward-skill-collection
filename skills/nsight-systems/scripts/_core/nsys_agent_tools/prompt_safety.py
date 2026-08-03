"""Prompt/output safety helpers for Nsight Systems tool evidence.

These helpers are intentionally small. They do not try to "clean" the meaning
of report data; they only remove control characters, hide obvious local paths,
and cap very large strings before tool output is sent back to a model.
"""

from __future__ import annotations

import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CONTROL_SENTINEL = "\n__NSYS_CONTROL_CHAR__\n"
# Avoid matching URL paths such as `https://docs.nvidia.com/...`: the preceding
# colon is a strong signal that `//...` is not a local POSIX path.
_PATH_FILE_SUFFIXES = (
    ".nsys-rep",
    ".jsonl",
    ".sqlite",
    ".duckdb",
    ".parquet",
    ".qdrep",
    ".log",
    ".txt",
    ".json",
    ".csv",
    ".rep",
    ".py",
    ".sh",
    ".so",
    ".dll",
    ".dylib",
)
_ABS_KNOWN_ROOT_START_RE = re.compile(
    r"(?<![\w.:-])/(?:etc|proc|sys|dev|root|home|var|Users|Volumes|mnt|opt|workspace|scratch|tmp|srv|data|cluster)(?=$|/)",
    re.IGNORECASE,
)
_ABS_KNOWN_ROOT_PATH_RE = re.compile(
    r"(?<![\w.:-])/(?:etc|proc|sys|dev|root|home|var|Users|Volumes|mnt|opt|workspace|scratch|tmp|srv|data|cluster)"
    r"(?:/[^\s/\n\r\"'<>|`$]+)+"
)
_ABS_POSIX_PATH_RE = re.compile(r"(?<![\w.:-])/(?:[^\s\"'<>|`$]+/)+[^\s\"'<>|`$]*")
_ABS_WINDOWS_PATH_RE = re.compile(r"\b[A-Za-z]:\\(?:[^\s\"'<>|`$]+\\)*[^\s\"'<>|`$]*")
_URL_RE = re.compile(r"\bhttps?://[^\s\"'<>`]+")
_PATH_HARD_TERMINATORS = frozenset("\n\r\"'<>|`$")
_PATH_SOFT_TERMINATORS = frozenset(".,;:)?!")
_PATH_SCAN_LIMIT = 512
_MAX_FLOAT_DECIMAL = Decimal(str(sys.float_info.max))


def sanitize_text(value: str, *, max_chars: int = 4000) -> str:
    """Return a prompt-safe representation of a report/tool string.

    Report fields such as NVTX labels, process names, command lines, and file
    paths are user-controlled data. Keep their meaning, but prevent accidental
    prompt/control-character issues and avoid exposing full local paths.
    """

    text = _CONTROL_RE.sub(_CONTROL_SENTINEL, value)
    urls: list[str] = []

    def keep_url(match: re.Match[str]) -> str:
        urls.append(match.group(0))
        return f"__NSYS_SAFE_URL_{len(urls) - 1}__"

    text = _URL_RE.sub(keep_url, text)
    text = _ABS_WINDOWS_PATH_RE.sub(lambda m: _path_placeholder(m.group(0)), text)
    text = _redact_known_root_paths(text)
    text = _ABS_KNOWN_ROOT_PATH_RE.sub(lambda m: _path_placeholder(m.group(0)), text)
    text = _ABS_POSIX_PATH_RE.sub(lambda m: _path_placeholder(m.group(0)), text)
    for index, url in enumerate(urls):
        text = text.replace(f"__NSYS_SAFE_URL_{index}__", url)
    text = text.replace(_CONTROL_SENTINEL, " ")
    if len(text) > max_chars:
        return text[: max(0, max_chars - 18)] + "\n... (truncated)"
    return text


def sanitize_value(value: Any, *, max_string_chars: int = 4000) -> Any:
    """Recursively sanitize JSON-like values before exposing them to a model."""

    if isinstance(value, str):
        return sanitize_text(value, max_chars=max_string_chars)
    if isinstance(value, Path):
        return _path_placeholder(str(value))
    if isinstance(value, bytes):
        return f"<bytes:{len(value)}>"
    if isinstance(value, Decimal):
        return _safe_decimal(value)
    if isinstance(value, dict):
        return {str(k): sanitize_value(v, max_string_chars=max_string_chars) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item, max_string_chars=max_string_chars) for item in value]
    if isinstance(value, tuple):
        return [sanitize_value(item, max_string_chars=max_string_chars) for item in value]
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    # For values we do not handle directly, convert to text and run the
    # same string cleanup. This keeps output JSON-safe and still hides
    # local paths.
    return sanitize_text(str(value), max_chars=max_string_chars)


def _safe_decimal(value: Decimal) -> int | float | str:
    """Return a JSON-safe Decimal without silently changing its value."""

    if not value.is_finite():
        return str(value)
    if value.copy_abs() > _MAX_FLOAT_DECIMAL:
        return str(value)
    if value == value.to_integral_value():
        return int(value)
    as_float = float(value)
    if Decimal(str(as_float)) != value:
        return str(value)
    return as_float


def exception_message(exc: BaseException, *, max_chars: int = 1000) -> str:
    """Return a sanitized exception summary for model-visible tool errors."""

    return sanitize_text(f"{type(exc).__name__}: {exc}", max_chars=max_chars)


def _redact_known_root_paths(text: str) -> str:
    """Redact known-root paths with a bounded scanner instead of nested regexes."""

    parts: list[str] = []
    last = 0
    for match in _ABS_KNOWN_ROOT_START_RE.finditer(text):
        if match.start() < last:
            continue
        end = _known_root_path_end(text, match.end())
        if end <= match.end():
            continue
        parts.append(text[last : match.start()])
        parts.append(_path_placeholder(text[match.start() : end]))
        last = end
    if last == 0:
        return text
    parts.append(text[last:])
    return "".join(parts)


def _known_root_path_end(text: str, index: int) -> int:
    """Return a bounded end offset for a local path after a known POSIX root."""

    limit = min(len(text), index + _PATH_SCAN_LIMIT)
    pos = index
    saw_spaced_segment = False
    while pos < limit and text[pos] == "/":
        segment_start = pos + 1
        segment_end, had_space = _path_segment_end(
            text,
            segment_start,
            limit,
            allow_space=saw_spaced_segment or _slash_before_sentence_end(text, segment_start, limit),
        )
        if segment_end <= segment_start:
            break
        saw_spaced_segment = saw_spaced_segment or had_space
        pos = segment_end
    return pos


def _path_segment_end(text: str, start: int, limit: int, *, allow_space: bool) -> tuple[int, bool]:
    pos = start
    words = 1
    had_space = False
    while pos < limit:
        char = text[pos]
        if char == "/" or char in _PATH_HARD_TERMINATORS:
            break
        if char in _PATH_SOFT_TERMINATORS:
            suffix = _matched_file_suffix_at(text, pos)
            if suffix:
                pos += len(suffix)
                continue
            if char == "." and pos + 1 < limit and (text[pos + 1].isalnum() or text[pos + 1] in "_-"):
                pos += 1
                continue
            break
        if char.isspace():
            if not allow_space:
                break
            next_token_start = pos + 1
            while next_token_start < limit and text[next_token_start].isspace():
                next_token_start += 1
            if (
                next_token_start >= limit
                or text[next_token_start] in _PATH_HARD_TERMINATORS
                or text[next_token_start] in _PATH_SOFT_TERMINATORS
            ):
                break
            if words >= 2:
                break
            had_space = True
            words += 1
            pos = next_token_start
            continue
        pos += 1
    return pos, had_space


def _slash_before_sentence_end(text: str, start: int, limit: int) -> bool:
    pos = start
    while pos < limit:
        char = text[pos]
        if char == "/":
            return True
        if char in _PATH_HARD_TERMINATORS or char in _PATH_SOFT_TERMINATORS:
            return False
        pos += 1
    return False


def _matched_file_suffix_at(text: str, pos: int) -> str:
    lower = text[pos:].lower()
    for suffix in _PATH_FILE_SUFFIXES:
        if lower.startswith(suffix):
            end = pos + len(suffix)
            if end == len(text) or not text[end].isalnum():
                return suffix
    return ""


def _path_placeholder(raw: str) -> str:
    path_text = raw.replace("\\", "/").strip().rstrip("/.,;:)")
    recipe_limit = ""
    match = re.search(r":\d+$", path_text)
    if match:
        path_text = path_text[: match.start()]
        recipe_limit = match.group(0)
    name = path_text.split("/")[-1] or "path"
    if len(name.split()) > 3:
        name = "path"
    return f"<local-path:{name}>{recipe_limit}"
