---
name: cuda
description: "CUDA kernel development, debugging, performance optimization, and code review for Claude Code. Use when writing, debugging, optimizing, or reviewing CUDA code, GPU kernels, or parallel algorithms. Covers non-interactive profiling with nsys/ncu, debugging with cuda-gdb/compute-sanitizer, binary inspection with cuobjdump, performance analysis workflows, and code compliance checks (D2H, CUDA Graph, Triton ban). Triggers on CUDA, GPU programming, kernel optimization, nsys, ncu, cuda-gdb, compute-sanitizer, PTX, GPU profiling, parallel performance, gpu check, kernel review."
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
---

# CUDA Programming Skill

## Core Philosophy

**Measure before guessing.** GPU performance is deeply counterintuitive. Profile first, hypothesize second, change third, verify fourth.

**Small, isolated changes.** CUDA bugs compound. Make one change, test it, commit it. Resist the urge to "fix everything at once."

**printf is your strongest tool.** When debuggers fail, when tools produce inscrutable output, printf in device code reveals truth. Don't be embarrassed to use it extensively.

**Sometimes, stare at the diff.** Inscrutable segfaults are common. Tools often don't help. The human approach: minimize the diff, read it carefully, see the bug. This is legitimate and often faster than tooling.

## Debugging Workflow

### First Response to a Bug

1. **Reproduce minimally** — Isolate the failing kernel with smallest possible input
2. **Add printf** — Before any tool, add `printf` in device code to trace execution
3. **Run compute-sanitizer** — Catch memory errors non-interactively:
   ```bash
   compute-sanitizer --tool memcheck ./your_program
   compute-sanitizer --tool racecheck ./your_program  # for race conditions
   compute-sanitizer --tool initcheck ./your_program  # uninitialized memory
   ```
4. **If still stuck**, try cuda-gdb non-interactively for backtrace:
   ```bash
   cuda-gdb -batch -ex "run" -ex "bt" ./your_program
   ```
5. **When tools fail** — Minimize the diff between working and broken code. Read it. The bug is in the diff.

### printf in Device Code

```cuda
__global__ void myKernel(float* data, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx == 0) {  // Limit output
        printf("Kernel launched, n=%d, data[0]=%f\n", n, data[0]);
    }
    // ... kernel logic ...
    if (idx < 10) {  // Sample a few threads
        printf("Thread %d: result=%f\n", idx, someValue);
    }
}
```

**Key patterns:**
- Guard with `if (idx == 0)` or `if (idx < N)` to avoid output flood
- Print at kernel entry to confirm launch
- Print intermediate values at suspected failure points
- Flush is automatic at kernel completion

### compute-sanitizer Quick Reference

**Common gotcha:** "Invalid __shared__ write... out of bounds" usually means insufficient dynamic shared memory allocation in the kernel launch, not wrong array indexing. Check `<<<grid, block, smem_size>>>`.

```bash
# Memory errors (most common)
compute-sanitizer --tool memcheck ./program

# Other tools: racecheck, initcheck, synccheck
# For detailed options, see references/debugging-tools.md
```

### cuda-gdb Non-Interactive

```bash
# Get backtrace on crash
cuda-gdb -batch -ex "run" -ex "bt" ./program

# For breakpoints, thread inspection, see references/debugging-tools.md
```

**Compile with debug info:**
```bash
nvcc -g -G -lineinfo program.cu -o program
```

### cuobjdump for Binary Inspection

```bash
# Dump PTX and SASS
cuobjdump -ptx ./program
cuobjdump -sass ./program

# For resource usage, symbol listing, see references/debugging-tools.md
```

**For complete debugging tool reference:** See `references/debugging-tools.md` for detailed compute-sanitizer options, cuda-gdb workflows, and cuobjdump analysis patterns.

## Performance Optimization Workflow

### Golden Rule

**Never optimize without profiling first.** Intuition about GPU bottlenecks is almost always wrong. The profile → fix → verify loop is the actual optimization work, not a preliminary step.

### Performance Investigation Steps

1. **Establish baseline** — Time the operation, record it
2. **Profile with nsys** — Get timeline, identify which kernels matter
3. **Deep-dive with ncu** — Analyze specific bottleneck kernels
4. **Hypothesize** — Based on metrics, form specific hypothesis
5. **Change one thing** — Make a single targeted change
6. **Verify** — Re-profile, confirm improvement
7. **Repeat**

### nsys (Nsight Systems) — Timeline Profiling

Use nsys for: "Where is time being spent?" — CPU/GPU interaction, kernel launch patterns, memory transfers, overall timeline.

