# Capability Boundaries

Decline in-domain requests when the requested answer would be misleading from available evidence.

Use a short State-Reason-Next shape:

1. State what cannot be concluded or performed.
2. Explain why the available evidence/tool is insufficient.
3. Offer a concrete next step.

## Destructive or out-of-skill actions

- Do not delete caches, recipe outputs, workspaces, or local files. Explain safe cleanup concepts if useful, but do not run the cleanup through this skill.
- Do not edit or patch source code. Suggest where NVTX annotations would help and show illustrative patterns, but source edits belong to a separate code-editing workflow.
- Do not launch or profile arbitrary user applications from this skill. Provide an `nsys profile ...` command and ask for the resulting native `.nsys-rep`.
- Do not generate complete ready-to-run custom recipes or all recipe files. You may explain official authoring concepts and review user-provided code, metadata, or errors.
- Do not operate the Nsight Systems GUI for the user. Identify timeline objects or time ranges from report evidence, but do not open, click, zoom, or select GUI items on the user's behalf.

## External local-file and path boundaries

- Do not read arbitrary host files or inspect external local files such as `/etc/passwd`.
- Do not use DuckDB/SQLite features such as `ATTACH`, `read_csv_auto('/path')`, or arbitrary recipe-output paths.
- Use only loaded reports, report sessions, and recipe output labels.

## Cross-product handoff boundaries

- Do not run Nsight Compute (`ncu`) from this skill. Identify candidate kernels and provide the details the user needs to inspect them in Nsight Compute.
- Do not provide detailed Nsight Compute metric explanations or counter values such as Speed Of Light, `gpc__...` metrics, occupancy, register pressure, roofline, SASS, replay modes, warp sampling, or PM sampling from Nsight Systems evidence alone. Do not give even a brief, general, or practical definition from memory; hand off to Nsight Compute docs/tools.

## Evidence-shape boundaries

- Do not rank sampled GPU metrics across short NVTX ranges without a recipe or validated time-weighted method.
- Do not present exact overlap/correlation between sampled GPU metric points and kernel intervals unless a validated time-weighted recipe/workflow produced that evidence.
- Do not infer workload/model/algorithm identity from symbol names alone.
- Do not make root-cause claims without corroborating report evidence.
- Do not make exact support/version claims when docs/live help do not state them.
- Do not claim OS runtime/syscall conclusions when the loaded report has no OS runtime tables. Do not substitute profiler/CUPTI overhead as OS runtime evidence.
- Do not claim multi-hop function/API/kernel correlation without shared correlation evidence such as NVTX or correlation IDs.

## Scope and input-shape boundaries

- Do not rank competing profilers; offer factual Nsight Systems capability information instead.
- Do not compare ranks, runs, or reports when only one report is loaded. Load a report directory or multiple reports first.
- Do not use invalid help-command forms such as `nsys --help --some-flag`; use `nsys <command> --help` or live flag search instead.
