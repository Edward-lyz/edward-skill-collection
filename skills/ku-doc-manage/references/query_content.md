# 查询文档正文内容

根据文档ID或URL查询知识库文档的完整正文内容。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc-id | string | 否* | 文档ID,知识库文档链接中以/分割后的最后一个字符串 |
| url | string | 否* | 文档完整URL链接 |
| show-doc-info | boolean | 否 | 是否返回文档元信息(标题、创建时间等)，默认false |
| show-resource-info | boolean | 否 | 是否返回文档内嵌资源信息，对应 API 参数 `showResourceInfo`，默认 false；只有在查询【查询文档内嵌资源数据】场景时才设置为 true |
| protocol | string | 否 | markdown | 返回内容格式："json"=知识库编辑器JSON, "markdown"/"md"=Markdown(默认), "html"=HTML, "aihtml"=AIHtml, "mdhtml"=MdHtml |
| version-id | integer | 否 | 文档版本ID。不传则返回最新文档版本内容；指定版本ID查询正文时需要有文档编辑权限（文档成员或管理员）。**配合 `query-version` 使用可查询任意历史版本内容** |

*注：doc-id和url至少提供一个

## 响应字段说明

`text` 与 `content` 字段互斥，取值规则如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| text | string | 文档正文文本：**protocol=markdown/html/aihtml/mdhtml 时优先取此字段**；protocol=markdown 返回 markdown，protocol=html 返回 html，protocol=aihtml 返回 aihtml，protocol=mdhtml 返回 mdhtml；protocol=json 时此字段为空 |
| content | array | 文档正文内容：**protocol=json 时必取此字段**，返回编辑器 JSON 数组；protocol=markdown/html/aihtml/mdhtml 时正常为空，但若处理失败会以此字段兜底返回 |

**取值优先级总结：**
- `protocol=json`：只取 `content`
- `protocol=markdown/html/aihtml/mdhtml`：优先取 `text`；若 `text` 为空，则降级取 `content`（兜底）

## 文档资源占位符

当正文中包含附件、图片、流程图、脑图、随心搭等异步资源时，返回内容会在资源所在位置出现占位符：

`[元素类型，文件类型，ID，name（可选），desc（可选）]`

Agent 应将占位符视为“这里有资源，但尚未展开理解”。默认总结或问答时，不应假装已经理解资源内容；只有用户明确要求“读取附件 / 理解流程图 / 分析 Excel / 包含 PDF / 查看图片 / 全量资源总结”等【查询文档内嵌资源数据】场景，才将 `show-resource-info` 设为 true，并使用占位符中的 ID 调用 `query-doc-resource` 等能力。

### 随心搭读取（两步链路）

`query-content` 本身不会返回随心搭的代码或数据，只返回随心搭占位符。要读取随心搭需两步：

1. 调用 `query-content --show-resource-info=true`，在返回中找到随心搭占位符（元素类型为 `flex-builder`）的资源 ID；
2. 使用该资源 ID 调用 `query-doc-resource --resource-type flex-builder --resource-id <id>`。**不传 `--flex-query-type` 时默认一次取回代码与数据**；只要代码用 `--flex-query-type code`，只要数据用 `kv`。数据按 `nextCursor` 自动翻页。

用户要求读取文档**全部内容**时，文档内的随心搭默认一并取回代码与数据，无需用户额外指定；用户只要正文、文档结构或组件清单时，只在这一步给出组件数量与位置，不调用 `query-doc-resource`。

组件数据的原始值缺少语义，必须结合代码理解 key 命名规则、value 结构与字段含义，并识别代码中按用户身份过滤展示的逻辑，详见 [query_doc_resource.md](./query_doc_resource.md)。

**本命令与 `query-doc-resource` 均只覆盖"读取"意图**：新建随心搭改用 **知识库随心搭flexbuilder** 技能；修改已有随心搭（含修改组件内数据）时返回当前文档 URL，引导用户在页面中操作。

## 响应示例

### protocol=markdown（Markdown，默认）

```json
{
    "msg": "OK",
    "result": {
        "text": "# 示例文档标题\n\n示例段落内容",
        "content": [],
        "docGuid": "1xosIYvQX3qxeI"
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "123456789012345678"
}
```

