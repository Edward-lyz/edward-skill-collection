"""Structured unsupported-capability contract for Nsight Systems AI capabilities.

This module is intentionally a *negative* capability planner, not a
natural-language router.  It answers one question: "Would an apparently helpful
answer be outside the supported Nsight Systems product/skill contract?"

The important design choice is that product policy is represented as structured
capability specs.  Text patterns are low-level signals that help detect a
request shape; they do not decide the boundary on their own.
Positive behavior should come from evidence tools, recipe metadata, generated
docs, deterministic report facts, and bounded SQL.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CapabilityBoundary:
    code: str
    message: str
    answer: str


@dataclass(frozen=True)
class BoundaryContext:
    """Inputs available to product-level unsupported-capability planning."""

    question: str
    report_loaded: bool
    report_count: int | None
    report_table_names: tuple[str, ...] | None


@dataclass(frozen=True)
class EvidenceRequirement:
    """Evidence class the planner expects for supported answers."""

    kind: str
    reason: str


@dataclass(frozen=True)
class CapabilityPlan:
    """Structured capability decision for a user turn."""

    boundary_codes: tuple[str, ...]
    evidence_requirements: tuple[EvidenceRequirement, ...]
    matched_signals: tuple[str, ...]


@dataclass(frozen=True)
class TextSignal:
    """High-precision request signal used by the capability contract.

    Signals are allowed to use regex because they identify concrete language
    features.  They should stay broad, reviewed, and stable; do not add
    question-specific patterns to satisfy one eval row.
    """

    name: str
    pattern: re.Pattern[str]
    rationale: str

    def matches(self, text: str) -> bool:
        return bool(self.pattern.search(text or ""))


@dataclass(frozen=True)
class BoundaryGate:
    """Context gates for a capability boundary.

    Gates keep request text separate from required runtime evidence shape.  This
    is what prevents text signals from becoming the full policy engine.
    """

    report_loaded: bool | None = None
    report_count: int | None = None
    missing_table_family: str | None = None

    def matches(self, ctx: BoundaryContext) -> bool:
        if self.report_loaded is not None and ctx.report_loaded is not self.report_loaded:
            return False
        if self.report_count is not None and ctx.report_count != self.report_count:
            return False
        if self.missing_table_family:
            if ctx.report_table_names is None:
                return False
            return not has_table_family(ctx.report_table_names, self.missing_table_family)
        return True


TABLE_FAMILY_PREFIXES = {
    "gpu_metrics": ("GPU_METRICS",),
    "osrt": ("OSRT", "OS_RUNTIME"),
}


def has_table_family(table_names: Iterable[str], family: str) -> bool:
    """Return whether a loaded report exposes a known semantic table family."""

    prefixes = TABLE_FAMILY_PREFIXES.get(family.lower(), ())
    return any(str(name).upper().startswith(prefixes) for name in table_names)


@dataclass(frozen=True)
class CapabilityBoundarySpec:
    """Reviewed unsupported-capability policy entry.

    Each entry has product intent (`category`, `status`, `rationale`) plus the
    minimal signals/context gates needed to detect the unsupported request.  The
    examples are for maintainer review and tests; they are not used as a
    nearest-neighbor answer map.
    """

    code: str
    category: str
    status: str
    rationale: str
    message: str
    answer: str
    required_signals: tuple[str, ...]
    excluded_signals: tuple[str, ...] = ()
    gate: BoundaryGate = field(default_factory=BoundaryGate)
    preflight: bool = True
    exclude_when: str | None = None
    allowed_examples: tuple[str, ...] = ()
    blocked_examples: tuple[str, ...] = ()

    def boundary(self) -> CapabilityBoundary:
        return CapabilityBoundary(code=self.code, message=self.message, answer=self.answer)

    def matches(self, ctx: BoundaryContext, matched_signals: frozenset[str]) -> bool:
        return (
            self.gate.matches(ctx)
            and all(signal in matched_signals for signal in self.required_signals)
            and not any(signal in matched_signals for signal in self.excluded_signals)
            and not _matches_exclusion(ctx, self.exclude_when)
        )


def _matches_exclusion(ctx: BoundaryContext, name: str | None) -> bool:
    if name is None:
        return False
    if name == "ncu_conceptual_handoff_without_execution":
        return asks_ncu_conceptual_handoff_without_execution(ctx.question)
    raise ValueError(f"unknown capability exclusion gate: {name}")


def asks_ncu_conceptual_handoff_without_execution(text: str) -> bool:
    """Return True for NCU guidance requests that do not ask the agent to run NCU."""

    lower = text.lower()
    mentions_ncu = re.search(r"\b(ncu|nsight\s+compute)\b", lower) is not None
    if not mentions_ncu:
        return False
    asks_assistant_to_execute = re.search(
        r"\b(can|could|would|will|please)\s+you\b.{0,80}\b(run|launch|execute|profile|collect)\b"
        r".{0,80}\b(ncu|nsight\s+compute)\b|"
        r"\b(run|launch|execute|profile|collect)\b.{0,80}\b(ncu|nsight\s+compute)\b"
        r".{0,80}\b(for\s+me|from\s+this\s+runtime)\b",
        lower,
    ) is not None
    if asks_assistant_to_execute:
        return False
    return re.search(
        r"\b(workflow|when|whether|should|decid(?:e|ing)|handoff|candidate|which\s+kernel|inspect|"
        r"should\s+i\s+(?:run|profile|collect)|should\s+we\s+(?:run|profile|collect))\b",
        lower,
    ) is not None
