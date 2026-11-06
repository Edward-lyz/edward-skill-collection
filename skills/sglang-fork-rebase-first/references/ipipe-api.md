# API notes behind the recipes

Findings of 2026-10-09 on module `baidu/bcc-test/ds_test`, workspace 437066. Recipe values in `scenarios.json` are the dominant values of each pipeline's last ≤100 builds.

## ipipe-cli calls used by `ipipe_run.py`

| Step | Command | Notes |
|---|---|---|
| Start build | `trigger start --pipeline-id P --branch master` | returns `pipelineBuildId`; the compile stage runs, the next stage waits as `PENDING_FOR_USER` |
| Stage list | `build status --pipeline-build-id B` | stage `id` **changes after a retry** (observed 644734865 → 644808294), so re-find by name |
| Start manual stage | `build retry --stage-build-id S --param k=v …` | `POST /api/agile/v1/stageBuilds/build?stageBuildId=S`; body is the flat `{k: v}` map; `--param` overrides the dialog defaults |
| Job result | `build job --job-build-id J` | `pluginJobBuild.outParams`, `reports`, `logs[0].url` (logonline, plain GET) |

A stage with no `--param` runs on dialog defaults — for Evalscope that means every dataset group `None`, which finishes in ~20 s with no evaluation.

## Reading a stage's parameter definitions (types, options, defaults)

`ipipe-cli build stage` returns `manualParams: null`. The dialog uses another endpoint that only works inside a logged-in console session:

`GET /api/ipipe/pipeline/rest/v0/agile/pipeline/v1/stageBuild/{stageBuildId}/manualParams?isContinueBuild=false`

It returns `[{key, type: INPUT|SELECT|MULTIPLE, values:[{value, description}], defaultValue, description}]`. To refresh `choices` in `scenarios.json`: open the build page in the in-app browser, call that URL with `fetch` through CDP `Runtime.evaluate`, and read the JSON. Credentials appear in `defaultValue`; do not copy them.

Web submit (not used by the script): `POST /stage-builds/{id}/operation-requests`, body `{type: START|RESTART|SELECT|CONTINUE, userInput: {pipelineBuildId, jobBuildParams, manualParams, ignoreStrategy, useLatestVersion}}`. Multi-select values are comma-joined (`join(",")` in the front-end).

History used for the recipes: `GET /api/ipipe/pipeline/rest/v3/pipeline-builds?_limit=100&pipelineConfId=P` and, per build, `GET /api/ipipe/pipeline/rest/v10/pipeline-build/{id}?_embed=stageBuilds&isExtend=true` — each stage's `inParams` holds the values actually used (`triggerMode` tells MANUAL from UPSTREAM stages).

## Model readiness (before using any modelid)

AIQA service base: `http://10.11.159.198:8001` (from the vendor skill `inference-engine-aiqa-test-assistant/references/service_config.json`).

- `GET /api/v1/model/status?model_id=M` → `engine_ready` (prefill and decode pods Ready) and `as_ready` (AS gateway answers). Use only modelids where both are true; the call takes 20–60 s.
- `GET /api/v1/modelid/feddeployments` → modelid ↔ FedDeployment/owner map; `unused_model_ids` have no deployment.
- `GET /standard_task/v1?status=running&model=M` → tasks in flight on that slot. Do not start a second run on a busy slot: concurrent accuracy runs corrupt each other's scores.
- Chat probe through AS: `POST http://10.178.29.70:80/v2/chat/completions` with `Authorization` = the pipeline's own `inference_auth` default and `model=M`; thinking models spend `max_tokens` on `reasoning_content`, so a short probe can return empty `content` and still be healthy.
- Cluster view: `kubectl get feddeployments` on the `virtualMachine` dev machine (`MODEL_ID` env on each pod). Namespace `pd-test` is forbidden for the current account.

## AI 智能测试 (pipeline 3389971, scenario `aiqa`)

