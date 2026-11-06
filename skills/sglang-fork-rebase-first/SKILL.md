---
name: sglang-fork-rebase-first
description: 把厂内 fork 升级到社区新版本：直接从社区新版本开新分支，再按分类清单挑出厂内提交重放上去。默认迁移链路、监控、多模态和 CI 四类 PR，框架层优化逐笔判受益面、所有模型受益的默认迁入（其余类别需用户明确要求）；本机 uv 环境优先，GPU 或依赖装不上时改用远端开发机；重放完成后自动提交 CR（refs/for）并从 ChangePipeline 的「构建镜像」任务取回镜像地址。fork 相对旧基线的提交先按七个类别定去留（社区已收录的丢弃、非交付模型的不迁、绑定特性的按交付特性清单取舍），剩余按原始拓扑序逐卡 pick；交付镜像构建文件放在最底下一笔；重放完成的判据是平台契约自动核对零退出码，即路由、指标族、req_id trace、token id dump、日志 schema、厂内环境变量逐项在位。触发词：追社区、升级基线、base swap、厂内 PR 梳理、rebase 到新版本、交付镜像换基础镜像、厂内适配栈重放、监控指标有没有漏迁、平台契约核对、提交 CR 拿镜像、base 镜像版本锚核对、重放后部署测试、提测发版报告。适用于 fork 与上游长期分叉、整支 merge 成本已失控的仓库。
---

# 追社区：从社区新版本开分支，按分类清单重放厂内提交

## 为什么把方向反过来

旧路线是把社区新版本 merge 进厂内分支。GLM-5.3-Flash 那次：merge diff 4,692 文件 /
+485k 行，冲突 217 文件 / 590 块逐处人工判，送审被迫 squash 成一个 3,570 文件的 CR，没法
逐项评审，合并后又冒出 M1–M9 九类不产生冲突的静默缺陷，追了 3 个修复提交和多轮镜像返工。
原因是 merge 把社区已收录的内容和厂内全量历史按行混在一起，双方各做过一遍的改动产生了
大部分冲突，而这些改动本来一行都不需要动。

新路线分两步。**换基线**：新分支直接从社区目标版本开出，这一步没有冲突。**按分类清单重放**：
fork 相对旧基线的提交先逐个分类，记进分类清单，只把需要的类别逐卡 pick 上去。冲突
仍会有，但每个都在一个目的单一、负责人明确的小补丁里，能逐个判断和评审。

K3 分支实测（226 提交 / 13.4 万行厂内改动）：社区已收录的 34 提交 / 6.4 万行在新基线上
不用再管；非交付模型的专属改动 43 提交 / 1.6 万行不迁移；绑定特性的改动只在交付开启对应
特性时迁（多模态 EPD 栈 2.4 万行、AttentionStore 1.5 万行、DSpark/VL kernel 1 千行，开启时
也先 diff 社区同类实现再搬差异）；**无条件必迁只剩 41 提交 / 3.6 千行（3%）**。完整分类清单见
references/pr-taxonomy.md。

## 何时使用

用户要把厂内 fork 追到社区某个新版本（换基线），或要求梳理厂内 PR 分类清单。本 skill 自带全部
脚本和规则：策略、分类清单和 pick 编排；每处冲突的语义判定（L1–L12）、合并后静默缺陷（M1–M9）、
九个静态门禁与 waiver、跨组件契约验证；以及最后的 ipipe 测试流水线。不依赖其他 skill。

冲突语义 L1–L12 定义在 `references/resolution-laws.md`，静默缺陷 M1–M9 在
`references/merge-case-taxonomy.md`，门禁与跨组件契约的操作手册在 `references/gates-workflow.md`
和 `references/pipeline-contract.md`。本文最常引用两条：L2「Preserve the Active Owner」，
保留新基线上真正被构造、注册、调用的那份实现，把厂内行为加在它或它的扩展点上（社区重构过的地方
不要把旧实现搬回来）；L9「Prove Absorption Through Active Use」，说「社区已收录」或「已移植到新
位置」时，要指出最终落点、活的调用点，以及源侧每个行为在那里的对应。类别 A1–A5、B1、C1、C2 和
框架判据 F1–F6 定义在 `references/pr-taxonomy.md`，开工前先读完它。

后文命令用到的变量，开工时一次设好（命令按 bash 写，zsh 下用 `bash -c` 或数组）：

| 变量 | 含义 | 来源 |
|---|---|---|
| `SKILL_DIR` | 本 skill 目录 | 本 SKILL.md 所在目录 |
| `REPO` | 厂内仓库 checkout | 用户给 |
| `FORK_REF` / `NEW_BASE_REF` | 厂内研发分支 tip / 要追的社区版本 | 用户给。用户给的是影子分支（squash 过）时，FORK_REF 取它正文「来源提交」所在的原研发分支（`git branch -r --contains <来源 SHA>`），影子分支只用来读来源清单 |
| `FORK_SHA` / `OLD_BASE_SHA` / `NEW_BASE_SHA` | 冻结的三个提交 | 第 0 步算出 |
| `SHADOW_REF` | 影子分支 tip | 用户给影子分支时才有 |
| `ENV` | 本机或远端执行前缀 | 第 0 步 `pick_env.sh` 输出；`remote <cmd>` 时后续需要 GPU 的命令前面加 `<cmd>` |
| `REMOTE_REF` | pick 源所在远端分支，硬规则 10 用 | 等于 FORK_REF 的远端分支（`origin/<分支名>`）；FORK_REF 本身就是远端分支时直接用它 |
| `DELIVERY_REF` | 交付 ref，emit 契约用 | 等于 `FORK_SHA` |
| `CANDIDATE_BRANCH` | 重放分支名，如 `codex/rebase-<日期>-<模型>` | 自定 |
| `WORKTREE` | 重放用 worktree | 第 2 步创建 |
| `ARTIFACTS` | 产物目录（分类清单、残差、契约、进度） | 自定，`mkdir -p "$ARTIFACTS/patches"` |
| `PREV_MERGE_CONFLICT_LIST` | 上次 merge 的冲突文件列表 | 有就给，没有就不设 |
| `CARD` / `CARD_FIRST` / `CARD_LAST` / `CARD_FILES` | 当前评审组的名字、首末源提交、涉及文件 | 第 3、4 步每个评审组当场设 |
| `SHA` / `SHAS` | 当前要 pick 的源提交 | 第 4 步从 surfaces.tsv 读出 |
| `TARGET_BRANCH` | CR 目标分支 | 用户给，第 8 步用 |
| `DELIVERY_TIP` | 重放后的交付提交 | `git -C "$WORKTREE" rev-parse HEAD`，第 6 步用 |
| `TEMPLATE_BRANCH` | 镜像构建文件模板 | origin 上同类 base 最近的交付分支：`git -C "$REPO" for-each-ref --sort=-committerdate --format='%(refname:short)' refs/remotes/origin \| while read -r b; do git -C "$REPO" cat-file -e "$b:ci.yml" 2>/dev/null && echo "$b"; done \| head`，再按 Dockerfile 的 FROM 是否同类 base 挑；拿不准问用户 |
| `SRC_ARGS` | 验证点 2 的源提交参数 | 第 7 步从分类清单的吸收行拼 |
| `BASE_IMAGE` | 交付镜像基础镜像 | 用户确认（硬规则 13），没有就 deferred |

开工前必须问用户的只有四件：交付模型与特性清单（定 pick 集，第 1 步）、BASE_IMAGE、远端执行
环境（GPU 验证用）、无落点行多到影响交付能力时取舍哪部分（第 4 步）。其余按本 skill 自行判定。

## 硬规则

1. 冻结三个引用再动手：FORK_SHA（厂内 tip）、OLD_BASE_SHA（merge-base(fork, 社区)）、
   NEW_BASE_SHA（要追的社区版本）。分类清单与 pick 全程用冻结值。
   fork 起点若是社区的 dev 线（不在社区 main 上，例如 DSv4.1 影子根 `8bd60a9913` 是社区
   DSv4.1 dev 线 tip），merge-base 会退到更早的 main 提交，OLD_BASE..FORK 里多出社区 dev 线
   提交和「merge main」合并。它们照样进分类清单，类别记「社区 dev 线」：PR 号在
   NEW_BASE 上、或社区已拆成别的 PR 重新合入（rg 到等价实现）→ C1；都不在 → 当厂内改动判。
   合并提交用 `git show --remerge-diff` 看解冲突带进来的残差，残差非空就按普通提交判。
   残差大多是「合并取舍」（删社区侧文件、丢测试，K3 实测 `6db569cd4b` 65 个文件 +329/-3855）时，
   decision 写「不迁:X merge 取舍残差，内容由各源提交分别判」，并抽查残差里有没有厂内新写的
   逻辑行（不是删除、不是社区原文），有就拆出来按普通提交判。
2. 没有分类清单不开始 pick。分类清单由脚本生成的信号加人工定类组成，分类结论落盘进产物目录。
3. pick 集按交付内容判定，看两个维度：**模型**：B 类只在交付就是该模型时迁（给 GLM 追新，K3
   专属不迁；K3 自己追新照迁）；**特性**：绑定特性的 A 类只在交付开启该特性时迁。分类清单里
   类别、模型标签、特性是三个独立字段。
   **默认范围是四类：链路（A1）、监控（A2）、多模态（EPD/encode/视频图像预处理等特性绑定块）和
   CI（C2）。** 框架层优化（A4）每轮都逐笔判受益面，全模型受益的默认迁入（见下）。其余 A3/A5 和
   B 类默认不迁，不为它们向用户确认；用户点名要加某类时才扩大，并把扩大的类别写进分类清单 decision 列。`fork_pr_inventory.py` 的 `cat_hint` 按改动路径的新增行数投票
   （`entrypoints/`、`serving_*`、tokenizer/detokenizer、`disaggregation/` 归链路，`observability/`、
   metrics 归监控，`mem_cache/` 归 Cache，`models/`、`dsv4`、`deepseek_v4*` 等归模型，只改测试/CI
   的归 C2），路径都不命中时才看标题关键词；`scope_hint` 列按默认范围预标（link / monitor /
   multimodal / ci / framework / out），人工复核后落进 decision。
   框架层（CP、MegaMoE、调度、量化 GEMM、通用模型支持）不整类迁：`scope_hint=framework` 的每笔
   都过 references/pr-taxonomy.md 的「框架层提交的吸收判据」F1–F6，F4 先回答「是不是所有模型都
   受益」：全模型受益的默认迁入；部分模型受益的，交付模型在名单里才迁；只有一个模型受益的随该
   模型走。放在通用文件里不等于全模型受益，要看生效条件（`hasattr(model, ...)`、`model_type`
   分岔）主线有几个模型满足。结论（吸收 / 随模型 / 已收录 / 暂缓 / 不迁）连同判据号和 F4 档位写进
   decision 列。
