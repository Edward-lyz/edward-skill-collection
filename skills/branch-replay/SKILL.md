---
name: branch-replay
description: |
  将开发分支相对真实分叉点的独有提交按原顺序 replay 到固定的新 base，并保持 old commit 与 new commit 一一对应，处理长距离 rebase、上游吸收、架构漂移、冲突重实现、断点续跑、并行审计、迁移报告和 Gerrit/refs-for 发布。
  当用户要求分支迁移、rebase 到新 base、branch replay、逐 commit rebase/cherry-pick、保留提交映射或续跑未完成的 replay 时使用。
---

# Branch Replay

把 source branch 的每个独有 commit 迁到固定 base。目标不是让 patch 勉强 apply，而是在新架构上保留每个 commit 的意图、顺序和可追溯性。

## 硬约束

- 开始写入前冻结 source ref、source full SHA、base ref、base full SHA、merge-base、目标分支、提交清单和验收命令。后续远端 ref 移动不得改变本次输入。
- scope 始终只有一个 source 和一个 base。用户提到多条 source 时，为每条 source 建独立 replay；除非用户明确要求，不得把多条开发分支先互相合并。
- source 独有 commit 必须按原顺序一一映射到新 commit。已被 base 精确或语义吸收的 commit 也保留为空 commit。不得 squash、重排、丢 commit 或生成 merge commit。
- canonical replay 分支同一时间只处理一个 commit，只有主 agent 可以操作其 Git index、sequencer、branch 和报告。不得并行 replay 后续 commit 再拼接结果。
- source worktree 只读。已有 dirty、merge、rebase 或 cherry-pick 现场不得 `abort`、`reset`、`clean` 或 checkout；新建专用 `rift`。无法隔离时停止，不得借用现有现场。
- 不把缺依赖、缺 GPU、未运行或测试收集失败写成通过；保留失败输出和待执行命令。
- 执行获批后持续推进到全部完成、真实 blocker、用户中断或明确的运行上限。进度 checkpoint 只发 commentary，不以任意批次结束任务。

## 1. 只读冻结 scope

先读取仓库指令和已有迁移资料，再检查 refs、worktree 和未完成 Git 操作。至少核实：

```bash
git rev-parse --verify '<source>^{commit}'
git rev-parse --verify '<base>^{commit}'
git merge-base '<source-sha>' '<base-sha>'
git status --short
git rev-list --reverse --topo-order '<base-sha>..<source-sha>'
git rev-list --min-parents=2 '<base-sha>..<source-sha>'
```

远端 tag 可能是 annotated tag；需要以远端为准时同时解析 peeled commit，不把本地陈旧 tag 或浮动 `main` 当作固定 base。不得假设远端 `master` 跟随社区，也不得按分支最后提交时间推断社区基线。

`<base>..<source>` 表示 source 可达而 base 不可达的提交，即本次 source 清单。若没有 merge-base、清单含 merge commit、scope 有多种解释、目标分支命名或验收方式不明确，写入前只问一个能解除风险的问题。merge commit 需要用户明确 mainline/线性化规则，不能擅自 `cherry-pick -m`。

用 `git cherry -v <base-sha> <source-sha>` 和 stable patch-id 找精确上游等价候选，但只把它当候选证据；patch 相同不证明在新上下文中行为完整。逐条查看 commit message、源 patch、父提交上下文、关联 issue/PR、目标代码和后续依赖。大 commit、跨层改动、CUDA/并发/分布式/内存所有权、modify/delete 和旧子系统整体移植标为高风险。

## 2. 建隔离工作区和持久报告

优先用 `rift` 从 base full SHA 创建专用 worktree 和符合仓库规则的新分支。创建后再次确认 HEAD 等于冻结的 base SHA、工作区 clean、source 现场未变化。不要因为 `rift` 失败自动改用 source worktree。

先创建完整报告清单，不能做到一半才补历史。报告头记录：

```text
source ref / frozen SHA:
base ref / frozen SHA:
merge-base:
target worktree / branch:
source commit count:
target test commands:
delivery target and branch policy:
```

每个 source commit 预建一条 `pending` 记录：

```text
## <i>/<N> <old-short-sha> -> PENDING [pending]

<原 commit 标题>
风险：<low/high + 原因>
```

报告既是恢复点也是最终测试失败的索引，不是聊天流水账。需要保留的完整命令输出写入持久日志，报告只写命令、退出码、关键结论和日志路径。

## 3. 续跑前先恢复事实

每次续跑先验证，不要凭上次回复里的进度继续：

