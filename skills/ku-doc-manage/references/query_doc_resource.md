# 查询文档内嵌资源数据

查询知识库文档正文中指定内嵌资源的结构化数据，支持附件、图片、流程图、思维导图、随心搭五类资源。随心搭可同时取回组件代码与组件内的数据。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| doc-id | string | 是 | 文档ID |
| resource-type | string | 是 | 资源类型：`attachment`、`image`、`diagram`、`flowchart`、`mxgraph`、`flex-builder` |
| resource-id | string | 是 | 资源ID，通常来自 `query-content` 返回正文中的资源占位符；查询文档内嵌资源数据前，可通过 `query-content --show-resource-info=true` 获取更完整的资源信息 |
| flex-query-type | string | 否 | **仅 `flex-builder` 有效**。`code`=只取组件代码，`kv`=只取组件数据，`all`=两者一起取。**本命令不传时默认 `all`** |
| key-prefix | string | 否 | 仅查询随心搭数据时有效，按 key 前缀过滤 |
| cursor | int | 否 | 仅查询随心搭数据时有效，分页游标。首页不传，后续传上一页返回的 `nextCursor` |
| limit | int | 否 | 仅查询随心搭数据时有效，单页条数，取值 1-20000，不传时服务端默认 2000 |

> ⚠️ **默认值口径差异**：底层 API 的 `flexBuilderQueryType` 不传时默认只返回 `CODE`；本 CLI 在 `--resource-type flex-builder` 下不传 `--flex-query-type` 时会显式补 `ALL`，即**默认一次拿回组件代码与数据**，调用方无需分两次请求。

## 资源类型说明

