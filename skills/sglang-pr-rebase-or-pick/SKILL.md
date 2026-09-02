---
name: sglang-pr-rebase-or-pick
description: 把一个 fork 分支上选定的连续提交集成到目标分支，或把上游分支整体合并进来。覆盖冻结 SHA、隔离 worktree、意图冲突对隔离、冲突语义解决、合并后缺陷分类、跨文件与跨组件契约验证和 review-only 发布。触发词：rebase、cherry-pick 一段提交、合并上游分支、merge 冲突重实现、发 CR 前的门禁。适用于 SGLang 这类 fork 与上游长期分叉的仓库；跨组件契约只给验证清单和判定点，不代管集群资源调度和精度调优。
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

### 先隔离意图冲突对

长期分叉的 fork 和上游经常把同一个能力各做一遍。这类提交对是整支合并做得最差的地方：按行合并要么留下两份实现，要么留下 fork 的调用方配上游的被调方，而且两种结果都不产生冲突。所以合并之前先把它们找出来，而不是等合并后的门禁在几百个符号里帮你捞：

```bash
python3 "$SKILL_DIR/scripts/intent_overlap_scan.py" \
  --repo "$WORKTREE" --target "$TARGET_SHA" --source "$SOURCE_SHA" \
  --waiver-file "$ARTIFACTS/gate-intent-waivers.tsv" \
  --output "$ARTIFACTS/intent-overlap.md"
```

配对依据是「双侧都改过的文件」加「提交标题的主题词」，共享文件按稀有度加权，所以被上百个提交改过的热点文件不会把所有提交两两配上。输出分四档，默认只报前两档：LOCAL-ADAPT 是 fork 侧带环境适配特征（cache、显存、监控、传输）的对子，RIVAL 是双方都在做同一件事，FILE-ONLY 和 TOPIC-ONLY 是偶然碰撞，要看得加 `--kinds`。没被报出来的提交在另一侧没有对手，可以直接跟着批量合并走。

每个 LOCAL-ADAPT / RIVAL 对子先定取舍再动手，结论只有三种，不要在合并现场即兴决定：

1. 上游做得更好：彻底删掉场内实现，按「跟随删除的执行标准」删干净，不留一份没人调用的代码等下次合并再冲突一遍。
2. 场内做的是环境适配、上游没有对应能力：保留场内行为并接到上游的新结构上（L2 / L9），不要因为上游有形似的代码就判为已吸收。
3. 两边各保了不同的性质：先分别写清各自要保什么，再合成一份实现。

落地分两段。第一段做批量合并，这些对子涉及的位置先整取一侧（一般取上游）让合并干净落地；第二段在合并之上一个对子一个提交地做处置，标题带 fork 短 SHA 和 upstream 短 SHA，正文写取舍理由。一个对子一个提交的价值在追查，不在 push 形态：评审只收一个提交时，worktree 里照样保留这份分段历史，`git log --oneline "$TARGET_SHA..HEAD"` 就是处置台账，push 前再用 `git commit-tree` 压成一个（见「发布」），处置清单进 commit message，`intent-overlap.md` 进 CR 描述。

判过的对子写进 waiver 文件，格式 `fork 短 SHA<TAB>理由`。两个父提交都是冻结 SHA，所以 waiver 跨 patchset 一直有效，理由列本身就是 CR 里的处置记录。

`pick` 模式在这个 worktree 里逐提交 `git cherry-pick`，每个 old commit 必须对应一个 new commit，冲突当场解决当场记录。`squash` 模式做一次整体合入，最终相对目标只留一个提交，后续修复一律 `git commit --amend --no-edit`。

冲突不要按行挑，先判断这一处属于哪种语义情形，再决定保留哪一侧、以及要不要在新结构上重新实现 fork 的行为。判断规律见 `references/resolution-laws.md`。

合并完成之后，按 `references/merge-case-taxonomy.md` 逐类过一遍。那份表列的 9 类缺陷都不产生冲突，靠肉眼看 diff 也基本看不出来，每类都写清了检测手段和正确改法。开工前先把交付目标要开的特性组合列成清单（模型、attention 后端、MTP、EP、PD 分离、cache），这份清单同时是 M8 的验证范围和 `--critical-path` 的取值来源。

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

八个门禁是这个 skill 自带的。日常直接用 `scripts/run_gates.sh` 一把跑完，它把结果汇成一张表，可以直接贴进 CR 描述：

```bash
REPO="$WORKTREE" TARGET_SHA="$TARGET_SHA" SOURCE_SHA="$SOURCE_SHA" \
  ARTIFACTS="$ARTIFACTS" \
  REVIEW_BASE_SHA="$REVIEW_TARGET_SHA" \
  CRITICAL_PATHS="<交付必经路径 glob，空格分隔>" \
  DEPLOY_YAMLS="<发版 YAML，空格分隔>" \
  CARD_PATTERN="<工单号正则>" \
  FLAG_WAIVERS="$ARTIFACTS/gate-flag-waivers.tsv" \
  SYMBOL_WAIVERS="$ARTIFACTS/gate-symbol-waivers.tsv" \
  INTENT_WAIVERS="$ARTIFACTS/gate-intent-waivers.tsv" \
  bash "$SKILL_DIR/scripts/run_gates.sh"
```

