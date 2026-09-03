---
name: memory-analysis
description: SGLang 显存与权重分析。用于两类请求：(1) 拆解 SGLang 启动各阶段 GPU 显存去向（NCCL init、权重加载、KV cache、attention backend、CUDA graph 等）并输出分阶段表格；(2) 只读 safetensors header 计算 HF checkpoint 的理论权重大小、按模块分类，并与 sglang 运行时权重 dump 做逐模块 diff。触发词："显存分析"、"各阶段显存"、"权重理论大小"、"按模块分类"、"权重 diff"、"gpu memory breakdown"、"analyze sglang startup memory"、"theoretical weight size from safetensors"。
---

# memory-analysis

SGLang 显存与权重分析。两大能力：

- **能力 B（analyze-weights）**：HF 理论权重 + 运行时 diff。只读 safetensors header、不下载权重体，可单机离线。
- **能力 A（analyze-memory / full-auto）**：SGLang 启动分阶段显存拆解。需要活着的 k8s pod + 目标 fork 的 sglang 源码树。

CLI 入口 `bin/mem-analysis`（首次 `chmod +x`）。能力 A 的编排与分步脚本在 `scripts/`，注入素材在 `assets/`。

## 何时使用

- 拆解 SGLang 启动显存去向（NCCL init / 权重加载 / KV cache / attention backend / CUDA graph）。
- CUDA graph 那几个 GB 的细拆、DeepEP buffer 占用、逐 batch size 的 capture 台账（能力 A 细粒度 trace）。
- 算 HF checkpoint 理论权重大小、按模块/shape 分类、导出 xlsx（能力 B）。
- 核对某类权重在 sglang 里是分片还是复制、量化是否生效（能力 B diff）。
- 给新模型接权重适配器，或 fork 改过 ModelRunner 方法名要先校验打桩点。

## 前置条件

- 远程 HF：本环境 `huggingface.co` 不可直连，任何远程 `--hf` 前先导出代理，否则挂到超时；本地模型目录免代理。
- 依赖：能力 B 仅 `requests`（远程时才用到）；能力 A 本机需 `torch`。
- 能力 A 需要：deploy yaml、kubeconfig、sleep 模式的 pod、pod 内 sglang 路径、本机一份对应 fork 的 sglang 源码树。

## 能力 B：analyze-weights（离线核心）

```bash
bin/mem-analysis analyze-weights --hf <repo_id|hf.co URL|本地目录> \
  [--model <适配器，如 kimi_k3>] [--stats-file <dump 日志>] \
  [--yaml deploy.yaml | --tp-size N --ep-size N --dcp-size N --dp-size N] \
  [--sglang-src <源码树>] [--out <dir>]
```

- 不带 `--stats-file`：只出 `weight_theory_report.{md,xlsx}`，三张表 `by_shape` / `by_category` / `by_module`（层与专家下标折叠为 `{L}`/`{E}` 去重）。**三张表一律按名称排序，绝不按大小排序**。
- 带 `--stats-file`：追加 `weight_diff_report.{md,xlsx}`，口径为 `Expect(来自配置) | ObsRatio(理论/实测, 仅展示) | Δ(实测−Expect)`。
- 远程模型只对 safetensors header 发 HTTP Range 请求（index.json + 各分片 `data_offsets`），**永不下载权重体**。
- 并行度（tp/ep/dcp/dp）只来自 `--yaml` 或显式参数，**绝不从 dump 反推**；不给配置时退化为 observed-ratio-only 模式。Δ≈0 才是真验证；`MISMATCH` 行才是真发现（复制而非分片、融合组没对上、量化生效），不许改分片轴去凑 Δ=0。

新模型接适配器：`python3 scripts/derive_adapter.py <sglang_src> <model_hint> <name>` 扫 `stacked_params_mapping` 自动生成 `model_adapters/<name>.py` 骨架，再按 dump 精修 `tp` 轴、把 runtime-only 张量拆成独立类别。分类规则见 `references/taxonomy_rules.md`。

## 能力 A：analyze-memory（需要集群）

**硬约束：先过预检门，未通过不得注入或启动**：

```bash
bin/mem-analysis preflight --yaml deploy.yaml --sglang-src <sglang 源码树>
```

预检强制三件事：① 逐阶段校验打桩点（任一规范阶段 MISS 即失败；`--allow-partial` 仅显式放行）并校验 `dump_param_memory_stats` 打点；② 权重适配器骨架存在（无则自动生成）；③ trace 开关全开（`SGLANG_TRACK_GPU_MEMORY=1`、`SGLANG_CAPTURE_MEM_LEDGER=1`、`SGLANG_CAPTURE_MEM_SNAPSHOT_DIR=/tmp/capsnap`）。

一条龙（推荐）：

