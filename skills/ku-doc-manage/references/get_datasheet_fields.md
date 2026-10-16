# get-datasheet-fields - 获取数据表字段

获取指定数据表的所有字段信息，包括字段名称、类型、属性等。

## 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| dist-id | string | 是 | 数据表ID，唯一标识一个数据表 |

## 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| msg | string | 请求消息，成功为 `SUCCESS` |
| returnCode | number | 返回码，200 表示成功 |
| returnMessage | string | 返回消息，成功为 `SUCCESS` |
| status | number | HTTP 状态码 |
| success | boolean | 是否成功 |
| traceId | string | 链路追踪 ID |
| result.fields | array | 字段列表 |

### fields 字段对象说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 字段唯一 ID，如 `fldCwGW8DK2Ny` |
| name | string | 字段名称 |
| type | string | 字段类型，见下方字段类型说明 |
| editable | boolean | 是否可编辑 |
| isPrimary | boolean | 是否为主键字段（仅主字段有此属性） |
| property | object | 字段属性，结构因 type 不同而不同 |

### 字段类型说明

| 类型 | 说明 | property 结构 |
|------|------|--------------|
| SingleText | 单行文本 | `{"defaultValue": ""}` |
| Text | 多行文本 | `{"defaultValue": ""}` |
| SingleSelect | 单选 | `{"options": [{"id": "optXxx", "name": "选项名", "color": {"name": "colorName", "value": "#hex"}}]}` |
| MultiSelect | 多选 | `{"options": [{"id": "optXxx", "name": "选项名", "color": {"name": "colorName", "value": "#hex"}}]}` |
| Member | 成员 | `{"isMulti": true, "shouldSendMsg": false, "subscription": false, "options": [{"id": "userId", "name": "姓名", "avatar": "url", "type": "Member"}]}` |
| Number | 数字 | `{"precision": 2}` |
| DateTime | 日期时间 | `{"dateFormat": "YYYY-MM-DD"}` |
| Checkbox | 复选框 | `{}` |
| URL | 网址 | `{}` |
| Phone | 电话 | `{}` |
| Email | 邮箱 | `{}` |

## 响应示例

```json
{
    "msg": "SUCCESS",
    "result": {
        "fields": [
            {
                "editable": true,
                "id": "fldCwGW8DK2Ny",
                "isPrimary": true,
                "name": "标题",
                "property": {
                    "defaultValue": ""
                },
                "type": "SingleText"
            },
            {
                "editable": true,
                "id": "fldjEo9qjSAeD",
                "name": "选项",
                "property": {
                    "options": [
                        {
                            "color": {
                                "name": "deepPurple_0",
                                "value": "#F2F0FD"
                            },
                            "id": "opts35dmlxfyU",
                            "name": "A"
                        },
                        {
                            "color": {
                                "name": "indigo_0",
                                "value": "#EEF3FF"
                            },
                            "id": "opt6lCtZXK13q",
                            "name": "B"
                        }
                    ]
                },
                "type": "MultiSelect"
            },
            {
                "editable": true,
                "id": "flderKZVGLspq",
                "name": "成员",
                "property": {
                    "isMulti": true,
                    "options": [
                        {
                            "avatar": "https://ku.baidu-int.com/wiki/as/users/XoBS3OZRDJ/avatar",
                            "id": "1947281378740871170",
                            "name": "v_申佳怡",
                            "type": "Member"
                        },
                        {
                            "avatar": "https://ku.baidu-int.com/wiki/as/users/vwgyJXRmo9/avatar",
                            "id": "1607941619916406786",
                            "name": "魏敏",
                            "type": "Member"
                        }
                    ],
                    "shouldSendMsg": false,
                    "subscription": false
                },
                "type": "Member"
            }
        ]
    },
    "returnCode": 200,
    "returnMessage": "SUCCESS",
    "status": 200,
    "success": true,
    "traceId": "689778181465172992"
}
```

## CLI调用示例

```bash
# 获取数据表字段列表
ku get-datasheet-fields --dist-id dstxRvKjhSZZJDNvpZ
```