4. 丢弃要有证据。C1 的每一条要么标题带社区 PR 号，要么能在 NEW_BASE 里指到等价实现（rg
   符号或文件）。厂内 pick 时常带私改：diff 厂内版与社区版，私改部分拆出来按 A/B 类处置，
   不能凭标题相似整条丢。
5. 选择按分类，重放按原始拓扑序。原分支按时间演进，原序天然满足卡内与卡间依赖。
6. 按评审组送审（一个评审组一个提交、一个 change，见第 4 步），正文逐条点名卡号，保留原工单号；
   同一变更迭代复用 Change-Id，几张卡合成一笔时在 message 文件末尾写 `Change-Id: <第一张卡那笔的值>`
   （commit-msg hook 见到已有 Change-Id 就不再生成）。每个提交落盘后跑
   该评审组所在子系统的门禁，不攒到最后一次性跑。
7. 部分重放和「缺落点」都要在分类清单 evidence 里写清留下的是什么、为什么、需要时从哪笔
   补迁；缺落点的另一条出路是按 L2/L9 补落点。不允许静默丢弃，`/ready`
   丢失就是这样出的事。
8. worktree 隔离、不直推保护分支、跑不起来记 deferred 不记 pass（L11）。
9. 重放完成的判据是三个验证点，不是「卡都 pick 完了」：**1 所需字段都能取到**
   （`verify_platform_contract.py` 零退出码）；**2 与源 PR 集 line-by-line 一致**
   （`replay_residual.py` 的漏迁与该删没删归零，例外只有上游改了接口，且理由要点名那处变更）；
   **3 起 EPD 服务实测能力与字段**。前两点查不出值错误，这部分只能靠第 3 点。
   第 3 点按部署形态排优先级：先起 PD 分离，资源允许再起集中式（不带
   `--disaggregation-mode`）；集中式没资源起时，必须做集中式路径静态检查，不能直接跳过。
   第 3 点因为没有 GPU、`REBASE_REMOTE` 或 BASE_IMAGE 跑不了时，可以报「静态重放完成」：验证点
   1、2 通过，门禁全绿，第 3 点、镜像构建、CR 列为 deferred，并写明缺哪个输入。静态重放完成
   不等于可以发版，交付报告里要把 deferred 项排在最前面。
   静态重放完成报告（`$ARTIFACTS/static-replay-report.md`）按这个顺序写，缺一节就不算完成：
   (1) deferred 清单：每项写缺哪个输入、找谁要（BASE_IMAGE、REBASE_REMOTE、发版 YAML、平台确认项）；
   (2) 未迁后果：未点名类别里的线上缺陷修复（分类清单 evidence 标「建议补点名」的）、暂缓的平行实现能力；
   (3) 重放提交列表（短 SHA、主题、Change-Id、源 SHA）；
   (4) 分类清单分布（五个词各几行）；(5) 验证点 1：通过项数、`contract-excluded.tsv` 条数和其中
   「原位置消失」项；(6) 验证点 2：残差四类数字、`accept-summary.md` 三类计数、抽检了哪几组、四条
   机检结果；(7) 门禁结果与 waiver；(8) 验证点 1 的三项手工核对（启动参数、label、面板），缺输入的写 deferred。
10. 产物是提交序列，不是一个 diff。每笔都从**远端 ref 上的原提交** pick，pick 前
    `git merge-base --is-ancestor <sha> <remote-ref>` 确认远端确实有它；只有远端不可达
    （提交没推过、分支已删）才改为打补丁，并在正文里写明这一笔是用补丁打的。
11. 环境本机优先：先 `scripts/pick_env.sh <static|unit|gpu>`，输出 `local <venv>` 就在
    本机 uv venv 里跑，输出 `remote <cmd>` 才走远端。远端由用户给的 `REBASE_REMOTE`
    决定（一条能在远端执行 shell 的命令前缀，如 `ssh user@gpu-host`），skill 不假设任何
    私有脚本；未设置而又必须走远端时，停下来向用户要这个值。判据：静态步骤（分类清单、pick、
    ruff、契约核对、residual、CR、取镜像）全在本机，它们只依赖 git 和 stdlib；单测在 venv
    装得上 torch 与 `sglang.srt` 才留本机；EPD 起服务、kernel 测试一律远端。fallback 要在
    分类清单里记一行原因，不静默切换。
12. 重放完成并通过本地门禁后，**自动提交 CR 并取回镜像地址**，不再停下来问用户要不要推
    （refs/for 评审提交可撤销，已由本规则授权）：`scripts/submit_cr.sh` → `scripts/cr_image.py`。
    受保护分支仍然不直推。流程见第 8 步。
13. **base 镜像地址是必填输入，且必须用户手动确认。** 开工时就要拿到 `BASE_IMAGE`（交付
    Dockerfile 的 FROM，形如 `iregistry.baidu-int.com/...:tag`）。用户没给就问；给了或者
    从模板推出了候选，也要把完整地址原样回显、等用户明确回复确认后才继续，不能因为「模板里
    就是这个」就自行确认。确认结果写进分类清单，Dockerfile 的 FROM 必须与之逐字一致，
    `submit_cr.sh` 会校验，未确认或不一致就拒绝推送。确认的是地址，不是兼容性：提交 CR 前还要跑
    `scripts/check_base_image_pins.py`，拿新基线 `python/pyproject.toml` 的 torch / sglang-kernel pin
    对这个镜像的 `pip list`，不过就换 base 再确认（见第 6 步）。
14. **进度落盘，随时可续跑。** 整轮重放常常超过一个会话的上下文（DSv4.1 实测：17 卡后上下文
    写满中断）。`$ARTIFACTS/progress.md` 每卡结束时追加一行：卡号、重放出的短 SHA、对应源
    SHA、门禁结果、未决事项；分类清单 decision 改动当场写回 TSV。接手的人只读 progress.md、
    inventory.tsv 和 `git log $NEW_BASE_SHA..HEAD`，就能从下一卡继续，不重做已提交的卡。
    大输出（diff、import_audit、契约核对）一律写文件，只把结论行读进上下文。
    分类清单也一样：判完一张卡就把它的 decision / evidence 写回 TSV，不要攒在上下文里最后一次性
    落盘。K3 实测 350 行攒到最后，上下文写满时 decision 列一行都没落下，前面的判断全部作废。
    超过 150 行的分类清单按卡切成几批（`decisions-<批号>.tsv`，列为 sha、decision、evidence），
    可以并行判，最后按 sha 合回 inventory.tsv，合完检查每个 sha 恰好一行。
    合并用一条 python（按列名取，不按列号，inventory.tsv 的列序会随脚本版本变）：

    ```bash
    python3 - "$ARTIFACTS" <<'EOF'
    import csv, glob, sys
    a = sys.argv[1]
    rows = list(csv.DictReader(open(f"{a}/inventory.tsv"), delimiter="\t"))
    got = {}
    for f in sorted(glob.glob(f"{a}/decisions-*.tsv")):
        for r in csv.DictReader(open(f), delimiter="\t"):
            k = r["sha"][:10]
            assert k not in got or got[k] == r, f"{k} 在多个批次里结论不同"
            got[k] = r
    for r in rows:
        d = got.get(r["sha"][:10])
        if d: r["decision"], r["evidence"] = d["decision"], d["evidence"]
    empty = [r["sha"][:10] for r in rows if not r["decision"]]
    w = csv.DictWriter(open(f"{a}/inventory.tsv", "w", newline=""), fieldnames=rows[0].keys(), delimiter="\t")
    w.writeheader(); w.writerows(rows)
    print("合并", len(got), "条；仍未判", empty)
    EOF
    ```

    分类清单 evidence 和 `accepted-residual.tsv` 里引用重放结果时写 Change-Id，不写重放 SHA：
    reword、fixup、重做栈都会换 SHA，旧 SHA 当场失效。收尾时用
    `git log --format='%h %(trailers:key=Change-Id,valueonly)' $NEW_BASE_SHA..HEAD` 对一遍。

## 流程

### 0 冻结与分类清单

用户给的是影子分支（每笔 squash 正文里有「来源提交（N 个）：sha, sha, …」）时，先做这一段，
用它选出 FORK_REF；用户直接给研发分支就跳过。影子分支的根是一个「基线快照」提交，和社区历史
不相连（`merge-base` 取不到），所以不用区间，直接按 first-parent 读带来源清单的提交：

```bash
NEW_BASE_SHA=$(git -C "$REPO" rev-parse --verify "$NEW_BASE_REF^{commit}")
git -C "$REPO" log --first-parent --format=%B --grep='来源提交' "$SHADOW_REF" | python3 -c '
import re, sys
t = sys.stdin.read(); out = set()
for m in re.finditer(r"来源提交（(\d+) 个）：([0-9a-f, \n]+)", t):
    got = re.findall(r"[0-9a-f]{10}", m.group(2)); out.update(got)
    if len(got) != int(m.group(1)): print("数量对不上:", m.group(0)[:60], file=sys.stderr)
print("\n".join(sorted(out)))' > "$ARTIFACTS/shadow-sources.txt"
first=$(head -1 "$ARTIFACTS/shadow-sources.txt")
for b in $(git -C "$REPO" branch -r --contains "$first" | grep -v -e ' -> ' -e '/HEAD$'); do
  n=0; while read -r s; do git -C "$REPO" merge-base --is-ancestor "$s" "$b" || n=$((n+1)); done \
    < "$ARTIFACTS/shadow-sources.txt"
  [ "$n" = 0 ] && echo "$b 共 $(git -C "$REPO" rev-list --count --no-merges "$(git -C "$REPO" merge-base "$b" "$NEW_BASE_SHA")..$b") 笔"
done   # 只列包含全部来源的分支，一条都没有就停下问用户
```

