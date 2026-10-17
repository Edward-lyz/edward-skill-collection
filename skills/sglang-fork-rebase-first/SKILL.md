---
name: sglang-fork-rebase-first
description: 追社区新版本的二分法：社区基线直换 + 厂内 PR 台账化选择重放。默认只迁移多模态和监控两类 PR（其余类别需用户明确要求）；本机 uv 环境优先、GPU 或依赖装不上时 fallback 远端开发机；重放完成后自动提交 CR（refs/for）并从 ChangePipeline 的「构建镜像」任务取回镜像地址。fork 相对旧基线的提交先按七类台账定去留（社区已收录丢弃、非交付模型不迁、特性绑定按交付特性清单取舍），剩余按原始拓扑序逐卡 pick；交付镜像四件套放栈底；重放完成的判据是平台契约自动核对零退出码——路由、指标族、req_id trace、token id dump、日志 schema、厂内环境变量逐项在位。触发词：追社区、升级基线、base swap、厂内 PR 梳理、rebase 到新版本、交付镜像换基础镜像、厂内适配栈重放、监控指标有没有漏迁、平台契约核对、提交 CR 拿镜像、base 镜像版本锚核对、重放后部署测试、提测发版报告。适用于 fork 与上游长期分叉、整支 merge 成本已失控的仓库；pick 冲突语义与合并后门禁复用 sglang-pr-rebase-or-pick。
---

# 追社区：基线直换 + 台账化重放

## 为什么把方向反过来

旧路线是把社区新版本 merge 进厂内分支。GLM-5.3-Flash 那次的实账：merge diff 4,692 文件 /
+485k 行，冲突 217 文件 / 590 块逐处人工判，送审被迫 squash 成一个 3,570 文件的 CR，评审
粒度归零，合并后又冒出 M1–M9 九类不产生冲突的静默缺陷，追了 3 个修复提交和多轮镜像返工。
根因：merge 把「社区已收录的内容 + 厂内全量历史」按行搅在一起，双方各做过一遍的东西制造
了最大的冲突面，而它们本来一行都不需要动。

新路线二分。**基线直换**：新分支直接从社区目标版本开出，这一步按构造无冲突。**台账化
重放**：fork 相对旧基线的提交先分类，只把必要的类逐卡 pick 上去——冲突仍会有，但每个都落
在单一意图、单一 owner 的小补丁里，可判可审。

K3 分支实测（226 提交 / 13.4 万行的厂内谱系）：社区已收录 34 提交 / 6.4 万行在新基线下免费
消失；非交付模型的专属改动 43 提交 / 1.6 万行显式不迁移；特性绑定的改动只在交付开启对应
特性时迁（多模态 EPD 栈 2.4 万行、AttentionStore 1.5 万行、DSpark/VL kernel 1 千行，开启时
也先 diff 社区 rival 再搬 delta）；**无条件必迁只剩 41 提交 / 3.6 千行（3%）**。完整台账见
references/pr-taxonomy.md。

## 何时使用

用户要把厂内 fork 追到社区某个新版本（换基线），或要求梳理厂内 PR 台账。不适用：把上游一段
提交搬进厂内旧基线、或单卡 cherry-pick——那是 sglang-pr-rebase-or-pick 的场景。两个 skill 的
分工固定：本 skill 管策略、台账和 pick 编排；每处冲突的语义判定（L1–L12）、合并后静默缺陷
（M1–M9）、八门禁与 waiver、跨组件契约验证，全部沿用 sibling skill，不重复实现。

## 硬规则

1. 冻结三个引用再动手：FORK_SHA（厂内 tip）、OLD_BASE_SHA（merge-base(fork, 社区)）、
   NEW_BASE_SHA（要追的社区版本）。台账与 pick 全程用冻结值。
2. 没有分类台账不开始 pick。台账 = 脚本生成的信号 + 人工定类，分类结论落盘进产物目录。
3. pick 集相对交付判定，两根轴：**模型轴**——B 类只在交付就是该模型时迁（给 GLM 追新，K3
   专属不迁；K3 自己追新照迁）；**特性轴**——特性绑定的 A 类只在交付开启该特性时迁。台账里
   类别、模型标签、特性是三个独立字段。
   **默认范围只有两类：监控（A2）和多模态（EPD/encode/视频图像预处理等特性绑定块）。**
   其余 A1/A3/A4/A5 和 B 类默认不迁，不为它们向用户确认；用户点名要加某类时才扩大，并把
   扩大的类别写进台账 decision 列。`fork_pr_inventory.py` 的 `scope_hint` 列按这个默认范围
   预标（monitor / multimodal / out），人工复核后落进 decision。
