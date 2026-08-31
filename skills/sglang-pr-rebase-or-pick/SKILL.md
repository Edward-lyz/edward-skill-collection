---
name: sglang-pr-rebase-or-pick
description: 把一个 fork 分支上选定的连续提交集成到目标分支，或把上游分支整体合并进来。覆盖冻结 SHA、隔离 worktree、冲突语义解决、合并后缺陷分类、跨文件契约验证和 review-only 发布。触发词：rebase、cherry-pick 一段提交、合并上游分支、merge 冲突重实现、发 CR 前的门禁。适用于 SGLang 这类 fork 与上游长期分叉的仓库；不做 GPU 引擎启动和精度对比。
---

# Fork 分支集成

## 何时使用

用户给出源引用和目标引用，需要把源上的提交搬到目标上，并且冲突不是靠 `--ours` / `--theirs` 一把梭就能了事的场景。上游重构过的代码和 fork 改过的代码同时存在时，这个 skill 的价值在冲突语义和跨文件契约验证，不在 Git 命令本身。

不适用：单个提交的干净 cherry-pick、没有冲突的 fast-forward、纯粹的分支改名。这些直接用 Git 即可。

## 两种模式

`pick`：对选定范围逐提交 cherry-pick，保留 old/new commit 一一映射。适合需要把每个提交单独送审、或需要在中途停下来的场景。

`squash`：把 `start^..end` 的整体变更一次合入，只产出一个提交。适合上游提交量大到无法逐个送审、或评审系统对单次批量有上限的场景。合并提交默认取第一父提交到合并结果的快照差异。

一次运行只锁定一种模式。要换模式就重新开一轮，不要在同一个候选分支上切。

## 硬规则

1. 先把源和目标解析成完整 SHA 并冻结，后续所有比较都用冻结值，不用会漂移的分支名。
2. 在从冻结目标 SHA 开出的独立 worktree 里做集成，不碰用户当前工作区。
3. 绝不直接 push 受保护的目标分支，只发 review-only。
4. 任何修复都会让之前的门禁结果失效，必须重跑受影响的门禁，不能沿用旧报告。
5. 缺硬件、缺依赖、跑不起来就记 deferred，不要把跳过说成通过，也不要为了变绿去改环境。
6. 不覆盖用户未提交的改动，不清理用户留下的冲突现场。
7. 门禁跑全树，不只跑改过的文件。会静默存活的缺陷大多落在没有冲突的文件里。
8. 落在交付目标必经路径上的继承缺陷同样是 blocker，不能以「父提交也这样」放行。

## 流程

```bash
SOURCE_SHA=$(git rev-parse --verify "$SOURCE_REF^{commit}")
TARGET_SHA=$(git rev-parse --verify "$TARGET_REF^{commit}")
git log --reverse --topo-order --format="%H%x09%cI%x09%an%x09%s" "$TARGET_SHA..$SOURCE_SHA"
```

把这份清单交给用户选 `start_commit` 和 `end_commit`；两个提交都必须在清单里，且起点不晚于终点。用户没选之前不要建分支、不要应用补丁。

```bash
git worktree add -b "$CANDIDATE_BRANCH" "$WORKTREE" "$TARGET_SHA"
```

`pick` 模式在这个 worktree 里逐提交 `git cherry-pick`，每个 old commit 必须对应一个 new commit，冲突当场解决当场记录。`squash` 模式做一次整体合入，最终相对目标只留一个提交，后续修复一律 `git commit --amend --no-edit`。

冲突不要按行挑，先判断这一处属于哪种语义情形，再决定保留哪一侧、以及要不要在新结构上重新实现 fork 的行为。判断规律见 `references/resolution-laws.md`。

合并完成之后，按 `references/merge-case-taxonomy.md` 逐类过一遍。那份表列的 8 类缺陷都不产生冲突，靠肉眼看 diff 也基本看不出来，每类都写清了检测手段和正确改法。开工前先把交付目标要开的特性组合列成清单（模型、attention 后端、MTP、EP、PD 分离、cache），这份清单同时是 M8 的验证范围和 `--critical-path` 的取值来源。

## 验证

按证据强度分级，别把弱证据当强证据用：

```text
E0  断言、文件存在
E1  diff / AST / 静态结构
E2  带反向对照的可执行探针（先证明未修复时会失败）
E3  仓库自带测试
E4  构建或集成测试
E5  代表性运行时冒烟
```

五个门禁是这个 skill 自带的，按顺序跑：

```bash
# import 可解析性：模块被上游改名、符号没补齐、同名 import 互相覆盖
python3 "$SKILL_DIR/scripts/import_audit.py" \
  --repo "$WORKTREE" --parent "$TARGET_SHA" --parent "$SOURCE_SHA" \
  --critical-path <交付目标必经路径的 glob，可重复> \
  --output "$ARTIFACTS/import-audit.md"
```

`import_audit.py` 把发现分成 NEW（只有最终树坏）和 INHERITED（父提交就坏）。NEW 一律是 blocker；INHERITED 落在 `--critical-path` 上也是 blocker，因为那条路径这次才第一次被执行。`ruff` 不解析模块是否存在，这一层它替代不了。

