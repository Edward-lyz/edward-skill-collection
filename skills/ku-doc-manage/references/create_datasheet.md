# create_datasheet - 创建数据表

在指定文档中创建新的数据表。

> ⚠️ **使用限制**
>
> 此命令**仅在识别到数据表 URL 后可用**，用于在已有的数据表夹下新建数据表。
>
> - `--doc-id` 参数**必须从数据表 URL 中提取**（即 `?tb=...` 参数前的 path 段，表示数据表夹所在文档）
> - **不支持创建数据表夹**：若用户想"创建数据表"但未提供数据表 URL，应提示用户：
>   > 需要先提供一个已有数据表的 URL，才能在该数据表夹下新建数据表。当前不支持创建新的数据表夹。
>
> **错误示例**：直接使用普通文档 ID 作为 `--doc-id` 参数调用此命令
> **正确用法**：先从用户提供的 `https://ku.baidu-int.com/knowledge/A/B/C?tb=xxx&type=dst` 中提取 `C` 作为 `--doc-id`

## 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| --doc-id | string | 是 | 文档ID（从数据表URL中提取），数据表将在此文档（数据表夹）下创建 |
| --username | string | 是 | 调用接口的用户名 |
| --name | string | 否 | 数据表名称 |

## 返回值说明

成功时返回：

```json
{
    "msg": "OK",
    "result": {
        "dstId": "dstv9pVzNB0q7KK9rw"
    },
    "returnCode": 200,
    "returnMessage": "OK",
    "status": 200,
    "success": true,
    "traceId": "689807744345196544"
}
```

### 返回字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `"OK"` |
| returnCode | int | 业务返回码，200 表示成功 |
| returnMessage | string | 业务返回消息 |
| status | int | HTTP 状态码 |
| success | bool | 请求是否成功 |
| traceId | string | 链路追踪 ID |
| result.dstId | string | 新创建的数据表 ID，可用于后续字段、记录等操作 |

## CLI调用示例

```bash
# 创建数据表
ku create-datasheet --doc-id WKoT7ltTnjU1oW --username zhangsan --name "项目任务表"
```

## 错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 参数错误 | 检查--doc-id是否正确 |
| 401 | 未授权 | 刷新token或检查认证配置 |
| 403 | 无权限 | 确认是否有文档的编辑权限 |
| 404 | 文档不存在 | 检查--doc-id是否正确 |
| 500 | 服务器错误 | 稍后重试或联系管理员 |

## 注意事项

1. **权限要求**: 需要对目标文档有编辑权限
2. **文档类型**: --doc-id 必须是数据表夹类型的文档
3. **命名规范**: --name 不超过100个字符，不传时使用默认名称
4. **默认结构**: 新创建的数据表会有默认字段和视图
5. **初始化**: 创建后需要手动添加字段和数据
6. **用户信息**: --username 用于记录创建者信息

## 相关API

- [add_datasheet_field](./add_datasheet_field.md) - 添加数据表字段
- [get_datasheet_views](./get_datasheet_views.md) - 获取数据表视图
- [add_datasheet_record](./add_datasheet_record.md) - 添加数据表记录
- [get_datasheet_fields](./get_datasheet_fields.md) - 获取数据表字段
