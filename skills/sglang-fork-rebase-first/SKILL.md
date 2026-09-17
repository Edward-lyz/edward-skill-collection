---
name: sglang-fork-rebase-first
description: 追社区新版本的二分法：社区基线直换 + 厂内 PR 台账化选择重放。先把 fork 相对旧基线的提交按七类台账化（链路适配、监控适配、Cache 适配、通用模型优化、通用 BUGFIX、具体模型优化、具体模型 BUGFIX），社区已收录直接丢弃、非交付模型的专属改动不迁移、特性绑定的改动（多模态 EPD/Cache/投机）按交付特性清单取舍，剩余按原始拓扑序逐卡 pick 到新基线；重放完成后按平台契约反向核对路由全集、启动参数、指标 label 与环境变量读取点；交付镜像的四件套（ci.yml + build/build.sh + dockerfile/）照厂内已有交付分支的格式改并放在栈底，继承来的每一步按 base 专属 / 运行时通用 / 版本锚判类。触发词：追社区、升级基线、base swap、厂内 PR 梳理、rebase 到新版本、交付镜像换基础镜像。适用于 fork 与上游长期分叉、整支 merge 成本已失控的仓库；pick 冲突语义与合并后门禁复用 sglang-pr-rebase-or-pick。
---

# 追社区：基线直换 + 台账化重放

## 为什么把方向反过来

旧路线是把社区新版本 merge 进厂内分支。GLM-5.3-Flash 那次的实账：merge diff 4,692
文件 / +485k 行，冲突 217 文件 / 590 块逐处人工判，送审被迫 squash 成一个 3,570 文件
的 CR，评审粒度归零，合并后又冒出 M1–M9 九类不产生冲突的静默缺陷，追了 3 个修复提交
和多轮镜像返工。根因：merge 把「社区已收录的内容 + 厂内全量历史」按行搅在一起，
双方各做过一遍的东西（fork pick 过的社区补丁、被社区吸收的模型支持）制造了最大的
冲突面，而它们本来一行都不需要动。

新路线二分：

1. **基线直换。** 新分支直接从社区目标版本开出，这一步无冲突，按构造成立。
2. **厂内 PR 台账化重放。** fork 相对旧基线的提交先分类，只把必要的类逐卡 pick
   上去。冲突仍会有，但每个冲突落在单一意图、单一 owner 的小补丁里，可判可审。

K3 分支实测（226 提交 / 13.4 万行的厂内谱系）：社区已收录 34 提交 / 6.4 万行在新基线
下免费消失；非交付模型的专属改动 43 提交 / 1.6 万行显式不迁移；特性绑定的改动只在
交付开启对应特性时迁（多模态 EPD 栈 2.4 万行——社区已有平行框架，开启时也先 diff
再搬 delta；AttentionStore 1.5 万行；DSpark/VL kernel 1 千行）；**无条件必迁只剩
41 提交 / 3.6 千行（3%）**。完整台账见 references/pr-taxonomy.md。

## 何时使用

用户要把厂内 fork 追到社区某个新版本（换基线），或要求梳理厂内 PR 台账。
不适用：把上游一段提交搬进厂内旧基线、或单卡 cherry-pick——那是
sglang-pr-rebase-or-pick 的场景。两个 skill 的分工固定：本 skill 管策略、台账和
pick 编排；每处冲突的语义判定（L1–L12）、合并后静默缺陷（M1–M9）、八门禁与
waiver、跨组件契约验证，全部沿用 sglang-pr-rebase-or-pick，不重复实现。

## 硬规则

1. 冻结三个引用再动手：FORK_SHA（厂内 tip）、OLD_BASE_SHA（merge-base(fork, 社区)）、
   NEW_BASE_SHA（要追的社区版本）。台账与 pick 全程用冻结值。
2. 没有分类台账不开始 pick。台账 = 脚本生成的信号 + 人工定类，分类结论落盘进产物目录。
3. pick 集相对交付判定，两根轴：**模型轴**——B 类只在交付就是该模型时迁（给 GLM
   追新，K3 专属不迁；K3 自己追新照迁）；**特性轴**——特性绑定的 A 类改动只在交付
   开启该特性时迁（不开多模态 EPD / AttentionStore / DSpark 整块跳过）。台账里
   类别、模型标签、特性是三个独立字段。
