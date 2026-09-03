# 启动阶段 hook 位置约定 (stage_hook_points)

各阶段 label 必须与 `assets/gpu_memory_tracker.py` 的 `module_pairs` 及
`report_memory.CANONICAL_STAGES` 完全一致，否则 delta 表不会显示该模块。

## 规范阶段（12 个，target/draft 角色化）

label 模板中的 `{role}` 由注入块在调用时按 `self.is_draft_worker` 解析为
`target` / `draft`，因此同一个 `load_model` wrap 自动产出
`load_target_model` 与 `load_draft_model` 两个阶段。

| 阶段 | before / after label | 打点方式（候选解析） |
|------|----------------------|----------------------|
| initial | `initial`（单快照，基线绝对值） | 注入块安装时 |
| nccl_init | before/after_nccl_init | `ModelRunner.init_torch_distributed` 等候选 |
| load_target_model / load_draft_model | before/after_load_{role}_model | `load_model` 等候选（后接权重 dump） |
| alloc_target_kv_cache / alloc_draft_kv_cache | before/after_alloc_{role}_kv_cache | `alloc_memory_pool` 等候选 |
| configure_aux_hidden | before/after_configure_aux_hidden | **模块全局** `configure_aux_hidden_state_capture`（注入块在 model_runner 命名空间改绑） |
| target/draft_build_attention_backends | before/after_{role}_build_attention_backends | target：模块全局 `build_attention_backends`（role 取自 model_runner= 实参）；draft：`EagleDraftWorker.init_attention_backend`（懒 wrap）；全局缺失时回退 wrap `init_attention_backends` |
| prepare_replicated_q_proj | before/after_prepare_replicated_q_proj | `ModelRunner._prepare_replicated_q_proj`（仅 dcp>1 且 replicate-q-proj） |
| target_cuda_graph | before/after_{role}_cuda_graph | `ModelRunner.init_cuda_graphs` 等候选（target 后打 summary） |
| draft_cuda_graph | before/after_draft_cuda_graph | `EagleDraftWorker._capture_cuda_graphs`（懒 wrap，后打 summary） |

legacy label（原生 aiak commit `491ed25b` 的 before_load_model / draft_* 等）仍
保留在 `module_pairs` 尾部，老日志/原生打点可照常渲染。

## 打桩要点
- 入口调用一次 `tracker = init_global_memory_tracker()`（幂等，主/draft worker 共用时间线）。
- 每个阶段调用点前后各插一次 `tracker.snapshot("before_x")` / `("after_x")`。
- target cuda graph 与 draft cuda graph 后各调用一次 `tracker.print_summary()`。
- 全程用环境变量 `SGLANG_TRACK_GPU_MEMORY=1` 开关，默认关闭零开销。

## 跨版本：先校验 + 候选回退
- 注入前先跑 `inject_hooks.py --validate <model_runner.py>`，报告每个阶段解析到的方法名或 MISS（含两个模块全局），确认覆盖率。
- 每个阶段在 `STAGE_SPEC` 里是一个**候选方法名列表**；注入块在运行时取第一个存在的方法包装，fork 改名会自动回退到下一个候选。
- 若某阶段所有候选都不存在，运行时打 warning 并**跳过该阶段**（优雅降级，不影响启动），报告里少这一段。此时应在 `STAGE_SPEC` 里为该阶段补上新方法名。
- 主/draft 权重 dump 用 `param_memory_dump`，文件名含 `模型类名_pid`，避免互相覆盖。

## 采集时机：必须等捕获跑完（否则漏 after_*_cuda_graph）
- CUDA graph 捕获遍历多个 batch size，耗时数分钟；投机解码下 **draft 的 cuda graph 在主模型之后再捕获一次**。过早拷日志会漏掉 target/draft 的 cuda_graph 阶段。
- `run_and_collect.wait_capture_complete()` 作为收集前的闸门：health 就绪 **或** `after_cuda_graph` 快照数 >0 且 `stable_secs` 内不再变化才收集（模式同时匹配 legacy `after_cuda_graph` 与规范 `after_target/draft_cuda_graph`——`grep 'Tracker] [after'` 级别的计数即可）。
- 用 `grep 'TP0 EP0'` 取单 rank、不去重、按序。

## 细粒度 trace：DeepEP buffer + CUDA graph（patch 核心统计）

