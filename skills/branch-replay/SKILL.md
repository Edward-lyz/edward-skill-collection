---
name: branch-replay
description: |
  逐 commit 将整条分支 replay 到新 base，处理长距离 rebase 迁移。
  适用场景：把一条开发分支迁移到大幅演进后的新 base（如新版本主干），要求逐 commit 一一对应并产出迁移报告。
  触发词："分支迁移"、"rebase 到新 base"、"branch replay"、"逐 commit rebase"。
---

# Branch Replay — 逐 commit 分支迁移

把 old 分支的每个 commit 按序 replay 到新 base。每个 commit 沿冲突阶梯落级处置，产出新分支和一份迁移报告。报告是最终测试失败时的调试索引，不是流水账。

## 前提（用户保证）

- old 分支、新 base 已明确，工作区干净。
- old 分支历史线性。发现 merge commit 时停下向用户确认线性化方案，不擅自决定。
- old 分支的中间 commit 没有正确性保证（半成品状态是常态），所以逐 commit 不跑测试、不做静态检查。正确性由最终验收测试兜底，这同时意味着测试失败时不能用 bisect 定位，只能查报告。

## 步骤

1. **建立清单。** git rev-list --reverse <new-base>..<old-branch> 得到 commit 序列，从新 base 建工作分支，创建报告文件。完成标准：报告里列出全部 commit 的序号、短 SHA、标题，状态待处理。

2. **逐 commit replay。** 对每个 commit 执行 git cherry-pick -x，按下方冲突阶梯处置，在报告里记下处置等级后再处理下一个。完成标准：清单上每个 commit 在新分支上有一个序号对应的 commit（含空 commit），报告无待处理项。
   - patch 为空（改动已存在于新 base）：用 --allow-empty 保留空 commit 维持一一对应，报告记 already-in-base。
   - commit message 沿用原文。重实现的 commit 在 message 末尾加一行 Reimplemented after rebase。

3. **跑最终验收测试。** 用用户指定的命令（例如精度测试）验收整条新分支。完成标准：命令和输出原样贴进报告。修复测试失败是另一个任务的范围，本 skill 到贴出结果为止。

4. **交付。** 给出新分支名和报告路径。

## 冲突阶梯

每个 commit 从上往下落，落在哪级按哪级处置：

| 级别 | 现象 | 处置 |
| --- | --- | --- |
| auto | cherry-pick 干净应用（含 3-way 自动合并的上下文漂移） | 无需动作 |
| rename | 目标文件在新 base 上改名，hunk 落空 | 用 git log --follow 找到新路径，把改动落到新位置 |
| modify/delete | 目标文件在新 base 上已删除 | 回答两个问题：这个改动的意图还需要存在吗；需要的话落到哪。答案写进报告 |
| text-conflict | 双方改了同一区域 | 读双方 commit message、PR、周边代码，理解两边意图后合成。保留双方意图；不能共存时按迁移目标取舍并在报告记 trade-off。不发明新行为，不 abort |
| reimplement | hunk 级修补不成立（冲突过多、目标代码面目全非） | 放弃 patch 文本。读懂原 commit 的意图，在新 base 上重新实现。报告写明原意图和新实现落点 |

语义冲突（patch 干净应用但行为错，如新 base 改了函数签名而本 commit 新增旧签名调用）在文本层不可见，只能被最终测试暴露。排查测试失败时按 reimplement、text-conflict、modify/delete、rename、auto 的嫌疑顺序查报告。

## 报告格式

每个 commit 一条记录：

    ## <序号>/<总数> <old 短 SHA> -> <new 短 SHA> [处置等级]

    <原 commit 标题>
    <仅 modify/delete、text-conflict、reimplement 需要：意图、落点、trade-off 各一句>

结尾附最终验收测试的命令和完整输出。
