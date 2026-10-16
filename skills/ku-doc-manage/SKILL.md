---
name: ku-doc-manage
description: 如流知识库（ku.baidu-int.com）是用户所在公司统一的文档与知识管理平台。用户提到“ku”、“知识库”、“wiki”、“文档”、“表格”、“数据表”，或提供含ku.baidu-int.com、https://ku.baidu-int.com/的url链接时，优先使用本技能。提供覆盖文档与数据表的增删改查、权限管理、评论/浏览记录、在线表格导入导出 Excel，以及文档正文读取、文内附件资源识别与按需导出能力。
metadata:
  security_level: L0
---

# 知识库文档与数据表管理 Skill

操作知识库文档与数据表，基于知识库 OpenAPI 官方文档开发，覆盖文档管理、权限控制、互动数据、附件与文内资源、表格导入导出、数据表管理等场景。


> 🔧 **安装配置（首次使用必读）**
> 首次使用前添加可执行权限：`chmod +x $SKILL_DIR/bin/ku`

## URL 解析与 ID 提取（必读）

### 普通文档 URL

**知识库 URL 格式**：`https://ku.baidu-int.com/knowledge/{path1}/{path2}/{path3}/{path4}`

| URL 段数 | 类型 | 文档ID | 知识库ID |
|---------|------|--------|----------|
| 4 段 path（文档页） | `https://ku.baidu-int.com/knowledge/A/B/C/D` | `D`（path4） | `C`（path3） |
| 3 段 path（知识库首页） | `https://ku.baidu-int.com/knowledge/A/B/C` | 无 | `C`（path3） |

### 数据表 URL

**数据表 URL 格式识别**：当 URL 包含 `tb=` 和 `type=dst` 参数时，表示数据表页面。

```
示例：https://ku.baidu-int.com/knowledge/A/B/C?tb=dstyEiJENZLcg8i9pC_viwAl8ytdFV2R&type=dst
```

**从 URL 提取数据表 ID 和 视图 ID**：
- `tb` 参数格式：`{dist-id}_{view-id}`
- `dist-id`（数据表 ID）：`tb` 参数中下划线前的部分
- `view-id`（视图 ID）：`tb` 参数中下划线后的部分（以 `viw` 开头）

**数据表 ID 提取示例**：
```
URL: https://ku.baidu-int.com/knowledge/A/B/C?tb=dstyEiJENZLcg8i9pC_viwAl8ytdFV2R&type=dst
dist-id: dstyEiJENZLcg8i9pC  (下划线前的部分)
view-id: viwAl8ytdFV2R  (下划线后的部分)
```

### 字段别名说明

| 字段 | 别名 |
|------|------|
| 文档ID | `doc_id` / `docId` / `doc_guid` / `docGuid` / `doc-id` |
| 知识库ID | `repo_id` / `repository_guid` / `repo_guid` / `repo-id` |

## 重要概念：文档即目录

知识库中**文档和目录是同一个概念**——任何文档都可以拥有子文档。当需要将新文档放入某个"目录"时，`parent_doc_guid` 填写该目录文档的 ID 即可。

## 资源类型识别（三层决策，按顺序执行）

### 第一层：URL 特征（最优先）

| URL 特征 | 类型 | 后续操作集 |
|---------|------|-----------|
| 含 `tb=` 且 `type=dst` 参数 | **数据表** | 字段/记录/视图管理命令 |
| 普通 4 段 path，无上述参数 | 文档或表格（继续第二层判断） | — |

### 第二层：用户意图关键词（URL 无法区分时）

| 用户描述中的关键词 | 类型判断 | 后续操作集 |
|-----------------|---------|-----------|
| 字段、记录、视图、数据表、datasheet | **数据表** | 数据表管理命令 |
| 表格、Excel、导入、导出、sheet | **表格** | `export-sheet` / `import-sheet` |
| 文档内容、编辑、评论、权限、浏览记录、关联信息、引用、被引用、删除文档、复制文档、重命名文档、改名 | **文档** | 文档管理命令 |
| 意图不明确 | 默认 **文档**，失败后降级 | 见第三层 |

### 第三层：失败降级（仅文档↔表格之间）