```bash
# Basic profile
nsys profile -o report ./program
nsys stats report.nsys-rep --report cuda_gpu_kern_sum

# With NVTX markers
nsys profile --trace=cuda,nvtx -o report ./program

# Key reports: cuda_gpu_kern_sum, cuda_api_sum, cuda_gpu_mem_time_sum, nvtx_sum
# For detailed usage, see references/nsys-guide.md
```

**Percentile discipline for repeated kernels:** When a kernel executes many times (CUDA Graph replay, warmup loops, inference batch), average duration understates tail behavior. Always report p50/avg/p99 for kernels with >10 invocations. For single-invocation or initialization kernels, avg is acceptable.

**For detailed nsys analysis patterns:** See `references/nsys-guide.md` for timeline interpretation, identifying common bottlenecks, and analysis workflows.

### nsys CUDA Graph Decode Report Format

When analyzing an nsys SQLite export for CUDA Graph decode, do not stop at `cuda_gpu_kern_sum` or a flat kernel-name summary. CUDA Graph replay breaks one logical decode step into many graph nodes; individual attention kernels can be only a few microseconds and still be valid. Reconstruct one decode replay from `graphNodeId` order and report operator-level timing.

**Required method:**

1. Use the SQLite export, not only text stats.
2. Pick the correct `deviceId` / DP rank and state it explicitly.
3. For `CUPTI_ACTIVITY_KIND_KERNEL` rows with non-null `graphNodeId`, sort graph nodes by first `start`.
4. For each `graphNodeId`, compute percentile statistics across replay occurrences:
   - Collect all `end - start` durations for that `graphNodeId`
   - Report **p50 (median)**, **p99**, and **count**. Also report avg and max.
   - **p99 is the primary metric** for operator-level timing — it represents the tail latency that determines actual throughput. Average understates tail behavior; jitter (max/avg ratio) quantifies variance.
   - Use Python `sorted(durs)[int(0.99 * n)]` for p99 (not avg). SQLite equivalent: `SELECT dur FROM ... ORDER BY dur LIMIT 1 OFFSET CAST(0.99 * cnt AS INTEGER)`.
5. Map graph-node order back to model structure. For DeepSeek-style decode, distinguish dense layers, MoE layers, and any MTP/tail nodes. Do not assume the tail is MTP unless the graph pattern actually contains full MTP transformer layers.
6. **Report every kernel individually. Never merge kernels** (especially offload) into aggregated groups in the final table. The table must list each `graphNodeId`'s semantic operator name and P99 separately so the user can identify individual bottlenecks.
7. **Use `demangledName`** to distinguish kernel semantics** — the template parameters in the full demangled name reveal GEMM shapes (M/N/K) which identify q_proj, kv_proj, gate_proj, expert up/down, etc. Join on `StringIds(id)` with `k.demangledName`.
8. For each operator group, compute timing from **p99 durations**:
   - raw duration: sum of member kernel p99 durations
   - visible occupancy: union of member kernel time intervals (use p99 durations for interval estimation)
   - internal overlap: raw duration minus visible occupancy
   - span: last end minus first start; label gaps/wait explicitly instead of treating span as compute
9. Save intermediate CSV reports locally when the analysis is nontrivial, and mention their paths in the final response.

**Why p99 instead of average:**

CUDA Graph replay on multi-GPU systems (especially with MoE dispatch) shows significant jitter. In production traces, `dispatch` kernels routinely show 1.5–2.6x jitter (p99/avg). `combine` kernels show **30–35x jitter** (P50 ≈ 7us, P99 ≈ 220us) due to bimodal distribution (fast path vs all-reduce stall). Using average hides the tail latency that actually limits throughput. P99 captures the real-world worst-case behavior per decode step.

**Kernel semantic identification:**

Use the kernel name + `demangledName` template params + position within the repeating graph-node pattern to map each kernel to its model semantic role:

