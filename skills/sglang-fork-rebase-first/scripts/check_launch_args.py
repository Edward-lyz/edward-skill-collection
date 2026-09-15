"""发版 YAML 的启动参数对着目标基线的 argparse 反查。

换基线后老交付 YAML 里常残留更老引擎或更老厂内分支的私有参数，容器会直接以
`sglang serve: error: unrecognized arguments: --x` 退出。这个脚本把「这次要出的镜像」
的可识别参数全集算出来，再和 YAML 里实际传的参数求差集。

    python3 check_launch_args.py --repo <worktree> --yaml 1prefill.yaml --yaml 1decode.yaml

可识别参数全集 = arg_groups/fields/*.py 各 dataclass 的字段名（下划线转横线）
              ∪ 全仓库 add_argument("--x") 的字面量。
退出码 0 表示零可疑项。
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

ARG_RE = re.compile(r"(?<![\w-])(--[a-z0-9][a-z0-9-]*)")
ADD_ARGUMENT_RE = re.compile(r"""add_argument\(\s*["'](--[a-z0-9][a-z0-9-]*)["']""")


def collect_valid_args(repo: Path) -> set[str]:
    """目标基线能识别的参数名全集。"""
    valid: set[str] = set()

    fields_dir = repo / "python/sglang/srt/arg_groups/fields"
    for path in sorted(fields_dir.glob("*.py")) if fields_dir.is_dir() else []:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    valid.add("--" + stmt.target.id.replace("_", "-"))

    for path in (repo / "python/sglang/srt").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "add_argument(" in text:
            valid.update(ADD_ARGUMENT_RE.findall(text))

    if not valid:
        raise SystemExit(f"在 {repo} 下没找到任何参数定义，--repo 指对了吗")
    return valid


def collect_yaml_args(path: Path) -> set[str]:
    """从 YAML 的容器 command/args 里抽出实际传的参数。

    只看 command 和 args 字符串，不扫整份 YAML，避免把注释和探针路径算进来。
    """
    try:
        import yaml
    except ImportError:
        raise SystemExit("需要 PyYAML：pip3 install pyyaml")

    used: set[str] = set()
    for doc in yaml.safe_load_all(path.read_text(encoding="utf-8")):
        if doc is None:
            continue
        stack = [doc]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ("command", "args") and isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                used.update(ARG_RE.findall(item))
                    else:
                        stack.append(value)
            elif isinstance(node, list):
                stack.extend(node)
    return used


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="目标基线的仓库或 worktree 根")
    parser.add_argument("--yaml", action="append", required=True, help="发版 YAML，可重复")
    parser.add_argument("--allow", action="append", default=[], help="白名单参数，可重复")
    parser.add_argument("--json", action="store_true", help="机器可读输出")
    args = parser.parse_args()

    valid = collect_valid_args(Path(args.repo)) | set(args.allow)
    report = []
    bad_total = 0
    for name in args.yaml:
        path = Path(name)
        used = sorted(collect_yaml_args(path))
        bad = [a for a in used if a not in valid]
        bad_total += len(bad)
        report.append({"yaml": str(path), "used": len(used), "unknown": bad})

    if args.json:
        print(json.dumps({"valid_args": len(valid), "files": report}, ensure_ascii=False, indent=1))
    else:
        print(f"目标基线可识别参数数: {len(valid)}")
        for row in report:
            state = "、".join(row["unknown"]) if row["unknown"] else "无"
            print(f"{row['yaml']}: 传了 {row['used']} 个参数 | 新基线不认: {state}")

    if bad_total:
        print(
            "\n处置三分：社区已删且能力默认开启 -> 删参数；厂内私有且这次需要 -> 补迁那笔提交；"
            "厂内私有且这次不需要 -> 删参数并在台账登记能力缺失。",
            file=sys.stderr,
        )
    return 1 if bad_total else 0


if __name__ == "__main__":
    raise SystemExit(main())
