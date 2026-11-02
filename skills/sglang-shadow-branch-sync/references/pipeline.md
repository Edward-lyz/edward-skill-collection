# 影子分支构建流程

以下用变量表示冻结值：

```
REPO     厂内 SGLang 仓库
SOURCE   origin/<source-branch>
BASE     <冻结基线>
SHADOW   master-<model>-shadow
WT       临时 worktree
```

## 1. 建 worktree

```bash
git -C "$REPO" worktree add -b "$SHADOW-tmp" "$WT" "$BASE"
```

不要在厂内主工作区直接操作，避免污染用户当前改动。

## 2. 分组

读取 `BASE..SOURCE` 的提交列表，按类别分组；组间顺序取该类别第一次出现的
顺序，组内保持原始顺序。

覆盖表格式（复核结论）：

```
sha10<TAB>[类别]
```

同一条提交只能出现在一组。未覆盖的提交走关键词规则。

## 3. 逐组重放

```bash
git cherry-pick -n <sha>
```

失败时列出冲突文件：

```bash
git diff --name-only --diff-filter=U
```

对每个冲突路径：

- `git cat-file -e <sha>:<path>` 成功 → `git checkout --theirs -- <path>`
- 不存在 → `git rm -f --ignore-unmatch -- <path>`

然后 `git add -A`、`git cherry-pick --quit`。

一组结束提交一次，正文写：

```
[类别] 中文摘要

来源提交（N 个）：sha10, sha10, ...
```

重排产生冲突是常态，冲突解决只保证“这一组能提交”，最终一致性由下一步
保证。

## 4. 收敛到目标 tree

比较：

```bash
git diff --name-only HEAD "$SOURCE"
```

对每个残留路径：

```bash
git log --reverse --format=%h "$BASE".."$SOURCE" -- "$path"
```

取最后一个提交，按它的类别把路径归入对应组。然后重建整条链：

1. 从 BASE 开始，逐个读取链上提交的 tree；
2. 把已归属的残留路径按累计集合写入 index（`git read-tree` +
   `git update-index --cacheinfo`，不存在则 `--force-remove`）；
3. `git write-tree`，用原提交信息 `git commit-tree`；
4. 更新分支 ref。

这样每个分类提交的 diff 逐步补齐，最终 tree 精确等于 SOURCE。

### 尾部修正

merge commit 造成的删除可能不出现在 `git log -- path` 里。重建后若仍有
少量差异，做一次尾部修正：取最终 tree，把残留路径按 SOURCE 的
`ls-tree` 结果重写（存在则写入 blob/mode，不存在则移除），再用同样的
提交信息重建最后一个提交。

循环直到 `git diff --quiet HEAD SOURCE` 为零。

## 5. 公开化

用 BASE 的 tree 造一个无父提交：

```bash
ROOT=$(git commit-tree "$(git rev-parse "$BASE^{tree}")" -F - <<EOF
[基线] <MODEL> 内部基线快照

影子分支的合成基线，内容等于内部基线 <BASE10> 的 tree。
EOF
)
```

然后把链上每个提交按原顺序 `commit-tree` 到 `ROOT` 上，更新分支。

公开化会改变所有 SHA，因此 **diffmap 必须在公开化之后生成**。

## 6. 常见坑

- 仓库里大量提交时间戳相同，`git log --reverse` 的显示位置不等于依赖顺序；
  用父链判断。
- 重排后不要用“冲突里谁更新”来猜内容；以最终 tree 为准。
- `git log -- path` 会做历史简化，找不到删除来源时加 `--full-history`。
- 大仓库 worktree 创建较慢，一次建好复用；结束后
  `git worktree remove --force`。
- 环境禁止 `rm -rf` 时用 Python `shutil.rmtree`。
- 推送大 HTML 失败时切 HTTP/1.1 并增大 `http.postBuffer`。
