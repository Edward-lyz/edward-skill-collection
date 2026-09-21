# 厂内平台适配栈：DSv4.1 实迁包

A1 链路适配 + A2 监控适配 + A5 通用 BUGFIX 在 DSv4.1 那轮的完整落地物。

**重放走提交，不走 diff。** 下面台账里的每个 SHA 都在 `origin/ds-dev-ds4.1f-0917` 上，逐笔
`cherry-pick` 就能搬到新基线，提交信息、作者、Change-Id 全都跟着走。
`assets/internal-platform-stack-dsv41.diff` 只是**兜底**：远端分支被删、提交不可达，或者只想
一眼看全量差值时用它，正常路径不用。台账另一个用途是**反向核对的对照物**——平台依赖的路由、
指标族、日志 schema、环境变量读取点在这里一次看全。

## 出处

| 项 | 值 |
|---|---|
| 仓库 / 分支 | baidu/hac-aiacc/aiak_sglang，`ds-dev-ds4.1f-0917` |
| 基线 | `8bd60a9913`（社区 dsv4.1 dev 线，厂内栈第一笔之前） |
| 区间 | `8bd60a9913..80f471dbd8`，24 提交，作者全部 liyanzhen01，无 merge |
| 包规模 | 40 文件 / +2,851 / −147（含 5 个 registered 测试文件） |

```bash
git diff 8bd60a9913..80f471dbd8 -- python test > internal-platform-stack-dsv41.diff
```

区间内没有其它作者、没有 merge，所以两点 diff 就是这 23 笔的精确合并效果，不需要 cherry-pick
重演。第 24 笔 `87fd6bb729` 交付镜像四件套（ci.yml / build/build.sh / dockerfile/）**刻意不在
包里**：它绑在 `iregistry.baidu-int.com/lyz/lmsysorg/sglang:dev-dsv41` 这一个 base 上，照搬到
新 base 等于把镜像指回旧 base。四件套按 references/delivery-image.md 的三分法重判。

## 台账

顺序自上而下 = 原始拓扑序 = 重放顺序。