然后冻结三个引用、生成分类清单：

```bash
ENV=$(bash "$SKILL_DIR/scripts/pick_env.sh" static)   # 硬规则 11：输出 local <venv> 或 remote <cmd>
[ "${ENV%% *}" = local ] && . "${ENV#local }/bin/activate"   # 本机时激活 venv
command -v rg >/dev/null && command -v ruff >/dev/null || { echo "缺 rg 或 ruff，后文「零输出即通过」的检查会跑空，先装上" >&2; exit 1; }
FORK_SHA=$(git -C "$REPO" rev-parse --verify "$FORK_REF^{commit}")
NEW_BASE_SHA=$(git -C "$REPO" rev-parse --verify "$NEW_BASE_REF^{commit}")
OLD_BASE_SHA=$(git -C "$REPO" merge-base "$FORK_SHA" "$NEW_BASE_SHA")

python3 "$SKILL_DIR/scripts/fork_pr_inventory.py" \
  --repo "$REPO" --fork "$FORK_SHA" --old-base "$OLD_BASE_SHA" \
  ${PREV_MERGE_CONFLICT_LIST:+--conflict-paths "$PREV_MERGE_CONFLICT_LIST"} \
  --card-pattern 'luno-[0-9]+|aihc-qa-[0-9]+' \
  --icafe-template 'http://newicafe.baidu.com/v5/issue/{card}/show' \
  --icode-template 'http://console.cloud.baidu-int.com/devops/icode/repos/baidu/hac-aiacc/aiak_sglang/commits/{sha}' \
  --output-dir "$ARTIFACTS"
```

影子场景下分类清单只留来源提交（按 10 位前缀匹配），删完行数应等于来源提交数：

```bash
python3 - "$ARTIFACTS" <<'PY'
import csv, sys
a = sys.argv[1]
keep = set(open(f"{a}/shadow-sources.txt").read().split())
rows = list(csv.DictReader(open(f"{a}/inventory.tsv"), delimiter="\t"))
kept = [r for r in rows if r["sha"][:10] in keep]
w = csv.DictWriter(open(f"{a}/inventory.tsv", "w", newline=""), fieldnames=rows[0].keys(), delimiter="\t")
w.writeheader(); w.writerows(kept)
print("分类清单", len(kept), "行；来源", len(keep), "个；缺", sorted(keep - {r["sha"][:10] for r in kept}))
PY
```

「缺」非空时逐个查：`git merge-base --is-ancestor <sha> "$NEW_BASE_SHA"` 成立的是社区已有，补一行分类清单
记「已收录:来源提交已在新基线」；不成立又不在 OLD_BASE..FORK 上的（FORK_REF 选错或 OLD_BASE 太靠后），
换一条候选分支重跑，还缺就停下问用户。

列出的分支都包含全部来源，分类清单又只留来源提交，所以选哪条对分类清单内容没有影响，只影响 OLD_BASE 和
远端校验用哪条分支。选法：去掉 `rb-*` 这类发版分支，剩下的研发分支里选和影子分支名同一条线的
（GLM 影子对 `ds-dev-glm-*`）；还剩多条就选 tip 最新的，在 progress.md 记下选了哪条、为什么。
笔数只用来看分支有多长，不作为选择依据。GLM 实测：153 个来源提交，包含全部来源的有 8 条分支
（研发分支 `ds-dev-glm-1013`、`ds-dev-glm-req-cache`、`ds-dev-glm-trace-1009` 和 5 条 `rb-*`），
取 `ds-dev-glm-1013`，过滤后分类清单正好 153 行。

产出 inventory.tsv（逐提交：规模、fork 独有文件数、冲突史交叠、类别 HINT、链接）和
cards_summary.md（卡片聚合）。HINT 只是关键词启发，**每张卡人工定类，混合卡逐提交定类**，
把最终 cat 列改回 TSV。--conflict-paths 给上一次整支 merge 的冲突文件清单，没有就省略。

### 1 用户确认 pick 集

默认 pick 集 = 监控 + 多模态（硬规则 3），不需要再问。只有两件事仍要对着分类清单确认，且
能从上下文推出就不问：交付模型是什么（多模态块里 B 类的模型专属部分去留）；多模态块
在社区是否有同类实现（有则先 diff 社区版再定搬什么）。
decision 列冒号前只能是五个词之一：吸收、随模型、已收录、暂缓、不迁（含义见 pr-taxonomy）。
部分吸收写「吸收:部分 …」，fixup 写「吸收:fixup 折叠进 <X>」，后文按冒号前的词取源集合，
写成别的形式会被漏掉。AttentionStore、DSpark、VL
kernel、通用 BUGFIX 等其余特性整块跳过，发版 YAML 同步去开关；用户明确要求时再加。C2
里的镜像构建文件属于交付流水线，不算「迁移 PR」，始终作为最底下一笔进入（第 6 步），因为自动取镜像
依赖它。确认结果写进分类清单的 decision 列。
镜像卡要把散在其他提交里的 Dockerfile、ci.yml、build.sh 改动并进来（DSv4.1 实测：镜像构建文件卡
并入了 583c5aac5b、9ef9d7caf5 的 Dockerfile hunk，Dockerfile 取 FORK tip 的文件内容）。被拆走
镜像 hunk 的提交在分类清单 evidence 写「镜像 hunk 并入 C2 卡」，它自己那卡只重放其余部分。
这种按 hunk 拆分会让同一个源 SHA 出现在两笔重放里，不算重复重放。

框架层改动从 shadow 分支吸收时，按 squash 正文里的「来源提交」回到原 SHA 逐笔判，先把
[性能优化] 里混进来的监控、AttentionStore 归回 A2/A3，剩下的走 F1–F6。判完的「吸收」项
和监控、多模态一起按原拓扑序重放；「暂缓」项在分类清单写清开关名和补迁条件。

A1 链路适配 + A2 监控适配 + A5 通用 BUGFIX 这部分在 DSv4.1 那轮已经落成一个 diff 加一份逐卡
分类清单，见 references/internal-platform-stack.md（diff 本身是 `assets/internal-platform-stack-dsv41.diff`，
只当对照物逐块看，不要整份 `git apply`：它基于 DSv4.1 那次的基线）：追新基线时拿它当重放起点和平台契约对照物，
这三类不必再从 fork 历史重新翻一遍。
只取本轮 pick 集里有的类：A5 默认不迁，用户没点名时这份 diff 里的 A5 部分不重放，它带进契约的条目
在验证点 1 挪进 `contract-excluded.tsv`，decision 写「不迁:未点名类别」。

### 2 换基线

```bash
git -C "$REPO" worktree add -b "$CANDIDATE_BRANCH" "$WORKTREE" "$NEW_BASE_SHA"
cd "$WORKTREE"          # 第 3、4 步的 git 命令默认都在这个 worktree 里跑
mkdir -p "$ARTIFACTS/patches"
```

第一步到此完成。不要在这一步夹带任何厂内改动。

### 3 清理 pick 清单

pick 清单生成前先做三件事：去掉成对的 revert（A 提交和后续 Revert "A" 同时出现，两笔都移出
清单，判据是两笔合起来净差为零：`git diff A^ R --stat -- <A 改过的文件>` 为空，限定到 A 自己
的文件；不限定会把两笔之间的其他提交也算进来（K3 实测 `bb2c201429`..`d005838a9a` 不限定是 83
个文件，限定到那 3 个文件为空）。标题写「撤回」但净差不空的，
剩下的部分按普通提交判，DSv4.1 的 `e8af4d22bd` + `1a42fc75a1` 净差还有 7 个文件 +138/-2）；
历史搬运提交跳过（标题形如 "Pick aiak code"、"merge X into Y" 的大杂烩，其内容已被
后续演进覆盖，pick 它等于回滚后面的修复）；同卡 fixup 折叠：一张 39 提交的卡有一半是对前
一半的补丁（补 import、编码规范、改签名），这些 fixup 在第 4 步随所属评审组一起连续 pick、折叠成一个提交。
要先看整卡净改动时可以算一份卡级补丁：

```bash
git diff "$CARD_FIRST^..$CARD_LAST" -- $CARD_FILES > "$ARTIFACTS/patches/$CARD.patch"
```

这份卡级补丁只用来评审前看净改动，以及第 4 步连续 pick失败时备用；正常重放走第 4 步的 `cherry-pick -n`。

混合卡例外：先按逐提交分类拆开，再各自归类折叠。

分类清单里写「折叠进 X」的 fixup 不能凭评语放过：逐笔看 `git show <fixup> --stat` 和净 diff，
改了判断逻辑、返回值、分支条件的，单独作为源提交进验证点 2 的源集合，评语改成写清它改了
什么。GLM 实测：`4f8e6369da` 分类清单里的评语是「serving_chat 日志修复」，实际给
`_check_for_unstreamed_tool_args` 加了三处守卫，重放时漏了，被 accept 盖住直到按组重审才露出。

### 4 逐卡重放

按原始拓扑序重放：inventory.tsv 的行序已经是 `--reverse --topo-order`，按行序取吸收行即可。
重放前把吸收行分到评审组，写一份 `$ARTIFACTS/surfaces.tsv`：每行一个评审组，三列用 TAB 分隔，
`评审组名<TAB>源 SHA 逗号分隔、按分类清单行序<TAB>Change-Id 取自哪笔源 SHA`，无表头。镜像卡不写进
surfaces.tsv：它不是从源提交逐笔 pick 出来的，按第 6 步单独建、作为第一笔提交，之后再跑下面的循环。**一个评审组一个提交**：
同一评审组的多张卡、每张卡的多笔、连同评审 fixup，用 `cherry-pick -n` 连着落进工作区再一次
commit，折叠动作就此完成，不必先算卡级补丁。怎么分组按「评审时要一起看的东西」定，不按卡数定：
DSv4.1 这轮六张监控卡合成两笔，一笔看指标发得对不对，一笔看日志与探针接不接得上平台，卡号在正文里
逐条点名，仍能追溯。卡多到评审组不清楚时再拆。

每个评审组这样做（message 文件 `msg-$CARD.txt` 先按下文格式写好）：

