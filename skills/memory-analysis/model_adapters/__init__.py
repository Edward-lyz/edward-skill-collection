"""Model adapter registry package.

Importing this package registers all bundled adapters so `get_adapter("kimi_k3")`
works without the caller knowing the module layout.
"""

from .base import (  # noqa: F401
    MapEntry,
    ModelAdapter,
    get_adapter,
    register,
)

# Register bundled adapters (import for side effect).
from . import kimi_k3  # noqa: F401,E402

__all__ = ["MapEntry", "ModelAdapter", "get_adapter", "register"]
from . import glm_5_2_fp8_20260616  # noqa: F401,E402  (auto-registered)
from . import glm_5_next_0808_20260820  # noqa: F401,E402  (auto-registered)