Not driven by stage retry. The AIQA service triggers it: `POST /standard_task/v1/trigger` (vendor script `trigger_pipeline.py`), body fields `model, stages, triggeredBy, branch, tasks, inferenceConcurrency, inferenceData, qps, perfTasks, stabilityTime, datasetName, datasetUrl, choiceCase, runType, inferenceHost, extra, prefillYamlPath, decodeYamlPath, encodeYamlPath, image, oldPrefillYamlPath, oldDecodeYamlPath`. `extra` passes pipeline variables through (real example: `{"inference_host": "http://…/v1/chat/completions"}`). The landing pipeline is decided by the service address, not by the request. Poll `GET /standard_task/v1/{task_id}`. Task vocabulary: OpenCompass `task_no_think|task_think|task_think_budget`, Evalscope `task_evalscope_fc_think|task_evalscope_fc_no_think|task_evalscope_video_no_think`, KVV `task_kvv_think|task_kvv_no_think`. `inference_model_lite`, temperature, top_p and thinking_budget are derived by the pipeline and cannot be set by the trigger.

Contract and rules: `aiak-loop` repo, `loop-design/aiqa-trigger-config-contract.json` and skill `qa-retest-trigger`.

## Reference options (dialog snapshot, 2026-10-09)

- Evalscope `evalscope_expand_dataset`: tau2_bench, tool_bench, bfcl_v3, multi_if. `evalscope_vlm_dataset`: mmmu, ocr_bench_v2, mm_star, mm_bench, math_vista, mmmu_pro, simple_vqa, math_vision, zerobench, blink, omni_doc_bench, infovqa, ocr_bench. `evalscope_v2t_dataset`: general_fc, bfcl_v3, tool_bench, video_mme, videomme_v2, msvd, mvbench.
- Evalscope history: `evalscope_v2t_dataset=general_fc` in 67 of 100 builds, `evalscope_llm_dataset=None` in 94, `inference_concurrency=50`, `inference_sampling=2000`, `inference_temperature=0.7`.
- OpenCompass history: full 12-dataset `inference_data` in 78 of 100 builds, concurrency 30, sampling 100.

## 压测自动化 (pipeline 2353017, scenario `stress`)

Findings of 2026-10-15. Stages: `编译` → `环境部署-参数校验` (manual) → `环境部署-环境部署（新建或扩缩容）` (SKIPPED when `skip_deploy_env=true`) → `DeepSeek压测` (manual; jobs `环境执行状态告警`, `环境变量更新`, `aiakperf压测`) → `自动保存日志` → `通知`. Of 125 builds only 10 ever ran the压测 stage; the other builds stop at `PENDING_FOR_USER`, so "last 10 builds" must mean the last 10 builds whose stage status is SUCC, FAIL or CANCEL.

- `build history --module M --limit 1500` lists builds of every pipeline in the module (about 1 s); filter on `pipelineConfId`.
- The stage's inputs are not returned by any CLI call. Recover them from the job logs (`set -x` trace): `aiak_perf.py` flags in the `aiakperf压测` log (`--n` is `num_requests`, `--of` is `fixed_output_length`, `--host` is `as_address`), and `dataset: '<label>##<file>'` in the alert job log. `scripts/stress_history.py` does this and prints the mode per key.
- Stage 1 sets `specific_model_path` and `prefill_job_name` in AGILE_OUT. `specific_k8s_pod=NA` makes `环境变量更新` run `kubectl get pod | grep <prefill_job_name> | grep prefill | head -n 1`; the default model path is `/pipeline-<model_id with - for _>`.
- The aiakperf job script embeds an inference credential in plain text. Never print job commands or whole log lines; print parsed flags only.
- Past runs: 12 h (`run_time_second=43200`) in 6 of 9 parsed runs; datasets `output_glm5-260331.jsonl` 4, `image2text_qianfan_total.jsonl` 2, others 1 each; qps differs per model (0.3 to 13).