4. 丢弃要有证据。C1 的每一条要么标题带社区 PR 号，要么能在 NEW_BASE 里指到等价实现（rg
   符号或文件）。厂内 pick 时常带私改：diff 厂内版与社区版，私改部分拆出来按 A/B 类处置，
   不能凭标题相似整条丢。
5. 选择按分类，重放按原始拓扑序。原分支按时间演进，原序天然满足卡内与卡间依赖。
6. 逐卡送审，保留原工单号；同一变更迭代复用 Change-Id。每卡 pick 完跑该卡子系统的门禁，
   不攒到最后一次性跑。
7. 部分重放和「缺宿主」都要在台账 evidence 里写清留下的是什么、为什么、需要时从哪笔捡
   回来；缺宿主的另一条出路是按 sibling skill 的 L2/L9 补宿主。不允许静默丢弃——`/ready`
   就是静默丢弃的代价。
8. worktree 隔离、不直推保护分支、跑不起来记 deferred 不记 pass——同 sibling skill。
9. 重放完成的判据是三个验证点，不是「卡都 pick 完了」：**1 所需字段都能取到**
   （`verify_platform_contract.py` 零退出码）；**2 与源 PR 集 line-by-line 一致**
   （`replay_residual.py` 的漏迁与该删没删归零，例外只有上游改了接口，且理由要点名那处变更）；
   **3 起 EPD 服务实测能力与字段**。前两点拦不住值失真，那部分必须由第 3 点接。
   第 3 点按部署形态排优先级：先起 PD 分离，资源允许再起集中式（不带
   `--disaggregation-mode`）；集中式没资源起时，必须做集中式路径静态检查，不能直接跳过。
10. 产物是提交序列，不是一个 diff。每笔都从**远端 ref 上的原提交** pick，pick 前
    `git merge-base --is-ancestor <sha> <remote-ref>` 确认远端确实有它；只有远端不可达
    （提交没推过、分支已删）才退到打补丁，并在正文里写明这一笔是补丁兜底。
11. 环境本机优先：先 `scripts/pick_env.sh <static|unit|gpu>`，输出 `local <venv>` 就在
    本机 uv venv 里跑，输出 `remote <cmd>` 才走远端。远端由用户给的 `REBASE_REMOTE`
    决定（一条能在远端执行 shell 的命令前缀，如 `ssh user@gpu-host`），skill 不假设任何
    私有脚本；未设置而又必须走远端时，停下来向用户要这个值。判据：静态步骤（台账、pick、
    ruff、契约核对、residual、CR、取镜像）全在本机，它们只依赖 git 和 stdlib；单测在 venv
    装得上 torch 与 `sglang.srt` 才留本机；EPD 起服务、kernel 测试一律远端。fallback 要在
    台账里记一行原因，不静默切换。
12. 重放完成并通过本地门禁后，**自动提交 CR 并取回镜像地址**，不再停下来问用户要不要推
    （refs/for 评审提交可撤销，已由本规则授权）：`scripts/submit_cr.sh` → `scripts/cr_image.py`。
    受保护分支仍然不直推。流程见第 8 步。
13. **base 镜像地址是必填输入，且必须用户手动确认。** 开工时就要拿到 `BASE_IMAGE`（交付
    Dockerfile 的 FROM，形如 `iregistry.baidu-int.com/...:tag`）。用户没给就问；给了或者
    从模板推出了候选，也要把完整地址原样回显、等用户明确回复确认后才继续——不因「模板里
    就是这个」自行确认。确认结果写进台账，Dockerfile 的 FROM 必须与之逐字一致，
    `submit_cr.sh` 会校验，未确认或不一致就拒绝推送。确认的是地址，不是兼容性：提交 CR 前还要跑
    `scripts/check_base_image_pins.py`，拿新基线 `python/pyproject.toml` 的 torch / sglang-kernel pin
    对这个镜像的 `pip list`，不过就换 base 再确认（见第 6 步）。

## 流程

### 0 冻结与台账

