#!/usr/bin/env python3
# coding: utf-8
"""
Functions: 通过 standard_test_record API 查询测试报告记录
Description: 通用 CLI，支持按记录 ID、P/D/E 镜像、创建人、测试结果和测试类型过滤，
    并可自动翻页获取全部记录。
Authors: liyanzhen
Date: 2026/08/03

Usage:
    python query_standard_test_records.py \
        --created-by suhang09 \
        --p-image '<P_IMAGE>' \
        --test-type function_think --test-type function_nothink
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


DEFAULT_BASE_URL = "http://10.11.159.198:8001"


def _normalize_multi_values(values: Optional[List[str]]) -> Optional[List[str]]:
    """将重复参数和逗号分隔参数规整为去空字符串列表。"""
    if not values:
        return None
    result = []
    for value in values:
        result.extend(item.strip() for item in value.split(",") if item.strip())
    return result or None


class StandardTestRecordClient:
    """standard_test_record API 查询客户端。"""

    def __init__(self, base_url: str):
        self.endpoint = f"{base_url.rstrip('/')}/standard_test_record"

    def fetch_page(
        self,
        filters: Dict,
        orderby: str,
        page: int,
        page_size: int,
    ) -> Dict:
        """查询单页标准测试记录。"""
        params = {key: value for key, value in filters.items() if value not in (None, [], "")}
        params.update({"orderby": orderby, "page": page, "page_size": page_size})
        url = f"{self.endpoint}?{urlencode(params, doseq=True)}"
        try:
            with urlopen(url, timeout=60) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"查询标准测试记录失败: {exc}") from exc
        if not payload.get("success"):
            raise RuntimeError(payload.get("message") or "接口返回失败")
        return payload["data"]

    def fetch_all(
        self,
        filters: Dict,
        orderby: str,
        page_size: int,
    ) -> Dict:
        """自动翻页获取全部匹配记录。"""
        records = []
        page = 1
        while True:
            data = self.fetch_page(filters, orderby, page, page_size)
            records.extend(data["records"])
            if page * page_size >= data["total"] or not data["records"]:
                return {
                    "total": data["total"],
                    "records": records,
                    "page": 1,
                    "page_size": page_size,
                }
            page += 1


def _print_report_links(records: List[Dict]) -> None:
    """输出测试报告链接，字段为空时显示 -。"""
    print("\t".join(("id", "test_type", "test_result", "report_url", "review_url")))
    for record in records:
        print("\t".join(str(record.get(field) or "-") for field in (
            "id", "test_type", "test_result", "report_url", "review_url",
        )))


def main() -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(
        description="通过 standard_test_record API 查询测试报告记录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例：\n"
               "  python query_standard_test_records.py --created-by suhang09 "
               "--test-type function_think --test-type function_nothink\n"
               "  python query_standard_test_records.py --record-id 2785 --links\n"
               "  python query_standard_test_records.py --p-image <image> --all",
    )
    parser.add_argument("--base-url", default=os.environ.get("AIQA_REPORT_API", DEFAULT_BASE_URL),
                        help="接口地址，默认使用环境变量 AIQA_REPORT_API 或内置地址")
    parser.add_argument("--record-id", type=int, help="按记录 ID 筛选")
    parser.add_argument("--p-image", help="按 P 镜像完整名称筛选")
    parser.add_argument("--d-image", help="按 D 镜像完整名称筛选")
    parser.add_argument("--e-image", help="按 E 镜像完整名称筛选")
    parser.add_argument("--created-by", help="按创建人筛选")
    parser.add_argument("--test-result", action="append", help="按测试结果筛选，可重复或逗号分隔")
    parser.add_argument("--test-type", action="append", help="按测试类型筛选，可重复或逗号分隔")
    parser.add_argument("--orderby", default="id desc", help="排序字段和方向，默认 id desc")
    parser.add_argument("--page", type=int, default=1, help="页码，默认 1")
    parser.add_argument("--page-size", type=int, default=20, help="每页记录数，默认 20")
    parser.add_argument("--all", action="store_true", help="自动翻页获取全部匹配记录")
    parser.add_argument("--links", action="store_true", help="只输出 id、测试类型、结果和报告链接")
    parser.add_argument("--output", help="可选输出 JSON 文件路径")
    args = parser.parse_args()

    if not 1 <= args.page_size <= 1000:
        parser.error("page_size 必须在 1 到 1000 之间")

    filters = {
        "record_id": args.record_id,
        "p_image": args.p_image,
        "d_image": args.d_image,
        "e_image": args.e_image,
        "created_by": args.created_by,
        "test_result": _normalize_multi_values(args.test_result),
        "test_type": _normalize_multi_values(args.test_type),
    }
    client = StandardTestRecordClient(args.base_url)
    if args.all:
        data = client.fetch_all(filters, args.orderby, args.page_size)
    else:
        data = client.fetch_page(filters, args.orderby, args.page, args.page_size)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"结果已写入 {output_path}", file=sys.stderr)

    if args.links:
        _print_report_links(data["records"])
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