```bash
python3 scripts/run_full_auto.py --yaml deploy.yaml --sglang-src <树> \
  [--kubeconfig <KUBECONFIG>] [--ns default] [--sg-dir <pod 内 sglang 包目录>] \
  [--max-retries 2] [--out <dir>]
```

执行链：预检 → `ensure_sleep_pod`（改写成 sleep 并**剥离所有探活配置**，否则 sleep 容器探活失败被 kubelet 反复重建）→ 注入可还原打桩 → 启动（全量 trace env）→ `wait_capture_complete`（等主 + 草稿 CUDA graph 捕获完再采集，否则漏 `after_cuda_graph`）→ collect → `report_memory` → `auto_weight_diff` 收尾。失败先自动诊断修复再重跑（预检 MISS 用 difflib 模糊匹配并持久化进 `STAGE_SPEC`；捕获超时杀进程重启；无 dump 则重新 collect 或整体重跑）。

手动分步（脚本在 `scripts/`，编排需要 pod）：

1. `inject_hooks.py --validate <model_runner.py>` 校验打桩点；`--validate-extras <src>` 看细粒度 trace 是 NATIVE（fork 已带 aiak commit `491ed25b`）还是 WRAP（注入补齐）。
2. `inject_hooks.py --render` 生成注入块；`apply_patch.py --restore` 可一键还原。拷进 pod 前先删目标目录，避免 `kubectl cp` 嵌套。
3. `deploy_and_patch.py` 拉起 sleep pod 并推送补丁；`run_and_collect.py` 启动并 `wait_capture_complete()` 后采集。
4. `report_memory.py <单 rank 日志> --xlsx out.xlsx`；单 rank 用 `grep 'TP0 EP0'` 过滤，预期**两对** `before/after_cuda_graph`（主 + 草稿）。
5. `auto_weight_diff.py <采集目录> --yaml deploy.yaml` 固定收尾；**exit 2（无 dump / 无 HF 源）= 能力 A 未完成**。

## 输出解读

- `staged_memory_gpu0.xlsx`：`snapshots` + `deltas` + **`stage_deltas`**（12 个 role-aware 规范阶段：initial / nccl_init / load_{target,draft}_model / alloc_{target,draft}_kv_cache / configure_aux_hidden / {target,draft}_build_attention_backends / prepare_replicated_q_proj / {target,draft}_cuda_graph，缺失阶段单独列出）+ 细粒度 `deepep_buffers` / `capture_ledger` / `cg_breakdown`。
- `cg_breakdown` 的 CUDA graph 5 桶：attention 图状态 / torch 图池 / DeepEP NVSHMEM / graphExec 实例化（**估算**：每图均值 × 补图数，汇报要说明）/ 图捕获与 NCCL 与 cubin 残差。
- `capture_mem_{target,draft}_tp{rank}.pickle`：capture 期 allocator 快照，用 pytorch.org/memory_viz 打开。
- 权重口径：`driver_used = total − free`、`non_torch = driver_used − torch_reserved`；`dtype changed`（BF16→FP8）表示量化生效，通常预期内。

## 常见坑

- 远程 `--hf` 挂起：没导代理；本地目录免代理。
- 预检某阶段 MISS：fork 改了方法名 → 在 `STAGE_SPEC` 补候选名或让 full-auto 模糊匹配；不要直接 `--allow-partial`。
- 报告缺 `after_cuda_graph` / 缺草稿那对：采集过早 → 必须走 `wait_capture_complete()`。
- pod 反复重启、补丁丢失：sleep yaml 没剥离探活 → 用 `ensure_sleep_pod()` 重新 apply。
- `kubectl cp` 目录嵌套：拷贝前先删目标目录。
- 同一日志行出现两次：fork 已原生带 aiak commit `491ed25b` 又被 wrap → 注入块有源码标记防双打点，注入前用 `--validate-extras` 预检。
- `size mismatch` / `only in HF` / `only in sglang`：两侧命名/分片不一致 → 按适配器校准环改 `extra_rules()` / `mapping()`；**度数只来自配置或源码**。
- 专家权重 dump 抓不到：某些 decode 配置 EP 动态分片不在 `named_parameters`，其占用体现在能力 A 的权重加载阶段。

## 资源导航

- `bin/mem-analysis` —— CLI（`analyze-weights` / `preflight`）。
- `scripts/` —— 能力 A 编排与各步脚本（`run_full_auto.py` 一条龙）。
- `model_adapters/` —— `base.py` 启发式 + 各模型适配器（`kimi_k3.py` 等）；新模型用 `derive_adapter.py` 生成骨架。
- `assets/` —— 注入素材：`gpu_memory_tracker.py`、`param_memory_dump.py`、`apply_patch.py`。
- `references/taxonomy_rules.md` —— 分类规则；改分类前读。
- `references/stage_hook_points.md` —— 打桩点、细粒度 trace 表和 5 桶方法学；改注入前读。