1. 重新读取冻结 SHA 和 source 清单，确认条数、顺序未变。
2. 工作区 clean 时，确认 `HEAD` 等于报告最后一个 completed new SHA，下一项是第一个 pending。
3. 工作区有冲突时，确认 `CHERRY_PICK_HEAD` 等于下一项 old SHA，且没有其他 Git 操作混入。
4. 报告落后于 Git 或 Git 落后于报告时，先用 commit message、`-x` trailer、reflog 和 tree 状态修复映射；证据不足就停止。
5. 清点临时 rift/agent；不得复用仍在运行或基线不同的 worker 结果。

## 4. 正确使用并行 agent

当用户要求并行或任务配置允许多 agent 时，持续利用空闲 slot，但只并行独立证据和当前 commit 内互不重叠的工作：

- 主 agent：唯一 sequencer 和 writer，执行 cherry-pick、暂存、commit、报告更新和最终集成。
- resolver：按互不重叠的文件/子系统处理当前 commit；不得操作 canonical worktree 的 Git 状态。
- intent analyst：还原 source intent、查上游吸收和 API 搬迁，可预分析后续高风险 commit。
- reviewer/tester：独立审查集成 diff、失败路径、并发/所有权边界和测试证据。

worker 可在 disposable rift 做实验，但必须从主 agent 给定的同一个 current parent 开始，只返回分析或最小 patch。主 agent 应在应用结果前复核 HEAD、目标文件和重叠范围。一个 worker 完成后立即安排下一个独立子任务；单一冲突块不足以拆分时，用剩余 slot 做意图分析和 review，不要制造并行写冲突。

禁止让多个 agent 各自迁移不同的后续 commit，再把产物 cherry-pick 回主线。commit N+1 的正确目标依赖 N 的最终语义，这种并行会在过期 base 上产生看似干净的错误结果。

## 5. 逐 commit replay

对第一个 pending commit 重复以下闭环，完成报告后才进入下一个。

### 5.1 建 intent packet

读取 old commit 的完整 message、patch、父提交代码和关联上下文；用 LSP 查目标符号的 definition、references、类型和 diagnostics。先调用 `lsp_server_status`，需要时启动对应 server。回答：

1. 这个 commit 改变的可观察行为和不变量是什么？
2. base 是否已经精确或语义实现了它？证据是什么？
3. 目标架构里的唯一正确落点在哪里？后续 source commit 依赖什么接口？
4. 哪些失败路径、并发边界、内存/资源所有权和硬件约束必须保留？

### 5.2 应用并分类

正常执行 `git cherry-pick -x <old-sha>`。若 Git 支持 `--empty=keep`，对预期会变空的 commit 使用它；source 本身为空时同时按本机 Git 帮助使用 `--allow-empty`。旧 Git 无对应选项时，显式创建保留原 message 和 `(cherry picked from commit <full-sha>)` 的 empty commit，并立即校验 message，不得 `--skip`。

按实际处置记录一种状态：

| 状态 | 判断 | 处置 |
| --- | --- | --- |
| `auto` | patch 干净应用 | 仍审查 3-way 拼接、调用签名和行为，不把 clean 当正确 |
| `exact-upstream` | stable patch-id 与 base 中 commit 等价，目标行为仍成立 | 保留 empty commit，记录 upstream SHA 和证据 |
| `semantic-upstream` | patch 不同，但目标已有完整行为 | 保留 empty commit，记录符号、测试或历史证据；不能只凭标题 |
| `rename` | 代码迁到新路径/符号 | 用 history 和 LSP 找新落点，迁移 intent，不复制旧文件 |
| `modify/delete` | base 删除了目标实现 | 证明 intent 是否仍需要；需要则落到替代架构，不需要则 empty |
| `text-conflict` | 同一区域双方修改 | 合成双方仍有效的意图；不能共存时按迁移目标取舍并记录 trade-off |
| `reimplement` | 旧 patch 结构已失效 | 放弃旧文本，在 base 的现有架构上最小重实现同一 intent |

禁止整文件选择 `ours` 或 `theirs`，除非逐项证明另一侧没有独有行为。禁止复活 base 已替换的平行子系统、旧默认路径、旧 feature flag 或 silent fallback。冲突过多不是照搬旧实现的理由。

`cherry-pick` clean 后也要审查 `HEAD^..HEAD`。自动 3-way 可能把旧调用接到新签名、重复已有逻辑或在两个架构之间留下半套实现。发现问题直接 amend 当前映射 commit，不增加修复 commit，也不留到最后统一塞进最后一个 commit。

