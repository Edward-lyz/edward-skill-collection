"""Public recipe API facade for lookup, execution, and output inspection.

The implementation is split across focused modules so future recipe changes do
not couple lookup/ranking, subprocess execution, output-handle state, and preview
logic. Keep public imports here for the CLI and BYO scripts.
"""

from __future__ import annotations

from .execution import run_recipe
from .lookup import expected_outputs, lookup_recipes, recipe_match_summary
from .outputs import RecipeOutputRef, RecipeOutputStore
from .preview import MAX_RECIPE_OUTPUT_FILES, inspect_recipe_output

__all__ = [
    "MAX_RECIPE_OUTPUT_FILES",
    "RecipeOutputRef",
    "RecipeOutputStore",
    "expected_outputs",
    "inspect_recipe_output",
    "lookup_recipes",
    "recipe_match_summary",
    "run_recipe",
]
