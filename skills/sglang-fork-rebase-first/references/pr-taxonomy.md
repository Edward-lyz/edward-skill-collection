# 厂内 PR 分类法与 K3/GLM 实测分类清单

分类是一个三元组：**类别 × 模型标签 × 特性绑定**。类别决定迁移语义；模型标签让
同一份分类清单服务不同交付（给 GLM 追新时 K3 标签的 B 类不迁；K3 自己追新时照迁）；
特性绑定让 A 类里「只为某个可开关特性存在」的改动跟交付特性清单走——不开多模态
EPD / AttentionStore / DSpark，对应改动整块跳过。

## 判定树：对每张卡问四个问题

术语先对齐：用户说的「AS 链路」指上层网关那层的链路（网关透传的 header、rid、路由、实例
信息、探活），归 A1 平台链路；AttentionStore（asradix、`mem_cache/storage/asradix/*`、AS
coordinator）是 A3。两者缩写都像 AS，范围扩大时按这个区分，拿不准就问用户，不要自己合并。

**问题 1：社区新基线已有等价实现？** 是 → C1 丢弃。
命中形态：标题带社区 PR 号或 [Cherry-pick to release/*]；厂内先行、社区后收的能力
（例：mooncake 0.3.12.post1 bump 厂内 8 月初 pick，社区 #32302 同版本已收；
[Kimi] Support kimi-k3 整棵 57k 行的模型支持，社区现已内置）。
证据标准：NEW_BASE 里 rg 到等价符号/文件并 diff 覆盖厂内行为。厂内私改部分拆出来
按 A/B 类单独处置。

**问题 2：只对某个模型/checkpoint 生效？** 是 → B1（优化/适配）或 B2（BUGFIX）。
判据：文件路径带模型名（models/kimi_k3.py、K3 专属 kernel、K2.6 mxfp4 加载、
V4 组 batch 特判），或行为仅在该模型开启。**本次先梳理、rebase 时不迁移**（除非
交付就是该模型）。模型退役时这两类整块划走，这是分类清单长期省工的来源。

**问题 3：只为某个可开关的特性存在？** 是 → 归对应 A 类 + 打特性标签，交付不开
该特性时整块跳过。特性实例：多模态 EPD 栈、AttentionStore/asradix、DSpark 投机、
VL 专用 kernel。**打特性标签时先查社区有没有同名子系统**——厂内特性栈常是与社区的
平行实现。K3 实例：厂内 encode/EPD 栈 65 提交 / 2.4 万行全是 fork 独有文件
（encode_server_aiak.py、encode_stage.py），而社区在分叉点之前就有
disaggregation/encoder/ 全套框架（server/receiver/preprocessor/健康检查、EPD 指标
#27564、paged embedding pool #28441、encoder batching #31275）。这种情况下次开启该
特性的交付**默认取社区框架，diff 后只搬社区缺失的行为**（视频解码抽帧、解码进程
隔离、背压、AVI 兼容），不整栈 pick。

有同类实现时，分类清单只用两种写法：给社区框架补上缺的行为（视频抽帧、解码进程隔离、背压、
`task_results` 校验、`pp_size>1`、指标）写「吸收:部分 <搬哪个行为、落到社区哪个文件>」；
只修 fork 平行实现自己所在文件的提交（所在文件在 NEW_BASE 不存在，行为社区框架已有或不需要）写
「不迁:平行实现内部 <所在文件>」。判定只看符号在不在不够，重放时还要对社区 `encoder/` 的对应
函数逐行 diff，确认搬的是差异；diff 发现社区已有的，分类清单改回已收录。

**问题 4：剩下的按子系统归 A 类或工程类。**

下表的「迁移语义」描述的是类别本身迁不迁的倾向，本轮实际迁哪些以 SKILL.md 硬规则 3 为准：
默认迁 A1、A2、多模态和 C2，A4 里 F4 判为全模型受益的也默认迁，其余类别用户点名才迁。写「必迁」的类别没被点名时，照样记
「不迁:未点名类别」，并在 evidence 里标出线上缺陷修复这类值得建议用户补点名的提交。

| 类别 | 覆盖 | 迁移语义 |
|---|---|---|
| A1 链路适配 | 无条件核心：接口协议、tokenize 端点、PD 传输、PP 组合；特性绑定：EPD/encode 多模态栈 | 核心必迁；EPD 栈按特性走且先和社区同类实现 diff |
| A2 监控适配 | metrics、统一日志 schema、Trace/content_detection、pyspy | 必迁，量小 |
| A3 Cache 适配 | AttentionStore/asradix、KV 复用、mm_cache 边界 | 可选：交付不开 cache 整类跳过 + 发版 YAML 去开关 |
| A4 通用模型优化 | DCP 传输、fp8 KV、TokenSpeed MLA、DSpark 投机框架层、CP / MegaMoE 框架层 | 逐提交过下文 F1–F6；F4 判为全模型受益的默认迁，其余看交付模型 |
| A5 通用 BUGFIX | FC keepalive、tokenizer/stream、PP 同步、kernel 寻址溢出 | 必迁，单条量小 |
| C2 工程/CI | ci.yml、Dockerfile、单测流水、镜像依赖 | 跟发版方式走，多为独立文件 |
| X 噪声 | 成对 revert、历史搬运提交、merge 残留 | 出清单 |

边界判例（实测中最常犹豫的三种）：

- DSpark/DCP/CP/MegaMoE 这类「因某模型引入、改在框架文件里」的层：先按 F1 拆面，
  框架面按 F4 分三档：全模型受益的默认迁入；部分模型受益的看交付模型在不在受益名单里；
  只有一个受益模型的是挂在框架文件里的模型钩子，随该模型按 B1 处置。
  放在通用文件里不等于全模型受益：DSv4.1 `207a80780e`（CP 下支持 vision）改的是
  `eager_runner.py`，但只在模型有 `_prepare_mm_embeddings` 时生效，主线只有
  `models/deepseek_v4.py` 定义它，所以是单模型。
- 用户点名 A4 时列了子项（如「CP、DCP、MegaMoE、框架调度」），范围按用户列的算，不按上表
  A4 的「覆盖」列扩大：DSpark 投机没被点名就整块「不迁:未点名类别 DSpark」，标题带 DCP 但改动
  全在 `speculative/dspark_components/*` 的也一样（F1 先归特性块）。
- 「框架调度」指调度策略和吞吐类改动（分块成本模型、准入、批构造）。PP / PD 调度里的崩溃、
  abort、replay 修复归 A5，未点名就「不迁:未点名类别」并在 evidence 标「建议补点名」；用户
  若把它们也算进框架调度，逐笔过 F1–F6。拿不准时问用户，不要自己扩大。
- 一笔里混着排除特性和范围内改动（K3 `2caf5e5e94`：AttentionStore + PP 权重过滤 + K3 模型）：
  按 hunk 拆，排除特性那部分不迁，其余照常判；不要整笔随排除特性丢掉。只有拆不开（范围内
  改动依赖排除特性的符号）时整笔不迁，evidence 写清依赖了哪个符号。
- 模型提交里夹带的 C2 文件（K3 `a39f854b5e` 改 `gpu_requirements.env` 升 flash_kda wheel）：
  C2 hunk 只在它服务的东西也迁时才进镜像卡，否则随主体一起不迁。镜像文件路径以交付分支为准
  （厂内是 `dockerfile/Dockerfile`，社区是 `docker/Dockerfile`），不要往社区路径上写。
- FC parser 修复：接口行为修复归 A5；只对某家模型模板生效的（kimi k2 json parser）归 B2。
- K3 的 cache 数据/warmup 挂载：归 B1（数据与模型绑定），AttentionStore 机制本体归 A3。

## 框架层提交的吸收判据（CP / MegaMoE / 通用模型支持）

每轮都要跑：fork 里所有 A4 候选（`scope_hint=framework`）以及用户点名的框架层改动（CP、DCP、
MegaMoE、量化 GEMM 路由、调度与显存策略等）都逐笔过一遍。核心问题是 F4：**是不是所有模型
都受益**。全模型受益的默认迁入；只有部分模型受益的，交付模型在受益名单里才迁；只有一个模型
受益的随该模型走。
shadow 分支没有单独的「框架」类，这类改动散在 [性能优化]、[模型适配]、[BUGFIX]、[其他]
的 squash 里。**判定单位是源提交**：按 squash 正文「来源提交」回到原 SHA 逐笔判，不按
squash、不按卡。先复核类别：[性能优化] 里混着监控（DSv4.1 的 luno-3716/4170 三笔）和
AttentionStore（6ab7e448be），先归回 A2/A3，不进本判据。

按 F1→F6 顺序判，命中结论就停：

**F1 拆面。** 按路径把每笔的 hunk 分成两面：
模型面 = `models/*`、路径或文件名带模型名（`dsv4/`、`kimi_k3/`、`glm5/`、
`deepseek_v4_backend.py`）、只被模型文件 import 的新文件；框架面 = 其余 `srt/`、
`kernels/`、`jit_kernel/` 改动，含 `environ.py` 新开关。框架文件里按模型条件分岔的分支
（`getattr(moe, "is_hash", False)`、`getattr(moe.config, "image_token_id", None)`）也算
模型面。fw% = 框架面新增行 / 总新增行，只用来预排：< 35% 整笔按模型面处置（B1）；
35–85% 是混合提交，两面分开判；≥ 85% 整笔走 F2–F6。模型面一律按 B1 走模型轴。
模型面按交付模型的类继承链判，不只看文件名：GLM 的 `GlmMoeDsaForCausalLM` 继承
DeepseekV2，`models/deepseek_v2.py` 的改动对 GLM 交付就是交付模型自己的模型面。先在
NEW_BASE 上 `rg -n 'class <交付模型类>\('` 把父类链列出来，链上的模型文件和它们的专属
后端都算交付模型；`fork_pr_inventory.py` 的 model 列只按文件名打标签，人工复核时按链改。
特性绑定路径（`speculative/dspark/`、`engram_*`、asradix）既不算模型面也不算通用框架面，
先按问题 3 归特性块，再看交付开不开；`fw_pct` 列把它们算在框架面里，人工复核时扣掉。

**F2 已收录。** 框架面在 NEW_BASE 有等价实现 → C1，diff 后私改拆出来继续 F3–F6。
先在 NEW_BASE 全树按符号查，不要只看原路径：社区大重构会让路径命中率接近零（GLM 实测：
`nsa` → `dsa`、Scheduler mixin → `scheduler_components`、collector → observability）。
等价按符号和行为判，逐行原文匹配会漏掉社区改名后的实现：DSv4.1 `583c5aac5b` 原文命中只有
15%，但 NEW_BASE 用 `decode_tp_size_aligns_prefill_world_size` 实现了同一逻辑，真正剩下的只有
两处残余。原文命中率低时先 rg 关键条件和调用点，再定 C1 还是吸收。
例：luno-5318 `fca9e8f887` 加的 megagate / megamhc，社区主线已有
`layers/moe/mega_gate.py`、`kernels/ops/moe/mega_gate.py`、`kernels/ops/layernorm/mhc_mega.py`。

**F3 落点。** 框架面改的文件和符号在 NEW_BASE 上还在吗？在 → 继续。不在、但社区有同职能
模块 → 同类实现，取社区框架只搬差异（同问题 3），例如 fork 的 `communicator_dsa_cp.py` 社区
没有，社区 CP 走 `layers/cp/*` 与 `layers/dcp/*`。不在、也没有同类实现 → 这等于新建一个子系统，
按特性栈处理，用户点名才迁。

**F4 受益面。** 在 NEW_BASE 加本次重放集上，数框架面新符号或新开关被几个模型用到：

```bash
rg -l '<新符号或开关名>' python/sglang/srt/models | wc -l     # 直接消费的模型文件
rg -l '<新符号或开关名>' python/sglang/srt -g '!models/**'    # 是否有模型无关入口
```

按受益面分三档，档位写进 evidence（`F4 全模型` / `F4 部分:<模型列表>` / `F4 单模型:<模型>`）：

| 档位 | 判定 | 去向 |
|---|---|---|
| 全模型 | 入口与模型无关，任何模型走到这条路径都生效：scheduler、tokenizer/detokenizer、PD 传输、runner 通用分支、通用量化与 MoE 路径（`fp8_utils.py`、`mega_moe.py` 本体）；代码里没有按模型名、`model_type`、模型专属方法分岔 | 默认迁入，不需要用户点名；继续过 F5、F6 |
| 部分模型 | 新符号被 ≥ 2 个模型消费，或通用文件里的分支只在模型具备某个能力时生效（有 vision、走 MLA、用 hash MoE） | 交付模型在受益名单里才迁，否则「不迁:F4 交付模型不受益」 |
| 单模型 | 只有 1 个模型消费，或分岔条件只有 1 个模型满足 | 随该模型按 B1 |

判全模型时要看生效条件，不只看文件路径：通用文件里 `getattr(model, "<方法>")`、
`hasattr(model, ...)`、`model_type ==` 这类守卫，要 rg 主线有几个模型满足，满足的模型数决定档位。
注册表、`getattr` 动态分派 rg 数不到，要人工看分派点。
例：`207a80780e`（CP 下支持 vision）改在 `eager_runner.py`，守卫是
`hasattr(model, "_prepare_mm_embeddings")`，主线只有 `models/deepseek_v4.py` 定义 → 单模型。
`583c5aac5b` 里的 W4A4 MegaMoE group-size fallback 改在 `mega_moe.py` 通用路径，任何
`moe_intermediate_size` 不是 512 倍数的 W4A4 模型都用得上 → 全模型。
`kernels/ops/layernorm/mhc.py` 在主线被 deepseek_v4*、
glm5_next、xing4_0 消费，通用。luno-5437 `2099e8a901` 加了 6 个开关，要逐个数：
`SGLANG_FUSE_CP_LAST_TOKEN_GATHER` 只在 `eager_runner.py` / `logits_processor.py` 消费，
走的是通用 `InterleaveCPStrategy`，入口模型无关，算框架通用；另外 5 个
（`FUSE_TAIL_*`、`FUSE_CP_KV_STORE_LOCAL_FIRST_TAIL`）只在 `models/deepseek_v4.py`、
`deepseek_v4_backend.py`、`dsv4_attn_metadata_kernels.py` 消费，是 DSv4 钩子。
`mega_moe.py` 本体在主线被 deepseek_v2/v4、kimi_k3、minimax_m3、
qwen2_moe/qwen3_moe 等消费，属于通用；fork 在里面加的 hash 层与 VL 分支拆到模型面。

**F5 默认行为与证据。** 只决定怎么迁，不推翻 F4 的全模型结论：

- 默认关闭的开关：全模型档直接吸收，开关保持默认关，交付 YAML 想开再开；部分模型档仍按
  交付 YAML 是否打开决定，不开就「暂缓:F5 开关默认关」。
- 改了默认路径（开关默认开）：必须有 NEW_BASE 上同 shape、同 checkpoint 的性能和精度实测，
  旧基线的收益不算数。有实测按原默认值吸收；没有实测也吸收，但把默认值改成关，evidence 写
  「F5 默认值改关，待实测」。
- 改了默认路径且没有开关：没有实测就暂缓，补迁条件写「补齐 NEW_BASE 实测」。

例：`576b74befa` 的 `SGLANG_MHC_USE_DEEPGEMM` 默认 `"1"`，属于改默认路径；`b029ecea99` 的
`SGLANG_OPT_BLOCK_FP8_MXFP8_DEEPGEMM` 默认 `False`。

**F6 社区热度与单测。** 数框架面每个文件在 `OLD_BASE..NEW_BASE` 的社区提交数，再跑这些文件
对应的社区单测：

```bash
git log --oneline "$OLD_BASE_SHA..$NEW_BASE_SHA" -- <文件> | wc -l
```

≥ 5 笔算热文件，不能按旧上下文搬，按 references/resolution-laws.md 的 L2/L9 在新结构上重实现并预留时间。
重实现后社区单测失败，说明厂内改动和社区设计冲突，不迁，也不改社区测试（luno-5298
`459ff8222e` 让 56 个 `test_prefill_result_polling` 失败）。2026-10-01 以来主线热度：
`fp8_utils.py` 26、`mega_moe.py` 19、`eager_runner.py` 12、`logits_processor.py` 11、
`mhc.py` 11、`layers/cp/interleave.py` 7。

结论只有五种，连同命中的判据号写进 decision 列（如「暂缓:F5 开关默认关」）：

| 结论 | 去向 |
|---|---|
| 吸收 | A4，按原拓扑序重放；热文件按 L2/L9 重实现 |
| 随模型 | B1，交付是该模型才迁 |
| 已收录 | C1，私改拆出后各自再判 |
| 暂缓 | 不迁，记 SHA、开关名和补迁条件（交付开开关 / 补齐实测） |
| 不迁 | 与社区设计冲突或被社区单测钉住，记原因 |

decision 列冒号前只能是这五个词，脚本按它分组。部分吸收、部分已收录写在冒号后：
`吸收:部分 F4 只迁 KEEP_NEW_SF_ONLY，其余已收录`。不要写成「部分吸收」「吸收(部分)」，
DSv4.1 和 GLM 两轮各写了一种，按前缀取源集合时会漏掉。

DSv4.1 flash `[性能优化]`（37 笔来源）的实测判例：

| 源提交 | 内容 | fw% | 命中 | 结论 |
|---|---|---:|---|---|
| `fca9e8f887` luno-5318 | megamhc / megagate | 69 | F2 主线已有 | 已收录；私改与 DSv4 分支拆出 |
| `583c5aac5b` luno-5232 | W4A4 MegaMoE down-GEMM group-size fallback | 90 | F2 主线 `check_mega_moe_shapes` 仍要求 `mxf4xmxf4` 下 intermediate %512；F4 全模型 | 吸收 |
| `b029ecea99` luno-5354 | block-fp8 dense GEMM 走 DeepGEMM | 100 | F4 全模型；F5 默认关；F6 热 | 吸收，开关保持默认关，按 L2/L9 重实现 |
| `c833093f7c` 等 luno-5274 | PD prefill forward 线程化 | 100 | F4 全模型；F5 默认关；F6 热（`prefill.py`、`scheduler.py`） | 吸收，重实现 |
| `77b5614d96` luno-5633 | 连续准入与成本调度 | 100 | F3 新子系统；F4 全模型；F5 默认关 | 吸收，3 个新文件整块重放 |
| `d46eb2dae5` `7c4d77e2a9` | 投机 + xgrammar host 开销 | 100 | F4 全模型；F5 开关默认开 | 吸收；无实测时默认值改关 |
| `14b3e4d1c9` | MoE 路由权重 fp32 + all-reduce 融合 finalize | 100 | F4 全模型；F5 改默认路径且无开关 | 暂缓，补齐 NEW_BASE 实测再迁 |
| `2099e8a901` luno-5437 | prefill-CP / 尾层融合 | 34 | F1 模型主导；last-token gather 走通用 `InterleaveCPStrategy`，F4 全模型、F5 默认关 | gather 开关吸收；5 个 DSv4 开关随模型 |
| `576b74befa` luno-5222 | mhc 走 DeepGEMM | 100 | F4 部分:deepseek_v4*/glm5_next/xing4_0；F5 开关默认开 | 交付是其中之一才吸收，无实测时默认值改关 |
| `207a80780e` luno-5211 | CP 下支持 vision | 84 | F4 单模型：守卫 `_prepare_mm_embeddings` 只有 deepseek_v4 定义 | 随模型 |
| `0845fd13f6` luno-5297 | 显存优化 | 59 | F1 混合；框架面 4 个热文件 | 拆面；框架面逐 hunk 过 F4–F6，DSpark 部分按特性 |
| DSv4 CP KV 存储 | `kernels/ops/attention/dsv4/cp_kv_store.py` | — | F1 路径带模型名 | 随模型 |
| `459ff8222e` luno-5298 | PD prefill 轮询合并 | 100 | F6 社区单测失败 | 不迁 |

GLM 与 K3 同理：GLM 的 `jit_kernel/csrc/glm5/mega_moe_tail.cuh` 在 F1 就落到模型面；K3 的
`layers/dcp/comm.py` 主线已有，走 F2/F3 后再按 F4 数受益模型。

## K3 分支实测分类清单（2026-09-07）

语料：ds-dev-kimi-k3-0819-opt ^a23f6ea090（社区 2026-07-25 基线），226 个非 merge
提交，52 张卡。逐提交明细与链接见
PRIVATE/project/aiak_sglang/rebase_first_20260907/k3_pr_inventory.tsv。

| 类别 | 提交 | 行数 | 冲突史交叠 |
|---|---:|---:|---:|
| A1 链路适配 | 65 | 25,807 | 83 |
| A2 监控适配 | 13 | 1,860 | 23 |
| A3 Cache 适配 | 15 | 14,779 | 20 |
| A4 通用模型优化 | 9 | 1,296 | 21 |
| A5 通用 BUGFIX | 26 | 1,503 | 39 |
| B1 模型优化/适配 | 34 | 15,182 | 67 |
| B2 模型 BUGFIX | 9 | 724 | 17 |
| C1 社区已收录 | 34 | 63,836 | 227 |
| C2 工程/CI | 17 | 2,773 | 0 |
| X 噪声 | 4 | 6,415 | 36 |

读法：

- A1–A5 合计 128 提交 / 45,245 行，再按特性轴拆：**无条件核心仅 41 提交 / 3,625 行
  （占全量 4%）**；多模态 EPD 栈 65 提交 / 24,287 行（社区有同类实现，见问题 3）；
  AttentionStore 16 提交 / 14,801 行；DSpark/VL kernel 4 提交 / 1,097 行。
  文本交付不开 AS/投机时，pick 集就是那 41 提交。还可以再细分成更小的 pick 单元（core-link/core-metrics/core-model-opt/core-bugfix + feat-*/model-*），并用 git merge-tree --write-tree --merge-base=<父> <新基线> <提交> 逐个提交做不改工作区的冲突预演；注意 sim 是单个提交单独 pick 的结果，同组按顺序连续 pick 时实际冲突会比 sim 多。
- C1 一类占了最大冲突面（227 文件次）：双方各有一份的内容在整支 merge 里全是
  add/add 与改动碰撞，在 rebase-first 里一行不用动。
- A1 的 2.6 万行里 fork 独有文件过半（EPD/encode 平行实现），pick 本身接近零冲突——
  但零冲突不等于该 pick，同类实现判定优先于难度判定。
- 六张混合卡（luno-3716/4648/4671/4784/4170/4311）贡献了逐提交覆盖分类的全部工作量，
  也是「难(先拆)」的全部来源。分类清单越干净，pick 成本越低——**日常开发一卡一主题，
  就是在给下一次追新降价**。

## GLM-5.3-Flash：同一交付的新旧路线对照

| | 旧路线（2026-08-27 实测） | 新路线（按分类清单推算） |
|---|---|---|
| 第一步 | merge 社区进厂内，冲突 217 文件/590 块 | 从社区分支开 worktree，零冲突 |
| 处理量 | 4,692 文件 / +485k 行一次落地 | 无条件核心 41 提交 / 3.6 千行 + 按特性勾选（EPD 2.4 万 / AS 1.5 万 / DSpark 2.5 千） |
| K3/K2.x/V4 专属 | 43 提交 / 1.6 万行全部带上 | 不迁移 |
| 社区已收录 | 227 文件次冲突的主要来源 | 免费消失 |
| 送审形态 | 1 个 3,570 文件的 squash CR | 逐卡 change，保工单号与评审粒度 |
| 合并后缺陷 | M1–M9 九类 + 3 个修复提交 | 每卡单一意图，门禁逐卡跑 |

厂内先例：GLM-5.2 线 0.5.16→0.5.17 已按此法完成（origin/ds-dev-community-0517-glm，
社区 release 基线 + d2397efab8 一个厂内合入提交 + 2 个修复）；0.5.18 基线分支已开出
待 pick（origin/ds-dev-community-0518-glm），即「换基线完成、重放未开始」的中间态。

## 链接规范（离线可推导）

- 工单页：http://newicafe.baidu.com/v5/issue/{card}/show
- 提交页（可跳 CR）：http://console.cloud.baidu-int.com/devops/icode/repos/{repo}/commits/{sha}
- CR 号不能离线由 Change-Id 反查（icode 的 gerrit ssh query 需要内部 RepoName 参数，
  外部拼不出），追溯统一走上面两个入口。

