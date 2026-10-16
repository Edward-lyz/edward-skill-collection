# 编辑文档正文

> 🚨 **正文编辑是「编辑 + 发布」两步不可分割的原子工作流**：`edit-mdsl-content` 只把内容保存到编辑态，**必须紧接着执行 `publish-doc`** 才能让内容对读者生效。**未发布视为任务未完成**，不得在未发布时向用户报告编辑成功。详见文末「编辑后发布」与「任务完成判定」。

> `append` / `cover` 不需要提前读取文档；`insert_before` / `insert_after` / `replace_range` / `delete_range` 等需要定位目标块的局部操作，必须先执行 `ku query-content --doc-id <DOC_ID> --protocol mdhtml` 获取文档内容。

## ⚠️ 能力边界

`edit-mdsl-content` **只用于编辑普通 Markdown 正文**，不承担以下能力：

- **不能创建或修改随心搭**（`flex-builder`）组件。随心搭虽可在正文中被识别，但本命令不会渲染或改动其 JSX：新建随心搭改用 **知识库随心搭** 技能(https://console.cloud.baidu-int.com/onetool/skills/287)；修改已有随心搭需返回当前文档完整 URL，建议用户打开页面直接修改（返回 URL 时优先使用用户提供的原始 URL，其次使用接口响应的真实 `url` / `docInfo.url`，禁止猜测拼接）。
- **不能创建思维导图等其他富格式组件**，这些组件由知识库前端专用编辑器生成。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `doc-id` | string | 是 | 文档 ID |
| `username` | string | 是 | 编辑者用户名（UUAP 格式，即邮箱前缀） |
| `operation` | object | 是 | Markdown编辑操作 |

## operation 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `mode` | string | 是 | 操作模式：`append` / `cover` / `insert_before` / `insert_after` / `replace_range` / `delete_range`。用户未明确表达模式意图时默认使用 `append` |
| `markdown` | string | 条件必填 | 要追加、覆盖、插入或替换的内容；支持纯 Markdown、纯 HTML，也支持 Markdown 中嵌入 HTML 的混合格式；`delete_range` 不需要 |
| `selectionWithEllipsis` | string | 条件必填 | 按内容定位。局部编辑时与 `selectionByTitle` 二选一 |
| `selectionByTitle` | string | 条件必填 | 按标题定位整节。局部编辑时与 `selectionWithEllipsis` 二选一 |

## 操作模式

| mode | 说明 | 是否需要定位 |
|------|------|--------------|
| `append` | 在文档末尾追加内容 | 否 |
| `cover` | 覆盖全文 | 否 |
| `insert_before` | 在定位块前插入内容 | 是 |
| `insert_after` | 在定位块后插入内容 | 是 |
| `replace_range` | 替换定位块或定位章节 | 是 |
| `delete_range` | 删除定位块或定位章节 | 是 |

## 调用示例

> 以下每个编辑示例都成对给出 `edit-mdsl-content` 与 `publish-doc` 两条命令，**必须按顺序执行两条**，缺一不可。

### 读取文档内容

```bash
ku query-content --doc-id <DOC_ID> --protocol mdhtml
```

### 追加内容

```bash
ku edit-mdsl-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --operation '{"mode":"append","markdown":"## 新增章节\n\n新增内容"}'

ku publish-doc --doc-id <DOC_ID> --username <USERNAME>
```

### 覆盖全文

```bash
ku edit-mdsl-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --operation '{"mode":"cover","markdown":"# 新标题\n\n新正文"}'

ku publish-doc --doc-id <DOC_ID> --username <USERNAME>
```

### 段落替换

需求：把“200ms”改成“50ms”。必须定位并替换完整段落。

```bash
ku edit-mdsl-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --operation '{"mode":"replace_range","selectionWithEllipsis":"模块初始化流程目前依赖配置文件 A，加载耗时约 200ms。","markdown":"模块初始化流程目前依赖配置文件 A，加载耗时约 50ms。"}'

ku publish-doc --doc-id <DOC_ID> --username <USERNAME>
```

### 在目标块后插入内容

```bash
ku edit-mdsl-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --operation '{"mode":"insert_after","selectionWithEllipsis":"这是定位文本","markdown":"插入的新内容"}'

ku publish-doc --doc-id <DOC_ID> --username <USERNAME>
```

### 删除指定章节

```bash
ku edit-mdsl-content \
  --doc-id <DOC_ID> \
  --username <USERNAME> \
  --operation '{"mode":"delete_range","selectionByTitle":"## 要删除的章节"}'

ku publish-doc --doc-id <DOC_ID> --username <USERNAME>
```

## 文档格式说明

原文档为 Markdown + HTML 混合格式，常见元素：

| 类型 | 示例 |
|------|------|
| Markdown | 标题、段落、列表、引用、代码块、链接、图片、加粗、斜体、Markdown 表格 |
| HTML 表格 | `<table><tr><td>…</td></tr></table>` |
| 高亮块 | `<callout><p>…</p></callout>` |
| 布局容器 | `<block>` / `<timeline>`，内部常有 `<cell><p>…</p></cell>` |
| 富格式 | @人、文档预览、外链预览、统计、目录、三方嵌入等（@人与@引用文档写法见"@人与@引用文档"；**随心搭可识别，但不能通过本命令创建或修改**，见"能力边界"） |

## 图片与附件资源处理

正文中需要插入图片或附件时，必须先调用 `upload-attachment` 上传资源，再用返回结果拼装 `markdown` 字段对应的内容片段。禁止直接编造 `attachId`/下载地址。

### 处理步骤

1. 调用 `ku upload-attachment --doc-id <DOC_ID> --file <本地文件路径>` 上传文件。
2. 从响应 `result` 中取出 `attachId`、`name`、`extension`、`size` 等字段。
3. 按下方对应格式拼装内容片段，作为 `markdown` 字段的值（或其中一部分）传入 `edit-mdsl-content`。

### 图片

图片以标准 Markdown 图片语法插入，`![]()` 括号内为下载地址，格式固定为：

```
https://rte.weiyun.baidu.com/wiki/attach/image/api/imageDownloadAddress?attachId=<attachId>&docGuid=<DOC_ID>
```

示例（上传返回 `attachId=82eb0bf9757c425ba5cbcfc3e602f78c`，文档 ID 为 `yqT4a4gxjigl1w`）：

```markdown
![马年吉祥](https://rte.weiyun.baidu.com/wiki/attach/image/api/imageDownloadAddress?attachId=82eb0bf9757c425ba5cbcfc3e602f78c&docGuid=yqT4a4gxjigl1w)
```

### 附件

附件以 `<attachment>` HTML 标签插入（嵌入在 Markdown 中的 HTML），字段来自上传响应：

| 标签属性 | 取值来源 |
|---------|---------|
| `fileId` | `result.attachId` |
| `filename` | `result.name` |
| `size` | `result.size` |
| `type` | 根据 `result.extension` 推断的 MIME 类型 |
| `extension` | `result.extension` |
| `view` | 固定为 `card` |
| `invalid` | 固定为 `false` |
| `docId` | 当前文档 ID |
| `data-id` | 留空或由系统生成，可不填 |
| `url` | 固定为空字符串 `""` |

示例（上传返回 `attachId=f49c39d17cc24d34ae3fef0ebf295fe3`，`name=report.xlsx`，`size=3764`，文档 ID 为 `eQgfKSA7NwuXSl`）：

```html
<attachment fileId="f49c39d17cc24d34ae3fef0ebf295fe3" filename="report.xlsx" size="3764" type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" extension="xlsx" view="card" invalid="false" docId="eQgfKSA7NwuXSl" url="" />
```

拼好的片段可直接用于 `append`/`cover` 的 `markdown` 字段，或与其它内容组合后用于 `insert_before`/`insert_after`/`replace_range`。

## @人与@引用文档

正文支持在 `markdown` 内嵌入两类特殊内容：@人（提醒某人）与 @引用文档（插入知识库文档链接）。两者都直接写进 `markdown` 字段，无需额外参数。

### @人

用 `<mention>` 标签表示，嵌在 `markdown` 文本中：

```
<mention uuap='UUAP' notify="true"></mention>
```

| 属性 | 必填 | 说明 |
|------|------|------|
| `uuap` | 是 | 被 @ 用户的 UUAP（邮箱前缀），**必须由用户提供**，禁止猜测或编造 |
| `notify` | 是 | 是否给该用户发送通知：`true`=通知，`false`=不通知。**默认 `false`（不通知）**，仅当用户明确要求通知某人时才置 `true` |

- **支持同时 @ 多人**：多个 `<mention>` 标签连写即可；也支持只 @ 单人。
- 每个被 @ 的用户可单独设置 `notify`，互不影响。

> 🚨 **@人 是「编辑 → 发布 → 校验权限」三步原子操作，缺一不可。**
> 只要 `markdown` 里出现了 `<mention>`，就**必须**在发布后执行下面「@人后必须校验被 @ 用户权限」的流程。跳过校验、或发现无权限却不询问用户，都算任务未完成，不得报告成功。下面每个示例的**第 3 步就是校验，不是可选项**。

**单人示例**（编辑 → 发布 → 校验权限，三步都要执行）：

```bash
# 1) 编辑：在正文追加 @人
ku edit-mdsl-content \
  --doc-id U-5jOyn_1YU5HX \
  --username qinqin \
  --operation '{"mode":"append","markdown":"请 <mention uuap=\"weimin03\" notify=\"true\"></mention> 关注此事"}'

# 2) 发布
ku publish-doc --doc-id U-5jOyn_1YU5HX --username qinqin

# 3) 【强制】校验被 @ 人权限，canRead=false 时询问用户是否加权限
ku query-permission --doc-id U-5jOyn_1YU5HX --usernames weimin03
```

**多人示例**（同时 @ 三人，其中两人通知、一人不通知；同样三步都要执行）：

```bash
# 1) 编辑：一次 @ 多人
ku edit-mdsl-content \
  --doc-id U-5jOyn_1YU5HX \
  --username qinqin \
  --operation '{"mode":"append","markdown":"这里是@多人测试哈：<mention uuap=\"v_shenjiayi02\" notify=\"true\"></mention><mention uuap=\"weimin03\" notify=\"false\"></mention><mention uuap=\"qinqin100\" notify=\"true\"></mention>"}'

# 2) 发布
ku publish-doc --doc-id U-5jOyn_1YU5HX --username qinqin

# 3) 【强制】一次性校验所有被 @ 人权限（逗号分隔），对 canRead=false 的人逐个询问用户
ku query-permission --doc-id U-5jOyn_1YU5HX --usernames v_shenjiayi02,weimin03,qinqin100
```

#### @人后必须校验被 @ 用户权限（强制，不可省略）

⚠️ **此步骤在实际使用中最容易被漏掉，务必执行。** 被 @ 的人如果没有文档访问权限，收到提醒也打不开文档，@ 等于无效。因此**只要本次编辑含 `<mention>`，发布后必须校验权限**：

1. 完成 `edit-mdsl-content` + `publish-doc`。
2. 对本次**所有**被 @ 的 UUAP 执行一次 `ku query-permission --doc-id <DOC_ID> --usernames <uuap1,uuap2,...>`（逗号分隔，一次查全，不要漏人）。
3. 逐个检查每个用户的 `canRead`：
   - `canRead=true` → 无需处理。
   - `canRead=false`（无权限）→ **必须主动告知用户"某某无该文档访问权限"，并用 `AskUserQuestion` 询问是否为其添加权限**；用户确认后再用 `add-member` 添加（详见 [add_member.md](./add_member.md)），未确认前不擅自添加，也不得静默跳过。

**完成判定（DoD）**：@人 任务只有在「已发布 + 已对所有被 @ 人查过 `query-permission` + 无权限者已询问用户并按其决定处理」全部满足后才算完成。只 @ 不校验、或查到无权限却不问用户直接结束，都属于**未完成**，不得报告成功。


### @引用文档

用户要求引用/插入某篇知识库文档时，用户会提供该文档的**完整链接或短链接**。

- **库域名（`https://ku.baidu-int.com`）开头的超链接：直接保留链接本身，写进 `markdown` 原样输出，禁止转成标准 Markdown 链接格式 `[标题](url)`**。知识库会自动把裸链接渲染为文档引用卡片；套上 `[]()` 反而无法识别为文档引用。
- 非库域名的普通外链（如第三方网站）按常规处理即可。

**示例**（引用一篇知识库文档，保留裸链接）：

```bash
ku edit-mdsl-content \
  --doc-id U-5jOyn_1YU5HX \
  --username qinqin \
  --operation '{"mode":"append","markdown":"QQ测试-知识库：https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/t7n0qKWNJW/AtKECXn-wv/"}'

ku publish-doc --doc-id U-5jOyn_1YU5HX --username qinqin
```

## 流程图（draw.io）支持

当用户要求插入流程图时，**默认使用 draw.io（XML）格式**；仅当用户明确要求 mermaid 时才使用 mermaid 格式。

### 插入格式

支持两种语法：

**HTML 格式（推荐）** — `<diagram>` 标签包裹完整 mxGraphModel XML：

```html
<diagram>
<mxGraphModel dx="1000" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
<root>
<mxCell id="0"/>
<mxCell id="1" parent="0"/>
<mxCell id="2" value="开始" style="ellipse;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1"><mxGeometry x="400" y="50" width="120" height="60" as="geometry"/></mxCell>
<mxCell id="3" value="审核" style="rhombus;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1"><mxGeometry x="380" y="200" width="160" height="80" as="geometry"/></mxCell>
<mxCell id="10" value="通过" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;" edge="1" parent="1" source="2" target="3"><mxGeometry relative="1" as="geometry"/></mxCell>
</root>
</mxGraphModel>
</diagram>
```

**Markdown 格式** — ` ```mxGraph ` 代码块包裹 mxGraphModel XML：

````markdown
```mxGraph
<mxGraphModel dx="600" dy="400" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827"><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" value="开始" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1"><mxGeometry x="100" y="100" width="120" height="60" as="geometry"/></mxCell><mxCell id="3" value="结束" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1"><mxGeometry x="350" y="100" width="120" height="60" as="geometry"/></mxCell></root></mxGraphModel>
```
````

### 硬性约束

1. 必须输出完整骨架：`<mxGraphModel>` → `<root>` → `id="0"` 和 `id="1"` 两个基础 mxCell，所有图元 `parent` 指向 `1`。
2. HTML 格式下 `<diagram>`、`<mxGraphModel ...>`、`</mxGraphModel>`、`</diagram>` 各占独立一行，**标签之间必须有换行**；严禁写成 `<diagram><mxGraphModel` 或 `</mxGraphModel></diagram>` 这类同行紧贴形式，否则无法渲染。
3. XML 内禁止空行，标签必须闭合；节点 id 全局唯一；连线 `source`/`target` 必须命中已有节点 id。
4. 节点文字换行用 `&#10;`；坐标必须显式给出（起始 `x=400,y=50`，纵向间距 150–200px）。
5. `<diagram>` 是顶层块级元素，**不可嵌入** `td`、`callout`、`column`/`timeline` 的 `cell`。

### 修改已有流程图

落库后正文只保留 `<diagram dataid="..."></diagram>` 空标签。修改前必须先用 `query-content` 取回完整 XML，在其基础上改动后整体回写。禁止凭空重造 XML 覆盖。

## MDSL 定位规则

### selectionWithEllipsis（按内容定位）

1. 精确定位：填写完整文本，适合短文本、单行内容。
2. 省略定位：`首部10-20字...尾部10-20字`，用于较长文本块，首尾需能唯一定位目标。
3. 内容本身包含 `...` 时，用 `\.\.\.` 表示字面量。
4. 定位对象必须是完整块/行；定位串必须唯一，不唯一时扩展上下文。

### selectionByTitle（按标题定位）

格式：`## 章节标题`（可带或不带 `#` 前缀）。

自动定位整个章节（从该标题到下一个同级或更高级标题之前）。

示例：
- `## 功能说明` → 定位二级标题“功能说明”及其下所有内容
- `功能说明` → 定位任意级别的“功能说明”标题及其内容

约束：替换时 `markdown` 字段必须包含标题本身，而不是只写新内容。

适用场景：替换或删除整节内容时使用。

## MDSL 安全约束

1. 定位以块为单位：块 = 段落、标题、列表项、代码块、完整 `<tr>`、`<td>`、`<cell>`。禁止定位块内局部文本；即使只改一个词，也要定位整个块，`markdown` 输出修改后的完整块。
2. 插入只能在完整块前后：不支持在单个 `<td>` 或 `<cell>` 前后插入。表格新增行时，在完整 `<tr>` 前后插入。
3. 删除以完整块为单位：不支持单独删除 `<td>` 或 `<cell>`，否则可能导致结构错乱。
4. 替换前后标签一致：`<tr>` 替换为 `<tr>`，`<td>` 替换为 `<td>`，`<cell>` 替换为 `<cell>`。替换 `<tr>` 时新旧行的 `<td>` 数量应一致。
5. Markdown 支持范围：标准 Markdown 和部分 HTML（`<p>` / `<h1>`~`<h6>` / `<table>` / `<tr>` / `<td>`）。

## 表格修改速查

| 需求 | 推荐做法 | 避免做法 |
|------|----------|----------|
| 末尾加行 | `insert_after` 定位最后一个 `<tr>` | 替换整表 |
| 某行前后插行 | `insert_before` / `insert_after` 定位目标 `<tr>` | 定位 `<td>` 插入 |
| 删除某行 | `delete_range` 定位完整 `<tr>` | 删除单个 `<td>` |
| 修改单元格 | `replace_range` 定位完整 `<td>` | 只替换单元格内文本 |
| 修改一行多个值 | `replace_range` 定位完整 `<tr>` | 替换整表 |
| 替换整表 | 仅用户明确要求时替换完整 `<table>` | 默认整表替换 |

## 决策流程

1. 判断 mode 意图：意图不明显时默认 `append`；明确要求覆盖、插入、替换、删除时选择对应 mode。
2. 判断范围：段落 / 标题 / 列表项 / 整节 / 表格单元格 / 表格行 / 整表 / 容器块。
3. 选择定位方式：整节用 `selectionByTitle`，其它用 `selectionWithEllipsis`。
4. 选择最小安全块。
5. 检查操作限制。
6. 无法定位或执行：输出 `# ERROR: <原因>`。


## 响应示例

```json
{
  "returnCode": 200,
  "returnMessage": "OK",
  "result": {
    "docGuid": "WSuIrx09hfg6zr",
    "success": true
  },
  "traceId": "694507417572758528",
  "status": 200,
  "msg": "OK",
  "success": true
}
```

## 编辑后发布

- `edit-mdsl-content` 执行成功后，**必须紧接着执行一次 `publish-doc`**，这是正文编辑工作流不可省略的第二步。
- 发布命令：`ku publish-doc --doc-id <DOC_ID> --username <USERNAME>`，能力细节见 [publish_doc.md](./publish_doc.md)。
- 若发布结果返回 `发布完成` 或 `发布已提交，将在约30秒内执行发布，预计于 HH:mm:ss 执行`，视为发布流程已处理完成。

## 任务完成判定（DoD）

正文编辑任务是否完成，以发布结果为准，**不以编辑结果为准**：

- `edit-mdsl-content` 返回 `success: true` **仅代表内容已保存到编辑态**，读者尚不可见，**不等于任务完成**。
- 只有在 `publish-doc` 返回 `发布完成` 或 `发布已提交…` 后，才算任务完成，才能向用户报告成功。
- 若只执行了编辑而未发布，属于**未完成状态**：不得报告成功，需补发 `publish-doc`。
- 若发布失败，需向用户说明「内容已保存但未发布」，并给出发布失败原因。

## 输出规范

- 仅输出 CLI 指令，不要解释、寒暄
- `doc-id` 未提供时用 `<DOC_ID>` 占位
- 无法执行时输出：`# ERROR: <原因>`
- 多步操作输出多条指令，指令之间空行分隔

## 常见错误处理

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| 定位失败（不唯一） | `selectionWithEllipsis` 匹配到多个位置 | 扩展上下文，包含更多前后文字 |
| 定位失败（不存在） | 原文已变化或定位串有误 | 重新 `query-content --protocol mdhtml` 获取最新内容 |
| 替换后结构错乱 | 标签不一致 | 确保 `<tr>` 替换为 `<tr>`，`<td>` 替换为 `<td>` |
| 插入位置错误 | 定位了 `<td>` 或 `<cell>` 内部 | 改为定位完整 `<tr>` 或外层块 |
| 缺少 markdown | 非 `delete_range` 模式必须提供 `markdown` | 补充 `markdown` 字段 |
| 缺少定位字段 | 局部编辑必须提供 `selectionWithEllipsis` 或 `selectionByTitle` | 先读取文档并补充定位字段 |