```bash
ENV=$(bash "$SKILL_DIR/scripts/pick_env.sh" static)   # 硬规则 11：local <venv> 或 remote <host>
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
cards_summary.md（卡片聚合）。HINT 只是关键词启发，**每张卡人工定类，混合卡逐提交定类**，
把最终 cat 列改回 TSV。--conflict-paths 给上一次整支 merge 的冲突文件清单，没有就省略。

### 1 用户确认 pick 集

默认 pick 集 = 监控 + 多模态（硬规则 3），不需要再问。只有两件事仍要对着台账确认，且
能从上下文推出就不问：交付模型是什么（多模态块里 B 类的模型专属部分去留）；多模态块
在社区是否有 rival 实现（有则先 diff 社区版再定搬什么）。AttentionStore、DSpark、VL
kernel、通用 BUGFIX 等其余特性整块跳过，发版 YAML 同步去开关；用户明确要求时再加。C2
里的镜像四件套是交付管道，不算「迁移 PR」，始终随栈底一卡进入（第 6 步），因为自动取镜像
依赖它。确认结果写进台账的 decision 列。

A1 链路适配 + A2 监控适配 + A5 通用 BUGFIX 这部分在 DSv4.1 那轮已经落成一个 diff 加一份逐卡
台账，见 references/internal-platform-stack.md：追新基线时拿它当重放起点和平台契约对照物，
这三类不必再从 fork 历史重新翻一遍。

### 2 基线直换

```bash
git worktree add -b "$CANDIDATE_BRANCH" "$WORKTREE" "$NEW_BASE_SHA"
```

第一步到此完成。不要在这一步夹带任何厂内改动。

### 3 清单消噪

pick 清单生成前先做三件事：成对 revert 互消（A 提交 + 后续 Revert "A" 同时出现则双双出
清单）；历史搬运提交跳过（标题形如 "Pick aiak code"、"merge X into Y" 的大杂烩，其内容已被
后续演进覆盖，pick 它等于回滚后面的修复）；同卡 fixup 折叠——一张 39 提交的卡有一半是对前
一半的补丁（补 import、编码规范、改签名），按卡折叠成一个补丁再重放：

```bash
git diff "$CARD_FIRST^..$CARD_LAST" -- $CARD_FILES > "$ARTIFACTS/patches/$CARD.patch"
```

混合卡例外：先按逐提交分类拆开，再各自归类折叠。

### 4 逐卡重放

按原始拓扑序（`git log --reverse --topo-order` 过滤出选中集）重放，**一个评审面一个提交**：
同一评审面的多张卡、每张卡的多笔、连同评审 fixup，用 `cherry-pick -n` 连着落进工作区再一次
commit，折叠动作就此完成，不必先算卡级补丁。粒度按「评审时要一起看的东西」定，不按卡数定：
DSv4.1 这轮六张监控卡合成两笔——指标发得对不对、日志与探针接不接得上平台——卡号在正文里
逐条点名，追溯不丢。卡多到评审面不清楚时再拆。

```bash
git merge-base --is-ancestor "$SHA" "$REMOTE_REF"        # 远端确有这笔，硬规则 10
git -c rerere.enabled=false cherry-pick -n $SHA_1 $SHA_2 # 连拣，rerere 先关
git commit -F -                                          # 折叠成一笔，写卡级 message
```

拣序错了就 `cherry-pick --abort` 重来：把后一笔排在前面，冲突里会出现「base 有而 HEAD
没有」的第三方内容，看着像社区改的，其实是自己乱序制造的。连拣中途出冲突就必须当场解完
再继续，后面几笔会静静地落进未解冲突的工作区，一路「干净」到最后 commit 才报 unmerged，
那时几笔已经搅在一起，只能 `cherry-pick --quit` + `reset --hard` 退回上一个提交重来。

别人的卡照原样搬：`git commit -C <原 SHA>` 连作者和 Change-Id 一起保留，同一评审继续迭代。
自己的卡重写 message，格式跟厂内 EPD 那组一致，一眼能看出进度和边界：

```
<卡号> [<模块>][PR i/N] <中文主题>: <要点> + <要点>

<为什么需要它：平台侧或用户侧看到的现象>

<分组标题>:
- <文件>: <这个文件里做了什么>

重放自 <来源短 SHA 列表>（<远端 ref>），<冲突与解法>，<与源提交的行为差>。
```

末段三件事必须写：来源 SHA 与远端 ref（可追溯）、冲突位置与判据（可复核）、与源提交的行为
差（可争论）。冲突逐处按 sibling skill 的 L 律判定；社区侧结构变了的按 L2/L9 把厂内行为接到
新结构上，不要凭形似判「已吸收」。解完冲突先扫一遍未定义名字——语法过了不等于名字在：

```bash
ruff check --isolated --select=F821 $(git diff --name-only "$NEW_BASE_SHA"..HEAD -- '*.py')
```

社区改过 API 名（`get_pp_group()` → `get_parallel().pp_group`）而厂内那笔把旧名搬了过来，
就只在这一步露出来。每卡完成后立即跑：

```bash
python3 "$SIBLING/scripts/import_audit.py" --repo "$WORKTREE" \
  --parent "$NEW_BASE_SHA" --critical-path <该卡子系统 glob> \
  --output "$ARTIFACTS/import-audit-$CARD.md"
