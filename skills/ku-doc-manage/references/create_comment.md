# 创建文档评论/批注

在文档中创建底部评论、划线评论（批注）或评论回复。默认创建划线评论。

## 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| doc-id | string | 是 | - | 文档ID |
| username | string | 是 | - | 评论者用户名（UUAP格式） |
| text | string | 条件 | - | 评论纯文本内容（text和content至少传一个，优先使用text） |
| content | string | 条件 | - | 评论内容JSON数组，用于图片/富文本场景（text和content至少传一个） |
| comment-type | string | 否 | side | 评论类型："bottom"=底部评论, "bottom-reply"=底部评论回复, "side"=划线评论（批注）, "side-reply"=划线评论回复 |
| reply-comment-guid | string | 条件 | - | 回复的评论ID（comment-type=bottom-reply或side-reply时必填） |
| root-comment-guid | string | 条件 | - | 根评论ID（comment-type=bottom-reply或side-reply时必填） |
| quote-text | string | 条件 | - | 划线评论引用文本（comment-type=side时必填，按完整文本进行正文匹配来选取划线评论锚点位置；若存在多个重复文本，则默认选择第一个划线位置） |
| room-type | string | 否 | preview | 评论所属房间类型：preview=预览态评论，edit=编辑态评论 |

## 评论类型说明

| comment-type | 说明 | 额外必填参数 |
|--------------|------|-------------|
| bottom | 底部评论 | 无 |
| bottom-reply | 底部评论回复 | reply-comment-guid, root-comment-guid |
| side | 划线评论（批注，默认） | quote-text |
| side-reply | 划线评论回复 | reply-comment-guid, root-comment-guid |

## 响应示例

```json
{
    "returnCode": 200,
    "returnMessage": "OK",
    "result":
    {
        "commentType": 1,
        "commentGuid": "评论ID",
        "commentUsername": "zhangsang",
        "text": "评论文本",
        "docGuid": "文档ID",
        "repositoryGuid": "知识库ID"
    },
    "traceId": "1234567890"
}
```

## CLI调用示例

```bash
# 创建划线评论/批注（默认）
ku create-comment --doc-id WKoT7ltTnjU1oW --username zhangsan --text "这里有问题" \n    --quote-text "这是要划线评论的文本内容"

# 创建底部评论
ku create-comment --doc-id WKoT7ltTnjU1oW --username zhangsan --text "这是一条评论" \n    --comment-type bottom

# 回复底部评论
ku create-comment --doc-id WKoT7ltTnjU1oW --username zhangsan --text "同意楼上" \n    --comment-type bottom-reply \n    --reply-comment-guid 5356d6774d \n    --root-comment-guid 5356d6774d

# 回复划线评论
ku create-comment --doc-id WKoT7ltTnjU1oW --username zhangsan --text "同意" \n    --comment-type side-reply \n    --reply-comment-guid d7818e9c77 \n    --root-comment-guid 5356d6774d
```

## 注意事项

1. **用户名格式**：`--username` 参数需要使用 UUAP 格式的用户名（如 `zhangsan`）

2. **回复评论完整流程**：
   ```bash
   # 1. 先查询评论获取 commentGuid
   ku query-comments --doc-id WKoT7ltTnjU1oW

   # 2. 从返回结果中获取需要的 guid，然后回复
   ku create-comment --doc-id WKoT7ltTnjU1oW --username zhangsan --text "同意楼上" \n       --comment-type bottom-reply \n       --reply-comment-guid 5356d6774d \n       --root-comment-guid 5356d6774d
   ```
   - `--reply-comment-guid`：要直接回复的那条评论的ID
   - `--root-comment-guid`：评论树的根评论ID
   - 如果回复的是根评论，两个参数值相同；如果回复的是子评论，`root-comment-guid` 保持不变

3. **划线评论说明**：
   - 创建划线评论（`comment-type=side`）时，`--quote-text` 必须与文档中的完整文本内容完全匹配才能正确定位锚点位置
   - 如果文档中有多段相同的文本，默认选择第一个划线位置

4. **文本与富文本**：
   - `--text` 和 `--content` 二者至少提供一个
   - 两者都提供时，优先使用 `--text`（纯文本）
   - 如需包含图片等富内容，请使用 `--content` 传入编辑器JSON格式