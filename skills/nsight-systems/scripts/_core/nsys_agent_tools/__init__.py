"""Shared Nsight Systems agent-tool implementation.

Keep this package import dependency-light. Report, recipe, and BYO CLI helpers
must remain usable without installing optional report dependencies, so the
package root stays safe for the vendored BYO script core.

Module map for maintainers:

- ``agent_cli.py``: ``nsys_skill_cli`` JSON CLI entry point.
- ``agent_gateway.py``: portable JSON command contract vendored into the pack.
- ``tool_registry.py`` / ``tool_service.py``: tool contract metadata and the
  shared implementation used by the CLI, packaged scripts, and eval.
- ``recipe/``: public recipe facade plus focused recipe lookup, execution,
  output, preview, and safety helpers.
- ``report.py`` plus ``reporting/``: public report facade and the report
  loading, Parquet/DuckDB, query, fact, and doctor subsystem.
- ``capability/`` and ``guardrails/``: reviewed product boundaries and
  evidence checks; keep these small and policy-focused.
- ``docs.py``, ``schema_reference.py``, ``search.py``, and ``skill_pack.py``:
  skill-pack reference loading and retrieval helpers.

The package intentionally keeps subpackages shallow. Add another nesting level
only when a cluster develops real internal subgroups with a clear owner and
benefit.
"""

from __future__ import annotations

__all__: list[str] = []
