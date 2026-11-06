# 发 KU（第 10 步用）

知识库命令行是本 skill 的 `bin/ku`。它按平台挑二进制，本地没有就从 `https://morpho.bj.bcebos.com/soqa/` 下载到
`bin/`（`bin/.gitignore` 不提交二进制），有新版自动更新；身份固定为 `liyanzhen01`，鉴权读同目录 `config.yaml`，
首次调用会在手机如流上确认身份。所有带 `--username` 的命令都传 `liyanzhen01`。

```bash
KU="$SKILL_DIR/bin/ku"
"$KU" query-user-info --username liyanzhen01            # 个人知识库 repositoryGuid
"$KU" query-content --doc-id <DOC_ID> --protocol markdown # 读格式样本或旧稿
"$KU" create-doc --repo-id <个人库 ID> --username liyanzhen01 \
  --title "<版本> 提测报告（精简版，草稿）" --md-file "$ARTIFACTS/release-report.md"
"$KU" move-doc --doc-id <DOC_ID> --target-repo-id <REPO_ID> \
  --parent-doc-id <发版目录 doc> --username liyanzhen01
"$KU" edit-mdsl-content --doc-id <DOC_ID> --username liyanzhen01 \
  --operation '{"mode":"cover","markdown":"..."}'
"$KU" publish-doc --doc-id <DOC_ID> --username liyanzhen01   # edit 之后发布
"$KU" delete-doc --doc-id <DOC_ID> --username liyanzhen01
```

- 正文长或含特殊字符时用 `--md-file`；`--content` 里换行写字面 `\n`。布尔参数写成 `--set-top=true`。
- 文档 URL `https://ku.baidu-int.com/knowledge/A/B/C/D`：`C` 是 repo ID，`D` 是 doc ID。文档即目录，放进某个目录就把
  它的 doc ID 传给 `--parent-doc-id`。
- `move-doc`、`delete-doc`、`cover` 都要用户明确同意后才执行。
- 401 / 403 是鉴权失败，让用户重新确认身份，不重试；404、无权限、5xx 如实告诉用户，不重试；60421（无权在该库建文档）
  问用户换库还是申请权限。
