#!/usr/bin/env python3
"""Apply the memtrack patch inside the pod. Idempotent + reversible.

Run:     python3 /tmp/memtrack_patch/apply_patch.py
Restore: python3 /tmp/memtrack_patch/apply_patch.py --restore
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SG = os.environ.get("SG_DIR", "/sgl-workspace/sglang/python/sglang")
UTILS = os.path.join(SG, "srt", "utils")
MR = os.path.join(SG, "srt", "model_executor", "model_runner.py")
BAK = MR + ".memtrack.bak"
MARKER = "memory-analysis skill (BEGIN)"


def restore():
    if os.path.exists(BAK):
        shutil.copyfile(BAK, MR)
        print(f"[restore] {MR} <- {BAK}")
    for fn in ("gpu_memory_tracker.py", "param_memory_dump.py"):
        p = os.path.join(UTILS, fn)
        if os.path.exists(p):
            os.remove(p)
            print(f"[restore] removed {p}")


def apply():
    for fn in ("gpu_memory_tracker.py", "param_memory_dump.py"):
        shutil.copyfile(os.path.join(HERE, fn), os.path.join(UTILS, fn))
        print(f"[stage] {os.path.join(UTILS, fn)}")
    if not os.path.exists(BAK):
        shutil.copyfile(MR, BAK)
        print(f"[backup] {BAK}")
    with open(MR, "r") as f:
        body = f.read()
    if MARKER in body:
        print("[skip] inject block already present")
    else:
        with open(os.path.join(HERE, "inject_block.txt")) as f:
            block = f.read()
        with open(MR, "a") as f:
            f.write(block)
        print(f"[inject] appended block to {MR}")
    for p in (MR, os.path.join(UTILS, "gpu_memory_tracker.py"),
              os.path.join(UTILS, "param_memory_dump.py")):
        if subprocess.run([sys.executable, "-m", "py_compile", p]).returncode != 0:
            print(f"[ERROR] py_compile failed: {p}")
            sys.exit(1)
    print("[ok] patch applied and compiles")


if __name__ == "__main__":
    restore() if "--restore" in sys.argv else apply()
