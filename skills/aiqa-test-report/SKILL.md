---
name: aiqa-test-report
description: |
  通过 standard_test_record API 获取 AIQA 标准测试报告记录，支持按记录 ID、P/D/E 镜像、创建人、测试结果和测试类型筛选，自动翻页获取全部记录，并输出 report_url / review_url。
  触发词："获取测试报告"、"查询测试记录"、"standard_test_record"、"测试报告链接"、"AIQA 测试报告"。
allowed-tools:
  - Bash
  - Read
  - Write
---

# AIQA Test Report

通用查询 AIQA 标准测试报告记录，返回每条记录的报告链接和 review 链接。

## 接口与客户端

- API: `GET /standard_test_record`
- 默认地址: `http://10.11.159.198:8001`
- 客户端: `$SKILL_DIR/scripts/query_standard_test_records.py`

## 使用方式

### 等价原 curl 的查询

```bash
cd $SKILL_DIR/scripts
python3 query_standard_test_records.py \
  --created-by suhang09 \
  --p-image 'iregistry.baidu-int.com/hac-aiacc/aiak-inference-sglang:ubuntu22.04-cu12.3-torch2.5.1-py310_v15.4.5.3_ubuntu' \
  --test-type function_think --test-type function_nothink \
  --links
```

### 按记录 ID 查单条

```bash
python3 query_standard_test_records.py --record-id 2785 --links
```

### 拉取全部匹配记录

```bash
python3 query_standard_test_records.py \
  --created-by suhang09 \
  --p-image '<P_IMAGE>' \
  --all \
  --output /tmp/test_records.json
```

### 通用查询参数

| 参数 | 说明 |
|------|------|
| `--record-id` | 按记录 ID 筛选 |
| `--p-image` / `--d-image` / `--e-image` | 按 P/D/E 镜像完整名称精确筛选 |
| `--created-by` | 按创建人筛选 |
| `--test-result` | 按测试结果筛选，可重复或逗号分隔 |
| `--test-type` | 按测试类型筛选，可重复或逗号分隔 |
| `--orderby` | 排序字段和方向，默认 `id desc` |
| `--page` / `--page-size` | 分页参数，page_size 上限 1000 |
| `--all` | 自动翻页获取全部匹配记录 |
| `--links` | 只输出 id、测试类型、结果和报告链接 |
| `--output` | 结果落盘为 JSON |
| `--base-url` | 覆盖接口地址，默认取环境变量 `AIQA_REPORT_API` 或内置地址 |

## 输出字段

每条记录包含 `report_url` 和 `review_url`，`test_detail` 中还有 `ipipe_url`、`yaml_bos_url`、`diagnosis_id` 等详情。报告链接字段为空时客户端以 `-` 显示。接口返回的 `test_detail`、`diagnosis_detail`、`failure_details` 是 JSON 字符串，需要解析后才能取嵌套字段。

## 注意事项

- 接口只做精确匹配，不支持日期范围、model_id 或镜像模糊搜索；需要时先在服务端扩展查询条件。
- 接口地址是内网地址，跨环境使用时通过 `--base-url` 或 `AIQA_REPORT_API` 覆盖。
- 测试结果值不统一，历史数据可能同时存在 `succ` 和 `SUCC`，按 `test_result` 筛选时按真实值填写。
