---
name: sglang-shadow-branch-sync
description: 把 SGLang 厂内模型研发分支整理成公开 fork 上的影子分支：冻结源 tip 与基线，按中文交付类别把厂内提交 squash 成少量 commit，保证最终 tree 与源分支完全一致，并生成单文件离线 diffmap 推到 fork。触发词：影子分支、shadow branch、把研发分支整理成 PR、按类别 squash、commit 分类、diffmap、同步到社区 fork、审核提交分类。
---

# SGLang 影子分支同步

把一个厂内研发分支（例如 `master-dsv41-flash`、`master-kimi-k3`）转成公开
fork 上的评审分支：历史是干净的分类提交，内容与原分支逐字节一致，附一份
单文件离线 diffmap。目标是让外部评审按交付链路看代码，而不是吞下几百个
内部 change。

## 适用与不适用

适用：用户要求把某条模型研发分支整理成 PR、按类别压缩提交、生成 diffmap、
推到 GitHub fork 做对照。

不适用：把某个具体 PR pick 到另一条分支（应逐卡 pick），或追社区新基线
（应做 baseline swap + 台账重放）。

## 硬规则

1. **只推 fork，不推厂内 origin。** 影子分支的目标远端由用户指定；默认
   fork 是 `https://github.com/<user>/sglang.git`。厂内仓库只作为对象库使用。
2. **不公开内部历史。** 影子分支的根提交是合成基线：
   `[基线] <MODEL> 内部基线快照`，tree 等于冻结的 BASE。后续提交全部
   re-parent 到这个根上。
3. **冻结三个引用再动手**：`SOURCE_TIP`（研发分支 tip）、`BASE`（内部改动
   的起点，通常是 `merge-base(source, origin/main)`）、`SHADOW`（输出分支）。
   全程用冻结 SHA，不在中途重新解引用分支名。
4. **分类依据是代码 diff，不是提交标题。** 标题只用于建立索引。每个
   来源提交至少要看改动文件与实际增删行；可疑项展开完整 hunk。禁止只按
   `fix`/`optimize` 等关键词定类。
5. **最终 tree 必须相等。** 判据是影子分支最后一个文档提交的父提交与
   `SOURCE_TIP` 的 `git diff --quiet` 为零。做不到就不推送。
6. **提交信息统一中文标签**：`[构建]`、`[平台适配]`、`[监控]`、`[EPD]`、
   `[缓存]`、`[PD传输]`、`[流式协议]`、`[模型适配]`、`[性能优化]`、
   `[BUGFIX]`、`[社区同步]`、`[测试]`、`[其他]`。不要用 SGLang 社区的
   `[Feature]`/`[Perf]` 前缀。
7. **每个分类提交正文列出全部来源**：
   `来源提交（N 个）：sha10, sha10, ...`。这是审计与回溯的唯一索引。
8. **diffmap 是单文件 HTML，直接放分支根目录。** 文件命名
   `<MODEL>_SHADOW_DIFFMAP.html`，用浏览器直接打开，不依赖网络或本地服务。
9. **重写过的影子分支可以 force-push。** 这是评审分支，不是交付分支。
10. **收尾必须清理**：临时 worktree、diffmap 构建目录、Chrome profile、
    中间 JSON/HTML 全部删除；只保留用户要的产物。

## 1. 冻结与体检

```bash
cd <repo>
SOURCE_TIP=$(git rev-parse origin/<source-branch>)
BASE=$(git merge-base "$SOURCE_TIP" origin/main)
git rev-list --count "$BASE".."$SOURCE_TIP"
```

如果用户给了显式 BASE，以用户为准。确认 BASE 之后的提交确实都是厂内改动；
若中间夹着社区 cherry-pick，它们照样属于本次范围，但分类时优先归
`[社区同步]`。

给影子分支起名：`master-<model>-shadow`，与研发分支一一对应。

## 2. 分类

先按交付链路分类，再处理修复。完整定义、优先级和边界案例见
[references/classification.md](references/classification.md)。

要点：

- 功能类优先：一个提交的主体如果是某条链路的新能力/行为变更，就归该链路，
  即使标题带 `fix`。