```bash
while IFS=$'\t' read -r CARD shas cid_from; do
  IFS=, read -r -a SHAS <<< "$shas"
  for SHA in "${SHAS[@]}"; do
    git merge-base --is-ancestor "$SHA" "$REMOTE_REF" || { echo "$SHA 不在 $REMOTE_REF，见硬规则 10"; break 2; }
  done
  git -c rerere.enabled=false cherry-pick -n "${SHAS[@]}" || break   # 冲突就停在这里，解完再续
  cid=$(git log -1 --format='%(trailers:key=Change-Id,valueonly)' "$cid_from" | head -1)
  [ -n "$cid" ] && ! grep -q '^Change-Id:' "$ARTIFACTS/msg-$CARD.txt" \
    && printf '\nChange-Id: %s\n' "$cid" >> "$ARTIFACTS/msg-$CARD.txt"   # 取不到就留给 hook 生成
  git commit -F "$ARTIFACTS/msg-$CARD.txt"
  # 门禁、progress.md 一行，再进下一个评审组
done < "$ARTIFACTS/surfaces.tsv"
```

实际执行时一次只跑一个评审组（把 `surfaces.tsv` 的那一行喂进去），冲突、混合提交、门禁都在
两个评审组之间处理。

混合提交（一笔里既有范围内改动又有不迁部分，K3 实测有 73 个文件的）不要整笔 cherry-pick，
冲突会多到无法逐处判。只取范围内的文件，一笔一笔地 apply，不要把多笔的整文件 diff 合起来
apply：两边文件分叉后，`--3way` 会把不相干的 hunk 也带进来：

```bash
IN_SCOPE=(python/sglang/srt/observability/metrics_collector.py)   # 例：这一笔里属于本轮范围的文件，逐笔列
git show "$SHA" -- "${IN_SCOPE[@]}" > "$ARTIFACTS/patches/$SHA.patch"
git apply --3way "$ARTIFACTS/patches/$SHA.patch"          # 冲突逐处按 L 规则解
# 同一文件里还混着不迁 hunk 时：git apply 后用 git add -p 只暂存范围内的 hunk，其余 git checkout -- <文件>
```

fork 独有的平行实现（社区有同类子系统，例如厂内 EPD 的 `encode_server_aiak.py` 对社区
`disaggregation/encoder/`）**禁止把 fork tip 的栈文件整体搬进来**，「先搬进来、默认不接入」也不行：
没人调用的 1 万行代码就是死代码，评审看不了，验证点 2 也会把它全报成新造。正确做法是逐个
行为找社区对应的函数，只把缺的差异写进社区文件，每个行为一笔或按评审组合并，正文写清
「fork 行为 X → 社区 `<文件>:<函数>`」。K3 实测：一张卡整栈搬了 25 个文件、+12265 行且没接入调用链，
整卡作废重做。

逐行为找落点时，每个行为落进三种结论之一，写进分类清单：

| 情形 | 判据 | 结论 |
|---|---|---|
| 社区已覆盖 | 社区对应函数逐行 diff 后行为一致 | `已收录:部分 <社区文件:函数>` |
| 社区缺这段 | 有对应函数，缺这段行为 | 写进社区文件，`吸收:部分 <社区文件:函数>` |
| 无落点 | 行为挂在 fork 独有的协议或文件上（K3：router 的 `task_results`、`embedding_transfer`、视频解码栈），社区没有对应位置 | 先写 `暂缓:平行实现内部 <所在文件>，待用户决定`；用户明确放弃这块能力才改「不迁」 |

「无落点」不能只凭「所在文件在 NEW_BASE 不存在」判：先在社区同功能模块里找对应函数（K3 的背压
对 `encoder/runtime.py:EncoderScheduler`、嵌入泄漏对 `encoder/receiver.py` 的释放路径），
找到了就逐行 diff，归前两种。线上缺陷修复和监控项即使原位置消失，也要尽量在社区落点上重写。
无落点行占这一块吸收行一半以上，或者丢掉的是交付会用到的能力时（K3：53 行里 50 行无落点，
丢掉视频抽帧、解码隔离、`pp_size>1`），停下来问用户：是引入 fork 的平行实现（要单独一张设计卡，
接到社区入口），还是只用社区框架、缺这些能力，或只补其中一部分。不要自己替用户选。
用户选择「本轮只补一部分、平行实现以后再说」时，留下的行写「暂缓:用户决定本轮只补 X，平行实现
能力（<哪一块>）以后单独设计卡」，不要写成不迁：暂缓会留在下一轮的补迁清单里，不迁不会。
K3 实测：用户选「只补线上缺陷和监控项」，53 行 EPD 落成吸收 3、已收录:部分 7、暂缓 43；
逐行 diff 后背压和编码指标社区已覆盖，只有嵌入泄漏缺 `disaggregation/utils.py:prepare_abort`
里的一次释放调用。

pick 顺序错了就 `cherry-pick --abort` 重来：把后一笔排在前面，冲突里会出现「base 有而 HEAD
没有」的第三方内容，看着像社区改的，其实是自己乱序制造的。连续 pick中途出冲突就必须当场解完
再继续，后面几笔会静静地落进未解冲突的工作区，一路「干净」到最后 commit 才报 unmerged，
那时几笔已经混在一起，只能 `cherry-pick --quit` + `reset --hard` 退回上一个提交重来。

一个评审组只含一笔源提交、且原样搬（不改 message）时：`git commit -C <原 SHA>`，作者和 Change-Id
一起保留，同一评审继续迭代。合并了多笔或改了 message 的，message 写进 `$ARTIFACTS/msg-$CARD.txt`，
末尾 Change-Id 用 surfaces.tsv 里指定那笔源提交的值
（`git log -1 --format='%(trailers:key=Change-Id,valueonly)' <那笔>`），那笔没有 Change-Id 就留给 hook 生成。
hook 要在位。worktree 共用主仓库的 hooks，先确认
`test -x "$(git rev-parse --git-common-dir)/hooks/commit-msg"`；没有就从评审系统装（Gerrit/icode：
`scp -p -P 8235 <用户>@<评审主机>:hooks/commit-msg "$(git rev-parse --git-common-dir)/hooks/"`，主机问用户），
格式跟厂内 EPD 那组一致，一眼能看出进度和边界：

```
<卡号> [<模块>][PR i/N] <中文主题>: <要点> + <要点>

<为什么需要它：平台侧或用户侧看到的现象>

<分组标题>:
- <文件>: <这个文件里做了什么>

重放自 <来源短 SHA 列表>（<远端 ref>），<冲突与解法>，<与源提交的行为差>。
```

末段三件事必须写：来源 SHA 与远端 ref（可追溯）、冲突位置与判据（可复核）、与源提交的行为
差（可讨论）。冲突逐处按 references/resolution-laws.md 的 L 规则判定；社区侧结构变了的按 L2/L9 把厂内行为接到
新结构上，不要凭形似判「已吸收」。解完冲突先扫一遍未定义名字，语法检查通过时名字也可能不存在：

```bash
FILES=$(git diff --name-only --diff-filter=AM "$NEW_BASE_SHA"..HEAD -- '*.py')
[ -z "$FILES" ] || ruff check --isolated --select=F821 $FILES   # zsh 下用 bash -c
```

社区改过 API 名（`get_pp_group()` → `get_parallel().pp_group`）而厂内那笔把旧名搬了过来，
就只在这一步露出来。每卡完成后立即跑：

```bash
python3 "$SKILL_DIR/scripts/import_audit.py" --repo "$WORKTREE" \
  --parent "$NEW_BASE_SHA" --critical-path <该卡子系统 glob> \
  --output "$ARTIFACTS/import-audit-$CARD.md"
```

import_audit 全仓一次约 90 秒，前台跑、给足超时（≥ 300 秒）；放后台再读常拿到空文件。

每卡还要跑一次集中式路径静态检查，组件类里新写 `self.server_args` / `self.enable_metrics`
在集中式部署里会让调度器退出（GLM 实测：luno-4170 在 `scheduler_components/batch_result_processor.py`
新写了 `self.server_args.enable_metrics`，改成 `get_observability().enable_metrics`）：

```bash
git diff "$NEW_BASE_SHA"..HEAD -- python/sglang/srt/managers python/sglang/srt/disaggregation \
  | rg '^\+.*self\.(server_args|enable_metrics)\b'   # 每条命中都要确认 self 是 Scheduler
```

加该卡子系统的仓库自带测试。红了当场修，修完重跑，不带着失败进下一卡。测试命令按子系统挑
`test/registered/unit/` 下对应目录，写成带 `{tree}` 占位的形式，第 5 步的 `TEST_COMMAND` 直接复用：
`TEST_COMMAND='cd {tree} && python -m pytest -q -x test/registered/unit/managers'`（目录按本轮改到的子系统换）。
本机装不上 torch / `sglang.srt` 跑不了单测时（硬规则 11），单测和 `TEST_COMMAND` 都记 deferred。

门禁只看本轮重放新引入的问题。import_audit 标 INHERITED 的条目（NEW_BASE 本来就有的
missing-module、shadowed-import）本身不算本轮重放的缺陷；但脚本对落在 `--critical-path` 上的
INHERITED 也会非零退出，因为交付马上要第一次执行那条路径。所以 `--critical-path` 只给本卡
交付会执行的文件 glob，退出码 1 时逐条看：NEW 的修；落在关键路径上的 INHERITED 确认交付配置
会不会走到，会走到就修，不会就在 import-audit 报告里写明理由。F811 同理：同一批文件在 NEW_BASE 上也跑一遍，两份结果求差，只修多出来的。
求差前去掉行号，只按「文件 + 名字 + 消息」比，否则重放插入的行会让基线上原有的告警行号
漂移，全部算成新增：

