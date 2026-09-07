---
name: sglang-fork-rebase-first
description: 追社区新版本的二分法：社区基线直换 + 厂内 PR 台账化选择重放。先把 fork 相对旧基线的提交按七类台账化（链路适配、监控适配、Cache 适配、通用模型优化、通用 BUGFIX、具体模型优化、具体模型 BUGFIX），社区已收录直接丢弃、非交付模型的专属改动不迁移，剩余按原始拓扑序逐卡 pick 到新基线。触发词：追社区、升级基线、base swap、厂内 PR 梳理、rebase 到新版本。适用于 fork 与上游长期分叉、整支 merge 成本已失控的仓库；pick 冲突语义与合并后门禁复用 sglang-pr-rebase-or-pick。
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
下免费消失；非交付模型的专属改动 43 提交 / 1.6 万行显式不迁移；**必迁只剩 128 提交 /
4.5 万行（34%）**，其中大头（EPD 链路 2.6 万行、AttentionStore 1.5 万行）以 fork 独有
文件为主，pick 接近零冲突。完整台账见 references/pr-taxonomy.md。

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
3. B 类（模型专属）是否迁移相对交付模型判定：给 GLM 交付追新，K3 专属不迁；
   K3 自己的分支追新，B 类照迁。台账里模型标签和类别是两个独立字段。
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

拿台账问三件事：交付模型是什么（决定 B 类去留）；Cache 适配要不要（不开
AttentionStore 就整类跳过，发版 YAML 同步去开关）；C2 工程物（ci.yml、Dockerfile、
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

### 6 发布

逐卡走 refs/for 送审，一卡一个 change。评审系统限单批数量时按类分批（A1 一批、
A2+A3 一批……），别退回整支 squash——粒度是这条路线的核心收益。

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
- 台账把 fixup 当独立 PR，逐条 pick 是在重放噪声；先折叠。
- 跳过 Cache 类却没动发版 YAML：起服务读不存在的开关，直接 fail fast 在参数校验。
- 换了 Change-Id 的迭代会开出新评审；preflight 用 sibling skill 的 review_preflight.py。
- 大卡的卡级补丁跨越社区重构点时，git apply 失败率高于逐提交 pick；该卡退回逐提交
  重放，fixup 在 worktree 里 autosquash。
- 台账枚举用 --no-merges 会漏掉 merge commit 本身携带的解冲突改动；上一代分支若有
  内部 merge，重放后跑 git diff FORK_SHA..HEAD -- <路径> 抽查关键子系统是否有语义残差。