- `[BUGFIX]` 只收跨领域稳定性修复、调度/分配器/内存安全这类没有单一功能
  归属的缺陷修复；某个功能内部的缺陷随该功能归组。
- `[社区同步]` 只收内容确属上游 cherry-pick/merge 的提交；内部聚合 merge
  按实际带入的内容归组，不能因为标题写了 merge 就整块算社区同步。
- `[其他]` 是异常桶：超过总提交数 3% 就说明分类规则或人工判断有问题，
  重新分。
- `[PD传输]` 收 PD/PP 的 KV 传输、连接、超时、重试、408、注册刷新、
  socket/端口和传输容错；不要把这类改动散进缓存或 BUGFIX。

## 3. 生成影子提交

按类别分组，组间顺序取该类别第一次出现的顺序；组内保持源分支原始顺序。
重放采用逐提交 `cherry-pick -n`，冲突时取被应用提交的版本
（`git checkout --theirs`）；文件在该提交中不存在则 `git rm`。每组结束
提交一次。

重排后中间状态允许不完美，最终以 tree 相等为准。若重放结束仍有差异：

1. 对每个残留路径，找到源分支中最后修改它的提交，按该提交的类别归属；
2. 用 `git commit-tree` 重建整条链，每个提交在自身 tree 上叠加累计的
   残留路径内容；
3. 再跑一次尾部修正，处理 merge commit 造成的删除（这些删除在
   `git log -- path` 里可能看不到，需要 `--full-history`）。

具体命令序列与踩坑见 [references/pipeline.md](references/pipeline.md)。

## 4. 审核循环

分类必然有主观项，交付前至少做一轮代码级复核。为每个来源提交生成摘要：
文件列表 + 前 25 行真实增删行；摘要写到独立目录，不塞进上下文。

```bash
python3 scripts/make_digest.py <repo> <base> <source-tip> <shadow-ref> /tmp/<name>-digest.md
```

让复核者逐条读 diff，输出“需要移动的提交清单”，每条必须有文件与代码证据。
复核者说“只看了标题”时，这轮结果作废重做。

把复核结论落成 `sha10 -> 类别` 的覆盖表，重新跑分组与重放；不要直接手改
已生成的提交历史。

## 5. 单文件 diffmap

在**公开化之后**的提交链上生成，否则页面里的 SHA 与推上去的提交对不上。
做法是把 diffmap 前端打成单一 JS/CSS，内嵌 gzip+base64 的 diff 数据，
并在运行时解压、接管 GitHub Gist API 请求。完整配方见
[references/diffmap-single-file.md](references/diffmap-single-file.md)。

把 HTML 作为最后一个提交加入分支：

```
[文档] 添加 <MODEL> 影子分支离线 diffmap
```

## 6. 推送与验收

推送前跑：

```bash
python3 scripts/verify_shadow.py <repo> origin/<source-branch> <shadow-ref> --base <BASE>
```

它检查：文档提交的父提交 tree 与源 tip 相等、没有冲突标记、全量 Python
文件可解析（并区分基线已有的 BOM 等旧问题）。

推送：

```bash
git push --force <fork-url> <shadow-branch>:refs/heads/<shadow-branch>
```

大文件推送失败（`curl 55` / HTTP2 重置）时设置
`git config http.version HTTP/1.1` 与 `http.postBuffer 524288000` 后重试。

推送后再用 `git ls-remote` 核对远端 tip，并至少用 headless Chrome 打开一次
HTML，确认阶段标题和 diff 卡片能渲染。

## 产物

- 远端：fork 上的 `<shadow-branch>`
- 分支根目录：`<MODEL>_SHADOW_DIFFMAP.html`
- 本地备份：单文件 HTML 与评审报告放在用户指定目录

## 常见失败

- 只看标题分类 → EPD 功能进了 BUGFIX、测试提交进了性能组。
- 先做 diffmap 再公开化 → 页面里的 SHA 在推送后的分支上不存在。
- 用 `git log --reverse` 的位置当作依赖顺序 → 时间戳相同，必须看父链。
- 重排后不收敛 → 影子分支树与源分支不一致，评审内容失真。
- 把内部历史直接推 fork → 泄露内部 commit 信息。