| Kernel name | Semantic role | How to identify |
|---|---|---|
| `RMSNormKernel` | Input layernorm | Position + name |
| `rmsnorm_split_col_kernel` | RMS norm split column | Name |
| `FusedAddRMSNormKernel` | Add + RMS norm fused | Name |
| `vectorized_layer_norm_kernel` | Layer norm | Name |
| `per_token_group_quant_8bit_kernel` | Per-token 8bit quant | Name |
| `per_token_group_quant_fp8_kernel` | Per-token FP8 quant | Name |
| `_act_quant_kernel` | Activation + quant fused | Name |
| `sm100_fp8_gemm_1d1d_impl` | GEMM (see shape) | demangledName M/N/K |
| `_w8a8_block_fp8_matmul` | Shared expert GEMM | Name + M/N from demangledName |
| `rotary_embedding_kernel` | RoPE | Name |
| `fast_hadamard_transform_kernel` | Hadamard (q_a in MLA) | Name |
| `_set_k_and_s_triton_kernel` | Set KV cache | Name |
| `kernel` (gemvx) | BMM qk scores | demangledName contains `gemvx` |
| `splitKreduce_kernel` | Split-K reduction | demangledName contains `splitKreduce` |
| `sm100_fp8_paged_mqa_logits` | MQA logits projection | Name |
| `topk_transform_decode_kernel` | Sparse top-k | Name |
| `nvjet_tst_*` (various) | BMM (rope, o_proj, gate) | demangledName tile sizes |
| `flash_fwd_splitkv_mla_fp8_sparse_kernel` | MLA attention core | Name |
| `doul_flash_fwd_mla_combine_kernel` | MLA combine | Name |
| `CatArrayBatchedCopy_alignedK_contig` | KV concat | Name |
| `_quantize_k_cache_fast_kernel` | KV cache quant | Name |
| `fast_set_kv_cpu_kernel` | Set KV to CPU | Name |
| `update_intra_lru_cache_and_get_evict_ids_kernel` | LRU cache update | Name |
| `compact_evict_ids` | Evict compaction | Name |
| `extract_hit_miss_indices_kernel` | Hit/miss extraction | Name |
| `fast_intra_layer_h2d_kernel_optimized_v2` | H2D copy | Name |
| `calc_intra_layer_trans_topk_ids_kernel` | Intra-layer topk | Name |
| `dispatch` | MoE dispatch (network) | Name |
| `combine` | MoE combine (network) | Name |
| `act_and_mul_kernel` | SiLU activation | demangledName contains `silu` |

**GEMM shape → semantic role (common patterns in DeepSeek-V3 decode):**

| Shape pattern | Likely role |
|---|---|
| M=7168, K=16, N=32 | q_proj (small absorbed projection) or kv_proj |
| M=1536, K=64, N=32 | q_proj (absorbed projection) |
| M=7168, K=128, N=32 | gate_proj |
| M=7168, K=224, N=128 | expert up_gemm |
| M=2048, K=224, N=128 | expert gate_gemm |
| M=7168, K=32, N=32 | expert down_gemm |
| M=2048, K=64, N=32 | expert post_gemm |
| M=18432, K=64, N=32 | shared expert down_proj |
| M=7168, K=2048, N=32 | o_proj |
| M=1536, K=192, N=32 | kv_bmm (rope) |

**Final report table shape (every kernel listed individually):**

```
|   q_proj_a gemm                 | 11.5 us  | (M=7168 N=32 K=16) |
|   kv_proj gemm                  | 13.4 us  | (M=7168 N=32 K=16) |
|   update_lru                     |  5.4 us  |
|   _quantize_k_cache_fast          |  2.0 us  |
|   fast_intra_layer_h2d          |  2.3 us  |
|   flash_mla (head 0)             | 10.8 us  |
|   dispatch                       | 243.4 us | ← bimodal: p50≈175us, p99≈243us |
|   combine (all-reduce)           | 220.9 us | ← bimodal: p50≈7us, p99≈221us |
|   ...
|   一层共计                       | 1073 us = 1.073 ms |
```

**Offload decode requirements:**

- **Never merge offload kernels into aggregated groups.** Each offload kernel (`update_lru`, `compact_evict`, `fast_intra_layer_h2d`, `extract_hit_miss`, `_quantize_k_cache_fast`, `fast_set_kv_cpu`, `topk_transform_decode`, `calc_intra_layer_trans_topk_ids`, `CatArrayBatchedCopy`) must appear as a separate row in the report.
- Separate attention core (`flash_fwd_splitkv_mla`, `doul_flash_fwd_mla_combine`) from surrounding Q/K/V projection, rope, bmm/logits, sparse top-k, KV cache/offload, output projection, and norm kernels.
- Separate MoE communication (`dispatch`, `combine`) from expert GEMMs and activation/quant kernels.
- If a first MoE layer or first replay is an outlier (e.g., cold-start dispatch >> steady state), report both all-layer p99 and steady-state p99 excluding the outlier, with the exclusion stated clearly. Mark outlier rows in the per-node table.

**Overlap discipline:**