4. 丢弃要有证据。C1 的每一条要么标题带社区 PR 号，要么能在 NEW_BASE 里指到等价实现
   （rg 符号或文件）。厂内 pick 时常带私改：diff 厂内版与社区版，私改部分拆出来按
   A/B 类处置，不能凭标题相似整条丢。
5. 选择按分类，重放按原始拓扑序。原分支按时间演进，原序天然满足卡内与卡间依赖。
6. 逐卡送审，保留原工单号；同一变更迭代复用 Change-Id。每卡 pick 完跑该卡子系统的
   门禁，不攒到最后一次性跑。
7. worktree 隔离、不直推保护分支、跑不起来记 deferred 不记 pass——同 sibling skill。

## 流程

### 0 冻结与台账

```bash
FORK_SHA=$(git rev-parse --verify "$FORK_REF^{commit}")
NEW_BASE_SHA=$(git rev-parse --verify "$NEW_BASE_REF^{commit}")
OLD_BASE_SHA=$(git merge-base "$FORK_SHA" "$NEW_BASE_SHA")

python3 "$SKILL_DIR/scripts/fork_pr_inventory.py" \
  --repo "$REPO" --fork "$FORK_SHA" --old-base "$OLD_BASE_SHA" \
  --conflict-paths "$PREV_MERGE_CONFLICT_LIST" \
  --card-pattern 'luno-[0-9]+|aihc-qa-[0-9]+' \
  --icafe-template 'http://newicafe.baidu.com/v5/issue/{card}/show' \
  --icode-template 'http://console.cloud.baidu-int.com/devops/icode/repos/baidu/hac-aiacc/aiak_sglang/commits/{sha}' \
  --output-dir "$ARTIFACTS"
```

产出 inventory.tsv（逐提交：规模、fork 独有文件数、冲突史交叠、类别 HINT、链接）和
cards_summary.md（卡片聚合）。HINT 只是关键词启发，**每张卡人工定类，混合卡逐提交
定类**，把最终 cat 列改回 TSV。--conflict-paths 给上一次整支 merge 的冲突文件清单，
没有就省略（难度预判少一个信号，不影响分类）。

### 1 用户确认 pick 集

拿台账问三件事：交付模型是什么（决定 B 类去留）；交付开启哪些特性（多模态 EPD、
AttentionStore、DSpark、VL——不开的特性块整块跳过，发版 YAML 同步去开关；开启且
社区有 rival 实现的，先 diff 社区版再定搬什么）；C2 工程物（ci.yml、Dockerfile、
单测流水）哪些跟着新镜像走。确认结果写进台账的 decision 列。

### 2 基线直换

```bash
git worktree add -b "$CANDIDATE_BRANCH" "$WORKTREE" "$NEW_BASE_SHA"
```

第一步到此完成。不要在这一步夹带任何厂内改动。

### 3 清单消噪

pick 清单生成前先做三件事：成对 revert 互消（A 提交 + 后续 Revert "A" 同时出现则
双双出清单）；历史搬运提交跳过（标题形如 "Pick aiak code"、"merge X into Y" 的
大杂烩，其内容已被后续演进覆盖，pick 它等于回滚后面的修复）；同卡 fixup 折叠——
一张 39 提交的卡有一半是对前一半的补丁（补 import、编码规范、改签名），按卡折叠成
一个补丁再重放：

```bash
git diff "$CARD_FIRST^..$CARD_LAST" -- $CARD_FILES > "$ARTIFACTS/patches/$CARD.patch"
```

混合卡例外：先按逐提交分类拆开，再各自归类折叠。

### 4 逐卡重放

按原始拓扑序（git log --reverse --topo-order 过滤出选中集）逐卡 cherry-pick 或
git apply 卡级补丁。commit message 保留工单号，正文记录来源短 SHA 区间。冲突逐处按
sibling skill 的 L 律判定；社区侧结构变了的，按 L2/L9 把厂内行为接到新结构上，
不要凭形似判「已吸收」。每卡完成后立即跑：