```bash
# 特性开关差分：被丢掉的 flag、默认值漂移、还在但没人读的空开关
python3 "$SKILL_DIR/scripts/flag_inventory.py" \
  --repo "$WORKTREE" --target "$TARGET_SHA" --source "$SOURCE_SHA" \
  --consumer-parity --output "$ARTIFACTS/flag-inventory.md"
```

`flag_inventory.py` 默认只对 fork 侧独有的开关做读者比对（`--parity-scope all` 会慢很多）。DROPPED 和 NO-OP 是 blocker，FORK-ONLY 那一节就是需要逐个确认的场内开关清单，拿它去部署仓库里 `rg -l -- '--flag-name'` 看哪些真的在用。

```bash
# 接口差分：两个父提交到最终树的签名、参数、call-keyword 变化
python3 "$SKILL_DIR/scripts/interface_delta.py" \
  --repo "$WORKTREE" --source "$SOURCE_SHA" --target "$TARGET_SHA" --final HEAD \
  --paths-file "$ARTIFACTS/python-audit-paths.txt" \
  --output "$ARTIFACTS/interface-delta.md"

# 重复定义：两侧都保留了同一个函数或守卫
python3 "$SKILL_DIR/scripts/duplicate_definition_check.py" \
  --repo "$WORKTREE" --base "$TARGET_SHA" --final HEAD \
  --waiver-file "$ARTIFACTS/duplicate-waivers.tsv" \
  --output "$ARTIFACTS/duplicate-definition.md"

# 父提交相对的测试差分：只在最终树失败的用例才是 merge 造成的
python3 "$SKILL_DIR/scripts/parent_test_delta.py" \
  --repo "$WORKTREE" --final HEAD --target "$TARGET_SHA" --source "$SOURCE_SHA" \
  --test-command "<仓库测试命令，{tree} 展开为 checkout 路径>" \
  --collect-command "<可选的用例列举命令，同一个占位符>" \
  --log-dir "$ARTIFACTS/logs/parent-test-delta" \
  --output "$ARTIFACTS/parent-test-delta.md"
```

`interface_delta.py` 的输出是候选而不是结论，只有 HIGH 行和落在冲突路径上的 MEDIUM 行值得逐条看。`import_audit.py`、`duplicate_definition_check.py`、`parent_test_delta.py` 有新增项就是 blocker，exit code 非零。

测试差分是这三个里命中率最高的一个：有冲突的每个子系统都要在最终树和两个父提交上跑同一批测试。只在最终树失败的用例是 merge 缺陷；和父提交共有的失败属于继承下来的债，不扩大范围；两个父提交都没有的用例单独标注待人工判定。父提交环境跑不起来就记 deferred，不要只拿最终树的结果当证据。

最后固定跑一遍：

```bash
git diff --check "$TARGET_SHA..HEAD"
git diff --name-only --diff-filter=U
git merge-base --is-ancestor "$TARGET_SHA" HEAD
git status --short
```

能编译就编译，能跑仓库自带的 lint 或 pre-commit 就跑。改动过的文件的静态检查要和冻结目标上的同一批文件对比条数，只关心新增的那几条。

## 发布

```bash
python3 "$SKILL_DIR/scripts/review_preflight.py" \
  --repo "$WORKTREE" --target-sha "$TARGET_SHA" --head HEAD --mode squash \
  --card-pattern "<工单号正则>" --output "$ARTIFACTS/review-preflight.json"

git push origin "HEAD:refs/for/$TARGET_BRANCH"
```

preflight 检查候选是否基于冻结目标、squash 模式是否只有一个提交、每个提交是否带有效 `Change-Id` 和工单号。同一个变更的后续 patchset 必须复用同一个 `Change-Id`，否则会开出新的评审。

评审系统限制单次批量提交数时，用 `git commit-tree` 把最终树挂在冻结目标上做成一个提交再 push，这样既满足上限又保留完整内容：

```bash
SQ=$(git commit-tree "$(git rev-parse HEAD^{tree})" -p "$TARGET_SHA" -F "$MSG_FILE")
git push origin "$SQ:refs/for/$TARGET_BRANCH"
```

## 常见坑

- 合并干净不等于合并对了。三方合并按行工作，跨文件的契约它看不见。
- 上游的测试在合并后变红，往往是合并的锅而不是上游的锅；先和父提交对比再下结论。
- 位置传参在参数顺序被换过之后仍然能通过参数个数检查，只在运行时炸；改成关键字传参。
- 只有开了某个可选特性才走到的路径，需要单独构造请求去打，否则冒烟全绿也说明不了它。
- 把坏 import 或坏引用注释掉不算修，删掉才算：注释行会在下一次合并里被当成需要保留的内容。
- 冲突多的时候按目录整取最省事，但很容易让调用方和被调方分属不同父提交；整取之后必须逐个确认新调用方依赖的符号在最终树里存在。
- 服务「挂住」经常不是死锁：worker 抛异常退出后 HTTP 进程还活着，外部只看到 health check 超时。看日志先搜 `Scheduler hit an exception` 之类的 traceback，再谈 hang。
- fork 加的硬化逻辑可能收窄了上游支持的输入形状，这类冲突要按"谁的调用方还在产出旧形状"来判，而不是按"谁的代码更新"。