- Do not invent "uncovered" or "unmasked" time from a flat kernel table.
- A safe statement from SQLite alone is internal overlap within a chosen operator group: `sum(duration) - union(intervals)`.
- If a kernel span is much larger than its raw duration, explain that the span contains gaps or other work; do not charge the full span to that kernel.
- High jitter (max/avg > 1.5x) on a graph node indicates non-deterministic execution — likely network/communication variance in dispatch/combine kernels. Flag these explicitly.
- Bimodal kernels (P99/P50 > 10x, P95 ≈ P99) indicate a binary fast/slow path distribution — report both paths explicitly.
- True critical-path or cross-operator masking requires graph edges / stream dependency analysis. If you have not computed that dependency path, say so.

### ncu (Nsight Compute) — Kernel Analysis

Use ncu for: "Why is this kernel slow?" — Detailed metrics, roofline, memory analysis, occupancy.

```bash
# Profile specific kernel
ncu --kernel-name "myKernel" -o report ./program

# Quick summary to stdout
ncu --set basic ./program

# Sets: basic, full, memory, launch, roofline
# Sections: ComputeWorkloadAnalysis, MemoryWorkloadAnalysis, Occupancy
# For detailed metrics and interpretation, see references/ncu-guide.md
```

**Warning:** ncu expert system recommendations can be misleading. Always verify with actual metrics and experiments.

**Scale matters:** Optimizations that help at large scale can hurt at small scale. Always profile at your actual problem size, not theoretical maximums.

**For detailed ncu metric interpretation:** See `references/ncu-guide.md` for understanding roofline analysis, memory bottlenecks, occupancy limits, and warp scheduling.

### NVTX for Custom Instrumentation

When you need finer granularity than kernel-level, use NVTX:

```cuda
#include <nvtx3/nvToolsExt.h>

nvtxRangePush("Operation Name");
// ... code to profile ...
nvtxRangePop();
```

**Compile:** `-lnvToolsExt` | **Profile:** `nsys profile --trace=cuda,nvtx`

**For complete patterns:** See `references/nvtx-patterns.md` for nested ranges, colors, and analysis workflows.

### Common Performance Patterns

| Symptom | Likely Cause | Investigation |
|---------|--------------|---------------|
| Low GPU utilization | Kernel launch overhead, CPU bottleneck | nsys timeline, look for gaps |
| Memory bound | Poor access patterns, low cache hit | ncu memory section, check coalescing |
| Compute bound but slow | Low occupancy, register pressure | ncu occupancy, reduce registers |
| Lots of small kernels | Launch overhead dominates | nsys timeline, consider fusion |
| High memcpy time | Excessive H2D/D2H transfers | nsys cuda_gpu_mem, batch transfers |
| Most cycles stalled | Bank conflicts, memory stalls | ncu SchedulerStatistics, check shared memory |
| High sectors/request | Poor coalescing (>4 sectors/req) | ncu memory metrics, use vectorized loads |

**Critical traps:** Bank conflicts and memory coalescing issues often dominate performance but aren't obvious without profiling. See `references/performance-traps.md` for detailed diagnosis and fixes.

**Reality check:** Budget 80% of optimization time for problems you didn't predict. Profile-driven iteration discovers the real bottlenecks.

## Compilation Reference

```bash
# Debug build
nvcc -g -G -lineinfo -O0 program.cu -o program_debug

# Release build
nvcc -O3 -lineinfo program.cu -o program

# Specific architecture
nvcc -arch=sm_80 program.cu -o program  # Ampere
nvcc -arch=sm_89 program.cu -o program  # Ada Lovelace
nvcc -arch=sm_90 program.cu -o program  # Hopper

# Generate PTX (inspect it)
nvcc -ptx program.cu

# Verbose compilation (see register usage)
nvcc --ptxas-options=-v program.cu

# With NVTX
nvcc program.cu -lnvToolsExt -o program
```

**Always compile with `-lineinfo` for production profiling** — minimal overhead, enables source correlation.

## Local API Documentation

Complete reference documentation available for grep-based search:

**PTX ISA 9.1** — `references/ptx-docs/` (405 files, 2.3MB)
- Search guide: `references/ptx-isa.md`
- Use for: Instruction-level optimization, inline PTX, TensorCore operations (WMMA, WGMMA, TMA), memory swizzling

**CUDA Runtime API 13.1** — `references/cuda-runtime-docs/` (107 files, 0.9MB)
- Search guide: `references/cuda-runtime.md`
- Use for: Error codes, API parameters, device properties (`cudaDeviceProp`), memory management, stream behavior

**CUDA Driver API 13.1** — `references/cuda-driver-docs/` (128 files, 0.8MB)
- Search guide: `references/cuda-driver.md`
- Use for: Context management (`cuCtxCreate`), module loading (`cuModuleLoad`), virtual memory, Driver errors (`CUDA_ERROR_*`), advanced features

