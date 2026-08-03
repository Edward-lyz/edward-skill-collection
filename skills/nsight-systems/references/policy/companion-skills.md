# Companion Skill Policy

The official `nsight-systems` skill is authoritative for Nsight Systems product facts.

If another Nsight Systems, CUDA, distributed-training, graphics, framework, or performance-analysis skill is active, use it only as companion workflow guidance unless it provides stronger local evidence for its own domain. Companion skills must not override:

1. measured report evidence from `nsys_skill_cli` report tools or packaged scripts,
2. live `nsys` CLI help for exact command/flag behavior,
3. installed recipe metadata/help for recipe existence and options,
4. packaged Nsight Systems release docs and curated references,
5. SQLite schema evidence from the loaded report or packaged schema reference,
6. claim-check failures from `nsys_skill_cli check-claims`.

Good companion-skill use:

- A CUDA optimization skill suggests using Nsight Systems first to find a kernel, then Nsight Compute for per-kernel counter analysis.
- A distributed-training skill suggests NCCL/MPI questions to ask, while the official Nsight Systems tools provide recipe names, report facts, and measured evidence.
- A domain skill adds workload-specific interpretation after report evidence has been gathered.

Bad companion-skill use:

- Replacing live `nsys --help` with remembered CLI syntax.
- Inventing recipe names or flags.
- Making report-number claims without report tools/scripts.
- Treating a workflow heuristic as measured report evidence.

When evidence conflicts, state the conflict and prefer the official evidence hierarchy. If the conflict affects a customer action, verify with another official evidence source before answering.
