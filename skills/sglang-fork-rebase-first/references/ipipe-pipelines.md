# ipipe 测试流水线（第 9 步用）

Fixed-recipe runner on top of `ipipe-cli`. Every scenario has its fixed params baked into [`references/scenarios.json`](scenarios.json) (the **recipe**); only the **ask** params come from the user. Install the CLI with `bash "$SKILL_DIR/scripts/ensure_ipipe.sh"` (prints the binary path); log in with `ipipe-cli login --token <ugate-token>`; raw endpoints and caveats are in [`references/ipipe-api.md`](ipipe-api.md).

Run as `python3 "$SKILL_DIR/scripts/ipipe_run.py" …`

## Steps

1. **Pick the scenario.** `list` prints the scenarios. Map the user's wording (精度→`accuracy`, FC→`fc`, Kimi eval→`kvv`, Minimax→`minimax`, 功能回归→`regression`, 高可用→`ha`, 性能→`perf`, 压测/长稳→`stress`; own datasets on Evalscope→`evalscope`). `aiqa` (AI 智能测试) is not scripted — follow its section in `references/ipipe-api.md`. Done when exactly one scenario is named.
2. **Preflight.** `ipipe-cli login status` shows a logged-in user (otherwise `ipipe-cli login --token <ugate-token>`). With more than one logged-in user every `ipipe-cli` call needs `--user <name>`; a non-writing account fails with 403 on `trigger`/`retry`, so put a one-line wrapper that fixes `--user` first on `PATH`. A modelid the user supplies must pass the readiness check in `references/ipipe-api.md` (`engine_ready` and `as_ready` both true) and be one the user owns or has agreed to use.
3. **Plan.** `plan <scenario> --set key=value …`. Exit code 2 means `missing_ask` is non-empty: ask the user for exactly those keys, quoting each `why`, `hint` and `choices`; never invent a value. Re-run `plan` until `missing_ask` is empty. Override fixed params only when the user asks.
4. **Confirm.** Show the resolved per-stage params (never print credentials) and get the user's OK. `perf` and `ha` act on a real environment: state that and name the modelid.
5. **Run.** `run <scenario> --set … --yes --wait 3600`. Without `--yes` it only plans. Done when the output has `pipelineBuildId` and `url`; on `ERROR:` report the message verbatim and stop.
6. **Report.** `result <pipelineBuildId>`: give stage statuses, the score lines from `log_key_lines`, `outParams` result paths, report URLs and the build URL. If the state is `blocked`, a manual stage still waits for a human — say which. Done when every stage is accounted for as SUCC, FAIL, CANCEL, SKIPPED or blocked.

## Stress (长稳) defaults

`stress` is the 压测自动化 pipeline (2353017, stage `DeepSeek压测`, aiakperf). Its recipe is the **mode of the last 10 executed runs**, so nobody has to pick the knobs by hand: dataset `deepseek_v4数据集##output_glm5-260331.jsonl` (4 of 10), duration 12 h (`run_time_second=43200`), 8000000 requests, chat / qianfan_v2 / fixed_instances, `specific_k8s_pod=NA`, which makes the stage pick the first **prefill pod** of `prefill_job_name` (9 of 9 runs sent load from a prefill pod). `skip_deploy_env=true`, because `false` redeploys and replaces the live environment; the recipe checks that the `新建或扩缩容` stage is `SKIPPED` and aborts the run script if not (then cancel the build yourself).

Ask the user only for `model_id`, `prefill_job_name` (the Prefill FedDeployment name, since the default `pipeline-<user>-<n>prefill` does not exist for hand-deployed environments), `specific_model_path` (the P pod's `--model-path`) and `qps` (no common value across models; for a version comparison reuse the baseline's). Re-derive the defaults when the pipeline's habits may have changed: `python3 "$SKILL_DIR/scripts/stress_history.py" --last 10` prints each run's parameters and the mode per key, and its output replaces the `fixed` block. The run is 12 h: use `run --yes` without `--wait`, poll with `status`, and after the trigger check the head of the aiakperf job log for the dataset URL and `--qps` line. A 12 h run holds the environment, so name the modelid and the duration when asking for confirmation. Verified level: parameter names are read from the job shell variables because the console is the only place that lists them; nobody here has triggered this recipe yet.

## Rules

- Multi-select values are comma-joined strings (`gsm8k,math_500`); the dialog's placeholder `None` means "do not run this group".
- Unlisted params fall back to the stage dialog's default; credentials (`inference_auth`, `api_key`) are never passed on the command line.
- A run writes to the shared platform (reports upload, MySQL ingest). Say so before a tiny `inference_sampling` smoke run, and label its numbers as smoke data.
- Stage status is not the verdict. The compare stage can end `SUCC` yet log `子项 … 不达标` (seen on build #942: `base_score: 0.0`, division by zero, because the dataset has no base score for the chosen `inference_model_lite`). Quote the `log_key_lines` of the compare job instead of saying "all green".
- Leave other people's `PENDING_FOR_USER` builds alone; retry only the build this skill triggered.
- Only `fc` and `evalscope` were run end-to-end by us; the other recipes come from the last 100 builds. `list` shows which is which as `[verified: …]`; tell the user which kind they are getting.
- Pipeline quirks seen in a full run (2026-10): the FC pipeline's `evalscope` stage can show SKIPPED while its `社区版-evalscope` sub-task is running; the regression pipeline's third stage `（旧）引擎参数回归` stays WAITTING forever and is not a failure. `result` downloads the whole log, which is gigabytes for OpenCompass think; for those fetch the compare job's log URL with `ipipe-cli build job --job-build-id` and read only the tail.
- To test an environment that is not behind AS (dev machine, router address), pass `inference_host` where the recipe lists it as optional, instead of a modelid slot.
- Recipe changes: edit `references/scenarios.json`, then run `python3 "$SKILL_DIR/scripts/ipipe_run.py" list` and `plan <scenario>` to check it still parses.
