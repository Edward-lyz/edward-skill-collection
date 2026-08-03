"""Reviewed capability-boundary contracts.

This package describes product-level supported and unsupported areas. It is not
an answer router: runtime code consults these boundaries to decline or scope
requests that the current Nsight Systems tools cannot verify safely.
"""

from __future__ import annotations

from .boundaries import (
    acknowledges_boundary,
    asks_custom_recipe_full_implementation,
    boundary_answer,
    capability_specs,
)
from .contract import BoundaryGate, CapabilityBoundarySpec, TextSignal

__all__ = [
    "BoundaryGate",
    "CapabilityBoundarySpec",
    "TextSignal",
    "acknowledges_boundary",
    "asks_custom_recipe_full_implementation",
    "boundary_answer",
    "capability_specs",
]
