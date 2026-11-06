#!/usr/bin/env python3
"""厂内平台契约的提取、生成与核对。

两个模式：

``--emit``   契约 = 交付 ref 有、而它所基于的社区基线没有的能力。求差得来，不手维护。
``--verify`` 契约里的每一项都必须在候选 ref 上存在，谁提供的不论——社区后来自己收了
             也算过。

能力共六类，都能从源码静态判定，不需要起服务：HTTP 路由（主 server 与 dummy server
分开）、指标族（定义 + 真实观测点，只 ``inc(0)`` 预热的单独记一类）、按 rid 的 stage
trace 行、token id dump 点、日志 schema、厂内环境变量读取点。
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple

SCAN_ROOT = "python/sglang/srt"
SUMMARY = "厂内平台契约的提取、生成与核对"
HTTP_METHODS = frozenset({"get", "post", "put", "delete", "patch"})
METRIC_OPS = frozenset({"observe", "inc", "dec", "set"})
# 只解析含这些标记的文件；每类能力都必然带其中一个，预筛掉的文件不可能有能力。
MARKERS = (
    '"sglang:',
    "@app.",
    "trace(",
    "log_input_ids",
    "configure_logger",
    "envs.",
    "os.getenv",
    "os.environ",
)
KIND_TITLES = {
    "route.main": "主 server 路由",
    "route.dummy": "dummy server 路由",
    "metric": "指标族（定义 + 写入点）",
    "metric.preheat": "计数器预热",
    "trace": "rid stage trace 行",
    "token_ids": "token id dump 点",
    "log": "日志 schema",
    "env": "厂内环境变量读取点",
}


@dataclass(frozen=True)
class Capability:
    """契约里的一项能力：类别、身份，以及当时的证据文件。"""

    kind: str
    key: str
    where: str

    @property
    def ident(self) -> Tuple[str, str]:
        """集合运算用的身份。证据文件会随基线变，不参与比对。"""
        return (self.kind, self.key)


@dataclass
class Snapshot:
    """一个 ref 上的能力集，加两份指标旁证。"""

    caps: Dict[Tuple[str, str], str]
    defined: Dict[str, str]          # 族名 -> 定义所在文件，含没有写入点的
    unobserved: List[str]            # 定义了但没人写的族名


def git(repo: Path, *args: str, allow_no_match: bool = False) -> str:
    """在 repo 上跑 git 取 stdout。allow_no_match 让 git grep 的「无命中」不算失败。"""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 and not (allow_no_match and proc.returncode == 1):
        raise SystemExit(f"git {' '.join(args)} 失败：{proc.stderr.strip()}")
    return proc.stdout


def read_tree(repo: Path, ref: str) -> Iterator[Tuple[str, str]]:
    """ref 上 SCAN_ROOT 下带能力标记的 .py 文件的 (相对路径, 源码)。

    用 git grep 一次筛出候选路径再逐个 show，避免把整棵树读进来。
    """
    grep = ["grep", "--name-only", "-F"]
    for marker in MARKERS:
        grep += ["-e", marker]
    listing = git(repo, *grep, ref, "--", SCAN_ROOT, allow_no_match=True)
    paths = sorted(
        {
            line.split(":", 1)[1]
            for line in listing.splitlines()
            if ":" in line and line.split(":", 1)[1].endswith(".py")
        }
    )
    if not paths:
        raise SystemExit(f"{ref} 上 {SCAN_ROOT} 里一个标记都没命中，ref 或仓库给错了")
    for path in paths:
        yield path, git(repo, "show", f"{ref}:{path}")


def _string(node: ast.expr) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _callee_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _metric_attr(call: ast.Call) -> Optional[str]:
    """``self.x.labels(...).inc(...)`` 里被观测的那个属性名 x。"""
    if not isinstance(call.func, ast.Attribute):
        return None
    node: ast.expr = call.func.value          # 去掉 observe / inc / set / dec 本身
    while True:
        if isinstance(node, ast.Call):
            node = node.func
        elif isinstance(node, ast.Attribute) and node.attr == "labels":
            node = node.value
        else:
            break
    return node.attr if isinstance(node, ast.Attribute) else None


def _literal_head(node: ast.expr) -> Optional[str]:
    """字符串字面量，或 f-string 开头那段字面量。"""
    text = _string(node)
    if text is not None:
        return text
    if isinstance(node, ast.JoinedStr) and node.values:
        return _string(node.values[0])
    return None


def _env_shaped(name: Optional[str]) -> bool:
    return bool(name) and name.isupper() and name.isidentifier()


def _is_zero(args: Sequence[ast.expr]) -> bool:
    return bool(args) and isinstance(args[0], ast.Constant) and args[0].value == 0


class FileScan:
    """一个文件里与平台契约有关的全部信号。"""

    def __init__(self, path: str, source: str, dummy_func: str) -> None:
        self.path = path
        self.module = path.rsplit("/", 1)[-1]
        # 路由与 dump 点按「上一级目录/文件名」定位所在文件：同一个路径可能由多个 server 提供
        # （主 server 与 encode server 都有 /health_forward），只按路径记会把它们并成一项，
        # 删掉其中一个照样过。两段路径足够区分所在文件，又不会因为整棵树搬家就失配。
        self.anchor = "/".join(path.split("/")[-2:])
        self.dummy_func = dummy_func
        self.routes: List[Tuple[str, bool]] = []
        self.metric_defs: Dict[str, str] = {}       # attr -> family
        self.metric_families: Set[str] = set()      # 出现过的族名，含无 attr 的
        self.observed: Set[str] = set()             # attr
        self.preheated: Set[str] = set()            # attr
        self.attr_loads: Dict[str, int] = {}        # attr -> 读取次数
        self.traces: List[str] = []
        self.token_stages: List[str] = []
        self.log_prefixes: List[str] = []
        self.levelname_first = False
        self.uvicorn_access_format = False
        self.env_names: Set[str] = set()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")      # 仓库里有失效转义，解析不该刷屏
            tree = ast.parse(source, filename=path)
        self._walk(tree, ())

    def _walk(self, node: ast.AST, funcs: Tuple[str, ...]) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._routes_of(node, funcs)
            funcs = (*funcs, node.name)
        elif isinstance(node, ast.Call):
            self._call(node)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "envs":
                self.env_names.add(node.attr)
            if isinstance(node.ctx, ast.Load):
                self.attr_loads[node.attr] = self.attr_loads.get(node.attr, 0) + 1
        elif isinstance(node, ast.Subscript):
            self._subscript(node)
        elif isinstance(node, ast.Assign):
            self._assign(node)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.startswith("%(levelname)s"):
                self.levelname_first = True
            if "%(client_addr)s" in node.value:
                self.uvicorn_access_format = True
        for child in ast.iter_child_nodes(node):
            self._walk(child, funcs)

    def _routes_of(self, node: ast.AST, funcs: Tuple[str, ...]) -> None:
        assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        dummy = self.dummy_func in funcs
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or _callee_name(dec.func) not in HTTP_METHODS:
                continue
            path = _string(dec.args[0]) if dec.args else None
            if path and path.startswith("/"):
                self.routes.append((path, dummy))

    def _assign(self, node: ast.Assign) -> None:
        if not isinstance(node.value, ast.Call):
            return
        family = next(
            (
                _string(kw.value)
                for kw in node.value.keywords
                if kw.arg == "name" and (_string(kw.value) or "").startswith("sglang:")
            ),
            None,
        )
        if not family:
            return
        self.metric_families.add(family)
        target = node.targets[0]
        if isinstance(target, ast.Attribute):
            self.metric_defs[target.attr] = family

    def _subscript(self, node: ast.Subscript) -> None:
        """``os.environ["X"]``。"""
        if not isinstance(node.value, ast.Attribute) or node.value.attr != "environ":
            return
        env = _string(node.slice)
        if env:
            self.env_names.add(env)

    def _call(self, node: ast.Call) -> None:
        # 环境变量读取点：除 os.getenv / os.environ.get，各包还有自己的
        # _env_bool("CD_X", ...) 包装，所以按「实参里的环境变量形状字面量」收。
        for arg in node.args:
            literal = _string(arg)
            if literal and _env_shaped(literal):
                self.env_names.add(literal)
        name = _callee_name(node.func)
        if name in METRIC_OPS:
            attr = _metric_attr(node)
            if attr:
                (self.preheated if _is_zero(node.args) else self.observed).add(attr)
        elif name == "trace" and len(node.args) >= 2:
            message = _string(node.args[1])
            if message:
                self.traces.append(message)
        elif name == "log_input_ids" and len(node.args) >= 3:
            stage = _string(node.args[2])
            if stage:
                self.token_stages.append(stage)
        elif name == "configure_logger":
            self._logger_prefix(node)

    def _logger_prefix(self, node: ast.Call) -> None:
        given = list(node.args[1:])
        given += [kw.value for kw in node.keywords if kw.arg == "prefix"]
        for value in given:
            prefix = (_literal_head(value) or "").strip()
            if prefix:
                self.log_prefixes.append(prefix)


def wanted_env(name: str, prefixes: Sequence[str], names: Sequence[str]) -> bool:
    """这个环境变量是否属于厂内关心的范围：命中前缀，或在显式名单里。"""
    return name in names or any(name.startswith(p) for p in prefixes)


def extract(
    repo: Path,
    ref: str,
    env_prefixes: Sequence[str],
    env_names: Sequence[str],
    dummy_func: str,
) -> Snapshot:
    """ref 上的能力集 {(kind, key): 证据文件}，加指标族的定义与写入点旁证。"""
    scans = [FileScan(path, source, dummy_func) for path, source in read_tree(repo, ref)]
    preheated: Set[str] = set()
    loads: Dict[str, int] = {}
    for scan in scans:
        preheated |= scan.preheated
        for attr, count in scan.attr_loads.items():
            loads[attr] = loads.get(attr, 0) + count

    def has_writer(attr: str) -> bool:
        """预热那行本身也是一次读取，扣掉它再看有没有真的写入点。"""
        return loads.get(attr, 0) - (1 if attr in preheated else 0) > 0

    caps: Dict[Tuple[str, str], str] = {}
    defined: Dict[str, str] = {}
    unobserved: List[str] = []

    def add(kind: str, key: str, where: str) -> None:
        caps.setdefault((kind, key), where)

    for scan in scans:
        for path, dummy in scan.routes:
            add(
                "route.dummy" if dummy else "route.main",
                f"{path}@{scan.anchor}",
                scan.path,
            )
        for attr, family in scan.metric_defs.items():
            defined.setdefault(family, scan.path)
            if has_writer(attr):
                add("metric", family, scan.path)
            else:
                unobserved.append(family)
            if attr in preheated:
                add("metric.preheat", family, scan.path)
        for message in scan.traces:
            add("trace", message, scan.path)
        for stage in scan.token_stages:
            add("token_ids", f"{stage}@{scan.anchor}", scan.path)
        for prefix in scan.log_prefixes:
            add("log", f"prefix:{prefix}", scan.path)
        if scan.levelname_first and scan.module == "common.py":
            add("log", "levelname-first", scan.path)
        if scan.uvicorn_access_format:
            add("log", "uvicorn-access-format", scan.path)
        for env in scan.env_names:
            if wanted_env(env, env_prefixes, env_names):
                add("env", env, scan.path)
    return Snapshot(caps=caps, defined=defined, unobserved=sorted(set(unobserved)))


def emit(args: argparse.Namespace) -> int:
    """生成契约：交付 ref 的能力集减去它所基于的社区基线的能力集。"""
    repo = Path(args.repo)
    delivery = extract(
        repo, args.ref, args.env_prefix, args.env_name, args.dummy_server_func
    )
    base = extract(
        repo, args.against, args.env_prefix, args.env_name, args.dummy_server_func
    )
    delta = sorted(
        (
            Capability(kind, key, where)
            for (kind, key), where in delivery.caps.items()
            if (kind, key) not in base.caps
        ),
        key=lambda cap: (cap.kind, cap.key),
    )
    contract = {
        "generated": {
            "repo": git(repo, "rev-parse", "--show-toplevel").strip(),
            "delivery_ref": git(repo, "rev-parse", "--short=10", args.ref).strip(),
            "community_base": git(repo, "rev-parse", "--short=10", args.against).strip(),
            "at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "env_prefixes": list(args.env_prefix),
            "env_names": list(args.env_name),
        },
        "capabilities": [
            {"kind": cap.kind, "key": cap.key, "where": cap.where} for cap in delta
        ],
    }
    text = json.dumps(contract, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    counts = {kind: sum(1 for cap in delta if cap.kind == kind) for kind in KIND_TITLES}
    summary = "，".join(f"{KIND_TITLES[k]} {n}" for k, n in counts.items() if n)
    print(f"契约 {len(delta)} 项：{summary}", file=sys.stderr)
    fresh = [f for f in delivery.unobserved if f not in base.unobserved]
    if fresh:
        print(
            f"交付 ref 上有 {len(fresh)} 个族定义了却没有写入点，不进契约，先在本分支修：",
            file=sys.stderr,
        )
        for family in fresh:
            print(f"  {family}（{delivery.defined[family]}）", file=sys.stderr)
    return 0


def verify(args: argparse.Namespace) -> int:
    """拿契约核对候选 ref，逐项给 PASS / MISSING / 无写入点，缺项即非零退出。"""
    repo = Path(args.repo)
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    wanted = [
        Capability(item["kind"], item["key"], item.get("where", ""))
        for item in contract["capabilities"]
    ]
    meta = contract.get("generated", {})
    snapshot = extract(
        repo,
        args.ref,
        meta.get("env_prefixes", args.env_prefix),
        meta.get("env_names", args.env_name),
        args.dummy_server_func,
    )
    have = snapshot.caps
    missing = [cap for cap in wanted if cap.ident not in have]

    def verdict(cap: Capability) -> Tuple[str, str]:
        hit = have.get(cap.ident)
        if hit:
            return "PASS", hit
        if cap.kind == "metric" and cap.key in snapshot.defined:
            return "**无写入点**", f"族在 {snapshot.defined[cap.key]}，但没人写它"
        return "**MISSING**", cap.where

    lines = [
        f"# 平台契约核对：{args.ref}",
        "",
        f"契约 {args.contract}，生成自 {meta.get('delivery_ref', '?')} "
        f"相对 {meta.get('community_base', '?')} 的求差。",
        "",
        "| 类 | 契约项 | 结果 | 证据 / 缺失时的原位置 |",
        "|---|---|---|---|",
    ]
    for cap in wanted:
        state, evidence = verdict(cap)
        lines.append(
            f"| {KIND_TITLES.get(cap.kind, cap.kind)} | `{cap.key}` | {state} | {evidence} |"
        )
    lines += ["", f"合计 {len(wanted)} 项，缺 {len(missing)} 项。"]
    if snapshot.unobserved:
        lines += [
            "",
            "## 定义了却没有写入点的指标族",
            "",
            "面板上是 No data。不在契约里的也列出来，本轮不处理也要知道：",
            "",
            *(f"- {family}（{snapshot.defined[family]}）" for family in snapshot.unobserved),
        ]
    report = "\n".join(lines) + "\n"
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)

    if missing:
        print(f"平台契约核对不通过：缺 {len(missing)} 项", file=sys.stderr)
        for cap in missing:
            state, evidence = verdict(cap)
            print(f"  {cap.kind} {cap.key}：{state.strip('*')}，{evidence}", file=sys.stderr)
        return 1
    print(f"平台契约核对通过：{len(wanted)}/{len(wanted)} 项在位", file=sys.stderr)
    return 0


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """解析命令行，并补上两个模式各自的必填项检查。"""
    parser = argparse.ArgumentParser(description=SUMMARY)
    parser.add_argument("--repo", required=True, help="仓库或 worktree 路径")
    parser.add_argument("--ref", default="HEAD", help="被提取 / 被核对的 ref")
    parser.add_argument("--emit", action="store_true", help="生成契约而不是核对")
    parser.add_argument("--against", help="--emit 用：交付 ref 所基于的社区基线")
    parser.add_argument("--contract", help="核对用的契约 JSON")
    parser.add_argument("-o", "--output", help="产物路径，默认 stdout")
    parser.add_argument(
        "--env-prefix", action="append", default=[], help="厂内环境变量前缀，可重复"
    )
    parser.add_argument(
        "--env-name", action="append", default=[], help="额外的单个环境变量名，可重复"
    )
    parser.add_argument(
        "--dummy-server-func",
        default="launch_dummy_health_check_server",
        help="dummy health server 的函数名，其内的路由单独归类",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if not args.env_prefix:
        args.env_prefix = ["AIAK_", "CD_"]
    if args.emit and not args.against:
        parser.error("--emit 需要 --against 给社区基线")
    if not args.emit and not args.contract:
        parser.error("核对模式需要 --contract")
    return args


def main() -> int:
    """入口：按 --emit 决定是生成契约还是核对契约。"""
    args = parse_args()
    return emit(args) if args.emit else verify(args)


if __name__ == "__main__":
    sys.exit(main())
