"""Path redaction for recipe commands and process diagnostics."""

from __future__ import annotations

from pathlib import Path

from ..prompt_safety import sanitize_text


def redact_error(
    exc: BaseException,
    *,
    report_path: Path,
    recipe_input: Path | None = None,
    recipe_out: Path,
    recipe_export: Path | None = None,
) -> str:
    raw = f"{type(exc).__name__}: {exc}"
    return redact_text(
        raw,
        report_path=report_path,
        recipe_input=recipe_input,
        recipe_out=recipe_out,
        recipe_export=recipe_export,
    )


def redact_command(
    args: list[str],
    *,
    report_path: Path,
    recipe_input: Path | None = None,
    recipe_out: Path,
    recipe_export: Path | None = None,
) -> list[str]:
    return [
        redact_text(
            arg,
            report_path=report_path,
            recipe_input=recipe_input,
            recipe_out=recipe_out,
            recipe_export=recipe_export,
        )
        for arg in args
    ]


def redact_process_text(
    text: str,
    *,
    report_path: Path,
    recipe_input: Path | None = None,
    recipe_out: Path,
    recipe_export: Path | None = None,
) -> str:
    """Keep both early and late diagnostics from recipe stdout/stderr."""

    if len(text) > 8000:
        text = text[:2000] + "\n... (truncated middle; kept start and end for diagnostics) ...\n" + text[-5800:]
    return redact_text(
        text,
        report_path=report_path,
        recipe_input=recipe_input,
        recipe_out=recipe_out,
        recipe_export=recipe_export,
        max_chars=8000,
    )


def redact_text(
    text: str,
    *,
    report_path: Path,
    recipe_input: Path | None = None,
    recipe_out: Path,
    recipe_export: Path | None = None,
    max_chars: int = 8000,
) -> str:
    if not text:
        return text
    redacted = text.replace(str(report_path), "<loaded-report>")
    if recipe_input is not None:
        redacted = redacted.replace(str(recipe_input), "<loaded-report>")
    if recipe_export is not None:
        redacted = redacted.replace(str(recipe_export), "<recipe-export>")
    redacted = redacted.replace(str(recipe_out), "<recipe-output>")
    redacted = redacted.replace(str(recipe_out.parent), "<recipe-output-root>")
    return sanitize_text(redacted, max_chars=max_chars)