```bash
python3 "$SIBLING/scripts/import_audit.py" --repo "$WORKTREE" \
  --parent "$NEW_BASE_SHA" --critical-path <该卡子系统 glob> \
  --output "$ARTIFACTS/import-audit-$CARD.md"
```

加该卡子系统的仓库自带测试。红了当场修，修完重跑，不带病进下一卡。

### 5 全量门禁与交付验证

全部卡重放完，按 sibling skill 跑 run_gates.sh 八门禁 + 交付特性组合清单
（模型、attention 后端、MTP、EP、PD 分离、cache）+ 跨组件契约三观测点。
两个专项检查：

- B 类跳过后的悬挂引用：A 类代码里 import 模型专属模块的行要跟着裁，import_audit
  的 NEW 段会报。
- C1 丢弃后的行为差：厂内 pick 版与社区收录版不一致的私改，确认已按硬规则 4 拆出。

### 6 交付镜像四件套

C2 里的镜像改动按厂内已有格式改：`ci.yml`、`build/build.sh`、`dockerfile/Dockerfile`、
`dockerfile/gpu_requirements.env`，模板取 origin 上**同类 base**（社区镜像 / 厂内
aiak-inference 镜像）的最近交付分支。DSv4.1 那次我另造了 `dockerfile/Dockerfile.dsv41`
+ `dockerfile/build_dsv41.sh`，流水线按固定路径取文件、自创的名字它不看，整卡被打回重做。

这一卡放在**栈底**。社区树里没有 ci.yml，基线直换后它必缺，而每个 change 的 CI 各自
checkout 自己那条 ref，排在它之后的卡才继承得到；漏了的表现是流水线一开工就停在
`can not get ci.yml from iCode`。

换 base 时把模板里继承来的每一步过一遍三分法：

| 类 | 判据 | 处置 |
|---|---|---|
| base 专属 | 这步操作的包或文件只存在于旧 base | 删，并在 Dockerfile 头注释写清替代做法 |
| 运行时通用 | 厂内环境要求，与模型无关 | 原样保留 |
| 版本锚 | 值绑在某个 base 上：版本号、dist-packages 路径、cuda12/13 wheel 变体 | 构建时从 base 现取，或按新 base 重挑 |

代价不对称：base 专属项留着，构建当场失败（patch 找不到目标文件）；运行时通用项删掉，
要等上线才发现（平台钩子失效、PD 起不来）。所以先扫一遍「这步碰的包在新 base 里存在吗」，
再判剩下的。

```bash
bash "$SKILL_DIR/scripts/check_image_layout.sh" "$DELIVERY_TIP" "$NEW_BASE_SHA" "$TEMPLATE_BRANCH"
```

脚本查四件套在位与 mode、ci.yml 与 build.sh 与模板同 blob、相对新基线只多这四个文件、没有
`Dockerfile.<x>` / `build_<x>.sh` 这类自创名、Dockerfile 的 COPY 源都在 `aiak_sglang/` 下。
完成判据：脚本零退出码。本机没有 docker 时到此为止，镜像构建与上机冒烟记 deferred。
逐步继承清单与两种 COPY 策略见 references/delivery-image.md。

### 7 监控与平台契约反向核对

台账是从 fork 提交出发的正向流程，它只能保证「我们挑中的都搬了」，保证不了「平台
依赖的都还在」。监控、探针、采集开关这几类东西的宿主在平台侧：平台按固定路由探活、
按固定指标名画图、按固定启动参数开采集。所以重放完成后必须再做一遍**反向核对**——
从平台契约出发回查代码和发版 YAML。DSv4.1 那次跳过这一步的代价是平台探针拿到 404、
POD 永远不进服务列表，白等一轮 12 分钟冷启动才发现。

**1. 路由全集 diff（探活与自愈契约）**

```bash
routes() { git grep -oh -E "@app\.(get|post|put|delete)\(\"[^\"]+\"" "$1" \
  -- python/sglang/srt/entrypoints | sed 's/.*("//' | sort -u; }
comm -23 <(routes "$PREV_DELIVERY_REF") <(routes HEAD)
```

