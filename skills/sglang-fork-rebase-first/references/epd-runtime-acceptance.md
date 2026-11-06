# 验证点 3：起 EPD 服务实测能力与字段

前两个验证点只证明代码里有、且与源 PR 一致，证不了值对。这一步把三角色拉起来打真实流量，逐项
取数。整套在有 GPU 的机器上跑，本机跑不了就记 deferred，不记 pass。

## 起服务

三个角色都要起：encode server（`--disaggregation-mode encode` 那侧）、prefill、decode。启动参数
两项必给，缺了后面全是空的：`--enable-metrics`（缺了不挂 `/metrics`，两侧 collector 都不建）、
`--enable-cache-report`（cache 命中类指标的开关）。发版 YAML 的四个平台标签按
references/monitoring-contract.md 填平台注册过的服务名，别自创。

两个环境变量按需打开，它们默认关：`SGLANG_LOG_REQUEST_TRACE=1` 出 rid 的 stage trace，
`SGLANG_LOG_TOKEN_IDS=1` 出两份 token id。

## 逐项判据

**探针与自省**（不用打流量就能查）

| 取什么 | 期望 |
|---|---|
| 主 server `/ready` | 200；`touch $AIAK_STOP_SIGNAL_DIR` 写入 `stop` 后变 507 |
| 非 master 节点 dummy server `/ready` | 转发到 `MASTER_IP` 后 200；master 不通时 503 |
| 主 server 与 dummy server 的 `/health_forward` | 都 200，少一侧就是半个拓扑的探针挂着 |
| `/get_instance_info` | `dp_ranks` 是本节点那一段（`node_rank * dp_size / nnodes` 起），不是整个范围 |
| encode server `/list_vit_caches` | 能返回 hold 快照 |

**指标**（必须先打一个成功请求，带 label 的指标在首次观测前不出现）

按族名（去掉 `_bucket` / `_count` / `_sum` / `_total` 后缀）做打流量前后的 diff，只能多不能少。
一条普通 chat 加一条带图 PD 请求之后，这些族要有值：

- 两端各观测一次的：`kvcache_transfer_time`（P 侧是发送耗时、D 侧是等待耗时，两边都要有序列）、
  `time_to_first_token_seconds`（两端都记）
- P 侧该有、D 侧不该有：`time_to_first_token_seconds` 有而 ITL 无——`collect_metrics` 里 ITL 只在
  非 PREFILL 侧记，这是设计好的不对称，不是缺失
- EPD 专有：`mm_receiver_waiting_requests` / `_failed` / `_timeout` /
  `mm_receiver_embedding_transfer_time`、`gpu_buffer_pool_used_bytes` / `_total_bytes`、
  `num_mm_requests_total`
- 链路时延：`detokenizer_to_tokenizer_time`、`generation_time` / `run_batch_time` /
  `iter_token_process_time`、`request_zmq_time_seconds`
- 预热类：`num_aborted_requests_total`、bootstrap 与 transfer 失败计数、`evicted_tokens_total`
  在空闲实例上是 **0**，不是 No data
- 启动耗时：`engine_startup_time` / `engine_load_weights_time` 是真值，不是硬编码 0

**日志与 token id**

- 每行行首是 levelname；四类组件前缀都出现过：`Server`（uvicorn）、`DPController`、
  `Detokenizer`、`Tokenizer <pid>`
- 同一个 rid 能在日志里串起这次拓扑会经过的 stage：api server 收请求 → tokenizer 发给
  scheduler → dp controller 路由 → scheduler 入队 → decode prealloc/bootstrap/kv 收到 →
  detokenizer 回传 → tokenizer 收回 → 请求结束。断在哪一段，那一段的 trace 行就是漏的
- `log_input_ids` 出两份：`tokenized`（tokenizer 出来的 raw id，多模态占位符还是裸的）与
  `padded`（填过 media pad 值的 id）。**跟平台 dump 逐位比的是 padded 那份**，它才是模型输入和
  prefix-cache key 用的

**响应字段**

- 流式 chunk 上每个 content-bearing chunk 带 token 增量，网关按它计费
- `role` / `tool_calls` / `tokens` 为空时不出现在 payload 里，`content` 与 `reasoning_content`
  恒为字符串——网关按严格 struct 反序列化，null 会直接失败
- 首 chunk 之前被 abort 的请求回真实 HTTP 状态码，不是 200 带内 error

## 取数的三个陷阱

1. **hostNetwork 下按 IP 取 `/metrics` 会串台**：POD IP == 节点 IP，POD 重建后同一个 IP 上跑的是
   别人的服务。先 `kubectl get pods -o wide` 核 IP 归属，再用 `/metrics` 里的 `model_name`
   （= `--served-model-name`）二次确认。
2. **带 label 的指标要等第一次观测**：`/metrics` 走 prometheus multiprocess 模式，`.labels()` 没
   被调用过就不落进 mmap 文件。冷启动后没打过请求时请求侧指标本来就是空的，不能据此判缺失。
   顺序固定：先打一个成功请求，再取 `/metrics`。
3. **调度器侧与请求侧是两个 collector**：`num_running_reqs` / `gen_throughput` / `kv_*` 只要
   `--enable-metrics` 就有；TTFT / e2e latency / prompt 与 generation 直方图还要请求真的走过
   tokenizer manager 才有。

## 不重启 POD 的快速通道

sleep 模式的 pod（主进程 `sleep inf`、探针已删、服务手动起）可以只热替文件加重起服务，把一次
验收压到分钟级。可信度靠三方 md5，步骤见 references/monitoring-contract.md 第九节。
