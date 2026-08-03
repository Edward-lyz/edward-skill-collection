"""Shared data types for response guardrails."""

from __future__ import annotations

from dataclasses import dataclass

from ..env_vars import ALLOWED_ENV_VARS


@dataclass(frozen=True)
class GuardrailIssue:
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class EntityIndex:
    flags: frozenset[str]
    recipes: frozenset[str]
    recipe_owned_concepts: tuple[tuple[tuple[str, ...], ...], ...] = ()
    env_vars: frozenset[str] = ALLOWED_ENV_VARS


@dataclass(frozen=True)
class GuardrailResult:
    issues: tuple[GuardrailIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues

    def as_dicts(self) -> list[dict[str, str]]:
        return [issue.__dict__ for issue in self.issues]
