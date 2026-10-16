# 知识库 API 索引

本文档提供所有知识库 API 的快速索引和使用指南。

## 📋 API分类概览

### 文档管理类 (11个)
| API | 功能 | 文档 |
|-----|------|------|
| query_content | 查询文档内容 | [详细文档](./query_content.md) |
| query_repo | 查询知识库文档列表 | [详细文档](./query_repo.md) |
| query_repo_dir | 查询知识库目录树结构 | [详细文档](./query_repo_dir.md) |
| create_doc | 创建新文档 | [详细文档](./create_doc.md) |
| create_book | 创建知识本 | [详细文档](./create_book.md) |
| edit_mdsl_content | 基于 Markdown/MDSL 编辑文档正文 | [详细文档](./edit_content.md) |
| publish_doc | 发布文档 | [详细文档](./publish_doc.md) |
| copy_doc | 复制文档 | [详细文档](./copy_doc.md) |
| rename_doc | 重命名文档 | [详细文档](./rename_doc.md) |
| move_doc | 移动文档 | [详细文档](./move_doc.md) |
| delete_doc | 删除文档 | [详细文档](./delete_doc.md) |
| query_version | 查询文档历史版本列表 | [详细文档](./query_version.md) |

### 权限管理类 (6个)
| API | 功能 | 文档 |
|-----|------|------|
| query_permission | 查询用户对文档的权限 | [详细文档](./query_permission.md) |
| add_member | 添加文档成员 | [详细文档](./add_member.md) |
| update_member | 更新成员角色 | [详细文档](./update_member.md) |
| change_scope | 修改文档公开范围 | [详细文档](./change_scope.md) |
| query_apply_member | 查询知识库/文档权限申请列表 | [详细文档](./query_apply_member.md) |
| apply_member | 申请知识库/文档权限 | [详细文档](./apply_member.md) |

### 互动数据 & 用户信息类 (6个)
| API | 功能 | 文档 |
|-----|------|------|
| query_comments | 查询文档评论（含批注） | [详细文档](./query_comments.md) |
| create_comment | 创建文档评论/批注 | [详细文档](./create_comment.md) |
| query_recent_view | 查询文档浏览记录 | [详细文档](./query_recent_view.md) |
| query_recent_doc | 查询用户最近浏览/编辑的文档 | [详细文档](./query_recent_doc.md) |
| query_user_info | 查询用户信息（含个人知识库ID） | [详细文档](./query_user_info.md) |
| query_relation | 分页查询文档关联信息（业务关联/引用/被引用/共创/读取） | [详细文档](./query_relation.md) |

### 附件与资源类 (1个)
| API | 功能 | 文档 |
|-----|------|------|
| query_doc_resource | 查询文档内嵌资源数据（附件/图片/流程图/脑图/随心搭；随心搭默认同时返回组件代码与组件内数据） | [详细文档](./query_doc_resource.md) |

### 表格操作类 (2个)
| API | 功能 | 文档 |
|-----|------|------|
| export_sheet | 导出在线表格为 Excel | [详细文档](./export_sheet.md) |
| import_sheet | 导入 Excel 为在线表格 | [详细文档](./import_sheet.md) |

### 数据表管理类 (11个)
| API | 功能 | 文档 |
|-----|------|------|
| get_datasheet_fields | 获取数据表所有字段信息 | [详细文档](./get_datasheet_fields.md) |
| add_datasheet_field | 向数据表添加新字段 | [详细文档](./add_datasheet_field.md) |
| del_datasheet_field | 删除数据表字段 | [详细文档](./del_datasheet_field.md) |
| get_datasheet_records | 查询数据表记录（支持分页、筛选、排序） | [详细文档](./get_datasheet_records.md) |
| add_datasheet_record | 添加新记录到数据表 | [详细文档](./add_datasheet_record.md) |
| update_datasheet_record | 更新数据表中的记录 | [详细文档](./update_datasheet_record.md) |
| upload_datasheet_attachment | 上传数据表附件并返回附件参数 | [详细文档](./upload_datasheet_attachment.md) |
| delete_datasheet_record | 删除数据表记录 | [详细文档](./delete_datasheet_record.md) |
| get_datasheet_views | 获取数据表所有视图信息 | [详细文档](./get_datasheet_views.md) |
| create_datasheet | 在文档中创建新数据表 | [详细文档](./create_datasheet.md) |
| get_datasheet_children | 查询数据表表夹下子表（数据表/仪表盘，分页） | [详细文档](./get_datasheet_children.md) |

