"""Parse a k8s deployment yaml to recover the sglang launch command and infer
which startup stages will run, so hooks can be placed only where relevant.

This is offline and deterministic: it reads the yaml, finds the container
command/args that launch sglang, and maps the presence of certain flags to the
startup stages defined by gpu_memory_tracker's module_pairs (NCCL init, model
load, quantization, kv cache, attention backend, warmup, cuda graph, eagle
draft, ...).
"""

import re
import sys
from typing import Dict, List, Optional

# Flag/condition -> stage label (aligned with gpu_memory_tracker.module_pairs).
# A stage is always-on unless it has a `flag` gate.
STAGES = [
    ("CUDA Context", None),
    ("NCCL/Distributed Init", None),
    ("Model Weights Loading", None),
    ("TorchAO Quantization", "quant"),
    ("KV Cache Allocation", None),
    ("cuBLAS Workspace", None),
    ("Attention Backend Init", None),
    ("Kernel Warmup", None),
    ("CUDA Graph Capture", "cuda_graph"),
    ("Piecewise CUDA Graph", "piecewise"),
    ("Symmetric Memory Pool", "symm_mem"),
    ("[Draft] phases", "eagle"),
]


def _load_yaml(path: str) -> dict:
    try:
        import yaml
    except ImportError:
        raise SystemExit("PyYAML required: pip install pyyaml")
    with open(path) as f:
        docs = [d for d in yaml.safe_load_all(f) if d]
    # pick the first doc containing a pod template with containers
    for d in docs:
        if _find_containers(d):
            return d
    return docs[0] if docs else {}


def _find_containers(obj) -> List[dict]:
    """Recursively locate a `containers:` list anywhere in the manifest."""
    found: List[dict] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "containers" and isinstance(v, list):
                found.extend(v)
            else:
                found.extend(_find_containers(v))
    elif isinstance(obj, list):
        for it in obj:
            found.extend(_find_containers(it))
    return found


def extract_launch(path: str) -> Dict:
    doc = _load_yaml(path)
    containers = _find_containers(doc)
    launch = {"command": [], "args": [], "container": None, "raw": ""}
    for c in containers:
        cmd = (c.get("command") or []) + (c.get("args") or [])
        blob = " ".join(str(x) for x in cmd)
        if "launch_server" in blob or "sglang" in blob:
            launch.update(command=c.get("command") or [], args=c.get("args") or [],
                          container=c.get("name"), raw=blob)
            break
    return launch


def infer_stages(launch_blob: str) -> List[str]:
    b = launch_blob.lower()
    gates = {
        "quant": any(k in b for k in ("quant", "fp8", "torchao", "w8a8", "awq", "gptq")),
        "cuda_graph": "disable-cuda-graph" not in b,
        "piecewise": "piecewise" in b or "torch-compile" in b or "enable-torch-compile" in b,
        "symm_mem": "symm" in b or "symmetric" in b,
        "eagle": "speculative" in b or "eagle" in b or "draft" in b,
    }
    out = []
    for label, flag in STAGES:
        if flag is None or gates.get(flag):
            out.append(label)
    return out


def _shell_bindings(blob: str) -> Dict[str, str]:
    """Collect variable bindings from the launch script blob.

    Both spellings matter: `export VAR=value` and the equally common
    `VAR=value` on one line with a bare `export VAR` on the next. Without the
    latter, a launch that says `--tp-size "$TP_SIZE"` cannot be resolved and the
    parallel degrees silently fall back to 1, which would make every row of the
    weight diff a false MISMATCH.
    """
    binds = {}
    for name, val in re.findall(r"export\s+([A-Za-z_]\w*)=([^\n]*)", blob):
        binds[name] = val.strip().strip('"').strip("'")
    for name, val in re.findall(r"(?m)^[ \t]*([A-Za-z_]\w*)=([^\s#]*)[ \t]*$",
                                blob):
        binds.setdefault(name, val.strip().strip('"').strip("'"))
    return binds


def _expand_shell(value: str, binds: Dict[str, str], depth: int = 0) -> str:
    """Expand ${VAR}/$VAR references and $((arith)) using the export bindings
    (launch scripts often say `--model-path ${MODEL_PATH}` with the export a
    few lines above). Purely textual; unknown vars are left as-is."""
    if depth > 5 or "$" not in value:
        return value

    def _sub_var(m):
        name = m.group(1) or m.group(2)
        if name in binds:
            return _expand_shell(binds[name], binds, depth + 1)
        return m.group(0)

    def _sub_arith(m):
        expr = re.sub(r"\$?\{?([A-Za-z_]\w*)\}?", _sub_name, m.group(1))
        if re.fullmatch(r"[\d\s+*/%()-]+", expr):
            try:
                return str(int(eval(expr)))  # digits/operators only
            except Exception:
                pass
        return m.group(0)

    def _sub_name(m):
        name = m.group(1)
        if name in binds:
            return _expand_shell(binds[name], binds, depth + 1)
        return m.group(0)

    value = re.sub(r"\$\(\(([^()]+(?:\([^()]*\)[^()]*)*)\)\)", _sub_arith, value)
    value = re.sub(r"\$\{(\w+)\}|\$(\w+)", _sub_var, value)
    return value


def parse_arg(launch_blob: str, name: str) -> Optional[str]:
    m = re.search(rf"--{re.escape(name)}[= ]([^\s]+)", launch_blob)
    if not m:
        return None
    # Values are frequently quoted (`--tp-size "$TP_SIZE"`); strip the quotes on
    # both sides of the expansion so the result is a bare value.
    val = m.group(1).strip('"').strip("'")
    return _expand_shell(val, _shell_bindings(launch_blob)).strip('"').strip("'")


def parse_parallel_config(launch_blob: str) -> Dict[str, int]:
    """Extract the parallelism degrees from the launch command.

    These come straight from the operator's launch flags (an INDEPENDENT source
    from any runtime memory dump) and are what the diff uses to *predict* per-rank
    weight sizes. Never infer these from a dump -- that would make the diff
    circular. Missing flags default to 1.
    """
    def _int(name, default=1):
        v = parse_arg(launch_blob, name)
        try:
            return int(v) if v is not None else default
        except ValueError:
            return default

    tp = _int("tp-size")
    ep = _int("ep-size")
    # sglang server_args semantics: with an all-to-all MoE backend (deepep) and
    # no explicit --ep-size, ep_size is set to tp_size (server_args.py:
    # `self.ep_size = self.tp_size`). This is a SOURCE-derived degree, not a
    # dump-derived one, so using it keeps the diff non-circular.
    a2a = parse_arg(launch_blob, "moe-a2a-backend")
    if ep == 1 and a2a and a2a.lower() in ("deepep", "mooncake"):
        ep = tp
    return {
        "tp": tp,
        "ep": ep,
        "dcp": _int("dcp-size"),
        "dp": _int("dp-size"),
    }


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        raise SystemExit("usage: analyze_startup_stages.py <deploy.yaml>")
    launch = extract_launch(argv[0])
    if not launch["raw"]:
        raise SystemExit("no sglang launch command found in yaml")
    print("sglang launch:", launch["raw"])
    print("container:", launch["container"])
    for k in ("tp-size", "dp-size", "ep-size", "attention-backend",
              "quantization", "mem-fraction-static"):
        v = parse_arg(launch["raw"], k)
        if v:
            print(f"  --{k} = {v}")
    print("\ninferred stages:")
    for s in infer_stages(launch["raw"]):
        print("  -", s)


if __name__ == "__main__":
    main()
