# 合并情形分类

`resolution-laws.md` 讲的是「这一处冲突按哪条不变量解」，这份表讲的是「合并做完之后
还剩哪几类会静默存活的缺陷，每类怎么找、怎么修」。它们都不是冲突：三方合并按行工作，
以下每一类在 `git merge` 眼里都是干净的。

每条给出判定信号、正确做法、检测手段，以及一个真实实例（SGLang fork 与
`community/glm-5.3-flash-support` 的两父合并，217 文件 / 590 hunk）。

## M1 同一文件两侧都改：一侧是 fork 的 bug fix，一侧是上游的新 API

判定信号：冲突文件里 fork 的改动带「为什么这么写」的注释（溢出、对齐、越界、精度），
上游的改动是新增公开函数或换算法写法。

正确做法：按 hunk 合，不按文件取。fork 的 bug fix 连注释一起保留；上游新增的公开 API
必须补齐，因为上游的调用方也一起合进来了。两边改的是同一段算法时，先写清各自要保的
性质，再合成一份实现。

检测：`import_audit.py` 的 `missing-symbol` 抓「上游 API 没补齐」；fork bug fix 被吃掉
这一半静态查不出来，要对 fork 侧带注释的 hunk 逐条确认。

实例：`kernels/ops/attention/vision_rope.py`。fork 把索引运算加宽到 int64（修长视频下
int32 溢出导致的 CUDA illegal memory access），上游新增 `PreparedInplaceComplexRoPE`
与两个 `*_inplace` 函数、并把 store 改成 `tl.fma`。整文件取 fork，上游的
`models/kimi_k25.py` 直接 ImportError；整文件取上游，越界修复丢失。

## M2 上游重命名或移动模块，fork-only 文件的 import 无人修改

判定信号：上游这轮有目录级重构，fork 有一整套只存在于 fork 的子系统。两边没同时改同
一个文件，所以零冲突。

正确做法：合并后拿「上游删除或重命名的模块清单」反查全树引用，把 fork 侧的 import 改
到新路径。不要把旧模块补回来制造两份实现。

检测：`import_audit.py` 的 `missing-module`，必须全树扫，不能只扫改过的文件。

实例：上游把 `srt/mem_cache/unified_cache_components/` 拆成
`srt/mem_cache/unified_cache/{component_type,components}/`；fork-only 的
`mem_cache/storage/asradix/{plans,checkpoint_coordinator}.py` 仍 import
`sglang.srt.mem_cache.unified_cache_components`，合并后必然 ImportError。

## M3 fork 侧遗留的坏引用，在新特性组合下第一次被执行

判定信号：某个 import 或引用在两个父提交上就已经指不到东西，但它所在的模块平时不被
加载，本次交付要开的特性刚好会加载它。

正确做法：落在交付目标必经路径上的继承缺陷要一起修，不能以「父提交也这样」为由留下。
修法是删除，不是注释掉——注释掉的 import 下一次合并还会被当成需要保留的一行。

检测：`import_audit.py` 把 `INHERITED` 与 `--critical-path` 交叉判定；只报「相对父提交
新增」的门禁会漏掉这一类。

实例：`srt/layers/attention/dsv4/indexer.py` 里 fork 侧多出一行
`from sglang.srt.layers.quantization.fp8_kernel import is_fp8_fnuz`，该模块两个父提交都
没有，而同一个符号上一行已经从正确模块导入过。不开 EAGLE 时不加载 indexer，所以从没
人踩到；开 MTP 当场 ModuleNotFoundError。

## M4 fork-only 逻辑对上游新引入的类型做了隐含假设

判定信号：fork 独有的代码读某个对象的属性或按类型分支，而这个对象的具体类由上游决定，
上游这轮引入了新模型、新后端或新 pool 实现。

正确做法：把裸属性访问换成能覆盖所有实现的取值函数，拿不到时显式报错，不要静默兜零；
新旧两类实现都在函数 docstring 里点名。

检测：静态查不出来。只能按交付目标枚举特性组合，把这条路径真跑一次；跑不了就写
deferred 并点名未验证的组合。

实例：PD 传 draft KV 时 `self.draft_token_to_kv_pool.head_num`。DeepSeek 系 MTP 的
draft pool 是 MHA，有 `head_num`；GLM-5.3-Flash 的 MTP 头共用 target 的 latent 布局，
draft pool 是 MLA 系，没有 `head_num`，开 MTP 起服务就 AttributeError。修法是
`get_draft_kv_head_num()`：先取 `head_num`，取不到退回 `kv_buffer[0].shape[1]`。

## M5 调用方与被调方来自不同父提交

判定信号：冲突量大时按目录整取（kernels 取 fork、models 取上游），于是新调用方和老被
调方拼在一起。

正确做法：目录级 `--ours` / `--theirs` 之后，把「一侧新增的调用方」列出来，逐个确认它
依赖的符号在最终树里存在、签名也对得上。

检测：`import_audit.py` 的 `missing-symbol` 加 `interface_delta.py`。

实例：同 M1 的 `kimi_k25.py` 与 `vision_rope.py`。

## M6 签名、参数顺序、异常类型变化