```

加该卡子系统的仓库自带测试。红了当场修，修完重跑，不带病进下一卡。

### 5 全量门禁与交付验证

全部卡重放完，按 sibling skill 跑 run_gates.sh 八门禁 + 交付特性组合清单 + 跨组件契约三
观测点。两个专项检查：B 类跳过后的悬挂引用（A 类代码里 import 模型专属模块的行要跟着裁，
import_audit 的 NEW 段会报）；C1 丢弃后的行为差（厂内 pick 版与社区收录版不一致的私改，
确认已按硬规则 4 拆出）。

### 6 交付镜像四件套

先拿到用户手动确认过的 `BASE_IMAGE`（硬规则 13），Dockerfile 的 FROM 写它，不写别的。

C2 里的镜像改动按厂内已有格式改：`ci.yml`、`build/build.sh`、`dockerfile/Dockerfile`、
`dockerfile/gpu_requirements.env`，模板取 origin 上**同类 base**（社区镜像 / 厂内
aiak-inference 镜像）的最近交付分支。自创 `Dockerfile.<x>` / `build_<x>.sh` 这类名字流水线
不看，DSv4.1 那次整卡被打回重做。

这一卡放在**栈底**。社区树里没有 ci.yml，基线直换后它必缺，而每个 change 的 CI 各自 checkout
自己那条 ref，排在它之后的卡才继承得到；漏了的表现是流水线一开工就停在
`can not get ci.yml from iCode`。

换 base 时把模板里继承来的每一步过一遍三分法：

| 类 | 判据 | 处置 |
|---|---|---|
| base 专属 | 这步操作的包或文件只存在于旧 base | 删，并在 Dockerfile 头注释写清替代做法 |
| 运行时通用 | 厂内环境要求，与模型无关 | 原样保留 |
| 版本锚 | 值绑在某个 base 上：版本号、dist-packages 路径、cuda12/13 wheel 变体 | 构建时从 base 现取，或按新 base 重挑 |

代价不对称：base 专属项留着，构建当场失败（patch 找不到目标文件）；运行时通用项删掉，要等
上线才发现（平台钩子失效、PD 起不来）。所以先扫一遍「这步碰的包在新 base 里存在吗」，再判
剩下的。

```bash
bash "$SKILL_DIR/scripts/check_image_layout.sh" "$DELIVERY_TIP" "$NEW_BASE_SHA" "$TEMPLATE_BRANCH"
```

完成判据：脚本零退出码。镜像不在本机构建：CR 流水线的「构建镜像」任务会构建并产出地址，
由第 8 步自动取回。本机没有 docker 不再是 deferred 理由；上机冒烟仍按验证点 3 在远端做。
逐步继承清单与两种 COPY 策略见 references/delivery-image.md。

**换基线时 BASE_IMAGE 要跟着换代。** DSv4.1 flash（2026-10）用户先确认了旧的厂内 dev 基础镜像
`…/sglang:dev-dsv41`，里面是 torch 2.13 / sglang-kernel 0.4.6.post1，而新基线固定 torch==2.14.1、
sglang-kernel==0.4.9：镜像构建成功，服务一启动就报 `sglang-kernel 0.4.6.post1 is less than the minimum
required version 0.4.9` 退出，整轮 CR 镜像白建，最后改用与基线同代的社区 nightly（cu13）。所以确认完地址、
提交 CR 之前：

```bash
docker run --rm --entrypoint python3 "$BASE_IMAGE" -m pip list --format=json > "$ARTIFACTS/base-pip.json"
python3 "$SKILL_DIR/scripts/check_base_image_pins.py" \
  --pyproject "$WORKTREE/python/pyproject.toml" --pip-list "$ARTIFACTS/base-pip.json" \
  -o "$ARTIFACTS/base-pins.md"
```

零退出码才继续。其余 pin 只列 WARN（运行时只断言少数几个包，Dockerfile 还会再装一批）。本机没有 docker 就在
远端开发机上跑 `pip list`。

### 7 平台契约反向核对

台账是从 fork 提交出发的正向流程，只能保证「我们挑中的都搬了」，保证不了「平台依赖的都还
在」——探针、指标、采集开关的宿主都在平台侧。重放完成后必须从平台契约回查代码和发版 YAML，
一次脚本核对加三项手工核对都要过。

**验证点 1：所需的字段都能够被 get 到。**

```bash
python3 "$SKILL_DIR/scripts/verify_platform_contract.py" \
  --repo "$WORKTREE" --ref HEAD \
  --contract "$SKILL_DIR/assets/contract-dsv41.json" \
  -o "$ARTIFACTS/contract-verify.md"