若目标是 Gerrit，逐 commit 检查 message footer：保留 author，预先设置合规 committer；将 `(cherry picked from commit ...)` 放在 `Change-Id` trailer block 之前，确保 `Change-Id` 仍是合法 footer。不要等 90 个 commit 完成后才重写整条历史。

### 5.3 当前 commit 验证与落盘

中间 commit 可能本来就是半成品，因此不默认跑全量 suite；但每条都做便宜且能定位责任的检查：

- `git diff --check HEAD^..HEAD`，并核对 changed files 与 old intent。
- 对改动语言执行 parse/compile/format 或项目已有增量检查。
- 用 LSP 检查改动文件 error diagnostics，并查签名变化的调用点。
- 对 `reimplement`、clean 3-way、高风险算法、并发、资源所有权和错误处理运行最小 targeted test/self-check；测试必须覆盖真实行为，不能只检查存在性。
- 测试无法运行时记录明确原因、原始退出码和目标环境命令，不写 pass。

验证后把报告记录改成：

```text
## <i>/<N> <old-short-sha> -> <new-short-sha> [<status>]

<原 commit 标题>
意图：<一句>
落点/吸收证据：<一句>
trade-off：<有取舍时写；没有则省略>
验证：<命令、退出码、结论或日志路径>
```

确认 new SHA、`-x` trailer、工作区状态和报告一致，再推进下一条。当前尝试损坏时，只能在专用 replay worktree 中保存证据后退回最后一个 verified SHA 重试；不得影响 source 或其他现场。

## 6. 最终验收

全部 commit 完成后先验证历史不变量，再跑用户指定测试：

```bash
git rev-list --count '<base-sha>..HEAD'              # 必须等于 N
git rev-list --min-parents=2 '<base-sha>..HEAD'      # 必须为空
git diff --check '<base-sha>..HEAD'
git status --short                                   # 必须为空
git range-diff '<merge-base>..<source-sha>' '<base-sha>..HEAD'
```

另外用脚本或逐条检查报告顺序、N 个 old/new SHA 唯一性、new commit 父链和每个 `-x` full SHA trailer。`range-diff` 只是审计索引，不是语义等价证明；empty 和 reimplement 必须以报告证据解释。

运行累计 changed files 的项目检查、用户指定的最终验收和硬件相关测试矩阵。把完整命令、环境、退出码和未运行项写入报告。缺依赖时优先使用项目既有虚拟环境安装；不适合本机的 GPU/NCCL/RDMA/SDK 测试保留目标环境命令并标为未运行。

## 7. 可选发布到 Gerrit/代码评审

只有用户要求发布时执行。发布前检查真实 remote policy、branch prefix、ref namespace、目标 branch 是否存在、它的 base 是否正确、单次 change 上限、empty commit 支持、committer 和 message footer；不得假设 `refs/for/<branch>` 会创建真实 branch。

需要真实目标 branch 时，从冻结的 peeled base commit 创建，不从远端当前 `master` tip 创建。若远端已有 `refs/heads/dev`，则 `dev/...` 可能因 ref namespace 冲突无法创建；先查 refs，再按仓库规则选如 `dev-...` 的合法名称。

CLI 不兼容 rift/worktree 时先保留原错误，再确认原生 Git refspec 的语义和权限后使用。zsh 中动态 refspec 写成 `${stage}:refs/for/${branch}`，避免 `$stage:...` 被参数修饰符吞掉。

先推 1–2 个有代表性的前缀，至少覆盖一个 normal 和一个 empty commit；确认 review 创建、依赖链、footer、identity 和 CI 行为后，再按明显低于远端上限的批次顺序推送，并保存完整日志。若远端拒绝 empty commit，停止并让用户在严格一一对应和发布策略之间做决定，不得静默丢 commit。

若发布只需改 metadata，在独立 staging ref/rift 重写，并验证重写前后每个对应 commit 的 tree 相同、数量和顺序不变，再更新报告映射。远端累计检查要求改代码时，把修复折回产生问题的 mapped commit 并重算后续 SHA；禁止把全分支的 lint/docstring/type 修复都 amend 到最后一个无关 commit。

等待最终远端检查完成。只有 required checks 全部成功才能报告发布完成；目标 branch 在 CR 合入前仍停在 base，这是正常状态，要明确告诉用户。

## 交付

最终给出 target branch、HEAD、old/new commit 数、报告和完整日志的绝对路径、通过/失败/未运行的验收项。只陈述实际完成的 commit、push、CR 和测试，不把本地静态检查写成远端或硬件验收通过。