```bash
FILES=$(git diff --name-only --diff-filter=AM "$NEW_BASE_SHA"..HEAD -- '*.py')   # 空时跳过，免得 ruff 去扫当前目录
[ -n "$FILES" ] || echo "本卡没有 .py 改动，跳过 F811"
ruff check --isolated --select=F811 --output-format=concise $FILES \
  | sed -E 's/:[0-9]+:[0-9]+:/:/; s/from line [0-9]+/from line N/' | sort -u > "$ARTIFACTS/f811-head.txt"
# 基线侧不用另建 worktree：逐文件取 NEW_BASE 的内容喂 stdin，NEW_BASE 不存在的文件跳过
for f in $FILES; do
  git show "$NEW_BASE_SHA:$f" 2>/dev/null \
    | ruff check --isolated --select=F811 --output-format=concise --stdin-filename "$f" -
done | sed -E 's/:[0-9]+:[0-9]+:/:/; s/from line [0-9]+/from line N/' | sort -u > "$ARTIFACTS/f811-base.txt"
comm -23 "$ARTIFACTS/f811-head.txt" "$ARTIFACTS/f811-base.txt"   # 只修这里列出的
```

本 skill 的命令都按 bash 写。zsh 下不加引号的 `$FILES` 不会按空白拆开，ruff 只收到一个参数，
静默跑空。用 `bash -c` 执行，或者先 `FILES=( $(git diff --name-only ...) )` 拼成数组。

每张卡都要留一份 `import-audit-$CARD.md`，漏了的卡在收尾时用全栈 import_audit 补一份并在
progress.md 注明。

源提交依赖的结构在新基线变了，按下表判，判完在提交末段写明是哪种情形、对应哪个社区提交：

| 情形 | 怎么查 | 处置 |
|---|---|---|
| 文件被删 | `git log --diff-filter=D --format='%h %s' "$OLD_BASE_SHA..$NEW_BASE_SHA" -- <文件>` 找删除提交，看它把职能搬到哪 | 有继任文件：把差异接到继任文件上（L2/L9）。职能被社区取消：不迁，evidence 写删除提交。不要把删掉的文件原样加回来；只有没有继任、交付又需要时才补落点，并在分类清单写「补落点」 |
| 类或函数搬家、改名 | `rg -n 'class X\b\|def x\b'` 查新位置；查不到用 `git log -S x --oneline "$OLD_BASE_SHA..$NEW_BASE_SHA"` | import 改到新位置，调用改用新名字（例：`MultimodalInputs` 搬到 `req_types`，`decode_image` 换成 `to_rgb` / `patchify_image`）。新函数语义不同就按 L2 重接 |
| 核心接口被重写 | 父类方法消失、字段被删（例：`cache_finished_req` 改为 `insert_req` + `release_kv_cache`，`cache_unfinished_req` 改为 `checkpoint_req`，`Req.prefix_indices` 被删） | 见下文 |
| 协议输出字段变了 | 拿源分支和 HEAD 跑同一条请求，比较流式 chunk 的字段集合；没法跑时 diff 构造 chunk 的代码 | 契约脚本看不到响应字段。平台读的字段缺了，按 A1 补回 |

核心接口被重写时，**特性在不在交付范围决定能不能暂缓**。用户点名了这个特性，或者交付发版
YAML 打开了它的开关且用户没有明确排除它，就必须移植：按 L9 在新
接口上重新实现提交时机，所有读旧字段的地方改成从新结构推导；没有运行环境就做静态移植，
运行验证记 deferred，不能因为工作量大判暂缓。暂缓只适用于两种情况：特性不在范围内，或者
用户看过移植方案后明确同意。暂缓时同步把开关从发版 YAML 里删掉，分类清单写清能力缺失和补迁
条件，否则新镜像会在参数校验阶段报错退出。
用户明确排除的特性优先于 YAML：发版 YAML 带着它的开关，也是删开关、不移植。例：
AttentionStore（asradix）用户明确不合入，prefill YAML 里的 `--enable-asradix-cache` 列为必删项。

### 5 全量门禁与交付验证

全部卡重放完，按 references/gates-workflow.md 跑 run_gates.sh 九个门禁（它要 `REPO=$WORKTREE`、
`TARGET_SHA=$NEW_BASE_SHA`、`SOURCE_SHA=$FORK_SHA`、`ARTIFACTS=$ARTIFACTS/gates`，再加 `MODE=pick`；
脚本注释里 target 指「被集成进去的一侧」，本 skill 里那一侧是社区新基线，所以和字面「fork parent」相反。
可选的 `CRITICAL_PATHS`（交付会执行的文件 glob）、`DEPLOY_YAMLS`（发版 YAML）、`PROVENANCE_SOURCES`
（`$REMOTE_REF`）有就给；九个门禁是 intent-overlap、import-audit、flag-inventory、duplicate-definitions、
interface-delta/absent-symbol-triage、orphan-scan、provenance-audit、parent-test-delta、review-preflight，
FAIL 必须修或写进对应 waiver 文件，deferred 不算通过）。调用：

```bash
export CRITICAL_PATHS DEPLOY_YAMLS TEST_COMMAND   # 没有就留空，脚本按未设处理
REPO="$WORKTREE" TARGET_SHA="$NEW_BASE_SHA" SOURCE_SHA="$FORK_SHA" ARTIFACTS="$ARTIFACTS/gates" MODE=pick \
  PROVENANCE_SOURCES="$REMOTE_REF" CARD_PATTERN='luno-[0-9]+|aihc-qa-[0-9]+' \
  FLAG_WAIVERS="$ARTIFACTS/gates/flag-waivers.tsv" SYMBOL_WAIVERS="$ARTIFACTS/gates/symbol-waivers.tsv" \
  INTENT_WAIVERS="$ARTIFACTS/gates/intent-waivers.tsv" PROVENANCE_WAIVERS="$ARTIFACTS/gates/provenance-waivers.tsv" \
  bash "$SKILL_DIR/scripts/run_gates.sh"
```

四个 waiver 文件格式各不相同：flag 是 `开关名<TAB>理由`，symbol 是 `符号名<TAB>理由`，intent 是
`fork 短 SHA<TAB>理由`，provenance 是 `路径<TAB>理由`。跑之前 `mkdir -p "$ARTIFACTS/gates"` 并
`touch` 这四个文件；`CRITICAL_PATHS`（交付会执行的文件 glob，空格分隔）、`DEPLOY_YAMLS`（发版 YAML）
没有就不设。`TEST_COMMAND` 取第 4 步每卡跑的仓库单测命令（含 `{tree}` 占位）；它和发版 YAML 缺的时候，
parent-test-delta、flag-inventory 会记 deferred，写进报告的 deferred 清单。门禁之外还要过交付特性组合清单和跨组件契约三观测点（references/gates-workflow.md）。
两个专项检查：B 类跳过后的悬挂引用（A 类代码里 import 模型专属模块的行要跟着裁，
import_audit 的 NEW 段会报）；C1 丢弃后的行为差（厂内 pick 版与社区收录版不一致的私改，
确认已按硬规则 4 拆出）。

### 6 交付镜像构建文件

先拿到用户手动确认过的 `BASE_IMAGE`（硬规则 13），Dockerfile 的 FROM 写它，不写别的。
还没确认时镜像卡照样放在最底下一笔（ci.yml、build.sh、gpu_requirements.env 照本节改），FROM 保留 FORK tip
上的原值，正文末段写「FROM 待确认：BASE_IMAGE 未给，保留 fork 原值 <值>」，报告的 deferred 清单
列这一项；确认后只改这一行，作为镜像卡的新 patchset。不要自己挑一个镜像地址填进去。

镜像卡的建法：在 worktree（NEW_BASE 上，还没有任何重放提交）里从 FORK tip 取四个文件，按本节的
三分法和模板改，单独提交，作为第一笔：

```bash
git checkout "$FORK_SHA" -- ci.yml build/build.sh dockerfile/Dockerfile dockerfile/gpu_requirements.env
# 按下面的三分法改 Dockerfile；ci.yml、build.sh 与 TEMPLATE_BRANCH 对齐；FROM 写 BASE_IMAGE 或按上段保留
git add ci.yml build/build.sh dockerfile && git commit -F "$ARTIFACTS/msg-image.txt"
```

分类清单里 C2 镜像提交的 decision 写「吸收:镜像卡」，evidence 写进了哪几个文件。验证点 2 只比 `python/`
和 `test/`，这些提交放进 `SRC_ARGS` 也不会报残差；它们夹带的 `python/` 改动按所属类别另行判。

C2 里的镜像改动按厂内已有格式改：`ci.yml`、`build/build.sh`、`dockerfile/Dockerfile`、
`dockerfile/gpu_requirements.env`，模板取 origin 上**同类 base**（社区镜像 / 厂内
aiak-inference 镜像）的最近交付分支。自创 `Dockerfile.<x>` / `build_<x>.sh` 这类名字流水线
不看，DSv4.1 那次整卡被打回重做。

这一卡放在**最底下一笔**：第 4 步重放的第一笔就做它（内容按本节改）；事后才补的话用
`git rebase -i "$NEW_BASE_SHA"` 把它挪到第一行，挪完上面每笔都换 SHA，分类清单和 progress 里只认 Change-Id。
验证点 2 默认只比 `python/` 和 `test/`，镜像四个文件不进残差，靠 `check_image_layout.sh` 验。
社区树里没有 ci.yml，换基线后它必缺，而每个 change 的 CI 各自 checkout
自己那条 ref，排在它之后的卡才继承得到；漏了的表现是流水线一开工就停在
`can not get ci.yml from iCode`。

换 base 时把模板里继承来的每一步过一遍三分法：

| 类 | 判据 | 处置 |
|---|---|---|
| base 专属 | 这步操作的包或文件只存在于旧 base | 删，并在 Dockerfile 头注释写清替代做法 |
| 运行时通用 | 厂内环境要求，与模型无关 | 原样保留 |
| 版本锚 | 值绑在某个 base 上：版本号、dist-packages 路径、cuda12/13 wheel 变体 | 构建时从 base 现取，或按新 base 重挑 |

两种错误的后果不一样：base 专属项留着，构建当场失败（patch 找不到目标文件）；运行时通用项删掉，要等
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
required version 0.4.9` 退出，整轮 CR 镜像都要重建，最后改用与基线同代的社区 nightly（cu13）。所以确认完地址、
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

分类清单是从 fork 提交出发的正向流程，只能保证「我们挑中的都搬了」，保证不了「平台依赖的都还
在」，因为探针、指标、采集开关是由平台侧决定要用的。重放完成后必须从平台契约回查代码和发版 YAML，
一次脚本核对加三项手工核对都要过。

**验证点 1：所需的字段都能够被 get 到。**

顺序固定三步：先用下面的 `--emit` 从交付 ref 生成 `contract-next.json`；再按分类清单把不迁、暂缓、
原位置消失的条目挪进 `contract-excluded.tsv`，剩下的存成 `contract-scoped.json`；最后拿它核对重放
tip。`assets/contract-dsv41.json` 只是 DSv4.1 那次的样例，不能直接拿来核对别的分支。

```bash
python3 "$SKILL_DIR/scripts/verify_platform_contract.py" \
  --repo "$WORKTREE" --ref HEAD \
  --contract "$ARTIFACTS/contract-scoped.json" \
  -o "$ARTIFACTS/contract-verify.md"