```

脚本遍历 `python/sglang/srt` 的 AST，提取当前分支的能力集与契约比对：路由（主 server 与
dummy server 分开）、指标族（有 `name="sglang:..."` 定义**且**有真实写入点，只 `inc(0)`
预热的单独归一类）、rid stage trace 行（`trace(logger, "…")`）、token id dump 点
（`log_input_ids(logger, rid, "<stage>", ids)`）、日志 schema（`configure_logger` 的 prefix
与 `%(levelname)s` 打头）、厂内环境变量读取点（`os.getenv` / `os.environ` / `envs.`，以及
`_env_bool("CD_X", …)` 这类自家包装）。

完成判据：退出码 0。退出码 1 时 stderr 逐条报缺什么、原来的宿主文件是哪个；指标族定义还在
但没人写它，报「无写入点」而不是 MISSING——面板一样是 No data，但修法不同。DSv4.1 实测：契约
76 项，交付 tip 76/76 过；拿只重放到 `43b2ba6d8b` 的中途状态核对，报缺 49 项（26 个指标族、
14 条 trace 行、5 个预热计数器、2 个 token id dump 点、2 个环境变量），路由与日志 schema 那
时已经在位。

契约不手维护，换基线后重新求差生成：

```bash
python3 "$SKILL_DIR/scripts/verify_platform_contract.py" \
  --repo "$REPO" --ref "$DELIVERY_REF" --against "$NEW_BASE_SHA" --emit \
  --env-name MASTER_IP -o "$ARTIFACTS/contract-next.json"