| SHA | 卡 | 类 | 平台侧触发 | 落点 |
|---|---|---|---|---|
| `c1780be6a3` | 4104/4170 | A1 | 网关按每 chunk 的 token 增量计费，社区协议不发这个字段 | `sse_utils.StreamDelta`、`serving_chat`、`protocol` |
| `31e6c6a381` | 4170 | A5 | FC 解析器攒 marker 时整个 delta 被吞，网关按 TPOT 超时断连 | `serving_chat` 空 chunk 保活，`SGLANG_TOOL_CALL_EMPTY_RETURN_INTERVAL` |
| `395d7c6dd5` | 3716 | A2 | P 侧不出 TTFT，且把跨 KV 交接的间隔算进 ITL 直方图 | `tokenizer_manager.collect_metrics` |
| `59b123ee43` | 4395 | A2 | 厂内日志管道按 level 字段 + 组件前缀分流，四类进程少一样 | `configure_logger`、uvicorn 格式、DP controller / detokenizer / 多 tokenizer worker |
| `6c231aba8e` | 4648 | A1 | 网关与 PaaS 探 `/health_forward`，社区不暴露 | `http_server` 主 server 别名 + dummy health server |
| `597cb83313` | 4784 | A2 | abort 计数按意图打点，多 tokenizer 下转发不属于本进程的 rid 使计数虚高 | `tokenizer_manager._handle_abort_req` + `_build_metrics_labels` |
| `61eeed88eb` | 3716 | A2 | PD 的 P 侧从不发 TTFT 样本，该侧面板恒空 | `prefill.py` KV 传输完成处观测 + `SchedulerMetricsCollector` |
| `6085834dff` | 4648/4996 | A1 | SDK/pydantic 生成的 `$ref`/`$defs` 工具 schema 语法后端跟不动，draft-07 `$id` 直接 400 | `function_call/utils`：`expand_json_schema_refs` + `normalize_json_schema_ids` |
| `08606e8acd` | 5010 | A1 | 首 chunk 前的 abort 也回 200 + 带内 error，网关无法与坏请求区分 | `serving_base.raise_abort_before_stream`，`/generate` 同样 kick-start |
| `c4e6bc4621` | 4648 | A1 | 网关按严格 struct 反序列化，null 的 role/tool_calls/tokens 整块失败 | `sse_utils.StreamDelta`、`protocol.DeltaMessage` |
| `581ee64e41` | 4648 | A5 | 续传 chunk 吃满预算后等待队列仍空转一次 radix 匹配 + hicache 预取 | `scheduler` 续传后即查预算，NO_TOKEN 时置 `batch_is_full` |
| `412047d3f2` | 4771 | A2 | 厂内内容合规栈在社区无对应物，复读与违禁只有网关事后能管 | `content_detection/`（`CD_ENABLE_DETECTION` 默认关）+ chat 流式挂钩 |
| `35f0a63153` | 4515 | A1 | 巡检工具轮询 `/get_instance_info` 取拓扑与实时负载 | 主 server + dummy server，`dp_ranks` 按 `node_rank` 切自己那段 |
| `5283390d5d` | 3716 | A2 | detokenizer→tokenizer 的 IPC 堵塞看起来像模型变慢 | `BatchStrOutput` 打 wall clock，`sglang:detokenizer_to_tokenizer_time` |
| `329df2475e` | 4170 | A2 | 只有吞吐与池占用，没有单次迭代里 forward 与调度开销的拆分 | `metrics_reporter` 打点：`generation_time` / `run_batch_time` / `iter_token_process_time` |
| `e075848f30` | 4515 | A1 | 网关按 `/ready` 轮转，社区 404 → POD 永不 ready；preStop 无处写排水标记 | `/ready` 同 handler + `AIAK_STOP_SIGNAL_DIR` 排水文件 + 非 master 转发 `MASTER_IP` |
| `43b2ba6d8b` | 4734 | A5 | `get_image_bytes` 把裸路径当服务端本地文件打开，信任边界过宽 | `utils/common` 只留 `file://` 前缀 |
| `eb01cc3cba` | 4446 | A1（DSv4.1 标签） | 参考工具自己 tokenize 请求体，全链路 token id 要逐位一致 | `multimodal/task_id`（`md5(model_id+url)`）、`encoding_dsv41` effort 表、`observability/request_trace`、`SGLANG_LOG_REQUEST_TRACE` / `SGLANG_LOG_TOKEN_IDS` |
| `4318fff319` | 4170 | A2 | 厂内 DSv4.1 页面读的九类族本基线从不发布，面板全 No data | `metrics_collector` + `metrics_reporter` + 各 loop 更新路径，旧族名留别名 |
| `d77aa7e77c` | 4170 | A2 | 与厂内 K3 的 `/metrics` dump 对比后仍缺八族 | 前缀命中率、receiver 等待队列、启动/加载耗时取启动计时汇总、abort 与 bootstrap/transfer 计数器预热、三条路由挂 `func_latency_seconds` |
| `5cdab3fab5` | 4170 | A2 | decode 侧 `kvcache_transfer_time` 无序列；L3 命中打扁平 `storage` | decode 出队处观测；`cache_source` 打后端类名 |
| `51736cebf4` | 4170 | A2 | 空闲实例不驱逐，带 label 的计数器首次观测前不出现 | `evicted_tokens_total` 预注册默认 label |
| `80f471dbd8` | 4170 | A2 | 评审查出 7 处缺陷：4 处能打挂请求或调度循环，3 处只失真 | Union `isinstance` 守卫、DECODE 分支兜底、除零、首 tick、`all_gather` 计时位置、跨进程 wall clock、锁一致性 |

## 包里的平台硬契约

反向核对时逐条确认新基线上还在，缺一条就是平台侧静默失效。这份清单已经机器化成
`assets/contract-dsv41.json`（76 项），由 `scripts/verify_platform_contract.py --emit` 从
`80f471dbd8` 相对 `8bd60a9913` 求差生成，核对是同一个脚本的默认模式，退出码即判据。下面是
人读的版本：

- **路由**：`/ready`、`/health_forward`、`/get_instance_info`，主 server 与 dummy health
  server 两套都要有。
- **指标**：包里出现 33 个 `sglang:` 族名（新增、旧名别名与 `inc(0)` 预热三种都算），重点是
  PD 两端各观测一次的 `kvcache_transfer_time` 与 `time_to_first_token_seconds`，以及四个必须
  预热的计数器：abort、bootstrap 失败、transfer 失败、驱逐。