`TARGET_SHA` 是 fork 侧父提交，用于所有父子对比；`REVIEW_BASE_SHA` 是评审要落的分支 tip，只给 preflight 用。两父合并时这两个值不同，混用会让 preflight 报出几百个提交。没给 `TEST_COMMAND` 时 parent-test-delta 记 deferred 而不是 pass。

`intent_overlap_scan` 是八个里唯一只读两个冻结父提交的，合并前后跑出来一样，所以它既是合并前的隔离清单，也是合并后的「这些对子你处置了吗」检查表。

已经判过的发现写进 waiver 文件，格式是 `名字<TAB>理由`，没写理由的行不生效。`flag_inventory` 收 DROPPED / NO-OP 的豁免，`absent_symbol_triage` 收 REAL-LOSS 的豁免，`intent_overlap_scan` 收已处置的意图冲突对（键是 fork 短 SHA）。这样门禁对新发现仍然会红，判过的东西不必每轮重判，而且理由本身就是 CR 里的处置记录。waiver 是每次合并的数据，跟产物放一起，不进 skill 仓库。

单独跑的话，其余七个门禁的命令如下（`intent_overlap_scan` 见上面「先隔离意图冲突对」）：

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

```bash
# 把 interface_delta 的 HIGH 行按处置顺序自动分类，只留下真正要人看的
python3 "$SKILL_DIR/scripts/absent_symbol_triage.py" \
  --repo "$WORKTREE" --report "$ARTIFACTS/interface-delta.md" \
  --target "$TARGET_SHA" --source "$SOURCE_SHA" \
  --output "$ARTIFACTS/absent-symbol-triage.md"
```

`absent_symbol_triage.py` 把「public symbol 在最终树里不存在」分成 MOVED（同名还在别处）、RENAMED-TWIN（改了名字但注释原文没变）、DEAD-IN-PARENT（父提交里本来就没人调用）和 REAL-LOSS。只有 REAL-LOSS 需要人看，而且要先问两个问题：这个符号上游有没有过（没有就是 fork 自己的能力，得显式决定跟不跟随删除），以及它在不在这次交付要开的路径上。

```bash
# fork-only 模块里已经没人调用的残留，拿发版 YAML 的开关做安全网
python3 "$SKILL_DIR/scripts/orphan_scan.py" \
  --repo "$WORKTREE" --target "$TARGET_SHA" --source "$SOURCE_SHA" \
  --deploy-yaml <发版 YAML，可重复> \
  --output "$ARTIFACTS/orphan-scan.md"
```

`orphan_scan.py` 的结论用来执行「不要的能力就跟着上游删掉」：ORPHAN 行（没有 importer、名字在别处也不出现、且不读任何发版 YAML 传的开关）直接删文件，别留到下次合并再冲突一遍；DYNAMIC-MAYBE 行意味着名字出现在字符串里，可能被 registry 或 importlib 拉起来，必须人工确认后再动；IN-USE 行不许删。删完重跑 import 门禁。

测试差分是这三个里命中率最高的一个：有冲突的每个子系统都要在最终树和两个父提交上跑同一批测试。只在最终树失败的用例是 merge 缺陷；和父提交共有的失败属于继承下来的债，不扩大范围；两个父提交都没有的用例单独标注待人工判定。父提交环境跑不起来就记 deferred，不要只拿最终树的结果当证据。

最后固定跑一遍：

```bash
git diff --check "$TARGET_SHA..HEAD"
git diff --name-only --diff-filter=U
git merge-base --is-ancestor "$TARGET_SHA" HEAD
git status --short
```

能编译就编译，能跑仓库自带的 lint 或 pre-commit 就跑。改动过的文件的静态检查要和冻结目标上的同一批文件对比条数，只关心新增的那几条。

### 跨组件契约

门禁全绿只说明仓库内部自洽。合并会同时换掉 reasoning parser、chat template 的消费逻辑和 protocol 的字段规范化，这三处的另一端在推理链路网关和评测框架里，diff 和静态门禁一个都看不见。判定点、八种请求写法的验证矩阵和本次实测出的契约事实见 `references/pipeline-contract.md`。那份文档的第一条规则是先用最小实验确定「谁在加工数据」再动代码：本次因为跳过这一步，连发了三版建立在错误假设上的 patchset，全部作废重写。

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
- 双方都做过同一个能力的提交对，合并时最容易两份实现都留下，而且不产生冲突；合并前先扫一遍，别指望合并后的门禁在几百个符号里帮你捞。
- 看起来只做输出格式化的参数（例如 `--reasoning-parser`）删掉之后坏的往往不是格式而是 function call。这类参数按「谁在消费它的输出」判，不能按名字判。
- 「同一条请求直连引擎正常、走网关不正常」不等于网关有问题：引擎侧会从转发来的字段合成 `chat_template_kwargs`，走网关的流量天然多带字段。先在裸 token、直连、经网关三个观测点各打一次，再决定改谁的代码。