- 对普通 path URL 执行文档操作时，若返回不支持或文档类型错误 → 降级尝试 `export-sheet`（表格）
- **数据表不参与降级**：数据表已由第一层 URL 精确识别，不会与文档/表格混淆


## Agent 工作流程

1. **解析意图**：从用户描述中提取 URL / 文档ID / 知识库ID / 数据表ID

2. **识别资源类型**：按照 [资源类型识别](#资源类型识别) 章节的三层决策规则判断类型，
   确定后续使用文档、表格还是数据表的操作集。

2.1. **随心搭组件意图分流**（优先于通用正文编辑规则）：

   随心搭是部分知识库在线文档中存在的应用组件（`flex-builder`），组件由 JSX 代码 + 组件内数据构成。仅当用户明确提到"随心搭"或 `flex-builder`，或要求读取文档**全部内容**时，按以下规则处理；普通文档及其他正文操作不受影响。

   | 用户意图 | 处理方式 |
   |---|---|
   | 读取、查看、分析或导出随心搭 | 先用 `query-content --show-resource-info=true` 定位随心搭资源 ID，再调用 `query-doc-resource --resource-type flex-builder`。**默认一次取回代码与数据**（不传 `--flex-query-type` 即等于 `all`），按 `nextCursor` 自动翻页 |
   | 只问代码怎么写、只看实现 | 加 `--flex-query-type code`，不取数据 |
   | 已确认组件无按身份过滤逻辑、只要数据 | 加 `--flex-query-type kv`，不返回代码 |
   | 只问"文档里有哪些组件" | 只用 `query-content` 给出组件数量、名称、位置，不调用 `query-doc-resource` 展开内容 |
   | 新建、生成或插入随心搭 | 改用 **知识库随心搭** 技能(https://console.cloud.baidu-int.com/onetool/skills/287)，不使用 `create-doc` 或 `edit-mdsl-content` 代替 |
   | 修改、调整或修复已有随心搭，或修改组件内数据 | 本技能不执行修改；返回当前知识库文档的完整 URL，建议用户打开页面直接修改 |

   **读取全文时的默认行为**：用户要求"读取这篇文档的全部内容"时，文档内的随心搭默认一并取回组件代码与数据，无需用户额外指定，并在输出中说明数据总条数与实际返回范围。用户只要求读正文、了解文档结构或列组件清单时，不取组件数据。

   意图表达不明确时默认不取组件数据，先提示："文档中包含 X 个随心搭组件。如需查看组件内的数据，请告诉我要看哪个组件。"

3. **确定目标知识库**（写入操作需要）：
   - 用户提供了 URL → 从 URL 提取 repo-id
   - 未提供 → 自动调用 `ku query-user-info` 获取个人知识库

3.1. **确定目标创建路径**（创建文档时需要）：
   - 用户明确提供 `parent-doc-id`、目录路径或可唯一解析的文档 URL / 文档 ID → 按当前请求指定路径创建；如果该目录未找到，回退到个人知识库根目录下的「智能体创作空间」
   - 用户明确提到根目录，或提供知识库首页 URL（3段 path）→ `parent-doc-id` 固定为 `00000000000000`
   - 用户只指定文档标题或位置名，但未提供 URL / ID → 默认写入个人知识库根目录下的「智能体创作空间」
   - 当前会话存在最近一次明确、可唯一解析且未被否定的路径 → 优先复用该路径
   - 个人知识库根目录不存在「智能体创作空间」→ 先创建该工作区，再以其为父文档创建新文档
   - 创建完成后向用户说明文档标题、实际创建位置和链接；不要猜测位置

4. **读取 references 文档**：根据子命令读取对应的 `references/*.md`，了解参数细节和业务规则

4.1. **如流群名称解析**（`add-member` / `update-member` 涉及如流群成员时的前置步骤）：

   | 用户输入 | 处理方式 |
   |---|---|
   | 提供如流群ID（群号） | 直接作为 `memberGuid` / `username` 使用，跳过解析 |
   | 提供如流群名称（如"把XX项目群加为可读"） | 先使用 **企业搜索** 技能（enterprise-search）按群名称搜索如流群，解析出群号后，再以群号作为 `memberGuid` / `username`（`member-type=group`）调用；禁止把群名称直接当作群ID传入 |
   | 搜索无结果或命中多个群 | 向用户展示候选群（群名称+群号）确认后再执行，不得猜测或默认取第一个 |
   | 企业搜索不可用（未安装、不支持搜如流群、调用失败或超时） | 不得重试轰炸或编造群号，直接向用户说明并请其提供如流群ID（群号）；用户也可选择先安装/配置企业搜索后再试 |

   用户直接提供群ID始终是最快兜底路径；企业搜索仅是群名称的解析增强手段，不可用时不应阻塞成员管理任务，但**任何情况下都不得把群名称当作群ID传入**。详见 [add_member.md](./references/add_member.md) 与 [update_member.md](./references/update_member.md)。

5. **二次确认检查**（高风险操作）：
   以下操作在每次执行前**必须**使用 `AskUserQuestion` 工具向用户进行二次确认：

   | 操作 | 确认场景 | 风险提示 |
   |------|---------|---------|
   | `move-doc`（移动文档） | 任何移动操作 | 你正在移动文档，此操作可能打乱原有目录结构，且移动后无法自动恢复到原位置，请确认你已核对目标位置无误 |
   | `delete-doc`（删除文档） | 任何删除操作 | 你正在删除文档，请确认你已备份或不再需要该文档 |
   | `change-scope`（修改公开范围） | scope=public-read（公开可读）或 scope=public-edit（公开可编辑） | 你正在将文档设为公开，公开后公司全员可见，存在信息泄露风险，请确认文档不包含敏感信息 |
   | `create-book`（创建知识本） | create-mode=public（公开模式） | 你正在创建公开知识本，知识本及其子页面默认企业内全员可见，存在信息泄露风险，请确认不包含敏感信息 |
   | `apply-member`（申请知识库/文档权限） | 同一次请求批量申请（≥3 个文档/知识库） | 将默认向管理员发送批量申请，请先展示完整清单、申请理由与角色，待用户确认后再逐个发起，详见 [apply_member.md](./references/apply_member.md) |

   **确认提示示例**：
   ```
   AskUserQuestion(questions=[
       {
           "question": "⚠️ 您即将将文档公开设置为【公开可读】，公司内部人员均可访问此文档。此操作存在信息泄露风险，是否确定继续？",
           "header": "风险确认",
           "options": [
               {"label": "确认继续", "description": "我已了解风险，继续执行操作"},
               {"label": "取消操作", "description": "放弃此次修改"}
           ],
           "multiSelect": false
       }
   ])
   ```

6. **文档正文编辑命令选择**：

   | 用户意图关键词 | 推荐命令 | 说明 |
   |--------------|---------|------|
   | 意图不明显、未说明写入位置 | `edit-mdsl-content` + `operation.mode=append` | 默认以 Markdown 追加到文档末尾 |
   | "追加"、"添加到末尾"、"新增内容" | `edit-mdsl-content` + `operation.mode=append` | 以 Markdown 追加到文档末尾 |
   | "覆盖"、"替换全文"、"重写整篇" | `edit-mdsl-content` + `operation.mode=cover` | 全文覆盖，高风险，需确认用户明确要求 |
   | "插入到某内容前/后" | `edit-mdsl-content` + `operation.mode=insert_before/insert_after` | 局部插入，需先读取文档定位完整块 |
   | "替换/修改/删除某段、某节、某行" | `edit-mdsl-content` + `operation.mode=replace_range/delete_range` | 局部替换或删除，需先读取文档定位完整块 |

   **普通文档正文编辑只使用 `edit-mdsl-content`**：普通文档正文的追加、覆盖、插入、替换、删除都使用 `edit-mdsl-content`；mode 意图不明显时默认 `append`。**随心搭组件不属于普通正文编辑范围**，按上方"随心搭组件意图分流"处理（读→本技能，建→知识库随心搭技能，改→返回文档链接引导页面操作）。

   **正文中 @人 / @引用文档**：用户要求"@某人""提醒某人""at 一下"时，在 `markdown` 内嵌 `<mention uuap='UUAP' notify="true|false"></mention>`（`uuap` 必须用户提供，`notify` 默认 `false`）；**含 @人 的编辑发布后必须执行下方步骤 7.1 的权限校验，不可省略**。@引用知识库文档时，库域名裸链接原样写入、禁止套 `[标题](url)`。详见 [edit_content.md](./references/edit_content.md) 的「@人与@引用文档」章节。

   **正文中插入图片/附件**：必须先调用 `upload-attachment` 上传文件，再用返回的 `attachId` 等信息拼装 `markdown` 字段内容后传入 `edit-mdsl-content`，禁止编造 `attachId` 或下载地址。详见 [edit_content.md](./references/edit_content.md) 的“图片与附件资源处理”章节。

7. 🚨 **正文编辑后必须发布（强制步骤，不可省略）**：正文编辑是「编辑 + 发布」两步不可分割的原子工作流。

   - `edit-mdsl-content` 执行成功后，**必须紧接着执行一次 `publish-doc`**：`ku publish-doc --doc-id <DOC_ID> --username <USERNAME>`。
   - **任务完成判定（DoD）**：`edit-mdsl-content` 返回 `success: true` 仅代表内容已保存到编辑态、读者尚不可见，**不等于任务完成**；只有 `publish-doc` 返回 `发布完成` 或 `发布已提交…` 后才算完成，才能向用户报告成功。
   - 只编辑未发布属于**未完成状态**，不得报告成功；发布失败时需说明「内容已保存但未发布」及失败原因。
   - 发布能力细节见 [publish_doc.md](./references/publish_doc.md)。

7.1. 🚨 **@人后必须校验被 @ 用户权限（强制步骤，不可省略）**：只要本次编辑内容中出现了 `<mention>`（@人），「编辑 → 发布 → 校验被 @ 人权限」就是三步不可分割的原子工作流，缺第三步即为未完成。

   - **触发条件**：本次 `edit-mdsl-content` 的 `markdown` 里含任意 `<mention uuap='...'>`。只要 @ 了人（无论通知与否、无论一人还是多人），本步骤强制执行。
   - **执行动作**：`publish-doc` 成功后，立即对本次**所有**被 @ 的 UUAP 执行一次
     `ku query-permission --doc-id <DOC_ID> --usernames <uuap1,uuap2,...>`（逗号分隔，一次查全部）。
   - **结果处理**：逐个检查 `canRead`——
     - `canRead=true` → 无需处理。
     - `canRead=false` → **必须主动向用户说明"某某无该文档访问权限，收到提醒也打不开"，并用 `AskUserQuestion` 询问是否为其添加权限**；用户确认后才用 `add-member` 添加，未确认前不擅自添加、也不静默略过。
   - **任务完成判定（DoD）**：@人 任务只有在"已发布 + 已对所有被 @ 人查过 `query-permission` + 无权限者已询问用户并按其决定处理"全部满足后，才算完成。**跳过权限校验、或发现无权限却不询问用户直接结束，都属于未完成，不得向用户报告成功。**
   - 详见 [edit_content.md](./references/edit_content.md) 的「@人与@引用文档」章节与 [query_permission.md](./references/query_permission.md)。

8. **处理结果与智能降级**：
   - 检查响应是否包含"文档类型不支持"错误
   - 从错误消息中提取真实类型（在线表格/数据表表夹/数据表）
   - 自动调用对应的导出或数据表管理命令
   - 向用户展示关键信息（如创建成功的文档 URL / 重命名后的 `result.docInfo.url` / 数据表记录）


## 文档正文与资源理解策略

知识库文档可能包含附件、图片、流程图、脑图、随心搭等异步资源。默认使用 `query-content` 读取正文与资源占位符，不主动下载或深度解析资源；只有用户明确要求读取附件、查看图片、理解流程图/脑图、分析 Excel/PDF、全量资源总结等场景，才使用 `query-doc-resource` 按需查询资源数据。**随心搭是例外**：用户要求读取文档全部内容，或提到随心搭的"数据""内容""存了什么""结果"等表述时，随心搭默认一并取回组件代码与组件内数据，见上方"随心搭组件意图分流"。

输出时需保持来源透明：区分正文、附件、图片、流程图等不同来源；未导出解析的资源只能说明存在，不能假装已经理解其内容。详细策略见 [query_content.md](./references/query_content.md) 与 [query_doc_resource.md](./references/query_doc_resource.md)。


## CLI 子命令速查

> ⚠️ **参数写法约定（所有子命令通用，防止参数被静默丢弃）**
> - **布尔标志传值必须用等号形式**：`--process-images=true`、`--set-top=true`。禁止 `--process-images true` 这种"空格+值"写法——Go 标准 flag 包会把 `true` 当作第一个位置参数并停止解析，**其后所有参数（哪怕再传 `--md-file`）都会被静默丢弃**，导致内容丢失或创建空文档。默认值即为 `true` 的标志（如 `--process-images`）可直接省略。
> - **多行内容用 `\n` 转义**：`--content` 传多行文本时，换行写成字面 `\n`（反斜杠+n），CLI 会自动还原为真实换行。禁止在命令行参数中传真实换行（Windows 下 cmd.exe 会把真实换行当新命令处理，`\n` 之后的内容全部丢失）；多行内容较长时优先用 `--md-file` 从本地文件读取。

### 文档管理类

| 子命令 | 说明 | 必填参数 | 常用可选参数 | 详细文档 |
|--------|------|---------|------------|---------|
| `query-content` | 查询文档正文，保留文内附件资源占位符；附件资源需按用户意图另行导出理解 | `--doc-id` 或 `--url`（二选一） | `--protocol`（json/markdown/html/aihtml/mdhtml，默认markdown）、`--show-doc-info`、`--show-resource-info`（默认 false，仅查询文档内嵌资源数据时设为 true）、`--version-id`（指定版本ID） | [query_content.md](./references/query_content.md) |
| `query-repo` | 查询知识库文档列表 | `--repo-id` | `--parent-doc-id`（查子目录）、`--page-num`、`--page-size`、`--order-by`、`--show-creator`、`--show-publisher` | [query_repo.md](./references/query_repo.md) |
| `query-repo-dir` | 查询知识库目录树结构（按层级返回树状结构） | `--repo-id` 或 `--parent-doc-id`（至少其一） | `--depth`（目录深度，**默认1只查一层**；用户无明确全量意图时必须保持默认，仅明确要求"完整目录树/所有层级"时才用-1）、`--parent-doc-id`（查指定父目录子树） | [query_repo_dir.md](./references/query_repo_dir.md) |
| `create-doc` | 创建文档 | 无（默认写入个人知识库） | `--repo-id`、`--username`、`--title`、`--content`、`--md-file`（从本地文件读取）、`--parent-doc-id`、`--create-mode`（empty/content默认/copy）、`--template-doc-id`（mode=copy时必填）、`--set-top`、`--process-images`（默认true）、`--base-dir` | [create_doc.md](./references/create_doc.md) |
| `create-book` | 创建知识本（目录型文档） | `--repo-id` | `--title`（默认"未命名知识本"，重名自动递增编号）、`--create-mode`（inherit权限继承默认/public公开/private保密）、`--parent-doc-id`（默认知识库根目录）、`--username`、`--set-top` | [create_book.md](./references/create_book.md) |
| `edit-mdsl-content` | 基于 Markdown 编辑文档正文，支持追加、覆盖、插入、替换、删除 | `--doc-id`、`--username`、`--operation` | `--operation` JSON 包含 `mode`、`markdown`、`selectionWithEllipsis`、`selectionByTitle` | [edit_content.md](./references/edit_content.md) |
| `publish-doc` | 发布文档 | `--doc-id`、`--username` | — | [publish_doc.md](./references/publish_doc.md) |
| `copy-doc` | 复制文档 | `--doc-id` | `--target-repo-id`（目标知识库）、`--parent-doc-id`（目标目录）、`--new-title` | [copy_doc.md](./references/copy_doc.md) |
| `rename-doc` | 重命名文档 | `--doc-id`、`--new-name`、`--username` | — | [rename_doc.md](./references/rename_doc.md) |
| `move-doc` | 移动文档 | `--doc-id`、`--target-repo-id`、`--username`（默认当前用户） | `--parent-doc-id`（目标父目录）、`--adjacent-doc-id`（目标相邻文档）、`--upper`（是否移动到上方） | [move_doc.md](./references/move_doc.md) |
| `delete-doc` | 删除文档 | `--doc-id`、`--username`（默认当前用户） | — | [delete_doc.md](./references/delete_doc.md) |
| `query-version` | 查询文档历史版本列表 | `--doc-id` 或 `--url`（二选一） | `--page-num`、`--page-size` | [query_version.md](./references/query_version.md) |

### 权限管理类

| 子命令 | 说明 | 必填参数 | 常用可选参数 | 详细文档 |
|--------|------|---------|------------|---------|
| `query-permission` | 查询用户对文档的权限 | `--doc-id` + `--usernames`（逗号分隔） | — | [query_permission.md](./references/query_permission.md) |
| `add-member` | 添加文档成员（支持用户/如流群混合；如流群传群名称时需先经企业搜索解析为群号） | `--doc-id` + `--member-list`（JSON数组，元素为`{"memberType":"user"或"group","memberGuid":"..."}`） | `--role`（DocReader只读默认/DocMember可编辑/DocAdmin管理员，如流群不可设为DocAdmin） | [add_member.md](./references/add_member.md) |
| `update-member` | 更新成员角色（如流群传群名称时需先经企业搜索解析为群号） | `--doc-id` + `--username` + `--role` | `--member-type`（user用户默认/group如流群） | [update_member.md](./references/update_member.md) |
| `change-scope` | 修改文档公开范围 | `--doc-id` + `--scope`（public-read/public-edit/private） | — | [change_scope.md](./references/change_scope.md) |
| `query-apply-member` | 查询知识库/文档权限申请列表 | `--repo-id` 或 `--doc-id`（二选一，doc-id优先） + `--apply-role-name` | — | [query_apply_member.md](./references/query_apply_member.md) |
| `apply-member` | 申请知识库/文档权限 | `--doc-id` 或 `--repo-id`（二选一，doc-id优先） + `--target-username` + `--apply-role-name` | `--apply-message`（申请原因，不超过200字符） | [apply_member.md](./references/apply_member.md) |

### 互动数据 & 用户信息类

| 子命令 | 说明 | 必填参数 | 常用可选参数 | 详细文档 |
|--------|------|---------|------------|---------|
| `query-comments` | 查询文档评论（含批注） | `--doc-id` | `--page-num`、`--page-size`、`--no-bottom`（跳过底部评论）、`--no-side`（跳过划线评论） | [query_comments.md](./references/query_comments.md) |
| `create-comment` | 创建文档评论/批注 | `--doc-id`、`--username`、`--text`（或 `--content`） | `--comment-type`（side/划线评论默认/bottom/bottom-reply/side-reply）、`--reply-comment-guid`、`--root-comment-guid`、`--quote-text`（划线引用文本）、`--room-type` | [create_comment.md](./references/create_comment.md) |
| `query-recent-view` | 查询文档浏览记录 | `--doc-id` | `--begin-time`（毫秒时间戳）、`--end-time`、`--page-num`、`--page-size` | [query_recent_view.md](./references/query_recent_view.md) |
| `query-relation` | 分页查询文档关联信息（业务关联/引用/被引用/共创/读取） | `--doc-id` + `--type`（link/reference/referenced/co_create/read） | `--business-type`（仅type=link有效：icafe/meeting/gitcase/iapi/purch）、`--page-num`、`--page-size`（最大50） | [query_relation.md](./references/query_relation.md) |
| `query-recent-doc` | 查询我最近浏览/编辑的文档 | `--action`（recent-view=最近浏览，recent-edit=最近编辑） | `--begin-time`（毫秒时间戳）、`--end-time`、`--page-num`、`--page-size`（最大20） | [query_recent_doc.md](./references/query_recent_doc.md) |
| `query-user-info` | 查询用户信息（含个人知识库ID） | 无 | `--username`（不传则读取环境变量当前用户） | [query_user_info.md](./references/query_user_info.md) |

### 附件与资源类

| 子命令 | 说明 | 必填参数 | 常用可选参数 | 详细文档 |
|--------|------|---------|------------|---------|
| `query-doc-resource` | 按需查询文档内嵌资源数据；仅在用户明确要求解析附件、图片、流程图、脑图、随心搭等资源时使用 | `--doc-id`、`--resource-type`、`--resource-id` | `--resource-type` 可选值：`attachment`（附件）、`image`（图片）、`diagram`/`flowchart`（流程图，两者等价）、`mxgraph`（思维导图/脑图）、`flex-builder`（随心搭）；随心搭专用：`--flex-query-type`（`code`/`kv`/`all`，**不传默认 `all`**，同时取回代码与数据）、`--key-prefix`（按数据 key 前缀过滤）、`--cursor`（翻页游标，传上页 `nextCursor`）、`--limit`（单页条数 1-20000，默认 2000） | [query_doc_resource.md](./references/query_doc_resource.md) |

## 表格操作说明

> ✅ **表格编辑支持方式**：本 SKILL 支持通过“导出 Excel → Agent 编辑 Excel → 导入 Excel”的流程完成在线表格内容读取、创建或更新。
>
> 🚫 **禁止操作**：涉及在线表格的需求，Agent **不得使用 Browser Use、Playwright、MCP 浏览器、打开网页等浏览器方式**访问或操作表格。

**可用能力**：
- `export-sheet`：导出在线表格为 Excel 文件
- `import-sheet`：导入 Excel 文件为在线表格

**处理原则**：
- 只要用户需求涉及在线表格，必须优先且只能使用本 SKILL 提供的表格能力处理。
- 如果 `export-sheet` / `import-sheet` 无法满足用户需求，直接告知用户当前不支持该表格操作，不要改用浏览器方式尝试。

**用户意图识别与处理**：

| 用户需求 | Agent 处理方式 |
|---------|--------------|
| **读取表格内容** / 查看表格数据 / 获取表格数据 | 直接执行 `export-sheet` 导出为 Excel，使用读取工具分析内容 |
| **编辑表格内容** / 修改表格数据 | 直接执行：`export-sheet` 导出 → Agent 编辑 Excel → `import-sheet` 导入；如该流程无法满足，直接说明不支持 |
| **创建新表格** | 直接创建 Excel 文件，然后 `import-sheet` 导入 |
| **其他在线表格操作** | 若无法通过 `export-sheet` / `import-sheet` 完成，直接说明不支持，禁止使用浏览器操作 |

### 表格导入导出类

| 子命令 | 说明 | 必填参数 | 常用可选参数 | 详细文档 |
|--------|------|---------|------------|---------|
| `export-sheet` | 导出在线表格为 Excel（用于读取内容） | `--doc-id` 或 `--url`（二选一） | — | [export_sheet.md](./references/export_sheet.md) |
| `import-sheet` | 导入 Excel 为在线表格（用于创建/更新表格） | `--repo-id` + `--file` | `--parent-doc-id`（目标目录）、`--title`（表格名称） | [import_sheet.md](./references/import_sheet.md) |

## 数据表管理说明

数据表（Datasheet）是知识库提供的在线表格功能，支持字段管理、记录管理、视图管理等完整能力。

### 数据表字段管理类

| 子命令 | 说明 | 必填参数 | 常用可选参数 | 详细文档 |
|--------|------|---------|------------|---------|
| `get-datasheet-fields` | 获取数据表字段列表 | `--dist-id` | — | [get_datasheet_fields.md](./references/get_datasheet_fields.md) |
| `add-datasheet-field` | 添加数据表字段 | `--dist-id`、`--type`、`--name` | `--property`（字段属性 JSON） | [add_datasheet_field.md](./references/add_datasheet_field.md) |
| `del-datasheet-field` | 删除数据表字段 | `--dist-id`、`--field-id` | — | [del_datasheet_field.md](./references/del_datasheet_field.md) |

### 数据表记录管理类

| 子命令 | 说明 | 必填参数 | 常用可选参数 | 详细文档 |
|--------|------|---------|------------|---------|
| `get-datasheet-records` | 获取数据表记录（支持分页、筛选、排序） | `--dist-id` | `--view-id`、`--page-num`、`--page-size`、`--max-records`、`--record-ids`、`--filter`、`--sort`、`--fields` | [get_datasheet_records.md](./references/get_datasheet_records.md) |
| `add-datasheet-records` | 添加数据表记录（支持批量） | `--dist-id`、`--view-id`、`--records` | — | [add_datasheet_record.md](./references/add_datasheet_record.md) |
| `update-datasheet-records` | 更新数据表记录（支持批量） | `--dist-id`、`--view-id`、`--records` | — | [update_datasheet_record.md](./references/update_datasheet_record.md) |
| `upload-datasheet-attachment` | 上传文件到数据表附件存储，返回可写入附件字段的附件参数 | `--dist-id`、`--file` | — | [upload_datasheet_attachment.md](./references/upload_datasheet_attachment.md) |
| `delete-datasheet-records` | 删除数据表记录（支持批量，最多10条） | `--dist-id`、`--record-ids` | — | [delete_datasheet_record.md](./references/delete_datasheet_record.md) |

**数据表附件字段写入流程**：需要向数据表附件字段写入文件时，先使用 `upload-datasheet-attachment` 上传单个不超过 5MB 的文件，获取 `id`、`name`、`size`、`mimeType`、`token`、`url` 等附件参数，再参考 [add_datasheet_record.md](./references/add_datasheet_record.md) 或 [update_datasheet_record.md](./references/update_datasheet_record.md) 调用 `add-datasheet-records` / `update-datasheet-records`，将附件参数写入目标记录的附件字段。接口按文件内容哈希去重，重复上传相同内容会复用已生成的附件属性。

### 数据表视图与创建类

| 子命令 | 说明 | 必填参数 | 常用可选参数 | 详细文档 |
|--------|------|---------|------------|---------|
| `get-datasheet-views` | 获取数据表视图列表 | `--dist-id` | — | [get_datasheet_views.md](./references/get_datasheet_views.md) |
| `get-datasheet-children` | 查询数据表表夹下的子表（数据表/仪表盘，分页） | `--doc-id`（数据表URL中的文档ID，即表夹） | `--page-num`、`--page-size`（最大100） | [get_datasheet_children.md](./references/get_datasheet_children.md) |
| `create-datasheet` | 在数据表夹下创建新数据表 | `--doc-id`（数据表URL中的文档ID） | `--username`、`--name` | [create_datasheet.md](./references/create_datasheet.md) |

## 认证说明

CLI 工具默认使用自动降级模式（个人身份认证 → 数字员工身份认证），无需额外配置。

**环境变量要求**：必须设置 `SANDBOX_USERNAME` 或 `BAIDU_CC_USERNAME`（用于确定当前用户身份和 token 文件路径）。

```bash
$SKILL_DIR/bin/ku query-content --doc-id WKoT7ltTnjU1oW
```

## 错误处理

| 错误 | 处理策略 |
|------|---------|
| 参数缺失 / ID 格式错误 | 自行修正后重试 |
| 401 / 403 认证失败 | 提示用户重新触发 ugate-auth 认证流程，勿重试 |
| 404 文档不存在 | 告知用户文档可能已被删除，勿重试 |
| 无操作权限 | 告知用户联系知识库管理员，勿重试 |
| 60412 无权限访问知识库 | 检查参数 `repository-guid` 是否有误；确认后向用户询问是否需要申请该知识库的只读/编辑/管理员权限，用户确认后按 [apply_member.md](./references/apply_member.md) 发起申请 |
| 60414 无权限访问文档 | 检查参数 `doc-id` 是否有误；确认后向用户询问是否需要申请该文档的只读/编辑/管理员权限，用户确认后按 [apply_member.md](./references/apply_member.md) 发起申请 |
| 601 无权限访问数据表 | 检查参数 `dist-id` 是否有误；确认后向用户询问是否需要申请该文档的只读/编辑/管理员权限，用户确认后按 [apply_member.md](./references/apply_member.md) 发起申请 |
| 60421 用户无权限创建文档 | 告知用户需要在对应知识库中有【成员】或【管理员】权限，询问是否更换用户或申请相应知识库权限，用户确认后按 [apply_member.md](./references/apply_member.md) 发起申请 |
| 5xx 服务端错误 | 告知用户稍后再试，勿重试 |

## API 详细文档索引

查看 [references/API_INDEX.md](./references/API_INDEX.md) 获取完整 API 列表。每个子命令的详细参数、响应格式、业务规则均在 `references/` 目录对应文件中。