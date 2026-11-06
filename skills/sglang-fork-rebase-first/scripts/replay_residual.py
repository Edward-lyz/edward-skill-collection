#!/usr/bin/env python3
"""重放语义残差：把「源提交想改的行」和「新分支实际改的行」对差。

存在性核对（verify_platform_contract.py）只回答「平台要的东西还在不在」。这个脚本回答
另一个问题：**选中的那些提交，内容都真的落到新基线上了吗**。判据不靠手写期望，靠源提交
自己——重放的正确性定义就是「与源提交等价，除了记录在案的适配」。

两侧各算一个「净改动行集合」。源侧把选中提交逐笔 diff 的加行与删行分别求并，再相减：
一笔加了、后一笔又改掉的中间态行会被抵消，剩下的才是这些提交合起来的最终意图。重放侧是
新基线到新分支的净 diff，同样相减。两边求差得三类残差：

``漏迁``  源侧有、重放侧没有。要么是冲突解丢了，要么是折叠时漏了 hunk，要么是有意不搬。
``新造``  重放侧有、源侧没有。要么是接新基线结构的适配，要么是自己写多了。
``该删没删``  源侧删了、重放侧还留着。比漏加更危险，双份实现就是这么来的。

每条残差都必须能落进 --accept 清单里的一条理由。清空残差不是目标，解释清残差才是。

一个已知盲点：**整行搬家在源侧会自相抵消**。某笔把一行加在 A 处、后一笔把同样一行移到 B
处，源侧的加集与删集各含一次、相减后为空，而重放侧的净 diff 里它在 B 处出现一次，于是被
报成「新造」。所以「漏迁」和「该删没删」是必须归零的信号，「新造」是复核清单。

两类假阳性在报告前滤掉：源侧加的行若仍原样在 tip 的同一文件里（社区基线本来就有、或重放
换了位置），不算漏迁；源侧删的行若 tip 的那个文件里已经没有，不算该删没删。源侧加在 A、
重放侧加在别的文件的行单列为「搬家」（例：schedule_batch 的类搬到 req_types），只复核不阻塞。
DSv4.1 实测：不滤时漏迁 430 行里约 370 行属于这两类。
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

SUMMARY = "重放语义残差：源提交的改动行与新分支实际改动行对差"
HUNK_FILE = re.compile(r"^\+\+\+ b/(.+)$")
NOISE = re.compile(r"^\s*$")


def git(repo: Path, *args: str) -> str:
    """在 repo 上跑 git 取 stdout，失败即终止。"""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败：{proc.stderr.strip()}")
    return proc.stdout


def normalize(line: str) -> str:
    """行内空白归一，行首行尾去掉——缩进和换行位置在重放里常变，语义不变。"""
    return " ".join(line.split())


def changed_lines(diff: str) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    """diff 文本里的 (文件, 归一化行)：加行集合与删行集合。"""
    added: Set[Tuple[str, str]] = set()
    removed: Set[Tuple[str, str]] = set()
    path = ""
    for line in diff.splitlines():
        head = HUNK_FILE.match(line)
        if head:
            path = head.group(1)
            continue
        if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
            continue
        if line.startswith("+") and not NOISE.match(line[1:]):
            added.add((path, normalize(line[1:])))
        elif line.startswith("-") and not NOISE.match(line[1:]):
            removed.add((path, normalize(line[1:])))
    return added, removed


def net(
    added: Set[Tuple[str, str]], removed: Set[Tuple[str, str]]
) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    """加行与删行互相抵消：同一行两边都出现，说明它只是中间态。"""
    return added - removed, removed - added


def source_side(
    repo: Path, commits: Sequence[str], paths: Sequence[str]
) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    """源侧净改动行：选中提交逐笔的加行、删行各自求并，再相互抵消。"""
    added: Set[Tuple[str, str]] = set()
    removed: Set[Tuple[str, str]] = set()
    for sha in commits:
        diff = git(
            repo, "show", "--format=", "--unified=0", "--no-color", sha, "--", *paths
        )
        one_added, one_removed = changed_lines(diff)
        added |= one_added
        removed |= one_removed
    return net(added, removed)


def replay_side(
    repo: Path, base: str, tip: str, paths: Sequence[str]
) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    """重放侧净改动行：新基线到分支 tip 的 diff。"""
    diff = git(
        repo, "diff", "--unified=0", "--no-color", f"{base}..{tip}", "--", *paths
    )
    return net(*changed_lines(diff))


def load_accept(path: str | None) -> List[Tuple[str, str, str]]:
    """--accept 文件：每行 `<匹配片段>\t<理由>` 或 `<路径片段>\t<行片段>\t<理由>`，# 开头是注释。

    两段式只匹配路径含 <匹配片段> 或行含 <匹配片段> 的残差，范围大；三段式要求路径和行同时
    命中，`)`、`else:` 这类通用行用三段式限定到文件内的具体行，避免整文件放行。

    判据是「line-by-line 一致，除非上游改了接口」，所以理由必须写出来并点名上游那处
    变更；没有理由的规则直接拒绝，免得例外清单退化成消音开关。
    """
    if not path:
        return []
    rules: List[Tuple[str, str, str]] = []
    for number, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        parts = raw.split("\t")
        if len(parts) >= 3:
            path_part, line_part, reason = parts[0], parts[1], "\t".join(parts[2:])
        else:
            path_part, line_part, reason = parts[0], "", parts[1] if len(parts) > 1 else ""
        if not reason.strip():
            raise SystemExit(f"{path}:{number} 这条例外没写理由，补上上游改了哪个接口")
        rules.append((path_part.strip(), line_part.strip(), reason.strip()))
    return rules


def accepted(item: Tuple[str, str], rules: Iterable[Tuple[str, str, str]]) -> str | None:
    """这条残差是否已被 --accept 里某条规则解释；命中就返回那条理由。"""
    path, line = item
    for path_part, line_part, reason in rules:
        if line_part:
            if path_part in path and line_part in line:
                return reason
        elif path_part in path or path_part in line:
            return reason
    return None


def group(items: Iterable[Tuple[str, str]]) -> Dict[str, List[str]]:
    """按文件归拢残差行，方便逐文件复核。"""
    grouped: Dict[str, List[str]] = {}
    for path, line in sorted(items):
        grouped.setdefault(path, []).append(line)
    return grouped


def render(title: str, items: Set[Tuple[str, str]], cap: int) -> List[str]:
    """把一类残差渲染成 markdown 小节，每个文件最多列 cap 行。"""
    if not items:
        return [f"## {title}：无", ""]
    lines = [f"## {title}：{len(items)} 行", ""]
    for path, entries in group(items).items():
        lines.append(f"### `{path}`（{len(entries)} 行）")
        lines.append("")
        lines += [f"- `{entry}`" for entry in (entries[:cap] if cap else entries)]
        if cap and len(entries) > cap:
            lines.append(f"- …另有 {len(entries) - cap} 行")
        lines.append("")
    return lines


def main() -> int:
    """入口：两侧求差，输出三类残差；漏迁或该删没删非空即非零退出。"""
    parser = argparse.ArgumentParser(description=SUMMARY)
    parser.add_argument("--repo", required=True)
    parser.add_argument(
        "--source-commit", action="append", required=True, help="选中的源提交，可重复"
    )
    parser.add_argument("--new-base", required=True, help="新基线 ref")
    parser.add_argument("--tip", default="HEAD", help="重放后的分支 tip")
    parser.add_argument("--path", action="append", default=[], help="限定路径，可重复")
    parser.add_argument("--accept", help="已解释残差的清单文件")
    parser.add_argument("--cap", type=int, default=0, help="每个文件最多列几行，0 表示全列")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()

    repo = Path(args.repo)
    paths = args.path or ["python", "test"]
    src_added, src_removed = source_side(repo, args.source_commit, paths)
    new_added, new_removed = replay_side(repo, args.new_base, args.tip, paths)
    rules = load_accept(args.accept)

    raw_missing = {i for i in src_added - new_added if not accepted(i, rules)}
    raw_kept = {i for i in src_removed - new_removed if not accepted(i, rules)}
    tip_lines: Dict[str, Set[str]] = {}
    for path in {p for p, _ in raw_missing | raw_kept}:
        blob = subprocess.run(
            ["git", "-C", str(repo), "show", f"{args.tip}:{path}"],
            capture_output=True,
            text=True,
            check=False,
        )
        tip_lines[path] = (
            {normalize(x) for x in blob.stdout.splitlines()} if blob.returncode == 0 else set()
        )
    present = {i for i in raw_missing if i[1] in tip_lines[i[0]]}
    added_elsewhere = {line for _, line in new_added}
    moved = {i for i in raw_missing - present if i[1] in added_elsewhere}
    missing = raw_missing - present - moved
    extra = {i for i in new_added - src_added if not accepted(i, rules)}
    extra -= {(p, line) for p, line in extra if line in {m[1] for m in moved}}
    kept = {i for i in raw_kept if i[1] in tip_lines[i[0]]}

    report = [
        f"# 重放语义残差：{args.new_base}..{args.tip}",
        "",
        f"源侧 {len(args.source_commit)} 笔提交，净加 {len(src_added)} 行、净删 "
        f"{len(src_removed)} 行；重放侧净加 {len(new_added)} 行、净删 {len(new_removed)} 行。"
        f"已解释规则 {len(rules)} 条。已滤掉：仍在 tip 同一文件的源侧加行 {len(present)} 行，"
        f"tip 文件里已不存在的源侧删行 {len(raw_kept) - len(kept)} 行。",
        "",
        *render("漏迁（源侧加了、重放侧没有）", missing, args.cap),
        *render("搬家（源侧加在此文件、重放侧加在别的文件，复核不阻塞）", moved, args.cap),
        *render("新造（重放侧加了、源侧没有）", extra, args.cap),
        *render("该删没删（源侧删了、重放侧还留着）", kept, args.cap),
    ]
    text = "\n".join(report) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)

    total = len(missing) + len(kept)
    print(
        f"残差：漏迁 {len(missing)} 行，该删没删 {len(kept)} 行，搬家 {len(moved)} 行，"
        f"新造 {len(extra)} 行",
        file=sys.stderr,
    )
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
