"""Shared recipe metadata contract helpers."""

from __future__ import annotations

from pathlib import Path

RecipeOwnedConcept = tuple[tuple[str, ...], ...]


def normalize_expected_outputs(raw: object) -> list[dict[str, str]]:
    """Return valid recipe output declarations from generated metadata."""

    outputs: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return outputs
    for item in raw:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            continue
        payload: dict[str, str] = {"path": path.strip()}
        description = item.get("description")
        if isinstance(description, str) and description.strip():
            payload["description"] = description.strip()
        outputs.append(payload)
    return outputs


def normalize_recipe_owned_concepts(raw: object) -> tuple[RecipeOwnedConcept, ...]:
    """Return valid recipe-owned concept groups from generated metadata."""

    if not isinstance(raw, list):
        return ()
    concepts: list[RecipeOwnedConcept] = []
    for concept in raw:
        if not isinstance(concept, list):
            continue
        groups: list[tuple[str, ...]] = []
        for group in concept:
            if not isinstance(group, list):
                continue
            words = tuple(
                dict.fromkeys(
                    item.strip().lower()
                    for item in group
                    if isinstance(item, str) and item.strip()
                )
            )
            if words:
                groups.append(words)
        if len(groups) >= 2:
            concepts.append(tuple(groups))
    return tuple(dict.fromkeys(concepts))


def recipe_owned_concepts_json(raw: object) -> list[list[list[str]]]:
    """Return recipe-owned concepts in JSON-serializable index form."""

    return [[list(group) for group in concept] for concept in normalize_recipe_owned_concepts(raw)]


def unsafe_recipe_artifact_path(path: str) -> bool:
    """Return whether an indexed recipe artifact path can escape output scope."""

    value = path.strip()
    return (
        not value
        or Path(value).is_absolute()
        or value.startswith("../")
        or "/../" in value
        or value.endswith("/..")
        or value == ".."
    )