```

脚本遍历 `python/sglang/srt` 的 AST，提取当前分支的能力集与契约比对：路由（主 server 与
dummy server 分开）、指标族（有 `name="sglang:..."` 定义**且**有真实写入点，只 `inc(0)`
预热的单独归一类）、rid stage trace 行（`trace(logger, "…")`）、token id dump 点
（`log_input_ids(logger, rid, "<stage>", ids)`）、日志 schema（`configure_logger` 的 prefix
与 `%(levelname)s` 打头）、厂内环境变量读取点（`os.getenv` / `os.environ` / `envs.`，以及
`_env_bool("CD_X", …)` 这类自家包装）。

完成判据：退出码 0。退出码 1 时 stderr 逐条报缺什么、原来所在的文件是哪个；指标族定义还在
但没人写它，报「无写入点」而不是 MISSING：面板一样是 No data，但修法不同。DSv4.1 实测：契约
76 项，交付 tip 76/76 过；拿只重放到 `43b2ba6d8b` 的中途状态核对，报缺 49 项（26 个指标族、
14 条 trace 行、5 个预热计数器、2 个 token id dump 点、2 个环境变量），路由与日志 schema 那
时已经在位。

契约不手维护，换基线后重新求差生成：

```bash
python3 "$SKILL_DIR/scripts/verify_platform_contract.py" \
  --repo "$REPO" --ref "$DELIVERY_REF" --against "$OLD_BASE_SHA" --emit \
  --env-name MASTER_IP --env-name SGLANG_LOG_REQUEST_TRACE --env-name SGLANG_LOG_TOKEN_IDS \
  --env-name SGLANG_TOOL_SCHEMA_ID_NORMALIZATION --env-name SGLANG_TOOL_SCHEMA_REF_EXPANSION \
  --env-name SGLANG_TOOL_CALL_EMPTY_RETURN_INTERVAL -o "$ARTIFACTS/contract-next.json"
```

`--against` 给 OLD_BASE：`--emit` 只收「交付 ref 有、它自己的社区基线没有」的能力，也就是
厂内加的那部分。给 NEW_BASE 会出两类错：社区在新基线删掉或改名的东西（DSv4.1 实测 12 条，
grammar 指标、`/get_load`、`/weight_version`）被当成厂内能力进契约；社区新基线也有的厂内
能力（`/ready`）被漏掉。社区后来自己收了的条目，在 HEAD 上自然在位，核对照样通过。
默认前缀只收 `AIAK_` / `CD_`，平台依赖的 `SGLANG_*` 开关要用 `--env-name` 逐个点名，
不要整个加 `SGLANG_` 前缀，否则没迁的性能开关也会进契约。交付 ref 上定义了却没有写入点的族不进契约，
emit 时单独打一份清单，这是本分支自己的问题，先修。
emit 出来的契约是「交付 ref 的全部厂内能力」，没按本轮范围过滤。拿它核对之前，把引入提交
在分类清单里判为「不迁」或「暂缓」的条目挪出来，另存 `contract-excluded.tsv`（条目、引入 SHA、
decision），剩下的才是本轮验证点 1 的契约。挪出的条目要能逐条对上分类清单，对不上就是漏判。
GLM 实测：44 项里 3 项随 AttentionStore、TraceManager、低接受率 abort 一起挪出，剩 41 项。
还有一种条目要挪出，但不能静默挪：所在类在 NEW_BASE 已不存在、社区换了实现（K3 实测：日志前缀
`TokenizerWorker` 绑在 fork 的类上，NEW_BASE 的 worker 入口前缀是 ` Tokenizer {pid}`）。这类
写进 `contract-excluded.tsv` 时 decision 列写「原位置消失:<社区替代>」，并列为发版前必须找平台
确认的事项：平台按字面解析这个前缀的话，要在社区实现上补回原前缀，不能当排除项放过。
分类清单改判以后契约要跟着重挪：平行实现或特性块被改成暂缓，它带进契约的路由、指标、预热项也要挪进
`contract-excluded.tsv`，引入 SHA 写这组实现的引入提交。按 `where` 字段在重放 tip 上是否存在先筛出
候选，再逐条对分类清单，不要按文件不存在就一律挪。K3 实测：EPD 整栈卡作废、53 行改判后，契约里
34 项所在文件是 `encode_server_aiak.py`、`encode_collector.py`（引入提交 `2c7ed60ff9`、`bcf4419850`，
均已暂缓），挪出后 49/49 通过。

过滤这一步按下面的办法做（契约 JSON 是 `{"capabilities": [{"kind", "key", "where"}, ...]}`）：
先列出 `where` 在重放 tip 不存在的条目作候选，再对每个条目用 `git log --format=%h "$OLD_BASE_SHA..$FORK_SHA" -S '<key>'`
找引入提交，查分类清单 decision；前缀是不迁或暂缓的写进 `contract-excluded.tsv`（列：条目、引入 SHA、
decision），其余留在 `contract-scoped.json`。`where` 在 tip 存在但分类清单判不迁的条目也要挪，同样逐条对。
核对退出码 1 时：缺的条目引入提交判了吸收，是真漏迁，补代码；判了不迁或暂缓，是漏挪，挪进
`contract-excluded.tsv`；分类清单里找不到引入提交，是分类清单漏了这一行，回第 0 步补判。

过滤命令（按每条的 `key` 在 OLD_BASE..FORK 上、限定所在文件找所有碰过它在分类清单里的提交：有一笔判吸收就留在契约里，
全是不迁、暂缓、已收录、随模型就挪出；结果要逐条看一遍，`-S` 按字符串找，可能找漏或找多）：

```bash
python3 - "$REPO" "$OLD_BASE_SHA" "$FORK_SHA" "$WORKTREE" "$ARTIFACTS" <<'EOF'
import csv, json, os, subprocess, sys
repo, old, fork, wt, a = sys.argv[1:]
inv = {r["sha"][:10]: r["decision"] for r in csv.DictReader(open(f"{a}/inventory.tsv"), delimiter="\t")}
c = json.load(open(f"{a}/contract-next.json"))
keep, out = [], open(f"{a}/contract-excluded.tsv", "w")
out.write("key\thost_sha\tdecision\n")
for cap in c["capabilities"]:
    key = cap["key"].split("@")[0]
    shas = subprocess.run(["git", "-C", repo, "log", "--reverse", "--format=%h", "--abbrev=10",
                           f"{old}..{fork}", "-S", key, "--", cap["where"]],   # 限定到所在文件，
                          capture_output=True, text=True).stdout.split()     # /health 这类短 key 才不会误配
    hosts = [s for s in shas if s in inv]          # 碰过这个 key 在分类清单里的提交，可能不止一笔
    gone = not os.path.exists(os.path.join(wt, cap["where"]))
    if any(inv[s].split(":")[0] == "吸收" for s in hosts) or (hosts == [] and not gone):
        keep.append(cap)                           # 有一笔吸收就该在位；分类清单找不到且所在文件还在的留着核对
    else:
        dec = "; ".join(f"{s} {inv[s][:40]}" for s in hosts) or "分类清单无此行"
        out.write(f'{cap["kind"]}:{cap["key"]}\t{",".join(hosts) or "?"}\t{dec}{"（所在文件已不存在）" if gone else ""}\n')