差集必须为空。主 server 和 dummy/备用 server 的路由集要分别取——DSv4.1 那次主
server 41 条、dummy 40 条，少的正好是 `/ready`。

`/ready` 为什么会正向漏掉，值得记住：台账里 `073d8e98d8 luno-4515` 那行的 evidence
自己写着 `/ready forwarding dropped`，重放时只搬了同一 commit 里的
`/get_instance_info`，把 `/ready` 当「缺宿主」丢了；而 `/ready` 最早是通过
`147c4e45af Pick aiak code 0522` 这类批量搬运提交进 fork 的，清单消噪规则专门跳过
这种提交，正向台账天然看不见它。

**2. 启动参数反查（采集开关契约）**

参考 YAML 不是参数契约。老交付 YAML 里的参数可能来自更老的引擎或更老的分支，照抄
会让容器直接以 `sglang serve: error: unrecognized arguments` 退出。必须对着**这次
要出的镜像**的 argparse 反查：

```bash
python3 "$SKILL_DIR/scripts/check_launch_args.py" --repo "$WORKTREE" \
  --yaml <发版 YAML> [--yaml ...]
```

脚本用 ast 取 `python/sglang/srt/arg_groups/fields/*.py` 各 dataclass 的字段名，
并集全仓库 `add_argument("--x")`，得到可识别参数全集，再从 YAML 的容器启动脚本里抽
`--xxx` 求差集。DSv4.1 那次抓到两个：

- `--collect-tokens-histogram`：社区 `6344b546c8 Deprecate --collect-tokens-histogram,
  auto-collect with --enable-metrics (#23595)` 已删除，token 直方图改成开
  `--enable-metrics` 就自动采，分桶用 `--prompt-tokens-buckets` /
  `--generation-tokens-buckets`。
- `--disaggregation-zmq-ports` / `--disaggregation-zmq-max-sockets`：厂内
  `ed3362f22c luno-3729` 的私有参数，`git branch --contains` 显示只活在
  `glm-0312-w4-v0.5.16-replay` 一条老线上，新基线和上一版交付分支都不认。

判据三分，别一律删也别一律迁：社区删掉且能力已默认开启就删参数；厂内私有参数而这次
确实需要，就把那笔厂内提交按 A 类补迁；厂内私有而这次不需要，删参数并在台账里记一行
「能力缺失，需要时迁 \<SHA\>」。

**3. 指标 label 集合逐字比对（画图契约）**

面板的 PromQL 按 label 选择序列，label 少一个图就空。取上一版交付分支和新分支的同一
处 label 字典比：

```bash
for ref in "$PREV_DELIVERY_REF" HEAD; do
  git show $ref:python/sglang/srt/observability/metrics_collector.py | rg -n "labels = \{" -A 10
done
```

DSv4.1 这次逐字一致：`model_name / engine_type / tp_rank / pp_rank / moe_ep_rank`，
条件项 `priority`（开优先级调度）和 `dp_rank`（DP > 1）。

**4. 厂内环境变量读取点 diff**

平台注入的 `AIAK_*` 之类环境变量，若在新基线里找不到读取点就是静默失效。取两个 ref
的 `os.getenv` / `envs.` 名字集合求差。

**5. 面板清单反查（画图契约的上位做法）**

label 比对只保证 series 选得到，保证不了每张图有数。指标名要从 dashboard 的 JSON 取，
不要按面板标题猜：`<dashboard-url>&editview=dashboard_json`，焦点给 Monaco 的
`.monaco-editor textarea` 全选复制，落盘后解析成「面板 → 指标名 → label 过滤」的映射。
（`/api/dashboards/uid/<uid>` 会被浏览器侧拦，页面内只读求值环境也没有 fetch。）同一个
dashboard 常被多个 model 共用（DSv4.1 与厂内 K3 就是同 uid 换 `var-model_id`），所以
「对齐某个模型的面板状态」= 让我们的 model_id 在同一组查询下有数，不是抄它的指标清单。

空面板按五类定性，判据先行，别一律当代码缺失：

