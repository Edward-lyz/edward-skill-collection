---
name: ipipe-run-pipeline
description: Use when the user wants to run a QA pipeline in baidu/bcc-test/ds_test and get its result — accuracy (OpenCompass), FC / Evalscope, Kimi eval (KVV), Minimax eval, functional regression, high availability, performance.
---

Fixed-recipe runner on top of `ipipe-cli`. Every scenario has its fixed params baked into [`references/scenarios.json`](references/scenarios.json) (the **recipe**); only the **ask** params come from the user. CLI install, login and command semantics live in the `ipipe-official` skill; raw endpoints and caveats are in [`references/api.md`](references/api.md).

Run from this skill's directory: `python3 scripts/ipipe_run.py …`

## Steps

1. **Pick the scenario.** `list` prints the scenarios. Map the user's wording (精度→`accuracy`, FC→`fc`, Kimi eval→`kvv`, Minimax→`minimax`, 功能回归→`regression`, 高可用→`ha`, 性能→`perf`; own datasets on Evalscope→`evalscope`). `aiqa` (AI 智能测试) is not scripted — follow its section in `api.md`. Done when exactly one scenario is named.
2. **Preflight.** `ipipe-cli login status` shows a logged-in user (otherwise follow `ipipe-official`). A modelid the user supplies must pass the readiness check in `api.md` (`engine_ready` and `as_ready` both true) and be one the user owns or has agreed to use.
3. **Plan.** `plan <scenario> --set key=value …`. Exit code 2 means `missing_ask` is non-empty: ask the user for exactly those keys, quoting each `why`, `hint` and `choices`; never invent a value. Re-run `plan` until `missing_ask` is empty. Override fixed params only when the user asks.
4. **Confirm.** Show the resolved per-stage params (never print credentials) and get the user's OK. `perf` and `ha` act on a real environment: state that and name the modelid.
5. **Run.** `run <scenario> --set … --yes --wait 3600`. Without `--yes` it only plans. Done when the output has `pipelineBuildId` and `url`; on `ERROR:` report the message verbatim and stop.
6. **Report.** `result <pipelineBuildId>`: give stage statuses, the score lines from `log_key_lines`, `outParams` result paths, report URLs and the build URL. If the state is `blocked`, a manual stage still waits for a human — say which. Done when every stage is accounted for as SUCC, FAIL, CANCEL, SKIPPED or blocked.

## Rules

- Multi-select values are comma-joined strings (`gsm8k,math_500`); the dialog's placeholder `None` means "do not run this group".
- Unlisted params fall back to the stage dialog's default; credentials (`inference_auth`, `api_key`) are never passed on the command line.
- A run writes to the shared platform (reports upload, MySQL ingest). Say so before a tiny `inference_sampling` smoke run, and label its numbers as smoke data.
- Stage status is not the verdict. The compare stage can end `SUCC` yet log `子项 … 不达标` (seen on build #942: `base_score: 0.0`, division by zero, because the dataset has no base score for the chosen `inference_model_lite`). Quote the `log_key_lines` of the compare job instead of saying "all green".
- Leave other people's `PENDING_FOR_USER` builds alone; retry only the build this skill triggered.
- Only `fc` and `evalscope` were run end-to-end by us; the other recipes come from the last 100 builds. `list` shows which is which as `[verified: …]`; tell the user which kind they are getting.
- Recipe changes: edit `scenarios.json`, then run `python3 -m unittest test_ipipe_run` inside `scripts/`.
