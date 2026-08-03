"""Validation for recipe-specific command-line arguments.

The runtime owns recipe input/output paths. These helpers only pass through
recipe-specific flags that live help exposes and that do not redirect files.
"""

from __future__ import annotations

import re

PATH_CONTROL_FLAGS = frozenset({"--input", "-i", "--output", "-o", "--output-dir", "--export-dir"})
INLINE_VALUE_FORBIDDEN_FLAGS = frozenset({"--csv"})

# Recipe extra args are intentionally conservative.  Even when live help lists a
# flag, path-like/output-like names can redirect data away from runtime-owned
# report/output/cache paths.  Keep this as a small reviewed safety boundary, not
# as a growing answer router.
PATHISH_FLAG_WORDS = ("output", "export", "dir", "path", "file", "save", "write")
PATHISH_FLAG_ALLOWLIST = frozenset({"--force-overwrite"})


def sanitize_extra_args(
    tokens: list[str],
    *,
    allowed_flags: set[str] | None = None,
    value_taking_flags: set[str] | None = None,
) -> list[str]:
    """Return recipe extra arguments that cannot override runtime-owned paths."""

    tokens = normalize_extra_args(tokens)
    out: list[str] = []
    expecting_value = False
    blocked_prefixes = tuple(f"{flag}=" for flag in PATH_CONTROL_FLAGS)
    for token in tokens:
        if expecting_value:
            if token.startswith("-") and not looks_like_negative_number(token):
                raise ValueError("missing value before next flag")
            out.append(token)
            expecting_value = False
            continue
        if token in PATH_CONTROL_FLAGS:
            raise ValueError(f"{token} is controlled by the runtime")
        if token.startswith(blocked_prefixes):
            raise ValueError(f"{token.split('=', 1)[0]} is controlled by the runtime")
        if token.startswith("-"):
            flag = token.split("=", 1)[0]
            if (
                flag not in PATHISH_FLAG_ALLOWLIST
                and any(word in flag.lower() for word in PATHISH_FLAG_WORDS)
            ):
                raise ValueError(f"{flag} is not allowed through extra_args")
            if allowed_flags is not None and flag not in allowed_flags:
                raise ValueError(f"{flag} is not in live help for this recipe")
            if "=" in token and flag in INLINE_VALUE_FORBIDDEN_FLAGS:
                raise ValueError(f"{flag} does not take an inline value")
            out.append(token)
            if "=" in token:
                expecting_value = False
            elif value_taking_flags is not None:
                expecting_value = flag in value_taking_flags
            else:
                expecting_value = flag not in INLINE_VALUE_FORBIDDEN_FLAGS
            continue
        raise ValueError(f"unexpected positional argument {token!r}")
    if expecting_value:
        raise ValueError("missing value for final flag")
    return out


def normalize_extra_args(tokens: list[str]) -> list[str]:
    """Drop an argparse ``--`` separator before recipe-specific arguments."""

    if tokens[:1] == ["--"]:
        return tokens[1:]
    return list(tokens)


def first_path_control_arg(tokens: list[str]) -> str:
    """Return the first recipe argument that would override runtime paths."""

    for token in normalize_extra_args(tokens):
        if token in PATH_CONTROL_FLAGS:
            return token
        if token.startswith(tuple(f"{flag}=" for flag in PATH_CONTROL_FLAGS)):
            return token.split("=", 1)[0]
    return ""


def looks_like_negative_number(token: str) -> bool:
    return bool(re.fullmatch(r"-\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", token))


def value_taking_flags_from_help(help_text: str) -> set[str]:
    """Infer which live recipe flags take values from argparse help text."""

    value_taking: set[str] = set()
    for raw_line in help_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        synopsis = re.split(r"\s{2,}", line, maxsplit=1)[0]
        for part in synopsis.split(","):
            match = re.match(r"(?P<flag>--[A-Za-z0-9][A-Za-z0-9-]*|-[A-Za-z0-9])(?P<trailer>.*)", part.strip())
            if match and match.group("trailer").strip():
                value_taking.add(match.group("flag"))
    return value_taking