来源：aiak_sglang commit `491ed25b` + skill 扩展。各特性均**懒安装**（在第一个
被包装的启动阶段调用时才 import 目标模块，规避 model_runner import 期循环依赖）：

| 特性 | 触发条件 | 打点位置（候选解析） | 日志行 / 产物 |
|------|----------|----------------------|---------------|
| DeepEP buffer 分配 | `SGLANG_TRACK_GPU_MEMORY=1` | deepep 模块 `Buffer.__init__`（deep_ep / zbal 均覆盖） | `Allocating DeepEP buffer: nvl=X MiB, rdma=Y MiB (...)` |
| cuda graph 子阶段快照 | `SGLANG_TRACK_GPU_MEMORY=1` | `cuda_graph_setup` 里 `GraphSharedOutput.create_for_model_runner` / `EagerRunner.__init__` / `capture_prefill_graph` / `capture_decode_graph` | 快照 label：`before/after_create_for_model_runner`、`after_EagerRunner`、`after_capture_prefill_graph`、`after_DecodeGraphCapture` |
| cg-breakdown 埋点 | `SGLANG_TRACK_GPU_MEMORY=1`（恒开） | Decode/EAGLEDraft graph runner 的 `__init__` 与 `capture()` | `[cg-breakdown] runner_init / torch_graph_pool / capture_total` 三类行 |
| capture 逐 bs 台账 | 另加 `SGLANG_CAPTURE_MEM_LEDGER=1` | runner `capture_one_shape`（回退 `capture_one_batch_size`），仅 tp_rank 0 | `[capture-mem-ledger] bs=N: driver +X MiB (torch reserved +Y MiB, non-torch +Z MiB)` |
| capture allocator 快照 | 另加 `SGLANG_CAPTURE_MEM_SNAPSHOT_DIR=<dir>` | 包装 `capture()`：`_record_memory_history` + `_dump_snapshot` | 每 runner 一个 `capture_mem_{target,draft}_tp{rank}.pickle`（用 pytorch.org/memory_viz 查看） |

### CUDA graph 占用 5 桶拆分（report_memory 自动计算）

每个 `capture_total` 行闭合一个「capture 窗口」，窗口内事件按下述口径归桶：

| 桶 | 度量来源 | 精度 |
|----|----------|------|
| attention 图状态 | `[cg-breakdown] runner_init` 的 torch_alloc（runner `__init__` 期间：attention backend graph state + 静态输入/输出 buffer） | 实测 |
| torch 图池 | `[cg-breakdown] torch_graph_pool`：capture() 前后 **私有 allocator pool** 段字节差（`torch.cuda.memory_snapshot()` 中 `segment_pool_id != (0,0)` 的段） | 实测；pool 统计不可用时回退 reserved 差并标注 FALLBACK |
| DeepEP NVSHMEM | 窗口内的 DeepEP buffer 分配行（nvl+rdma；low-latency buffer 常在首个 capture 内分配） | 实测（buffer 实参字节） |
| graphExec 实例化 | 估算：窗口内逐 bs 台账（`SGLANG_CAPTURE_MEM_LEDGER=1` 时才有）去掉首个 bs 后的 non-torch 均值 × 补图数量（首个 bs 混入 cubin 加载，故剔除）；报告中同时给出“每图均值占用”与“本阶段补图 N 个” | 估算 |
| 图捕获/NCCL/cubin | 残差：`capture_total.non_torch − DeepEP − graphExec`（clamp ≥0，负残差单独提示） | 残差 |

注意：
- 不开 ledger 时 graphExec 无法估算（报 n/a），残差桶将包含 graphExec。
- `torch 图池` + `attention 图状态` 属 torch 侧；后三桶属 non-torch（driver）侧。
- 恒等式核对：`capture_total.driver ≈ torch_reserved 增量 + non_torch 增量`。

### 幂等 / 防双打点
- 行格式与原生 commit 相同的特性（DeepEP 行、ledger、snapshot dump、子阶段
  label）先用 `inspect.getsource` 查源码标记，fork 原生携带时让位不包装。
- 规范阶段 label 与 `[cg-breakdown]` 行原生 commit 中不存在，**恒定安装**、
  永不冲突；原生 fork 上会额外出现 legacy label 的第二条时间线（并行可读，
  report 的规范阶段表只认规范 label）。
- 注入前可用 `inject_hooks.py --validate-extras <sglang_src>` 预检。
