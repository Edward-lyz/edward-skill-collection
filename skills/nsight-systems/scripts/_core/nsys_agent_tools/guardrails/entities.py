"""Entity extraction used by guardrail checks.

The entity index is built from live ``nsys`` help and packaged recipe metadata;
it is not a natural-language router. Guardrails use it only to verify exact
flags, recipe names, environment variables, and recipe-owned semantic concepts.
"""

from __future__ import annotations

from contextlib import suppress

from ..cli_tools import NsysCli
from ..recipe.metadata import normalize_recipe_owned_concepts
from ..skill_pack import SkillPack
from .types import EntityIndex


def build_entity_index(pack: SkillPack, cli: NsysCli) -> EntityIndex:
    # `--help` is accepted by every nsys help target even when a specific
    # command's rendered help omits it from the option table. Treat it as a
    # globally-known flag so the claim checker does not reject the canonical
    # discovery command `nsys recipe --help`.
    flags: set[str] = {"help"}
    for target in ("", "profile", "launch", "start", "stop", "status", "stats", "export", "recipe"):
        payload = cli.help(target, max_chars=30000)
        if payload.get("ok"):
            flags.update(str(flag).lstrip("-") for flag in payload.get("flags", []))
    recipes = {str(entry.get("name")) for entry in pack.recipes_index if entry.get("name")}
    with suppress(Exception):
        recipes.update(cli.recipes().keys())
    for entry in pack.recipes_index:
        flags.update(str(flag).lstrip("-") for flag in entry.get("options", []) if flag)
    return EntityIndex(
        flags=frozenset(flags),
        recipes=frozenset(recipes),
        recipe_owned_concepts=_recipe_owned_concepts(pack),
    )


def _recipe_owned_concepts(pack: SkillPack) -> tuple[tuple[tuple[str, ...], ...], ...]:
    """Load recipe-owned semantic concepts from packaged recipe metadata.

    Some report concepts are not safe to classify from raw tables alone because
    the installed recipe defines the filtering/classification semantics. The
    skill builder promotes those release-varying concepts into
    ``indexes/recipes.json``; runtime guardrails only consume that reviewed
    metadata.
    """

    concepts: list[tuple[tuple[str, ...], ...]] = []
    for entry in pack.recipes_index:
        concepts.extend(normalize_recipe_owned_concepts(entry.get("recipe_owned_concepts")))
    return tuple(dict.fromkeys(concepts))