```

`--emit` 只收「交付 ref 有、社区基线没有」的能力，所以社区后来自己收了某条路由或某个族，它
就自动从契约里退出，不会留下永远要人解释的历史项。交付 ref 上定义了却没有写入点的族不进契约，
emit 时单独打一份清单——那是本分支自己的坑，先修。

**手工：三项脚本判不了的。**

1. **启动参数反查**。参考 YAML 不是参数契约，照抄会让容器直接以 `unrecognized arguments`
   退出；对**这次要出的镜像**的 argparse 反查：
   `python3 "$SKILL_DIR/scripts/check_launch_args.py" --repo "$WORKTREE" --yaml <发版 YAML>`。
   差集三分：社区已删且能力默认开启 → 删参数；厂内私有且这次需要 → 按 A 类补迁那笔提交；
   厂内私有且不需要 → 删参数并在台账记一行「能力缺失，需要时迁 \<SHA\>」。
2. **指标 label 集合逐字比**。面板的 PromQL 按 label 选序列，少一个图就空；取上一版交付分支
   和 HEAD 的同一处 `labels = {` 比。
3. **面板清单反查**。指标名从 dashboard 的 JSON（`<url>&editview=dashboard_json`）取，不要
   按面板标题猜；空面板按五类根因定性（缺观测点 / label 值不匹配 / label 集由拓扑决定 /
   部署开关未开 / 计数器未预热），再排除看板查询自身写错。

完成判据：1 的未识别参数清零，2 逐字一致，3 的每个空面板有定性结论。DSv4.1 那次跳过反向核对
的代价是平台探针拿到 404、POD 永远不进服务列表，白等一轮 12 分钟冷启动才发现。

**验证点 2：对比源 PR 集，代码 line-by-line 一致。** 字段都在不等于内容都落地了。以源提交为
判准，两侧各算净改动行集合再求差：

```bash
python3 "$SKILL_DIR/scripts/replay_residual.py" --repo "$WORKTREE" \
  --new-base "$NEW_BASE_SHA" --tip HEAD \
  --source-commit <选中的每一笔> [--accept "$ARTIFACTS/accepted-residual.tsv"] \
  -o "$ARTIFACTS/residual.md"
```

完成判据：漏迁与「该删没删」两类归零。唯一允许的例外是**上游改了接口**，写进 `--accept` 清单
并在理由里点名那处变更，只写「有意改写」不算，没写理由的规则脚本直接拒绝。这两类是承重信号
（冲突解丢一行、折叠漏 hunk、老实现没删干净）；「新造」不进判据，整行搬家会造成假阳性。
DSv4.1 实测：18 笔源提交对 6 笔重放，4 行漏迁全指向社区自己新增 `/ready` 那处接口变更，挂上
`assets/accepted-residual-dsv41-main.tsv` 后归零。

**验证点 3：实际启动 EPD 服务，测试能力和字段。** 前两点只看代码长什么样，看不出值对不对。
三角色拉起来打一条带图 PD 请求，然后逐项取数：探针回什么码、`/metrics` 按族名前后 diff 只多
不少、同一个 rid 能串起全链路的 stage 行、`tokenized` 与 `padded` 两份 token id 都能 dump 且
padded 与平台 dump 逐位一致。启动参数缺 `--enable-metrics` 就全是空的。逐项判据、响应字段清单
和取数的三个陷阱见 references/epd-runtime-acceptance.md。跑不起来记 deferred，不记 pass。

**集中式也要起（优先级低于 PD 分离）。** PD 分离跑通不代表集中式能跑：`Scheduler.process_batch_result`
按 `disaggregation_mode` 分岔，PD prefill 节点走 `disaggregation/prefill.py` 的
`process_batch_result_disagg_prefill`（Scheduler mixin，`self` 是 Scheduler），集中式走
`scheduler_components/batch_result_processor.py` 的 `process_batch_result_prefill`（独立的
`slots=True, frozen=True` dataclass，`self` 只有构造时传入的字段）。同一笔监控代码在两边各加一份，
只有集中式那份会炸。顺序是：

1. 先起 PD 分离（交付形态），按上面逐项取数。
2. 资源允许再起集中式：同一套模型参数去掉 `--disaggregation-mode` 系列，带 `--enable-metrics`，
   打一轮有并发、含短输出（`max_tokens` 小或首 token 即 EOS）的请求，让请求在 prefill 后就结束，
   覆盖 `req.finished()` 分支。scheduler 不报错、`/metrics` 族名齐全才算过。
3. 集中式确实没资源起，做集中式路径静态检查，结论写进台账，记「静态通过 / 运行 deferred」：

```bash
# 重放引入的 self.<attr> 访问，逐个对照所在类有没有这个字段
git diff "$NEW_BASE_SHA"..HEAD -U0 -- python/sglang/srt/managers/scheduler_components \
  | rg '^\+.*self\.(server_args|enable_metrics)\b'
# 组件类的字段表：dataclass 字段 + scheduler.py 里构造时传的关键字参数
rg -n '^class |^    [a-z_]+: ' python/sglang/srt/managers/scheduler_components/batch_result_processor.py
```

   组件类里读开关一律走全局 getter（`get_observability().enable_metrics`、`get_memory()`、
   `get_disagg()`）；Scheduler 及其 mixin 里走 `self.metrics_reporter.enable_metrics`。
   案例与判据见 references/monitoring-contract.md 第八节第 8 条。

**核对脚本自己的正确性**靠变异探针，改过核对脚本或加过能力类之后跑一次：

```bash
python3 "$SKILL_DIR/scripts/verify_mutations.py" --repo "$REPO" --ref "$DELIVERY_REF" \
  --contract <该分支自己 --emit 出来的契约> -o "$ARTIFACTS/mutations.md"
```

逐个种入一类真实发生过的缺陷，看验证点 1 是否变红：应拦的 CAUGHT、登记在案的盲点 SURVIVED 才算
通过。这一轮它抓出核对脚本自己的 bug——路由只按路径记 key，encode server 上的同名 `/health_forward`
把主 server 那份盖住了，删主 server 的照样过。三个验证点的分工、盲点移交和实测数据见
references/verification-ladder.md。

案例证据全部在 references/monitoring-contract.md：`/ready` 静默丢失的根因链、两个已不存在的
启动参数、13 个空面板逐条定性、监控代码八条高危写法（四条会打挂服务）、读 `/metrics` 的三个
陷阱（hostNetwork IP 串台、带 label 指标要等首次观测、两个 collector 分开判）、发版 YAML 监控
必查项、不重启 POD 的三方 md5 热替验收。迁完监控代码和判「指标缺失」之前各读一遍。

### 8 发布：自动提交 CR 并取镜像地址

逐卡走 refs/for 送审，一卡一个 change。评审系统限单批数量时按类分批（监控一批、多模态
一批），别退回整支 squash——粒度是这条路线的核心收益。门禁和契约核对全绿后直接执行：

```bash
bash "$SKILL_DIR/scripts/submit_cr.sh" "$TARGET_BRANCH" --base "$NEW_BASE_SHA" \
  --base-image "$BASE_IMAGE" --base-image-confirmed \
  | tee "$ARTIFACTS/cr-push.txt"
TIP=$(git rev-parse HEAD)
python3 "$SKILL_DIR/scripts/cr_image.py" --revision "$TIP" --base-image "$BASE_IMAGE" \
  -o "$ARTIFACTS/image.json" | tee "$ARTIFACTS/image.txt"
```

`submit_cr.sh` 先校验每笔都有 Change-Id（缺了会多开 change）、工作区干净、目标不是
master/main，再 `git push origin HEAD:refs/for/<target>`；`--dry-run` 只做校验。
`cr_image.py` 用 `ipipe-cli build commit` 按 tip SHA 找 ChangePipeline（conf 2205943）的
构建，轮询到「构建镜像」任务结束，从其 outParams 的 `NORMAL_IMAGE_VERSION` 取地址，形如
`iregistry.baidu-int.com/hac_test/aiak-inference-sglang:<user>_<yyyymmdd>_<hhmmss>`。用 tip
而不是第一笔：每个 change 的 CI checkout 自己那条 ref，只有 tip 的镜像含整栈。退出码
0 = 取到、1 = 构建失败（stderr 给 buildUrl，按 ipipe-official 看日志）、2 = 超时。
ipipe-cli 不在 PATH 时 `cr_image.py` 自动调用 `ensure_ipipe.sh`：从官方地址下载
ipipe-official 包，按其 SKILL.md 里的版本与安装脚本装好 CLI（官方包地址可用
`IPIPE_SKILL_URL` 覆盖）。未登录（`ipipe-cli login status`）时按 `ipipe-official` 的
登录步骤让用户给 token 后停下。最终汇报同时给出 **base 镜像地址（用户已确认的）** 和
**构建出的镜像地址**，`image.json` 里两者都有。镜像失败的修复提交要保留原 Change-Id 再推，镜像
地址随新 patchset 重取。机制与字段见 references/cr-image.md。

改已推过的评审必须保留原 Change-Id：换消息文件时 commit-msg hook 会生成新的，icode 会拒并
提示 `git fetch ... refs/changes/<nn>/<change>/<ps>` 重放；带原 Change-Id 再
`git commit --amend` 就是正常的下一个 patchset。LLM 评审的 BLOCK 报告逐条核实再改，本轮 9 条
里 2 条是误报，误报也要把判据写进回复。

### 9 部署与测试（外部阶段）

镜像取回后部署 E/P/D，按「精度 → FC → 功能回归 → 长稳」触发 ipipe 流水线（走 `ipipe-run-pipeline` skill，
长稳用其 `stress` 场景的默认值：12 h、数据集取最近 10 次执行里出现最多的、Prefill pod 内发压）。起服务前
先做 import 冒烟与启动参数反查；部署命名、model_id 选取、测试判读，以及静态契约漏掉的 4 个运行期缺陷，
见 references/deploy-and-test.md。

### 10 提测发版报告

报告按知识库的发版文档格式写，章节骨架、写法规则和发 KU 的约束见 references/release-report.md。流水线结果
原样写入，没做的写「未执行」，修复后没重跑的写「推断」。

## 难度预判（分级用信号，不用感觉）

| 级别 | 信号 | 处置 |
|---|---|---|
| 易 | fork 独有文件为主，冲突史 = 0 | 直接 pick |
| 中 | 触少量社区文件，冲突史 1–5 | pick 后小修 |
| 难 | 冲突史 > 5，或触 scheduler / model_runner / serving_chat 等热点 | 预留 L2/L9 重实现时间 |
| 难(先拆) | 一卡多主题（≥3 个类别） | 先逐提交拆类再处置 |

冲突史 = 卡片触碰文件与上次整支 merge 冲突清单的交叠文件次，是「社区也在改这片」的实证代理。
52 卡的实测分布见 references/pr-taxonomy.md。

## 常见坑

- 「社区已收录」按标题判会误判：厂内 pick 时常改过签名或加过开关。证据是 NEW_BASE 的实现
  覆盖厂内行为，不是标题相似。
- 零冲突不等于该 pick：厂内特性栈（如 encode/EPD）常是与社区同名子系统的平行实现，全 fork
  独有文件、pick 必零冲突，但正确动作是取社区框架再搬 delta。rival 判定优先于难度判定。
- 台账把 fixup 当独立 PR，逐条 pick 是在重放噪声；先折叠。
- 跳过 Cache 类却没动发版 YAML：起服务读不存在的开关，直接 fail fast 在参数校验。
- 换了 Change-Id 的迭代会开出新评审；preflight 用 sibling skill 的 review_preflight.py。
- 大卡的卡级补丁跨越社区重构点时，git apply 失败率高于逐提交 pick；该卡退回逐提交重放，
  fixup 在 worktree 里 autosquash。
- 台账枚举用 --no-merges 会漏掉 merge commit 本身携带的解冲突改动；上一代分支若有内部
  merge，重放后跑 `git diff FORK_SHA..HEAD -- <路径>` 抽查关键子系统有无语义残差。
- `.gitignore` 的 `**/build/` 会挡住 `build/build.sh`，`git add -f` 才进得去；所以
  git ls-tree 看得到它而 git add 会拒。
- 改动四件套那一卡会让它后面的卡全部换 SHA、跟着升 patchset。送审前 diff 一次 Change-Id
  集合，确认没有多开 change。
- 上一轮解过的冲突会被 rerere 整文件顶回来，与本卡无关的 hunk 一起进来（实测：pick 一行
  media 收紧，顺带多出 CLIENT_MEDIA_EXCEPTIONS 加 OSError）。第一次看冲突用
  `git -c rerere.enabled=false cherry-pick`，解完 `git diff HEAD` 逐 hunk 核对只剩本卡的行。
- 一行改动照搬前先查新基线上谁在喂这个函数，同一行的语义可能反过来：厂内把 get_image_bytes
  的裸 `/` 分支删掉做收紧，而新基线的 load_image 已改成先剥 file:// 再把纯路径传下去，照搬
  后留下的 file:// 分支不可达、真正在用的裸路径分支被删，仓库自带的 registered 测试还把旧
  契约钉着。判据是 rg 出全部调用点，看清谁剥 scheme、谁读文件，再决定照搬 / 改写 / 放弃。
- 旧基线的 Scheduler 方法在新基线被拆成独立组件后，照搬的 `self.server_args` 会指向不存在的
  字段。DSv4.1 实测：`4318fff319` 把首 token 指标同时加进 PD prefill mixin 和
  `SchedulerBatchResultProcessor`，只验了 PD 分离，集中式压测时请求在 prefill 结束即
  `AttributeError: 'SchedulerBatchResultProcessor' object has no attribute 'server_args'`，
  全部 TP rank 退出。所以集中式也要起，起不了做上面的静态检查。
- 同一类错误会在不同卡上复发：DSv4.1 flash 的非 PD 部署里，Prefill 读 `self.server_args.enable_metrics`
  又让调度器退出（改成 `get_observability().enable_metrics`）。每张监控卡 pick 完都跑一遍上面的
  `rg '^\+.*self\.(server_args|enable_metrics)\b'`，不要等到集中式起服务。
- `from X import Y` 里的 Y 被社区重构掉，既不是 F821 也不影响契约核对，只在角色启动时 ImportError
  （luno-5185 引用的 `decode_image`，社区已改为 `patchify_image`）。每卡 pick 完在 BASE_IMAGE 里做 import 冒烟。
- 社区改行为不改结构，也会让厂内用例失败：V4.1 的工具调用约束换成 xgrammar 内置 XML 约束后，
  `tool_choice=required` 的非标识符参数名被改写。修法是 required / 指定函数走 JSON 约束，auto 保持内置约束；
  全部改 JSON 会让 FC 的 tool_calls 数从 940 掉到 677，所以拆成两条路径。这类缺陷只有功能回归能发现。
- 二次追新（基线又往前走了几百笔）时，直接把上一轮已评审的候选栈逐笔 cherry-pick 到新基线，比从 fork 历史
  重放省得多：DSv4.1 flash 从 1013 追到 1017 main，34 笔栈只有 2 处小冲突。但静态契约全绿不代表能起服务，
  之后必须跑 references/deploy-and-test.md 的 9.1.1（社区单测），它抓出了多 tokenizer 拆分的真缺陷。
- 社区重写了你要搬的循环时（例如 PD prefill 事件循环），先看社区单测钉住了什么。luno-5298 把三次轮询合成一次，
  按新循环重实现后 56 个 `test_prefill_result_polling` 用例失败，说明行为被改了；没有性能实测就不迁，别硬改测试。
- 厂内对社区有偏离的地方（例如强制调用的 DeepSeek 工具调用语法），先写一个探针脚本在镜像里直接问 xgrammar
  「编码器真实输出被不被接受」，再决定改法。1017 这一轮用探针确认：社区内置语法对非严格工具会改写
  `field.name`，而把 JSON 体换进去又会拒绝编码器的原生输出；正确做法是强制调用时把工具声明成按名字严格，
  自动调用保持社区内置语法。