### protocol=json（知识库编辑器JSON）

```json
{
    "msg": "OK",
    "result": {
        "text": "",
        "content": [
            {
                "blockId": "docyg-cd25d2a0-1bb3-11f1-a2f8-6fa8bbe5641c",
                "children": [
                    {
                        "children": null,
                        "diffId": null,
                        "text": "示例文档标题",
                        "type": null
                    }
                ],
                "diffId": "SayHappy",
                "type": "title"
            },
            {
                "blockId": "docyg-cd25d2a1-1bb3-11f1-a2f8-6fa8bbe5641c",
                "children": [
                    {
                        "text": "示例段落内容"
                    }
                ],
                "diffId": "5XgYSsnA",
                "type": "paragraph"
            }
        ],
        "docGuid": "1xosIYvQX3qxeI"
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "123456789012345678"
}
```

## CLI调用示例

```bash
# 使用文档ID，默认返回Markdown
ku query-content --doc-id WKoT7ltTnjU1oW

# 使用完整URL
ku query-content --url https://ku.baidu-int.com/knowledge/xxx/xxx/xxx/WKoT7ltTnjU1oW

# 指定协议版本
ku query-content --doc-id WKoT7ltTnjU1oW --protocol json  # 返回编辑器JSON
ku query-content --doc-id WKoT7ltTnjU1oW --protocol markdown  # 返回Markdown（默认）
ku query-content --doc-id WKoT7ltTnjU1oW --protocol html  # 返回HTML
ku query-content --doc-id WKoT7ltTnjU1oW --protocol aihtml  # 返回AIHtml
ku query-content --doc-id WKoT7ltTnjU1oW --protocol mdhtml  # 返回MdHtml

# 指定文档版本ID
ku query-content --doc-id WKoT7ltTnjU1oW --version-id 123456
```

---

## Agent 使用指南

### 文档类型自动识别与降级

当查询文档内容时，如果返回文档类型不支持，响应会包含真实类型信息：

#### 响应示例

```json
{
    "msg": "文档类型不支持，当前文档(AbvmMiC7x_7ut6)类型为数据表表夹",
    "result": null,
    "returnCode": 20129,
    "returnMessage": "文档类型不支持，当前文档(AbvmMiC7x_7ut6)类型为数据表表夹",
    "status": 20129,
    "success": false,
    "traceId": "708940596371833856"
}
```

#### 类型映射与处理

| 返回类型信息 | 真实类型 | 推荐操作 |
|------------|---------|---------|
| "类型为在线表格" | 在线表格 | 使用 `export-sheet` 导出为 Excel 查看/编辑 |
| "类型为数据表表夹" | 数据表表夹 | 使用 `get-datasheet-views` / `create-datasheet` 等数据表命令 |

#### 处理流程

```bash
# 尝试查询文档内容
RESULT=$(ku query-content --doc-id <doc-id>)

# 检查是否为类型不支持错误
if echo "$RESULT" | grep -q "文档类型不支持.*类型为在线表格"; then
    echo "检测到在线表格，自动使用导出功能..."
    ku export-sheet --doc-id <doc-id> > sheet.xlsx
elif echo "$RESULT" | grep -q "文档类型不支持.*类型为数据表"; then
    echo "检测到数据表，请使用数据表管理命令:"
    echo "  ku get-datasheet-views --dist-id <dist-id>"
    echo "  ku get-datasheet-records --dist-id <dist-id>"
fi
```


### 查询历史版本

先通过 `query-version` 获取版本 ID，再读取指定版本内容：

```bash
# 获取最新10个版本列表
ku query-version --doc-id WKoT7ltTnjU1oW --page-num 1 --page-size 10

# 读取指定版本正文
ku query-content --doc-id WKoT7ltTnjU1oW --version-id ver123456
```

### 常用场景

**版本对比**：导出两个版本后 diff 对比，或让 Agent 自动生成差异摘要

**修改前备份**：保存修改前的版本 ID 和内容用于回滚

**版本恢复**：查看历史版本内容后，通过 `edit-mdsl-content` 恢复