- **A 缺观测点**：族在但少一侧。PD 两端语义不同的量必须两端各观测一次——
  `kvcache_transfer_time` 我们只在 prefill 侧观测，D 实例面板过滤 `pod=~".*decode.*"`
  恒空；补上 decode 侧后两端分别是等待与发送耗时。
- **B label 值不匹配**：面板要 `cache_source="storage_MooncakeStore"`，我们打扁平
  `storage`。改 label 值会同时打断既有查询和钉着旧值的单测，要一起改并在说明里标不兼容。
- **C label 集由拓扑决定**：DP 面板全过滤 `dp_rank="0"`，而 `dp_rank` 只在
  `dp_rank is not None`（DP attention / dp_size>1）时进 label 字典。这类是部署选择，
  不是代码缺陷，参照模型的 dump 里往往同样没有。
- **D 部署开关未开**：EPD（`mm_receiver_*`、`gpu_buffer_pool_*`）、HiCache
  （`cache_source="host"`）、L3 storage 各有自己的创建条件，代码在也不会有值。
- **E 计数器未预热**：带 label 的 Counter 首次观测前不出现，健康实例上是 No data 而不是
  0。abort / bootstrap 失败 / transfer 失败 / 驱逐这几个都要在构造时 `inc(0)`。
- **F 看板自身写错**：`num_used_tokens[1m] / num_running_reqs[1m]` 两侧 range vector
  相除，PromQL 非法，对任何 model 都空。报看板 owner，别在引擎侧找原因。

对齐不等于照抄坏实现：参照分支的 `engine_startup_time` / `engine_load_weights_time` 是
硬编码 0，我们从 `init_startup_timing_summary` 取真值发（`emit_metrics_constants` 跑在
启动计时汇总之前，放那儿只能发 0）；对方恒 0 的死指标（如无离线批队列的
`num_running_reqs_offline_batch`）记「结构性不发」，别造永远 0 的 gauge。

**6. 监控代码的高危写法自查**

迁完监控代码按这七条扫一遍，前三条会直接打挂服务：属性名错写成 `self.enable_metrics`
（本基线只有 `self.metrics_reporter.enable_metrics`，第一个真实请求即 AttributeError →
SIGQUIT → P/D 双双重启）；时间戳 helper 缺 DECODE 分支隐式返回 None（
`Histogram.observe(None)` TypeError 炸在批结果主循环）；msgspec Struct 配 Union 形参时
漏 `isinstance` 守卫（未声明字段不能动态赋值，embedding / rerank 请求直接失败）。另外
四条是数值失真：跨进程时间戳用 `perf_counter`（原点按主机，多机部署无意义，要用 wall
clock）；计时行落在 `if/elif` 之外（把本地准备耗时当集合通信延迟）；除法不兜零（同一
文件里隔壁用了 `max(1, ...)` 就是漏改信号）；首 tick 时间戳还是 0 时相减（把进程 uptime
当迭代耗时）。

#### 读指标时的三个陷阱

1. **hostNetwork 下 IP 会串台。** POD IP == 节点 IP，POD 重建或被回收后同一个 IP 上
   跑的是别人的服务。DSv4.1 这次我把两个节点 IP 上别人的 DeepSeek / Kimi 服务当成
   自己的，据此得出「tokenizer 侧指标全缺」的错误结论。取数前先
   `kubectl get pods -o wide` 核 IP 归属，再用 `/metrics` 里的 `model_name` 标签
   （= `--served-model-name` / `MODEL_ID`）二次确认。
2. **带 label 的指标要等第一次观测才出现。** `/metrics` 走 prometheus multiprocess
   模式（`PROMETHEUS_MULTIPROC_DIR` + `MultiProcessCollector`），Histogram / Counter
   只有 `.labels()` 被调用过才落进 mmap 文件。冷启动后没打过请求时，请求侧指标家族
   本来就是空的，不能据此判缺失。验证顺序固定：先打一个成功请求，再取 `/metrics`。