Each search guide contains grep examples, documentation structure, and common usage patterns.

**Search strategy:** Use grep/ripgrep to search directly in the `*-docs/` directories. The search guides (`.md` files) provide navigation patterns and common queries.

## Additional References

- `references/performance-traps.md` — Bank conflicts, memory coalescing, scale-dependent optimizations
- `references/debugging-tools.md` — compute-sanitizer, cuda-gdb, cuobjdump detailed usage
- `references/nsys-guide.md` — nsys timeline analysis and bottleneck identification
- `references/ncu-guide.md` — ncu metrics, roofline, occupancy interpretation
- `references/nvtx-patterns.md` — NVTX instrumentation and profiling patterns

## Code Compliance Check

对涉及 GPU 的代码变更做全面高性能合规检查。任何涉及 GPU 操作的文件都在检查范围内。

### 基本规则

- **禁止 Triton**: 所有 kernel 必须用 CUDA C/C++ 编写。`import triton` / `@triton.jit` / `tl.*` 一律 FAIL（第三方库内部使用如 FlashInfer 除外）
- **禁止不必要的 D2H**: `.item()` / `.cpu()` / `.numpy()` / `.tolist()` 除非在非热路径的日志/调试中，否则 FAIL
- **禁止 CPU-GPU 隐式同步**: boolean mask indexing、`torch.nonzero` + indexing、`if tensor:` 等
- **以性能为第一优先级**: 正确但慢的代码不可接受

### 检查维度

**1. D2H 传输合理性 (Critical)**

| 模式 | 判定标准 |
|------|----------|
| `.item()` | 仅允许在非热路径的日志/调试中 |
| `.cpu()` | 如果是为了 numpy 计算，考虑是否可以全部在 GPU 完成 |
| `.numpy()` / `.tolist()` | 几乎总是错误的 |
| `tensor.data_ptr()` | 安全（不触发同步），但确认调用侧不会意外同步 |

不只看当前文件，追溯调用链确认 D2H 是否在 CUDA graph capture 路径上。

**2. CUDA Graph 兼容性 (Critical)**

| 禁止操作 | 替代方案 |
|----------|----------|
| `tensor[bool_mask]` | `torch.where(mask, val, fallback)` |
| `.item()` / `.cpu()` | GPU-resident 计算 |
| `torch.nonzero` + indexing | 静态 shape 操作 |
| `if tensor:` / `bool(tensor)` | `torch.where` |
| `cudaStreamSynchronize` | stream event |
| 动态 tensor 创建 | 预分配 + slice |

**3. Kernel 高性能 (Critical)**

- Python 循环调 kernel → 必须批处理或融合
- 小 tensor 频繁操作 → kernel launch overhead 可能超过计算本身
- 内存访问模式是否 coalesced？shared memory 是否有 bank conflict？
- occupancy 是否合理？block/grid size 是否匹配？
- 不必要的数据搬运（copy/transpose/contiguous）

**4. 调用正确性 (High)**

- shape/dtype/device 一致性
- kernel 是否假设了输入 contiguous？调用侧是否保证？
- 隐式 broadcast 风险

**5. 竞争与同步 (High)**

- 多 stream 访问同一内存 → 需要 event 同步
- `__shared__` 读写之间 → 需要 `__syncthreads()`
- atomic 操作是否必要？能否用 reduction 替代？

**6. 内存管理 (Medium)**

- 不必要的 `.clone()` / `.contiguous()`
- 循环内分配应提到外面或用 `fill_`
- 大 tensor 计算完及时 `del`

### 检查执行

1. 从参数获取文件，或用 `git diff --name-only` 筛选涉及 GPU 的文件
2. 逐文件执行上述 6 项检查，Grep + Read 定位问题
3. 对可疑 pattern 读取上下文（前后 10 行）判断是否在热路径
4. 追溯调用链 2-3 层确认 D2H / sync 是否在 graph capture 路径

### 判定规则

- 任何 Critical 项 FAIL → 整体 NEEDS_FIX
- 仅 WARN → 整体 PASS，列出改进建议
- Triton 禁令 FAIL → 必须给出 CUDA 替代方案方向

## Checklist Before Optimizing

- [ ] Established reproducible baseline timing
- [ ] Profiled with nsys to identify hotspots
- [ ] Know which kernel(s) dominate runtime
- [ ] Profiled target kernel with ncu
- [ ] Identified specific bottleneck (memory? compute? latency?)
- [ ] Formed specific, testable hypothesis
- [ ] Plan to change ONE thing
