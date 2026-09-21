#!/usr/bin/env python3
"""变异探针：证明核对脚本真的拦得住，以及拦不住什么。

「核对通过」只有在核对本身会因为真缺陷变红时才有意义。做法是逐个往一个已知合格的分支里
种入一个缺陷，跑 verify_platform_contract.py，看它是否变红：

``CAUGHT``   变红了，这一类缺陷有覆盖。
``SURVIVED`` 没变红。要么是盲点（表里写明 expect_caught=False，说明留给运行时取数或人工
             评审），要么是覆盖退化了——那就是核对脚本的 bug。

变异表里每一行对应一类真实发生过的缺陷，不是凭空造的语法错。全部在一次性 worktree 里做，
原分支不动。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

SUMMARY = "变异探针：往合格分支里种入已知缺陷，看核对是否变红"
SRT = "python/sglang/srt"


@dataclass(frozen=True)
class Mutation:
    name: str
    kind: str            # 对应契约里的能力类，盲点写 "-"
    path: str
    old: str
    new: str
    expect_caught: bool
    note: str


MUTATIONS: List[Mutation] = [
    Mutation(
        "删主 server 探针路由", "route.main", f"{SRT}/entrypoints/http_server.py",
        '@app.get("/health_forward")\n', "",
        True, "平台探针 404 的成因，DSv4.1 那次 /ready 就是这么丢的",
    ),
    Mutation(
        "删 dummy server 自省路由", "route.dummy", f"{SRT}/utils/common.py",
        '    @app.get("/get_instance_info")\n', "",
        True, "只补主 server、漏 dummy server，一半拓扑的探针继续挂",
    ),
    Mutation(
        "改指标族名", "metric", f"{SRT}/observability/metrics_collector.py",
        '"sglang:detokenizer_to_tokenizer_time"', '"sglang:detok_to_tok_time"',
        True, "族名漂一个字，面板 PromQL 直接选不到序列",
    ),
    Mutation(
        "删计数器预热", "metric.preheat", f"{SRT}/observability/metrics_collector.py",
        "self.eviction_num_tokens.labels(**labels).inc(0)", "pass",
        True, "带 label 的计数器首次观测前不出现，空闲实例上面板是 No data 不是 0",
    ),
    Mutation(
        "删一条 rid trace 行", "trace", f"{SRT}/managers/data_parallel_controller.py",
        'trace(logger, "dp controller routed request %s to a scheduler", rid)', "pass",
        True, "rid 在某一段断掉，请求堵在哪里就查不出来",
    ),
    Mutation(
        "删 token id dump 点", "token_ids", f"{SRT}/managers/tokenizer_manager.py",
        'log_input_ids(logger, obj.rid, "tokenized", input_ids)', "pass",
        True, "跟平台 dump 逐位比的那一份没了，编码对齐无法复核",
    ),
    Mutation(
        "删日志组件前缀", "log", f"{SRT}/managers/data_parallel_controller.py",
        'configure_logger(server_args, " DPController")', "configure_logger(server_args)",
        True, "厂内日志管道按组件前缀分流，这一路进错解析分支",
    ),
    Mutation(
        "改厂内环境变量名", "env", f"{SRT}/entrypoints/http_server.py",
        '"AIAK_STOP_SIGNAL_DIR"', '"AIAK_STOP_DIR"',
        True, "平台注入的变量找不到读取点，排水钩子静默失效",
    ),
    Mutation(
        "跨进程时间戳换回 perf_counter", "-", f"{SRT}/managers/tokenizer_manager.py",
        "tokenized_obj.dispatch_to_scheduler_time = time.time()",
        "tokenized_obj.dispatch_to_scheduler_time = time.perf_counter()",
        False, "盲点：名字都在、值失真。多机部署下差值无意义，要靠运行时取数发现",
    ),
    Mutation(
        "除法去掉兜零", "-", f"{SRT}/managers/scheduler_components/metrics_reporter.py",
        "max(1, self.scheduler.max_running_requests)", "self.scheduler.max_running_requests",
        False, "盲点：存在性不变，除零要等真实流量或单测才炸",
    ),
]


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败：{proc.stderr.strip()}")
    return proc.stdout


def run_verify(script: Path, worktree: Path, contract: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, str(script),
            "--repo", str(worktree), "--ref", "HEAD",
            "--contract", str(contract), "-o", "/dev/null",
        ],
        capture_output=True, text=True, check=False,
    )


def apply_mutation(worktree: Path, mutation: Mutation) -> Optional[str]:
    """改文件并提交（核对脚本读 ref，不读工作区）。返回失败原因。"""
    target = worktree / mutation.path
    if not target.exists():
        return f"文件不存在：{mutation.path}"
    text = target.read_text(encoding="utf-8")
    hits = text.count(mutation.old)
    if hits != 1:
        return f"锚点命中 {hits} 次，变异表该更新了"
    target.write_text(text.replace(mutation.old, mutation.new), encoding="utf-8")
    git(worktree, "commit", "-q", "--no-verify", "-a", "-m", f"mutation: {mutation.name}")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=SUMMARY)
    parser.add_argument("--repo", required=True, help="源仓库")
    parser.add_argument("--ref", required=True, help="已核对通过的分支或提交")
    parser.add_argument("--contract", required=True)
    parser.add_argument("--worktree", default="/tmp/agent-work/mutation-probe")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()

    repo = Path(args.repo)
    verify = Path(__file__).with_name("verify_platform_contract.py")
    contract = Path(args.contract).resolve()
    worktree = Path(args.worktree)

    if worktree.exists():
        git(repo, "worktree", "remove", str(worktree), "--force")
    git(repo, "worktree", "add", "--detach", str(worktree), args.ref)
    rows: List[str] = []
    failures = 0
    try:
        baseline = run_verify(verify, worktree, contract)
        if baseline.returncode != 0:
            raise SystemExit(
                f"基线就不过，先修分支再探变异：{baseline.stderr.strip().splitlines()[0]}"
            )
        print("基线核对通过，开始逐个种入缺陷", file=sys.stderr)

        for mutation in MUTATIONS:
            problem = apply_mutation(worktree, mutation)
            if problem:
                rows.append(f"| {mutation.name} | {mutation.kind} | 跳过 | {problem} |")
                failures += 1
                continue
            result = run_verify(verify, worktree, contract)
            caught = result.returncode != 0
            verdict = "CAUGHT" if caught else "SURVIVED"
            ok = caught == mutation.expect_caught
            failures += 0 if ok else 1
            mark = "" if ok else "  **与预期不符**"
            rows.append(
                f"| {mutation.name} | {mutation.kind} | {verdict}{mark} | {mutation.note} |"
            )
            print(f"  {verdict:8} {mutation.name}", file=sys.stderr)
            git(worktree, "reset", "-q", "--hard", args.ref)
    finally:
        git(repo, "worktree", "remove", str(worktree), "--force")
        shutil.rmtree(worktree, ignore_errors=True)

    expected_blind = sum(1 for m in MUTATIONS if not m.expect_caught)
    report = [
        f"# 变异探针：{args.ref}",
        "",
        f"变异 {len(MUTATIONS)} 条，其中 {expected_blind} 条是登记在案的盲点。",
        "",
        "| 变异 | 能力类 | 结果 | 这类缺陷在线上的样子 |",
        "|---|---|---|---|",
        *rows,
        "",
        "盲点不是放着不管：值失真那一类只能靠造流量后取 `/metrics` 前后 diff，"
        "或者该指标的单测来接。",
    ]
    text = "\n".join(report) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if failures:
        print(f"{failures} 条与预期不符，核对脚本的覆盖变了", file=sys.stderr)
        return 1
    print("全部与预期一致", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