3. **调度器侧和请求侧是两个 collector，别混着判。** `SchedulerMetricsCollector` 出
   `num_running_reqs / gen_throughput / kv_*`，只要 `--enable-metrics` 就有；
   `TokenizerMetricsCollector` 出 `time_to_first_token_seconds /
   e2e_request_latency_seconds / prompt_tokens_histogram /
   generation_tokens_histogram / num_requests_total`，还要请求真的走过 tokenizer
   manager 才有。

PD 分离下的不对称是设计好的，不是缺失：`collect_metrics` 里 ITL 只在非 PREFILL 侧记
（`elif self.disaggregation_mode != DisaggregationMode.PREFILL`），TTFT 两侧都记。
这是厂内 luno-3716 两笔（`5063a923df ttft metric in prefill`、
`1058353184 Remove itl metric in prefill`）的效果，核对时别把 prefill 侧没有 ITL 当
成漏迁。

#### 监控类台账怎么记

监控类整体倾向必迁：DSv4.1 那批 6 笔全部 replayed（itl、ttft、abort with multi
tokenizer、detokenizer_to_tokenizer、generation time、unified log schema）。唯一
一笔 `13cdb6224c Trace tool integration` 是 replayed in part，留下 KV-dump 的
TraceManager 及其 io_struct / scheduler 管线，理由是它属调试工具、与
`observability/trace.py` 是平行实现。

**部分重放必须在台账 evidence 里写清留下的是什么、为什么、需要时从哪笔捡回来**，
否则下一轮没人分得清那块能力是有意不要还是漏了。

「缺宿主」的处置同样要收口：重放某笔时如果它的一部分改动在新基线里找不到宿主，两条
出路——补宿主（按 sibling skill 的 L2/L9 把行为接到新结构上），或者显式在台账里登记
为阻塞项并写明平台影响。不允许静默丢弃，`/ready` 就是静默丢弃的代价。

#### 发版 YAML 的监控必查项

- `--enable-metrics`：缺了 `add_prometheus_middleware` 不挂 `/metrics`，
  `init_metric_collector_watchdog` 也不建 collector，两侧指标全无。
- `--enable-cache-report`：cache 命中类指标的开关。
- 平台注册标签四件套 `ernie-ops.baidu-int.com/{feddeploy-name,
  inference-service-name,model-name,platform}` 必须填平台注册过的服务名，自创名字
  的后果是网关找不到后端（踩过），区分谁的实例靠 `MODEL_ID` 而不是改服务名。
- 探针路径与代码里真实存在的路由对齐（`/ready`、`/health_forward`）。
- 手工 `kubectl apply` 的 fed 不带平台的 `ernie-ops.baidu-int.com/update-by-job`
  注解，是否影响监控清单收录需平台侧确认——这条未证实，按疑点记录，别当结论。

完整案例证据与命令回执见 references/monitoring-contract.md。

#### 不重启 POD 的监控验收

sleep 模式的 pod（主进程 `sleep inf`、探针已删、服务手动起）可以只热替文件加重起服务，
把一次监控改动的验收压到分钟级。可信度靠三方 md5：pod 里的文件对上老栈某个 commit，
`git diff --numstat <老> <新>` 的逐文件增删行对上 commit stat，替完的 md5 对上本地
worktree——三者齐了才能说「逐文件热替等价于精确打进那一个 commit」。替前备份到
`/shared/backup_<round>/`，替后清 `__pycache__` 并用容器内解释器 `ast.parse` 过语法。
取数要在造过流量之后，按族名（去掉 `_bucket` / `_count` / `_sum` / `_total`）做前后 diff，
并把流量带出来的族与本次改动带出来的族分开。

### 8 发布

逐卡走 refs/for 送审，一卡一个 change。评审系统限单批数量时按类分批（A1 一批、
A2+A3 一批……），别退回整支 squash——粒度是这条路线的核心收益。

改已推过的评审必须保留原 Change-Id：换消息文件时 commit-msg hook 会生成新的，icode 会拒
并提示 `git fetch ... refs/changes/<nn>/<change>/<ps>` 重放；带原 Change-Id 再
`git commit --amend` 就是正常的下一个 patchset。LLM 评审的 BLOCK 报告逐条核实再改，本轮
9 条里 2 条是误报（同一把锁被当成两把、只在字段为 0 时赋值的时间戳被当成覆盖写），误报
也要把判据写进回复。