| resource-type | 类型 | 说明 |
|---------------|------|------|
| `attachment` | 附件 | 常规文件（Office文档、PDF、压缩包等） |
| `image` | 图片 | 图片资源 |
| `diagram` | 流程图 | 流程图 |
| `flowchart` | 流程图 | `diagram` 的别名 |
| `mxgraph` | 思维导图 | 脑图 |
| `flex-builder` | 随心搭 | 组件代码 + 组件内数据。**仅用于读取/导出**；新建随心搭改用 **知识库随心搭** 技能(https://console.cloud.baidu-int.com/onetool/skills/287)，修改已有随心搭（含修改组件内数据）返回文档 URL 引导用户在页面中操作，本命令不承担创建/修改能力 |

## CLI 调用示例

```bash
# 查询附件资源
$SKILL_DIR/bin/ku query-doc-resource \
  --doc-id WKoT7ltTnjU1oW \
  --resource-type attachment \
  --resource-id <attachId>

# 查询流程图
$SKILL_DIR/bin/ku query-doc-resource \
  --doc-id WKoT7ltTnjU1oW \
  --resource-type flowchart \
  --resource-id <flowchartId>

# 查询思维导图
$SKILL_DIR/bin/ku query-doc-resource \
  --doc-id WKoT7ltTnjU1oW \
  --resource-type mxgraph \
  --resource-id <mindmapId>

# 查询随心搭（默认 all：代码 + 数据一并返回）
$SKILL_DIR/bin/ku query-doc-resource \
  --doc-id WKoT7ltTnjU1oW \
  --resource-type flex-builder \
  --resource-id <flexBuilderId>

# 只看组件代码实现，不取数据
$SKILL_DIR/bin/ku query-doc-resource \
  --doc-id WKoT7ltTnjU1oW \
  --resource-type flex-builder \
  --resource-id <flexBuilderId> \
  --flex-query-type code

# 只取组件数据（已确认组件无按身份过滤的展示逻辑时才用）
$SKILL_DIR/bin/ku query-doc-resource \
  --doc-id WKoT7ltTnjU1oW \
  --resource-type flex-builder \
  --resource-id <flexBuilderId> \
  --flex-query-type kv

# 按 key 前缀过滤 + 指定单页条数
$SKILL_DIR/bin/ku query-doc-resource \
  --doc-id WKoT7ltTnjU1oW \
  --resource-type flex-builder \
  --resource-id <flexBuilderId> \
  --flex-query-type kv \
  --key-prefix vote_ \
  --limit 500

# 翻下一页：传上一页返回的 nextCursor
$SKILL_DIR/bin/ku query-doc-resource \
  --doc-id WKoT7ltTnjU1oW \
  --resource-type flex-builder \
  --resource-id <flexBuilderId> \
  --flex-query-type kv \
  --cursor 500
```

## 响应示例

```json
{
  "returnCode": 200,
  "returnMessage": "OK",
  "result": {
    "docGuid": "ya9oBE2KkXCZbT",
    "resourceId": "bee8e03122b3454c919f77492a8c3584",
    "resourceType": 3,
    "fileType": ".json",
    "fileName": "flowchart_ya9oBE2KkXCZbT_bee8e03122b3454c919f77492a8c3584",
    "contentType": "application/json; charset=utf-8",
    "contentDisposition": "attachment; filename=\"flowchart_ya9oBE2KkXCZbT_bee8e03122b3454c919f77492a8c3584.json\"",
    "downloadUrl": "https://ku-open-api-qa1.dev.weiyun.baidu.com/v1/doc/resource/download?token=..."
  },
  "traceId": "2069340796251627520",
  "status": 200,
  "msg": "OK",
  "success": true
}
```

查询随心搭数据（`flex-query-type` 为 `kv` / `all`）时，`result` 中额外带上 `total` / `cursor` / `nextCursor` / `currentCount` 分页字段；组件代码与数据本体在 `downloadUrl` 下载到的 JSON 文件里，结构见下方「随心搭资源 JSON 结构」。

## 核心响应字段

| 参数名 | 类型 | 描述 |
|--------|------|------|
| docGuid | string | 文档ID |
| resourceType | int | 资源类型 |
| resourceId | string | 资源ID |
| fileType | string | 文件类型 |
| fileName | string | 文件名称 |
| downloadUrl | string | 资源临时下载地址，有效期约 1 小时 |
| contentType | string | 下载地址的 response content type |
| contentDisposition | string | 下载地址的 response content disposition |

### 随心搭数据专有字段

仅在查询随心搭且 `flex-query-type` 为 `kv` / `all` 时返回：

| 参数名 | 类型 | 描述 |
|--------|------|------|
| total | int | 满足前缀条件的数据总条数 |
| cursor | int | 本次请求传入的游标 |
| nextCursor | int | 下一页游标；**不返回该字段表示已查完** |
| currentCount | int | 当前页实际返回的条数 |

## 随心搭资源 JSON 结构

`downloadUrl` 下载到的 JSON 分 `code`（组件代码）与 `kv`（组件数据）两部分，按 `flex-query-type` 决定哪部分存在：`code` 只有 `code` 段，`kv` 只有 `kv` 段，`all`（默认）两段都有。

```json
{
  "code": {
    "docGuid": "KrkEdcipiQCFxk",
    "builderId": "zSCIvcluOQ4eLJ",
    "content": [{
      "id": "jsx-app-demo",
      "code": "import React, { useState, useEffect } from 'react';\n...",
      "title": "投票组件",
      "type": "code/jsx",
      "size": 38869
    }]
  },
  "kv": [{
    "key": "poll_config",
    "value": {
      "title": "投票1",
      "type": "single",
      "options": ["吃饭", "密室", "逛公园"],
      "deadline": "2026-09-30T10:29",
      "allowModifyVote": true,
      "createdBy": "qinqin@baidu.com",
      "createdAt": "2026-09-01T02:29:46.827Z"
    },
    "createdBy": "wzXq-DUqOL",
    "createdAt": "2026-09-01T02:29:47.000Z",
    "updatedAt": null
  }]
}
```

### code 段字段

| 字段 | 类型 | 描述 |
|------|------|------|
| code.docGuid | string | 组件所在文档ID |
| code.builderId | string | 随心搭组件ID |
| code.content | array | 组件代码块列表 |
| code.content[].id | string | 代码块ID |
| code.content[].code | string | 源码文本，JSX 内容在这里（含 `\n` 转义） |
| code.content[].title | string | 组件名称，如"投票组件" |
| code.content[].type | string | 代码类型，如 `code/jsx` |
| code.content[].size | int | 源码字节数 |

### kv 段字段

| 字段 | 类型 | 描述 |
|------|------|------|
| kv[].key | string | 数据条目的 key，命名规则由组件代码决定 |
| kv[].value | object / string / number | 数据条目的值，可能是嵌套 JSON 对象，字段含义由组件代码决定 |
| kv[].createdBy | string | 写入者的**用户 GUID**（如 `wzXq-DUqOL`），不是邮箱、不是用户名 |
| kv[].createdAt | string | 写入时间（ISO 8601，UTC） |
| kv[].updatedAt | string / null | 最近更新时间，从未更新过时为 `null` |

> ⚠️ **`kv[].createdBy` 与 value 内的用户字段不是一回事**。`kv[].createdBy` 是平台侧的用户 GUID；组件自己写入 `value` 里的用户标识（上例中 `value.createdBy` = `qinqin@baidu.com`，投票记录里的 `voterEmail`）才是邮箱。做身份过滤、判断"谁创建的""是否本人数据"时，用组件代码实际读写的那个字段（通常来自 `Ku.getUserInfo()` 的 `email`），**不要拿 `kv[].createdBy` 的 GUID 去和邮箱比较**。

## 重要限制

`downloadUrl` 是临时地址，有效期约 1 小时。超时后该链接将无法继续下载资源，不能把它当作长期可用的附件地址保存或复用。

因此，本能力返回 `downloadUrl` 后，Agent 应在同一轮任务中立即下载并读取资源内容；如果后续处理时发现链接已过期，必须重新调用 `query-doc-resource` 获取新的下载地址，而不是继续使用旧链接。

**数据分页**：翻页判断以 `nextCursor` 是否返回为准，不要用 `currentCount < limit` 判断结束。用户要求"全部数据"时，Agent 需按 `nextCursor` 自动翻页直到 `nextCursor` 不再返回，并在输出中说明 `total` 与实际已返回条数。

## Agent 使用指南

**何时调用**：仅在用户明确要求理解某类内嵌资源时调用（如"流程图表达了什么""帮我看看这个思维导图""把图片也分析一下"）。默认阅读文档时不主动调用，保留正文中的资源占位符即可。

**资源 ID 来源**：通常从 `query-content --protocol markdown --show-resource-info=true` 返回的正文资源占位符 `[元素类型，文件类型，ID，name，desc]` 中提取；`showResourceInfo` 默认值为 false，仅在查询文档内嵌资源数据场景时设置为 true。

**下载与读取**：拿到 `downloadUrl` 后必须立即下载资源并读取内容，不要只把链接返回给用户，也不要依赖后续轮次再下载。若当前无法下载或解析，应明确告知用户资源未读取成功；若链接过期，应重新调用本能力刷新下载地址。

**输出标注**：解析资源后，回答中需明确标注来源，例如："流程图（ID=xxx）显示……"，不能与正文内容混淆。

**随心搭三路分流**：本命令仅覆盖随心搭的**读取/导出**意图（`--resource-type flex-builder`）。若用户要新建随心搭，改用 **知识库随心搭flexbuilder** 技能；若用户要修改已有随心搭（**包括修改组件内数据**），本命令不执行修改，需返回当前文档 URL 并建议用户打开页面直接修改，话术如"随心搭数据修改请在文档页面内操作：<文档链接>"。返回文档链接时优先使用用户提供的原始 URL，其次使用接口响应中的真实 `url` / `docInfo.url`，禁止根据不完整 ID 猜测拼接。

**随心搭读取意图与参数对应**：

| 用户意图（示例说法） | 参数 | 说明 |
|---|---|---|
| 读取文档全部内容 / 全文 | 默认（`all`） | 文档内随心搭一并取回代码与数据，无需用户额外指定；输出说明总条数与实际返回范围 |
| "把随心搭的数据拉出来" / "这个随心搭里存了什么" / "投票结果是什么" / "有哪些记录" / "帮我分析/导出这个组件的数据" | 默认（`all`） | 定位组件后自动翻页取全量数据，再按代码语义与当前用户身份整理输出 |
| "这个随心搭的代码是怎么写的" / 只看实现 | `--flex-query-type code` | 只返回代码，不取数据 |
| 已确认组件无身份过滤，只要数据 | `--flex-query-type kv` | 只返回数据，不返回代码 |
| "文档里有哪些组件" / 只问结构清单 | 不调用本命令 | 只用 `query-content` 给出组件数量、名称或位置，不展开组件内容 |
| 修改组件内数据 | 不调用本命令 | 返回文档链接，引导用户在页面内操作 |

**"数据"与数据表的歧义**：用户只说"数据"时，先看目标文档里有什么——只有随心搭 → 指随心搭数据；含数据表（URL 带 `tb=` / `type=dst`）→ 优先按数据表处理；两者都有且无法判断 → 向用户确认，不要默认猜。

**意图不明确时**：默认不取组件数据，先提示用户确认，例如："文档中包含 X 个随心搭组件。如需查看组件内的数据，请告诉我要看哪个组件。"

**多个随心搭组件**：文档内存在多个组件时不新增强制引导流程，按现有意图识别与组件定位方式处理；用户未指定组件时，查询文档内符合条件的全部随心搭组件并说明范围。
