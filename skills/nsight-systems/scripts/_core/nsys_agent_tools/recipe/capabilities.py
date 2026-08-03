"""Recipe capability metadata exposed to agents.

This module does not choose a recipe from user text and it does not encode
recipe-specific answer logic. It turns installed/packaged recipe metadata into a
small contract that tells adapters what is safe to do with a recipe: look it up,
run it through runtime-owned paths, then inspect/query generated outputs.
"""

from __future__ import annotations

from typing import Any

RECIPE_CAPABILITY_SCHEMA = "nsys-recipe-capability-v1"


def recipe_capability_summary(
    entry: dict[str, Any],
    *,
    live_options: set[str] | list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Return the stable recipe contract inferred from recipe metadata.

    The fields are deliberately generic. They avoid hard-coding concepts such
    as "overlap" into Python. Official recipes own their analysis logic; report
    SQL may inspect raw facts, and recipe-output SQL may inspect files generated
    by a recipe run.

    Callers may pass an ``expected_outputs`` list in ``entry`` when those
    filenames were literally present in packaged recipe metadata. This helper
    does not infer recipe outputs on its own.
    """

    options = _recipe_options(entry, live_options=live_options)
    text = str(entry.get("text", "")).lower()
    has_report_input = "--input" in options
    return {
        "schema": RECIPE_CAPABILITY_SCHEMA,
        "recipe": entry.get("name"),
        "source": entry.get("source", "packaged"),
        "evidence_posture": entry.get("evidence_posture", "installed-recipe-metadata"),
        "execution": {
            "requires_report_input": has_report_input,
            "runtime_controls_input_output": True,
            "accepts_directory_input": _accepts_directory_input(text),
            "exact_output_files_require_execution": True,
        },
        "output": {
            "known_options": sorted(options),
            "common_outputs": list(entry.get("expected_outputs") or []),
            "schema_after_run": "Use recipe-output-schema on the returned handle/label.",
            "query_after_run": "Use recipe-output-query against generated output tables only.",
        },
        "analysis_boundary": recipe_analysis_boundary(),
    }


def recipe_run_contract(recipe: str) -> dict[str, Any]:
    """Return the contract attached to an executed recipe payload."""

    return {
        "schema": RECIPE_CAPABILITY_SCHEMA,
        "recipe": recipe,
        "source": "official-nsys-recipe-execution",
        "analysis_boundary": recipe_analysis_boundary(),
        "followup": {
            "inspect_outputs": "Use the returned output_handle/output_label with recipe-output-schema.",
            "query_outputs": "Use recipe-output-query for bounded SQL over generated recipe outputs.",
            "do_not_use_local_paths": True,
        },
    }


def recipe_analysis_boundary() -> dict[str, Any]:
    """Return the durable recipe-vs-SQL boundary."""

    return {
        "recipe_owns_complex_analysis_semantics": True,
        "do_not_replace_recipe_with_ad_hoc_report_sql": True,
        "report_sql_scope": "bounded factual inspection of raw report tables",
        "recipe_output_sql_scope": "bounded inspection of files produced by an executed recipe",
    }


def _recipe_options(
    entry: dict[str, Any],
    *,
    live_options: set[str] | list[str] | tuple[str, ...] | None,
) -> set[str]:
    options = {str(option) for option in entry.get("options", []) if str(option).startswith("--")}
    if live_options is not None:
        options |= {str(option) for option in live_options if str(option).startswith("--")}
    return options


def _accepts_directory_input(text: str) -> bool:
    # This mirrors the wording generated from the installed recipe input parser.
    # If the parser/docs wording changes, prefer returning False over inventing
    # directory support from broad terms such as "directory".
    return "directories can optionally be followed by ':n'" in text