## 难度预判（分级用信号，不用感觉）

| 级别 | 信号 | 处置 |
|---|---|---|
| 易 | fork 独有文件为主，冲突史 = 0 | 直接 pick |
| 中 | 触少量社区文件，冲突史 1–5 | pick 后小修 |
| 难 | 冲突史 > 5，或触 scheduler / model_runner / serving_chat 等热点 | 预留 L2/L9 重实现时间 |
| 难(先拆) | 一卡多主题（≥3 个类别） | 先逐提交拆类再处置 |

冲突史 = 卡片触碰文件与上次整支 merge 冲突清单的交叠文件次，是「社区也在改这片」的
实证代理。52 卡的实测分布见 references/pr-taxonomy.md。

## 常见坑

- 「社区已收录」按标题判会误判：厂内 pick 时常改过签名或加过开关。证据是 NEW_BASE
  的实现覆盖厂内行为，不是标题相似。
- 零冲突不等于该 pick：厂内特性栈（如 encode/EPD）常是与社区同名子系统的平行实现，
  全 fork 独有文件、pick 必零冲突，但正确动作是取社区框架再搬 delta。rival 判定
  优先于难度判定。
- 台账把 fixup 当独立 PR，逐条 pick 是在重放噪声；先折叠。
- 跳过 Cache 类却没动发版 YAML：起服务读不存在的开关，直接 fail fast 在参数校验。
- 换了 Change-Id 的迭代会开出新评审；preflight 用 sibling skill 的 review_preflight.py。
- 大卡的卡级补丁跨越社区重构点时，git apply 失败率高于逐提交 pick；该卡退回逐提交
  重放，fixup 在 worktree 里 autosquash。
- 台账枚举用 --no-merges 会漏掉 merge commit 本身携带的解冲突改动；上一代分支若有
  内部 merge，重放后跑 git diff FORK_SHA..HEAD -- <路径> 抽查关键子系统是否有语义残差。
- `.gitignore` 的 `**/build/` 会挡住 `build/build.sh`，`git add -f` 才进得去；厂内交付
  分支也是这么进的，所以 git ls-tree 看得到它而 git add 会拒。
- 改动四件套那一卡会让它后面的卡全部换 SHA、跟着升 patchset。送审前 diff 一次 Change-Id
  集合，确认没有多开 change。
- 参考 YAML 的启动参数不是契约：老交付 YAML 会带着更老引擎或更老分支的私有参数，
  照抄的表现是容器以 unrecognized arguments 直接退出。每次换基线用
  scripts/check_launch_args.py 对新镜像的 argparse 反查一遍。
- hostNetwork 下按 IP 取 /metrics 会串台：POD 重建后同一个节点 IP 上是别人的服务，
  必须用 model_name 标签核对归属再下结论。
- 冷启动后请求侧指标家族为空是 prometheus multiprocess 的正常表现，不是漏迁；先打
  一个成功请求再取 /metrics。
- 上一轮解过的冲突会被 rerere 整文件顶回来：同一处冲突再现时 git 直接写入上个交付
  分支那次的 postimage，与本卡无关的 hunk 一起进来（实测：pick 一行 media 收紧，
  顺带多出 CLIENT_MEDIA_EXCEPTIONS 加 OSError）。第一次看冲突用
  `git -c rerere.enabled=false cherry-pick`，解完 `git diff HEAD` 逐 hunk 核对只剩本卡的行。
- 一行改动照搬前先查新基线上谁在喂这个函数，同一行的语义可能反过来：厂内把
  get_image_bytes 的裸 `/` 分支删掉做收紧，而新基线的 load_image 已改成先剥 file://
  再把纯路径传下去，照搬后留下的 file:// 分支不可达、真正在用的裸路径分支被删，仓库
  自带的 registered 测试还把旧契约钉着。判据是 rg 出全部调用点，看清谁剥 scheme、
  谁读文件，再决定照搬 / 改写 / 放弃。