- **日志**：`levelname` 前置，加四类组件前缀——`Server`（uvicorn 的两种格式）、
  `DPController`、`Detokenizer`、`Tokenizer <pid>`（每个 spawn 出来的 tokenizer worker）。
- **环境变量**：15 个。`AIAK_STOP_SIGNAL_DIR`、`MASTER_IP`、`CD_*` 8 个（检测开关、窗口、
  间隔、复读参数、trace dump 目录）、`SGLANG_TOOL_CALL_EMPTY_RETURN_INTERVAL`、
  `SGLANG_LOG_REQUEST_TRACE`、`SGLANG_LOG_TOKEN_IDS`、
  `SGLANG_ENABLE_TOOL_SCHEMA_REF_EXPANSION`(默认关)、
  `SGLANG_ENABLE_TOOL_SCHEMA_ID_NORMALIZATION`(默认开)。
- **req_id trace**：14 条 `trace(logger, "…")` 行，覆盖 api server 收请求、tokenizer 发给
  scheduler、dp controller 路由、scheduler 入队、decode prealloc 入队、decode bootstrap
  完成与失败、kv cache 收到与传输失败、detokenizer 回传、tokenizer 收回、请求结束与 abort。
- **token id dump**：2 个 `log_input_ids` 调用点，`tokenized@tokenizer_manager.py`（tokenizer
  出来的 id，多模态占位符还是裸的）与 `padded@scheduler.py`（填过 media pad 值的 id，才是
  模型输入和 prefix-cache key 用的那份，跟平台 dump 比就比这个）。

契约项里指标族的判据是「有定义**且**有写入点」：只 `inc(0)` 预热的单独归一类，定义还在但没人
写的会被报成「无写入点」。这是 DSv4.1 那轮面板 No data 的两种成因，修法不同，所以分开报。

## 用法

1. **按卡 cherry-pick**：台账自上而下就是原始拓扑序。同卡多笔用 `cherry-pick -n` 连拣再一次
   commit，`80f471dbd8` 是对监控栈的评审 fixup，连在它修的那几笔后面一起折叠，不单独成卡。
2. **只核对不重放时**：拿「包里的平台硬契约」当清单，对着新分支跑
   `scripts/verify_platform_contract.py`，比从平台侧 dashboard 反推快一个量级。
3. **兜底才用 diff**：`git apply --check --3way` 逐块看状态，报 already applied 的多半是社区
   后来自己收了（按 C1 处置），报找不到宿主的进 sibling skill 的 L2/L9 重实现，别硬塞。

## 2026-09-21 实账：整支重放到社区 main

社区 main 已对齐，从 main 开 `codex/dsv41-replay-on-main-0921`，把监控与 DSv4.1 多模态两组
按卡重放：17 笔源提交（全部确认在 `origin/ds-dev-ds4.1f-0917` 上）折叠成 6 个提交，
56 文件 / +7,343 / −102。

| 新提交 | 折叠的源提交 |
|---|---|
| `luno-4395 [监控][PR1/2] 平台接入: 日志 schema + 三个探针路由` | `59b123ee43` `6c231aba8e` `35f0a63153` `e075848f30` |
| `luno-4170 [监控][PR2/2] 指标: 时延 + 全量族 + 面板缺失 + 评审修复` | `395d7c6dd5` `597cb83313` `61eeed88eb` `5283390d5d` `329df2475e` `4318fff319` `d77aa7e77c` `5cdab3fab5` `51736cebf4` `80f471dbd8` |
| `luno-4446 [EPD][PR1/4] 前置: token id 对齐 + trace 框架` | `eb01cc3cba` |
| `luno-5183 [EPD][PR2/4]` / `luno-5184 [EPD][PR3/4]` / `luno-5185 [EPD][PR4/4]` | 原提交照搬，作者与 Change-Id 保留，只把 `PRi/3` 改成 `PRi/4` |

**分组的三条判据**，比「一卡一提交」更贴合评审：

- 监控合成两笔而不是六笔：评审面只有两个——「指标发得对不对」和「日志与探针接得上不上
  平台」。六张卡（3716/4784/4170 与 4395/4515/4648）按这两个面归并，卡号在正文里逐条点名，
  追溯不丢。