c["capabilities"] = keep
json.dump(c, open(f"{a}/contract-scoped.json", "w"), ensure_ascii=False, indent=1)
print("保留", len(keep), "挪出见 contract-excluded.tsv；decision 为「分类清单无此行」的回第 0 步补判")
EOF
```

过滤后核对仍报 MISSING 的，逐条归三种：引入提交是「吸收:部分」而这一项正好在没吸收的那段里
（K3 实测：`AIAK_DISABLE_THINKING` 属 `147c4e45af` 未点名段），手工挪出并在 decision 写明属哪段；
在吸收段里，是真漏迁，补代码；所在类消失、社区换了实现（上面 TokenizerWorker 那类），挪出并写
「原位置消失:<社区替代>」。K3 实测：脚本从 88 项留下 53 项，核对剩 4 项 MISSING 全属前一种和后一种，
手工挪完 49/49。
`--env-name` 点名哪些 `SGLANG_*` 开关：取发版 YAML 和平台采集配置里出现的 `SGLANG_*`
（`rg -o 'SGLANG_[A-Z0-9_]+' <发版 YAML> | sort -u`），上面那 6 个是 DSv4.1 平台的例子。

**手工：三项脚本判不了的。**

1. **启动参数反查**。参考 YAML 不是参数契约，照抄会让容器直接以 `unrecognized arguments`
   退出；对**这次要出的镜像**的 argparse 反查：
   `python3 "$SKILL_DIR/scripts/check_launch_args.py" --repo "$WORKTREE" --yaml <发版 YAML>`。
   `--yaml` 也收 `.sh` 启动脚本；脚本自带的选项用 `--allow=--bench-mode` 放行，必须写成
   `=` 形式，`--allow --bench-mode` 会被 argparse 当成另一个选项拒掉。
   差集三分：社区已删且能力默认开启 → 删参数；厂内私有且这次需要 → 按 A 类补迁那笔提交；
   厂内私有且不需要 → 删参数并在分类清单记一行「能力缺失，需要时迁 \<SHA\>」。
2. **指标 label 集合逐字比**。面板的 PromQL 按 label 选序列，少一个图就空；取上一版交付分支
   和 HEAD 的同一处 `labels = {` 比。
3. **面板清单反查**。指标名从 dashboard 的 JSON（`<url>&editview=dashboard_json`）取，不要
   按面板标题猜；空面板按五类根因定性（缺观测点 / label 值不匹配 / label 集由拓扑决定 /
   部署开关未开 / 计数器未预热），再排除看板查询自身写错。

完成判据：1 的未识别参数清零，2 逐字一致，3 的每个空面板有定性结论。缺输入时（没有发版 YAML、
没有上一版交付分支、拿不到 dashboard JSON）对应那项记 deferred，写明缺什么，列进报告的 deferred 清单。DSv4.1 那次跳过反向核对
的代价是平台探针拿到 404、POD 永远不进服务列表，多等一轮 12 分钟冷启动才发现。

**验证点 2：对比源 PR 集，代码 line-by-line 一致。** 字段都在不等于内容都落地了。以源提交为
判准，两侧各算净改动行集合再求差：

```bash
python3 "$SKILL_DIR/scripts/replay_residual.py" --repo "$WORKTREE" \
  --new-base "$NEW_BASE_SHA" --tip HEAD \
  "${SRC_ARGS[@]}" --accept "$ARTIFACTS/accepted-residual.tsv" \
  -o "$ARTIFACTS/residual.md"
```

第一次跑可以不带 `--accept`（文件还不存在），看全量残差后再逐条写清单。

`SRC_ARGS` 是分类清单里所有「吸收」行的源 SHA，用 bash 数组拼，zsh 下不加引号的字符串变量不分词，
脚本会只收到一个参数：

```bash
SRC_ARGS=(); while read -r s; do SRC_ARGS+=(--source-commit "$s"); done \
  < <(python3 -c 'import csv,sys
for r in csv.DictReader(open(sys.argv[1]), delimiter="\t"):
    if r["decision"].split(":")[0] == "吸收": print(r["sha"])' "$ARTIFACTS/inventory.tsv")
```

源集合以分类清单为准，不从提交正文的 `Source:` / 「重放自」行反抽：正文会引用别的分支的参考
提交（GLM 实测：正文引了 DSv4.1 的 412047d3f2 作先例，它不在本 fork 的 OLD..FORK 里）。
拼完用 `git merge-base --is-ancestor <sha> "$FORK_SHA"` 逐个确认都在 fork 上（FORK 是原研发分支，
见变量表；不在的说明分类清单混进了别的分支的提交）。`SRC_ARGS` 为空说明分类清单没有吸收行，先回第 1 步查。

源集合只放「吸收」行，不迁、暂缓、随模型、已收录的提交不放，否则它们全会报成漏迁。
部分吸收的提交放进来，没吸收的那部分写进 accept 并在理由里引分类清单 decision。

完成判据：漏迁与「该删没删」两类归零。唯一允许的例外是**上游改了接口**，写进 `--accept` 清单
并在理由里点名那处变更，只写「有意改写」不算，没写理由的规则脚本直接拒绝。这两类是必须归零的信号
（冲突解丢一行、折叠漏 hunk、老实现没删干净）；「新造」不进判据，整行搬家会造成假阳性。
脚本已滤掉两类假阳性：源侧加的行仍在 tip 同一文件里的不算漏迁，源侧删的行在 tip 文件里已
不存在的不算该删没删；加到别的文件的行单列「搬家」，复核不阻塞。accept 规则两段式
`<片段>\t<理由>` 匹配路径或行，三段式 `<路径片段>\t<行片段>\t<理由>` 要求两者同时命中，
`)`、`else:` 这类通用行必须用三段式，免得整个文件被放行。
DSv4.1 第二轮实测：42 笔源提交对 17 笔重放，不挂 accept 时漏迁 325、该删没删 8、搬家 46；
挂 38 条点名社区提交的 accept 后归零，新造 131 行逐条复核为接新结构的适配。

accept 清单本身要能审。每条理由只能落进三类，并按类写够证据：

| 类 | 理由必须写 | 例 |
|---|---|---|
| 分类清单判不迁 | 源 SHA + 分类清单 decision 原文 | `54f59fa2f1 吸收:部分 …；此块 thinking budget 未点名` |
| 上游改接口 | NEW_BASE 上的社区提交或 PR 号 | `peer_data_parallel_rank → disagg_prefill_dp_rank #19268` |
| 写法差 | 重放侧落点 `文件:函数` | `[trace] 改走 observability/request_trace.py:trace()` |

写法差只写「写法差」「已移植」不算，没有落点的条目当真漏迁处理。收口后按理由分组计数，
出一份 `accept-summary.md`（每类条数、每个源 SHA 条数）。**单个源 SHA 的写法差条目超过 30 条，
或写法差占全部 accept 一半以上，就要抽检**：从该组随机挑 5 条，到重放侧落点逐行对，确认行为
一致；有一条对不上，整组重审：去掉该组规则重跑，露出的块逐个判，真漏迁补代码，判错的规则改写。
重审后仍说不清的块按漏迁处理，不留在 accept 里。GLM 实测：876 条里约 640 条是一轮新加的三段式，`b92cfe4aee`
一个源 114 条、`710b5d3e3c` 48 条，归零全靠 accept，没有一行真漏迁补丁，这种结果必须抽检后
才能报「验证点 2 通过」，报告里写明抽检了哪几组、各挑了哪几条。

残差要按源 SHA 归因时，对单个源跑一次（`--source-commit <那一笔>`，其余参数不变），
不要临时写归因脚本。`--path` 给仓库根下的完整路径（`python/sglang/srt/...`），不是包内路径。

漏迁里有一类是 fork 上的死代码：只有定义、在 FORK_SHA 全树没有调用点（K3 实测：bootstrap-room
reject 逻辑）。先 `git grep -n '<函数名>(' $FORK_SHA -- python` 确认除定义外零命中，再写
`[不迁] <sha> fork 死代码：<函数> 在 FORK 无调用点`，不要为了归零把它搬进来。有调用点但调用点
在不迁的块里的，按调用点所在块的分类清单 decision 写。

理由里引的提交号用两种之一：源 SHA（分类清单 sha 列，fork 上固定不变）或 Change-Id。不要引重放侧
的短 SHA：每次 autosquash 都会换，清单写完就过期（GLM、K3 都发生过）。

**不许按整个文件放行 NEW_BASE 已删掉的旧结构文件**（两段式规则只写 `scheduler_metrics_mixin.py`
这种路径片段）。社区重构删文件时，fork 在旧文件里加的行要么已按 L9 搬到新文件（脚本会列进
「搬家」），要么还没迁；路径级规则会把后一种一起盖掉。旧文件的处理办法：先去掉路径级规则跑一次，
露出的漏迁逐块对分类清单，属于不迁的部分写块级规则，属于吸收的部分到社区新文件补上；理由写
`[接口] <源 sha> 文件由 <社区提交> 删除，内容迁到 <新文件:函数>` 或 `[不迁] <源 sha> <decision>`。
GLM 实测：12 条「旧结构文件 NB 已重构删除」路径级规则盖住了 264 行漏迁（scheduler_metrics_mixin.py
91 行、scheduler_runtime_checker_mixin.py 57 行、collector.py 43 行等），去掉后才露出来。

路径级规则（两段式，片段只是路径或目录）只允许用在重放栈完全没碰过的文件上，而且要逐文件确认
源提交对该文件的整份 diff 都属于不迁的块。重放碰过的文件（`git diff --name-only NEW..HEAD` 里有）
一律写块级或三段式规则。收口前加一条机检，必须零输出：

```bash
git -C "$WORKTREE" diff --name-only "$NEW_BASE_SHA"..HEAD > "$ARTIFACTS/touched.txt"
rg -v '^#' "$ARTIFACTS/accepted-residual.tsv" | awk -F'\t' 'NF==2 && ($1 ~ /\.py$/ || $1 ~ /\/$/) {print $1}' \
  | while read -r frag; do rg -F -q -- "$frag" "$ARTIFACTS/touched.txt" && echo "$frag"; done
```

K3、DSv4.1 实测：K3 有 55 条路径级规则，其中 17 条落在重放改过的文件上，盖住 484 行；DSv4.1 有
23 条路径级规则，其中 15 条落在改过的文件上，盖住 231 行。改写成块级规则前，这两个分支的
「漏迁 0」都不能算数。

源提交把社区原函数体整个换成自己的分发器，而重放选择保留社区函数体、在它上面扩展时，同一个
文件会同时露出一组漏迁（分发器的行）和一组该删没删（社区原 body）。这两组都写 `[写法]`，落点
指向重放侧保留并扩展的那个函数，在理由里说明行为由它承接。GLM 实测：`serving_tokenize.py`
99 行漏迁和 18 行该删没删，落点是 `http_server.py:openai_v1_chat_tokenize` 和
`serving_tokenize.py:_handle_non_streaming_request`。

同一个吸收提交里夹着未点名类别的 hunk（GLM `5395819de4`：ZMQ 端口里夹着 `mooncake/conn.py` 的
传输失败处理），分类清单 decision 要改成「吸收:部分 …；<那块> 属 <类别> 不迁」，accept 的 `[不迁]`
才对得上分类清单原文。

反过来，吸收提交的 evidence 里写「模型面随 X」（X 是本轮吸收的特性）时，那些模型文件的 hunk
属于吸收范围，要和框架面一起重放，不能在 accept 里写 `[不迁]`。只有 X 本身没吸收时才不迁。
DSv4.1 实测：`135c8de07b` 判「吸收:EPD」，evidence 写「deepseek_v4 模型面随 EPD」，PP 下传
hc pre-mix 的三处（`deepseek_v4.py`、`runner_utils/buffers.py`、`runner/base_runner.py`）却被
32 条「PP hc 不迁」规则盖住，去掉路径级规则才露出来，补进 K3 parity 卡。

accept 是按行子串匹配的，一条理由会盖住同一语义块里的所有行，没移植的 hunk 也一起被盖住。
所以抽检**按 hunk 做，不按行随机挑**：对要抽检的源 SHA，把它的规则从清单里去掉再跑一次，
看露出来的每个 hunk 在重放侧有没有对应实现：

```bash
rg -v '<源 SHA 前 10 位>' "$ARTIFACTS/accepted-residual.tsv" > "$ARTIFACTS/accept-minus.tsv"
python3 "$SKILL_DIR/scripts/replay_residual.py" --repo "$WORKTREE" \
  --new-base "$NEW_BASE_SHA" --tip HEAD --source-commit <那一笔> \
  --accept "$ARTIFACTS/accept-minus.tsv" -o "$ARTIFACTS/residual-<sha>.md"
```

GLM 实测：`710b5d3e3c` 组随机挑 5 行看都对，整组去掉规则重跑才露出 `4f8e6369da` 对
`_check_for_unstreamed_tool_args` 的三处守卫没移植（+26/−6），之前被「写法差」盖住了。

理由的格式要能机检，开头写类别标签和源 SHA：`[不迁] <sha> <分类清单 decision 原文>`、
`[接口] <sha> <社区提交或 #PR>`、`[写法] <sha> <path.py>:<函数>`。收口前跑一次，下面三条都要
零输出，有输出的条目补证据或删掉重审：

```bash
A="$ARTIFACTS/accepted-residual.tsv"
rg -v '^(#|$)' "$A" | rg -v '\t\[(不迁|接口|写法)\] [0-9a-f]{7,}'      # 没有标签或没有 SHA
rg '\t\[写法\]' "$A" | rg -v '\.py:[A-Za-z_]'                     # 写法差没写落点
rg '\t\[接口\]' "$A" | rg -v '#[0-9]+|[0-9a-f]{10}'                # 接口变更没点名社区提交
```

查重和查漏按内容核对，不在提交正文里 grep SHA，因为正文末段会点名没迁的 SHA 来解释取舍。
查重：每个吸收 SHA 的改动行只落在一笔重放里（镜像 hunk 拆分除外）；查漏：上面的残差归零；
不该进栈的：对不迁、暂缓提交单独跑一次 replay_residual，它们的加行在重放侧净 diff 里一行
都不能出现（看报告里该源的「漏迁」应等于它的全部加行）。
出现了先看分类清单：那行确实属于不迁块，就从重放里删掉；那行其实是重放需要的（比如被吸收提交依赖），
把那块改判成吸收并写进 evidence。
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
只有集中式那份会出错。顺序是：

1. 先起 PD 分离（交付形态），按上面逐项取数。
2. 资源允许再起集中式：同一套模型参数去掉 `--disaggregation-mode` 系列，带 `--enable-metrics`，
   打一轮有并发、含短输出（`max_tokens` 小或首 token 即 EOS）的请求，让请求在 prefill 后就结束，
   覆盖 `req.finished()` 分支。scheduler 不报错、`/metrics` 族名齐全才算过。
3. 集中式确实没资源起，做集中式路径静态检查，结论写进分类清单，记「静态通过 / 运行 deferred」：

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
通过。这一轮它抓出核对脚本自己的 bug：路由只按路径记 key，encode server 上的同名 `/health_forward`
把主 server 那份盖住了，删主 server 的照样过。三个验证点的分工、盲点移交和实测数据见
references/verification-ladder.md。

案例证据全部在 references/monitoring-contract.md：`/ready` 静默丢失的根因链、两个已不存在的
启动参数、13 个空面板逐条定性、监控代码八条高危写法（四条会让服务崩溃）、读 `/metrics` 的三个
陷阱（hostNetwork IP 串台、带 label 指标要等首次观测、两个 collector 分开判）、发版 YAML 监控
必查项、不重启 POD 的三方 md5 热替验收。迁完监控代码和判「指标缺失」之前各读一遍。

### 8 发布：自动提交 CR 并取镜像地址

按评审组走 refs/for 送审，一个提交一个 change。评审系统限单批数量时按类分批（监控一批、多模态
一批），不要退回整支 squash，能逐项评审是这条路线的主要收益。门禁和契约核对全绿后直接执行：

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
0 = 取到、1 = 构建失败（stderr 给 buildUrl，用 `ipipe-cli build job --job-build-id` 看日志）、2 = 超时。
ipipe-cli 不在 PATH 时 `cr_image.py` 自动调用 `ensure_ipipe.sh`：从官方地址下载
CLI 安装包，按包内固定的版本与安装脚本装好 CLI（安装包地址可用
`IPIPE_SKILL_URL` 覆盖）。未登录（`ipipe-cli login status`）时让用户给 ugate token，
执行 `ipipe-cli login --token <token>`，拿不到 token 就停下。最终汇报同时给出 **base 镜像地址（用户已确认的）** 和
**构建出的镜像地址**，`image.json` 里两者都有。镜像失败的修复提交要保留原 Change-Id 再推，镜像
地址随新 patchset 重取。机制与字段见 references/cr-image.md。

改已推过的评审必须保留原 Change-Id：换消息文件时 commit-msg hook 会生成新的，icode 会拒并
提示 `git fetch ... refs/changes/<nn>/<change>/<ps>` 重放；带原 Change-Id 再
`git commit --amend` 就是正常的下一个 patchset。LLM 评审的 BLOCK 报告逐条核实再改，本轮 9 条
里 2 条是误报，误报也要把判据写进回复。

### 9 部署与测试（外部阶段）

镜像取回后部署 E/P/D，按「精度 → FC → 功能回归 → 长稳」触发 ipipe 流水线（用本 skill 的 `scripts/ipipe_run.py`，
场景与步骤见 references/ipipe-pipelines.md；长稳用 `stress` 场景的默认值：12 h、数据集取最近 10 次执行里出现最多的、Prefill pod 内发压）。起服务前
先做 import 冒烟与启动参数反查；部署命名、model_id 选取、测试判读，以及静态契约漏掉的 4 个运行期缺陷，
见 references/deploy-and-test.md。

### 10 提测发版报告

报告按知识库的发版文档格式写，章节骨架、写法规则和发 KU 的约束见 references/release-report.md，发 KU 用本 skill 的 `bin/ku`（命令见 references/ku-publish.md）。流水线结果
原样写入，没做的写「未执行」，修复后没重跑的写「推断」。

## 难度预判（分级用信号，不用感觉）

| 级别 | 信号 | 处置 |
|---|---|---|
| 易 | fork 独有文件为主，冲突史 = 0 | 直接 pick |
| 中 | 触少量社区文件，冲突史 1–5 | pick 后小修 |
| 难 | 冲突史 > 5，或触 scheduler / model_runner / serving_chat 等热点 | 预留 L2/L9 重实现时间 |
| 难(先拆) | 一卡多主题（≥3 个类别） | 先逐提交拆类再处置 |

冲突史 = 卡片触碰文件与上次整支 merge 冲突清单的交叠文件次，用来衡量社区是否也在改这些文件。
52 卡的实测分布见 references/pr-taxonomy.md。

## 常见坑

- 「社区已收录」按标题判会误判：厂内 pick 时常改过签名或加过开关。证据是 NEW_BASE 的实现
  覆盖厂内行为，不是标题相似。
- 零冲突不等于该 pick：厂内特性栈（如 encode/EPD）常是与社区同名子系统的平行实现，全 fork
  独有文件、pick 必零冲突，但正确动作是取社区框架再搬差异。同类实现判定优先于难度判定。
- 一笔提交里的开关要逐个数受益面，不按整笔定性。luno-5437 加了 6 个 CP 尾层融合开关：
  `SGLANG_FUSE_CP_LAST_TOKEN_GATHER` 在 runner 里走通用 CP 策略，是框架通用（默认关，暂缓）；
  另外 5 个只有 deepseek_v4 的模型、后端和 kernel 消费，随模型走 B1。
- 社区已有同名框架时（主线的 `layers/moe/mega_moe.py`、`layers/cp/*`、`layers/dcp/*`），
  厂内差异要对新基线的当前版本重算，不能拿旧基线上的 diff 直接套：`mega_moe.py` 一个月
  内社区就改了 19 笔。
- 分类清单把 fixup 当独立 PR 逐条 pick，只会重放无意义的中间状态；先折叠。
- 跳过 Cache 类却没动发版 YAML：起服务读不存在的开关，直接 fail fast 在参数校验。
- 换了 Change-Id 的迭代会开出新评审；preflight 用 scripts/review_preflight.py。
- 大卡的卡级补丁跨越社区重构点时，git apply 失败率高于逐提交 pick；该卡退回逐提交重放，
  fixup 在 worktree 里 autosquash。
- 分类清单枚举用 --no-merges 会漏掉 merge commit 本身携带的解冲突改动；上一代分支若有内部
  merge，重放后跑 `git diff FORK_SHA..HEAD -- <路径>` 抽查关键子系统有无语义残差。
- `.gitignore` 的 `**/build/` 会挡住 `build/build.sh`，`git add -f` 才进得去；所以
  git ls-tree 看得到它而 git add 会拒。
- 改动镜像构建文件那一卡会让它后面的卡全部换 SHA、跟着升 patchset。送审前 diff 一次 Change-Id
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
  重放省得多：DSv4.1 flash 从 1013 追到 1017 main，34 笔栈只有 2 处小冲突。这是硬规则 10 的唯一例外，
  三个条件都满足才走：候选栈在远端 ref 上；每笔正文里的来源 SHA 都能 `git cat-file -e` 解析到
  （占位 SHA 如 `7a1f6a0e8c3d…` 说明追溯链断了）；这一轮的 pick 范围和 fork tip 没超出候选栈当时覆盖的。
  任一不满足就按硬规则 10 从 fork 原提交 pick，候选栈只当冲突解法和 fixup 的参照，分类清单里逐卡记下对应
  的候选栈提交。范围扩大时（例如这轮加了框架层 A4）也一样：超出的部分只能从 fork 历史来。
  静态契约全绿不代表能起服务，
  之后必须跑 references/deploy-and-test.md 的 9.1.1（社区单测），它抓出了多 tokenizer 拆分的真缺陷。
- 社区重写了你要搬的循环时（例如 PD prefill 事件循环），先看社区单测钉住了什么。luno-5298 把三次轮询合成一次，
  按新循环重实现后 56 个 `test_prefill_result_polling` 用例失败，说明行为被改了；没有性能实测就不迁，别硬改测试。
- 厂内对社区有偏离的地方（例如强制调用的 DeepSeek 工具调用语法），先写一个探针脚本在镜像里直接问 xgrammar
  「编码器真实输出被不被接受」，再决定改法。1017 这一轮用探针确认：社区内置语法对非严格工具会改写
  `field.name`，而把 JSON 体换进去又会拒绝编码器的原生输出；正确做法是强制调用时把工具声明成按名字严格，
  自动调用保持社区内置语法。
