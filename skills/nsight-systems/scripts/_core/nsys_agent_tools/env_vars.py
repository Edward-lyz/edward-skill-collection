"""Shared environment-variable policy for Nsight Systems AI helpers."""

from __future__ import annotations

import os
from collections.abc import Mapping

from .defaults import (
    NSYS_AGENT_CACHE_DIR_ENV,
    NSYS_AGENT_RECIPE_OUTPUT_DIR_ENV,
    NSYS_AGENT_REPORT_ROOTS_ENV,
    NSYS_AGENT_SKILL_PACK_ENV,
)

NVIDIA_INFERENCE_KEY_ENV = "NVIDIA_INFERENCE_KEY"

# The claim checker accepts the union of user and developer/eval variables
# below. The split is for reviewer navigation only; it is not a runtime policy
# boundary.
#
# Keep the user-facing set small and product-related. Broadening it weakens the
# claim checker and response guardrails.
_USER_ENV_VARS = {
    "NSYS_PATH",
    "NSYS_RECIPE_PATH",
    NSYS_AGENT_SKILL_PACK_ENV,
    NSYS_AGENT_CACHE_DIR_ENV,
    NSYS_AGENT_RECIPE_OUTPUT_DIR_ENV,
    NSYS_AGENT_REPORT_ROOTS_ENV,
    "NSYS_TMPDIR",
    "CUDA_VISIBLE_DEVICES",
    "CUDA_DEVICE_ORDER",
    "CUDA_HOME",
    "PATH",
    "HOME",
    "TMPDIR",
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "OMP_NUM_THREADS",
}

# Developer/eval/CI names are allowed so repo-maintenance answers can cite
# documented setup without tripping unknown-env guardrails. Keep this list
# reviewer-owned; do not add arbitrary CI scratch variables.
_DEVELOPER_ENV_VARS = {
    NVIDIA_INFERENCE_KEY_ENV,
    "PYTHONPATH",
    "NSYS_DOCS_ROOT",
    "NSYS_BINARY",
    "NSYS_TARBALL_URL",
    "NSYS_AGENT_ALLOW_FORK_DUCKDB_WORKER",
    "NV_BASE_INDEX_URL",
}

ALLOWED_ENV_VARS = frozenset(_USER_ENV_VARS | _DEVELOPER_ENV_VARS)


def nvidia_inference_key(environ: Mapping[str, str] | None = None) -> str:
    """Return the configured NVIDIA inference key.

    ``NVIDIA_INFERENCE_KEY`` is the single supported environment variable for
    NV-BASE/ACES Tier 3 eval model access.
    """

    env = environ if environ is not None else os.environ
    return env.get(NVIDIA_INFERENCE_KEY_ENV, "")