- token id 对齐（luno-4446）归到 EPD 而不是单独一组：EPD 把编码搬成独立角色后，encoder
  的 embedding 与 scheduler 侧 token id 必须逐位对齐，它是后面三卡的地基，所以排 PR1/4。
  为此把厂内那三笔的 `PRi/3` 顺序改成 `PRi/4`——同一 Change-Id 在新目标分支上开的是新
  change，改标题不动老分支上的评审。
- `207a80780e`（luno-5211 CP 视觉，jiashurui）不迁：它是模型内部的 CP 分片路径，不属于
  平台适配这两组的交付面。顺带省掉一处行为差——源提交在解除 CP 限制时把 MoE A2A 的 guard
  也删了，提交信息和注释都没提这件事。

五处冲突，四类判据：

- **社区已自己收了一个同名路由**：main 上已有 `/ready`（返回 `is_ready()`）。没有照搬厂内那版
  「把 /ready 挂到 health_generate 上」的写法，而是保留社区 handler，在它前面加排水判断——
  排水语义只属于 `/ready`，挂到 health_generate 上会连 `/health` 一起受影响。
- **两笔改动插在同一行**：监控卡的时间戳与 luno-4446 的 trace 行落在同一位置，三处 add/add
  两边都留，trace 在前、计时在后。
- **社区换了 API 名**：`get_pp_group()` → `get_parallel().pp_group`，两处按新名重写。
- **社区已自己收了一个同名赋值**：`get_pp_group()` 那行被 EPD PR4/4 上移到 encoder_only
  分支之前，原位置的赋值社区侧已存在，取删除并把上移的那行按新 API 重写。漏了这一步的表现
  是 `F821 Undefined name get_pp_group`——`ruff --select=F821` 扫一遍改动文件就能抓到，
  这类「解完冲突语法没错但名字不存在」的缺陷值得在每轮重放后固定跑一次。

核对结果：契约 76 项过 65 项。缺的 11 项是 `CD_*` 八个（内容合规 luno-4771）与
`SGLANG_TOOL_*`/`SGLANG_TOOL_CALL_*` 三个（工具 schema 与 FC 保活 luno-4648/4996），两张卡本轮
不在范围内。指标族 30、预热计数器 5、路由 6、日志 4、rid trace 14、token id dump 2 全部在位。
合并成 6 个提交后重跑，结果与 11 个提交时逐项一致——折叠改的是评审粒度，不是交付内容。

## 包里刻意留下的口子

按硬规则 4，部分重放要写清留下什么、为什么、需要时从哪笔捡回来。这轮的五处：

- `412047d3f2` 只搬了合规检测，丢掉 KV-dump 的 `TraceManager`、`TraceReq`/`TraceType` 的
  io_struct 与 scheduler 管线、msit_llm NPU 调试器——它们是调试设施，且与社区
  `observability/trace.py` 是平行实现，要时从 `13cdb6224c` 捡。
- 同一笔的 `_build_trace_info` 目前恒空：响应字段先留着，等 scheduler 侧填
  `meta_info["trace_info"]`，这样能力落地时网关契约不变。
- `581ee64e41` 去掉了 `authoritative_admissions` 分支（PP 准入路径本基线没有），源
  `1aff7c5998`。
- `597cb83313` 去掉了 `only_if_pending` 参数与其单测：本基线的 `create_abort_task` 已经用
  `rid in rid_to_state` + `ReqState.abort_sent` 覆盖了派发侧，源 `b2151e080e`。
- `31e6c6a381` 的两个后续 `c481af55c5` / `852ace0cae` 不迁：它们打的是 fork 本地的 FC
  续传重放路径，社区 `JsonArrayParser` 不收 tools 参数、`ReasonerGrammarObject` 已用
  `tokens_after_end`。

另有一条已知残留：`43b2ba6d8b` 收紧后 `file://` 分支实际不可达（新基线的 `load_image` 先剥
scheme 再传纯路径），且 `test/registered/unit/multimodal/rust/shared/test_fetch.py` 还钉着旧的
裸路径契约，在编了 Rust mm 扩展的环境里会红。重放到新基线时按 SKILL.md 常见坑最后一条重判，
不要照搬这一行。