## 🎯 使用场景速查

### 场景1: 文档查询与读取
1. 使用 `query_user_info` 获取个人知识库ID
2. 使用 `query_repo` 列出知识库文档
3. 使用 `query_content` 读取文档正文与资源占位符（支持 JSON/MD/HTML/AIHtml 格式，可通过 `--version-id` 查询特定版本内容）
4. 使用 `query_version` 查询文档历史版本列表

### 场景1.1: 按需读取附件与文内资源
1. 默认只用 `query_content` 读取正文和资源占位符，不主动展开附件
2. 用户明确要求附件、流程图、图片、脑图、随心搭等文内资源时，使用 `query_doc_resource` 按资源 ID 查询
3. 输出时区分正文、附件、流程图等来源

### 场景1.2: 随心搭组件（读/建/改三路分流）
1. **读取/导出**：先 `query_content --show-resource-info=true` 定位随心搭资源 ID，再 `query_doc_resource --resource-type flex-builder --resource-id <id>`。**不传 `--flex-query-type` 默认 `all`**，一次取回组件代码与组件内数据；`code` 只取代码，`kv` 只取数据。数据可用 `--key-prefix` 过滤、`--cursor` / `--limit` 翻页，翻页以 `nextCursor` 是否返回为准
2. **只列组件清单**：用户只问"文档里有哪些组件"时，只用 `query_content` 给出数量与位置，不调用 `query_doc_resource`
3. **新建随心搭**：不在本技能内创建，改用 **知识库随心搭** 技能(https://console.cloud.baidu-int.com/onetool/skills/287)，禁止用 `create_doc` / `edit_mdsl_content` 替代
4. **修改已有随心搭（含修改组件内数据）**：本技能不执行修改，返回当前文档完整 URL（优先用户原始 URL，其次接口响应中的真实 `url` / `docInfo.url`，禁止猜测拼接），建议用户打开页面直接修改

### 场景2: 创建并管理文档
1. 使用 `query_user_info` 获取个人知识库ID
2. 使用 `create_doc` 创建新文档（支持从文件导入内容）；需要新建目录时使用 `create_book` 创建知识本
3. 使用 `edit_mdsl_content` 编辑文档正文
4. 使用 `add_member` 添加协作者并设置权限

### 场景3: 处理在线表格
1. 使用 `export_sheet` 导出在线表格为 Excel 进行分析
2. 修改 Excel 内容后，使用 `import-sheet` 重新导入

### 场景4: 数据表管理
1. 使用 `create_datasheet` 创建新数据表
2. 使用 `add_datasheet_field` 添加字段
3. 使用 `add_datasheet_record` 添加初始数据
4. 使用 `get_datasheet_records` 查询数据（支持筛选、排序、分页）
5. 需要写入附件字段时，先使用 `upload_datasheet_attachment` 上传文件获取附件参数，再使用 `update_datasheet_record` 更新目标记录的附件字段
6. 用户提供数据表 URL、但想知道表夹下有哪些子表（含仪表盘）时，用 `get_datasheet_children` 从 URL 提取 `--doc-id`（`?tb=` 前的 path 段）分页查询；翻页以 `result.hasMore` 判断，`--page-size` 最大 100

### 场景5: 互动数据查询
1. 使用 `query_comments` 查看文档评论和批注
2. 使用 `query_recent_view` 查看浏览记录
3. 使用 `query_relation` 查询文档关联信息（业务关联/引用/被引用/共创/读取）

## 📝 CLI 快速使用指南

### 环境准备

```bash
# 确保二进制有执行权限（首次使用）
chmod +x $SKILL_DIR/bin/ku
```

### 常用操作示例

#### 1. 查询文档内容

```bash
# 使用文档ID查询
ku query-content --doc-id WKoT7ltTnjU1oW --protocol markdown

# 使用URL查询
ku query-content --url "https://ku.baidu-int.com/knowledge/A/B/C/D"
```

#### 2. 创建文档

```bash
ku create-doc --repo-id repo_xxx --username zhangsan \
--title "文档标题" --content "# 内容" --parent-doc-id parent_xxx
```

> ⚠️ 布尔标志（如 `--process-images`、`--set-top`）传值必须用等号形式（`--process-images=true`），禁止 `--process-images true` 空格写法——空格后的 `true` 会导致解析提前停止，其后的参数被静默丢弃。多行内容把换行写成字面 `\n` 或改用 `--md-file` 传文件。

#### 3. 查询知识库文档列表

```bash
ku query-repo --repo-id repo_xxx --parent-doc-id parent_xxx \
--page-num 1 --page-size 50
```

#### 4. 导出在线表格

```bash
ku export-sheet --doc-id WKoT7ltTnjU1oW
```

#### 5. 查询数据表记录

```bash
ku get-datasheet-records --dist-id dstxRvKjhSZZJDNvpZ --page-num 1 \
--page-size 100 --filter '{字段名}="值"' --sort '[{"field":"创建时间","order":"desc"}]'
```

## 🔍 参数说明

### 通用参数

| 参数 | 类型 | 说明 |
|------|------|------|
| doc-id | string | 文档ID，常用参数 |
| repo-id | string | 知识库ID，常用参数 |
| username | string | 用户名，用于确定操作身份 |
| dist-id | string | 数据表ID，数据表API必需参数 |

### 文档ID字段别名

| 字段 | 别名 |
|------|------|
| 文档ID | `doc_id` / `docId` / `doc_guid` / `docGuid` |
| 知识库ID | `repo_id` / `repository_guid` / `repo_guid` |

## ⚠️ 注意事项

1. **认证要求**: 所有API都需要有效的认证token
2. **权限检查**: 确保有对应文档或数据表的操作权限
3. **参数验证**: 参数格式和类型必须正确
4. **错误处理**: 建议对所有API调用进行错误处理
5. **限流控制**: 注意API调用频率限制
6. **在线表格操作**: 统一使用 `export-sheet` / `import-sheet` 的导出-修改-导入方式操作

## 📚 相关资源

- [知识库开放API官方文档](https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/2tsPs8CtSd/AhkQkHD47-/CTnyWU03v7GXaf)
- [get-ugate-token SKILL](./../../../get-ugate-token/SKILL.md)

## 🆘 常见问题

### Q1: 如何获取文档ID (doc-id)?
A: 可以从知识库URL中提取（path的最后一部分），或通过 `query-repo` 查询列表获取。

### Q2: 如何获取数据表ID (dist-id)?
A: 数据表ID通常从知识库URL中获取，URL格式为 `https://ku.baidu-int.com/knowledge/A/B/C?tb={dist-id}_{view-id}&type=dst`

### Q3: 为什么API返回401错误?
A: 通常是token过期或无效，检查认证配置或刷新token。

### Q4: 如何批量操作数据表记录?
A: 使用 `add_datasheet_record` 或 `update_datasheet_record` 时，在 `records` 数组中传入多个记录对象即可。

### Q5: 如何编辑在线表格?
A: 使用 `export-sheet` 导出为 Excel，编辑后再用 `import-sheet` 导入；不要通过浏览器方式操作在线表格。