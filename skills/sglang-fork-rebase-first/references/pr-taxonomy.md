# 厂内 PR 分类法与 K3/GLM 实测台账

分类是一个二元组：**类别 × 模型标签**。类别决定迁移语义，模型标签让同一份台账
服务不同交付（给 GLM 追新时 K3 标签的 B 类不迁；K3 自己追新时照迁）。

## 判定树：对每张卡问三个问题

**问题 1：社区新基线已有等价实现？** 是 → C1 丢弃。
命中形态：标题带社区 PR 号或 [Cherry-pick to release/*]；厂内先行、社区后收的能力
（例：mooncake 0.3.12.post1 bump 厂内 8 月初 pick，社区 #32302 同版本已收；
[Kimi] Support kimi-k3 整棵 57k 行的模型支持，社区现已内置）。
证据标准：NEW_BASE 里 rg 到等价符号/文件并 diff 覆盖厂内行为。厂内私改部分拆出来
按 A/B 类单独处置。

**问题 2：只对某个模型/checkpoint 生效？** 是 → B1（优化/适配）或 B2（BUGFIX）。
判据：文件路径带模型名（models/kimi_k3.py、K3 专属 kernel、K2.6 mxfp4 加载、
V4 组 batch 特判），或行为仅在该模型开启。**本次先梳理、rebase 时不迁移**（除非
交付就是该模型）。模型退役时这两类整块划走，这是台账复利的来源。

**问题 3：剩下的按子系统归 A 类或工程类。**

| 类别 | 覆盖 | 迁移语义 |
|---|---|---|
| A1 链路适配 | EPD/encode 服务、PD 传输、PP 组合、接口协议、tokenize 端点、传输配置 | 必迁，fork 独有模块为主 |
| A2 监控适配 | metrics、统一日志 schema、Trace/content_detection、pyspy | 必迁，量小 |
| A3 Cache 适配 | AttentionStore/asradix、KV 复用、mm_cache 边界 | 可选：交付不开 cache 整类跳过 + 发版 YAML 去开关 |
| A4 通用模型优化 | DCP 传输、fp8 KV、TokenSpeed MLA、DSpark 投机框架层 | 必迁（框架级按交付特性取舍） |
| A5 通用 BUGFIX | FC keepalive、tokenizer/stream、PP 同步、kernel 寻址溢出 | 必迁，单条量小 |
| C2 工程/CI | ci.yml、Dockerfile、单测流水、镜像依赖 | 跟发版方式走，多为独立文件 |
| X 噪声 | 成对 revert、历史搬运提交、merge 残留 | 出清单 |

边界判例（实测中最常犹豫的三种）：

- DSpark/DCP 这类「因某模型引入但框架通用」的层：按 A4 归类、模型打标签，
  交付不开该特性时按特性开关取舍，不按模型取舍。
- FC parser 修复：接口行为修复归 A5；只对某家模型模板生效的（kimi k2 json parser）归 B2。
- K3 的 cache 数据/warmup 挂载：归 B1（数据与模型绑定），AttentionStore 机制本体归 A3。

## K3 分支实测台账（2026-09-07）

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

- 必迁 A1–A5 = 128 提交 / 45,245 行，占全量 134,175 行的 34%。
- C1 一类占了最大冲突面（227 文件次）：双方各有一份的内容在整支 merge 里全是
  add/add 与改动碰撞，在 rebase-first 里一行不用动。
- A1 的 2.6 万行里 fork 独有文件过半（EPD/encode 是厂内自有模块），实际冲突面
  集中在 scheduler 接线的十几个文件。
- 六张混合卡（luno-3716/4648/4671/4784/4170/4311）贡献了逐提交覆盖分类的全部工作量，
  也是「难(先拆)」的全部来源。台账干净程度直接决定 pick 成本——**日常开发一卡一主题，
  就是在给下一次追新降价**。

## GLM-5.3-Flash：同一交付的新旧路线对照

| | 旧路线（2026-08-27 实账） | 新路线（台账推演） |
|---|---|---|
| 第一步 | merge 社区进厂内，冲突 217 文件/590 块 | 从社区分支开 worktree，零冲突 |
| 处理量 | 4,692 文件 / +485k 行一次落地 | 128 提交 / 4.5 万行逐卡重放（不开 cache 再减 1.5 万） |
| K3/K2.x/V4 专属 | 43 提交 / 1.6 万行全部带上 | 不迁移 |
| 社区已收录 | 227 文件次冲突的主要来源 | 免费消失 |
| 送审形态 | 1 个 3,570 文件的 squash CR | 逐卡 change，保工单号与评审粒度 |
| 合并后缺陷 | M1–M9 九类 + 3 个修复提交 | 每卡单一意图，门禁逐卡跑 |

厂内先例：GLM-5.2 线 0.5.16→0.5.17 已按此法完成（origin/ds-dev-community-0517-glm，
社区 release 基线 + d2397efab8 一个厂内合入提交 + 2 个修复）；0.5.18 基线分支已开出
待 pick（origin/ds-dev-community-0518-glm），即「基线直换完成、重放未开始」的中间态。

## 链接规范（离线可推导）

- 工单页：http://newicafe.baidu.com/v5/issue/{card}/show
- 提交页（可跳 CR）：http://console.cloud.baidu-int.com/devops/icode/repos/{repo}/commits/{sha}
- CR 号不能离线由 Change-Id 反查（icode 的 gerrit ssh query 需要内部 RepoName 参数，
  外部拼不出），追溯统一走上面两个入口。