判定与做法见 `resolution-laws.md` 的 L12 和 Caller/Callee Re-Pairing Shapes，7 种形状都
不产生冲突。检测靠 `interface_delta.py` 加 `parent_test_delta.py`。

## M7 上游删掉了 fork 还在用的能力

判定信号：冲突表现为「上游这边整段没了」。

正确做法：先找上游的替代品，有替代就迁过去；没有替代就保留 fork 实现并接到上游的扩展
点（见 L2 / L9），不要因为「看起来有相似代码」就判为已吸收。

检测：`parent_test_delta.py`，以及对该能力的调用方逐个确认。

## M8 只有开关打开才走到的路径

判定信号：交付目标要开的特性（MTP / EAGLE、某个 attention 后端、EP、hicache、PD 分离）
在默认配置下不加载对应模块。

正确做法：先把交付目标要开的 flag 组合列成清单，再逐个组合做最小验证：import 得通、
服务起得来、一条请求打得通。清单和验证结果一起写进 CR 描述。

检测：`import_audit.py --critical-path` 覆盖静态那一半，剩下一半只能跑。开关本身还有
档位：自适应类特性（例如 adaptive speculative decoding）会在运行时改变步数与 draft
token 数，低档位是独立代码路径，必须让它真的进过一次，压测或手工把每个档位都固定跑一遍。

实例：本次 M1 / M3 / M4 三个缺陷在 MTP 关闭时全部静默，开 MTP 后两个当场炸。另一例在
压测中出现：自适应控制器把 speculative steps 降到 0 后走进 1 节点 verify 分支，那里把
int32 的 bonus_tokens 当成 candidates 传给只接受 int64 的采样 kernel，8 个 scheduler
同时抛异常退出，HTTP 进程还活着，外部只看到 health check 一直超时。两个父提交在该处
代码完全一致，属于 M3 而不是合并引入。

## M9 特性开关被丢掉、或者还在但变成空开关

判定信号：某个 flag 只有一个父提交声明；或者 flag 还在，但读它的代码没了。两种情况都
不产生冲突，起服务也不报错——CLI 依旧接受这个参数，只是不再有任何效果。

正确做法：先看上游是不是把整套能力（flag 加消费方）一起删了。是就确认场内有没有人在用
这个参数，没人用才允许跟随删除，并在 CR 描述里点名；有人用就得把能力接回上游的新结构。
flag 还在但读者没了的情况一律当 blocker：参数看起来生效，实际什么都没做。

检测：`flag_inventory.py` 比对配置 dataclass 在两个父提交与最终树上的字段，报出
DROPPED / DEFAULT-DRIFT / NO-OP / DEAD 四类；再用 `rg -l -- '--flag-name'` 扫场内的
部署仓库，确认哪些开关真的在用。

实例：这次合并丢了 `torchao_config` 和 `enable_expert_distribution_metrics` 两个 fork
侧字段——上游把两套能力连消费方一起删了，场内 YAML 也没人传，可以跟随。另有 8 个场内
开关（`disaggregation_zmq_ports`、`disaggregation_zmq_max_sockets`、
`enable_asradix_cache`、`per_node_gpu_num`、`vit_server_url`、`enable_task_results_pull`、
`enable_mooncake_in_zmq_mode`、`embedding_ib_device`）逐个比对过消费方文件集合，合并前后
完全一致；其中 `enable_task_results_pull` 在两个父提交里就没有任何读者，属于 DEAD——场内
54 个 YAML 在传一个空开关。

## 处置「public symbol 在最终树里不存在」

`interface_delta.py` 的 HIGH 行只说明符号名在最终树里查不到，不等于能力丢了。按顺序查：

1. 全树搜同名符号：类被上游搬到别的文件时，调用方仍然解析得到，属于误报；
2. 找改名后的孪生实现：上游改名常常照抄原注释，拿原实现的注释或 docstring 原文去搜，
   比按名字猜命中率高；
3. 查两个父提交里有没有调用方：本来就没人调用的，是 fork 自己的死代码，删掉无害；
4. 以上都不成立，才是真的能力丢失，按 M7 处理。

实例：本次 5 条 HIGH 全部落在前三种。`CommonKVSender.poll` 等三个是上游把类挪到
`base/conn.py`、`mori/conn.py`；`page_indices_to_cp_rank_page_indices` 在 fork 里就没有
调用方；`war_fastpath_runner` 被上游改名成 `last_shared_read_runner`、
`war_fastpath_read_done_event` 改成 `shared_read_done_event`，注释原文一字未改，靠注释
搜出来的，WAR barrier 的快路径其实完整保留。

## 上一版门禁为什么没抓到

四个盲区，都已经补进流程：

1. 静态检查只跑在改过的文件上。M2 和 M5 的坏引用在没冲突的文件里，必须全树跑。
2. 门禁只报「相对父提交新增」的问题。M3 是继承缺陷，落在必经路径上照样是 blocker。
3. 没有 import 可解析性这一层。`ruff` 不判断模块是否存在，`import_audit.py` 补这层。
4. 没有按交付目标枚举 flag 组合。M4 只能靠跑，跑不了就必须写成 deferred 而不是沉默。
