"""Prepare + validate tracker/weight-stats hooks for a sglang source tree.

Core robustness features:

1. Hook-point validation + fallback. sglang forks rename ModelRunner methods, so
   each startup stage is described by a LIST of candidate method names. Before a
   run, `validate_hooks()` parses the target model_runner.py and reports which
   stage each candidate resolves to (or misses). The injected block itself also
   resolves candidates at *runtime* and skips (with a warning) any stage whose
   candidates are all absent -> graceful degrade instead of a crash.

2. The injected block is generated from STAGE_SPEC so the skill and the patched
   pod always agree on what gets wrapped.

Canonical stages (role-aware): labels may contain `{role}` which resolves to
`target` / `draft` at call time from `self.is_draft_worker`, so ONE wrap of
e.g. `load_model` yields the canonical `load_target_model` / `load_draft_model`
stages. The full canonical list (mirrored in gpu_memory_tracker.module_pairs
and report_memory.CANONICAL_STAGES):

  initial, nccl_init, load_target_model, load_draft_model,
  alloc_target_kv_cache, alloc_draft_kv_cache, configure_aux_hidden,
  target_build_attention_backends, prepare_replicated_q_proj,
  draft_build_attention_backends, target_cuda_graph, draft_cuda_graph

configure_aux_hidden / build_attention_backends are wrapped as model_runner
MODULE GLOBALS (the injected block lives in model_runner.py, so it can rebind
the names `init_attention_backends` looks up at call time); the draft-side
attention backends + draft cuda graph are wrapped on EagleDraftWorker (lazy).

Fine-grained trace extras (back-port of aiak_sglang commit 491ed25b + the
5-bucket cuda-graph breakdown):

- DeepEP buffer allocation trace: wraps `Buffer.__init__` in the sglang deepep
  token-dispatcher module and logs the exact nvl/rdma byte sizes (main
  *non-torch* allocation during MoE init).
- CUDA graph capture ledger (`SGLANG_CAPTURE_MEM_LEDGER=1`): per-batch-size
  driver / torch-reserved / non-torch deltas, `[capture-mem-ledger] bs=N: ...`.
- Capture allocator snapshot (`SGLANG_CAPTURE_MEM_SNAPSHOT_DIR=<dir>`): torch
  allocator history across capture(), dumped as
  `capture_mem_{target|draft}_tp{rank}.pickle`.
- cuda_graph_setup sub-stage snapshots (before/after_create_for_model_runner,
  after_EagerRunner, after_capture_prefill_graph, after_DecodeGraphCapture).
- `[cg-breakdown]` lines (always on with tracking) feeding the 5-bucket
  cuda-graph decomposition in report_memory:
    runner_init      -> attention graph state + static buffers (torch alloc)
    torch_graph_pool -> private-pool segment bytes delta across capture()
    capture_total    -> driver/alloc/reserved/non-torch totals per capture()
  DeepEP/NVSHMEM comes from the DeepEP alloc lines inside the capture window;
  graphExec instantiation is estimated in the report from the per-bs ledger.

Idempotency vs forks that already contain commit 491ed25b natively: the
line-identical features (DeepEP alloc line, ledger, snapshot dump, sub-stage
snapshot labels) check a SOURCE MARKER and defer to the native instrumentation
instead of double-wrapping. Canonical stage labels and `[cg-breakdown]` lines
do not exist natively, so they are always installed and never collide.
"""

import glob as _glob
import os
import re
import shutil
from typing import Dict, List, Optional, Tuple

# Each stage: snapshot labels (aligned with gpu_memory_tracker.module_pairs) plus
# an ordered list of candidate ModelRunner method names (first present wins).
# `{role}` in a label resolves to target/draft from self.is_draft_worker.
STAGE_SPEC = [
    {"before": "before_nccl_init", "after": "after_nccl_init",
     "methods": ["init_torch_distributed", "init_distributed",
                 "init_torch_distributed_environment"]},
    {"before": "before_load_{role}_model", "after": "after_load_{role}_model",
     "methods": ["load_model", "load_weights", "init_model"],
     "dump_after": True},
    {"before": "before_alloc_{role}_kv_cache", "after": "after_alloc_{role}_kv_cache",
     "methods": ["init_memory_pool", "alloc_memory_pool", "init_kv_cache",
                 "initialize_kv_cache"]},
    {"before": "before_prepare_replicated_q_proj",
     "after": "after_prepare_replicated_q_proj",
     "methods": ["_prepare_replicated_q_proj"],
     # model-specific (Kimi MLA); forks without it skip the stage
     "optional": True},
    {"before": "before_kernel_warmup", "after": "after_kernel_warmup",
     "methods": ["maybe_precompile_model_kernels_after_loading",
                 "precompile_kernels", "kernel_warmup", "warmup"]},
    {"before": "before_{role}_cuda_graph", "after": "after_{role}_cuda_graph",
     "methods": ["init_device_graphs", "init_cuda_graphs", "init_cuda_graph", "capture_cuda_graph",
                 "capture"], "summary_after": True},
]

# model_runner MODULE GLOBALS wrapped by the injected block (call-time lookup
# from init_attention_backends). role_from_mr: resolve {role} from the
# model_runner= kwarg / first positional arg.
GLOBAL_WRAP_SPEC = [
    {"global": "configure_aux_hidden_state_capture",
     "before": "before_configure_aux_hidden", "after": "after_configure_aux_hidden"},
    {"global": "build_attention_backends",
     "before": "before_{role}_build_attention_backends",
     "after": "after_{role}_build_attention_backends", "role_from_mr": True},
]

# Fine-grained trace extras: (feature, source marker, file glob under sglang_src).
# If the marker is found in the fork's source the commit is native and the
# injected block will NOT wrap that feature (no double logging).
EXTRA_MARKERS = [
    ("deepep_buffer_trace", "Allocating DeepEP buffer",
     "**/layers/moe/token_dispatcher/deepep.py"),
    ("capture_mem_ledger", "capture-mem-ledger",
     "**/model_executor/**/*cuda_graph_runner.py"),
    ("capture_mem_snapshot", "SGLANG_CAPTURE_MEM_SNAPSHOT_DIR",
     "**/model_executor/**/*cuda_graph_runner.py"),
    ("cuda_graph_substages", "before_create_for_model_runner",
     "**/model_executor/**/cuda_graph_setup.py"),
]


def _defined_methods(src_text: str) -> set:
    return set(re.findall(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", src_text, re.M))


def validate_hooks(model_runner_path: str) -> Dict:
    """Parse model_runner.py; resolve each stage to a present method or None.
    Also checks the module-global wrap targets."""
    with open(model_runner_path, "r", errors="ignore") as f:
        text = f.read()
    defined = _defined_methods(text)
    # Mixin methods (e.g. init_memory_pool in model_runner_kv_cache_mixin.py)
    # are inherited by the runtime class, so sibling model_runner_*.py files
    # count as present for static validation too.
    _dir = os.path.dirname(os.path.abspath(model_runner_path))
    for sib in sorted(_glob.glob(os.path.join(_dir, "model_runner_*.py"))):
        try:
            with open(sib, "r", errors="ignore") as f:
                defined |= _defined_methods(f.read())
        except OSError:
            pass
    resolved, missing, optional_missing = [], [], []
    for st in STAGE_SPEC:
        hit = next((m for m in st["methods"] if m in defined), None)
        if hit:
            resolved.append((st, hit))
        elif st.get("optional"):
            optional_missing.append(st)
        else:
            missing.append(st)
    globals_ok = {g["global"]: (g["global"] in text) for g in GLOBAL_WRAP_SPEC}
    return {"resolved": resolved, "missing": missing,
            "optional_missing": optional_missing, "defined": defined,
            "globals": globals_ok}


def print_validation(report: Dict) -> str:
    lines = ["# Hook-point validation"]
    for st, hit in report["resolved"]:
        lines.append(f"  [OK]   {st['before']}/{st['after']:<38} -> {hit}()")
    for st in report["missing"]:
        lines.append(f"  [MISS] {st['before']}/{st['after']:<38} -> none of "
                     f"{st['methods']} (stage will be skipped)")
    for st in report.get("optional_missing", []):
        lines.append(f"  [SKIP] {st['before']}/{st['after']:<38} -> optional "
                     f"stage absent in this fork (not counted as MISS)")
    for g, ok in report.get("globals", {}).items():
        lines.append(f"  [{'OK' if ok else 'MISS'}]{'  ' if ok else ''} "
                     f"module-global {g} "
                     f"{'' if ok else '(falls back to init_attention_backends wrap)'}")
    cov = len(report["resolved"])
    lines.append(f"coverage: {cov}/{len(STAGE_SPEC)} stages")
    return "\n".join(lines)


def validate_extras(sglang_src: str) -> str:
    """Report, per fine-grained trace feature, whether the fork already has the
    aiak commit natively (patch defers) or the injected block will wrap it."""
    lines = ["# Fine-grained trace extras validation"]
    for feat, marker, pat in EXTRA_MARKERS:
        hits = _glob.glob(os.path.join(sglang_src, pat), recursive=True)
        native = False
        for p in hits:
            try:
                with open(p, "r", errors="ignore") as f:
                    if marker in f.read():
                        native = True
                        break
            except OSError:
                continue
        tag = "NATIVE" if native else "WRAP"
        desc = ("fork has commit, wrap skipped" if native
                else "injected block will monkeypatch")
        lines.append(f"  [{tag:<6}] {feat:<24} {desc}")
    lines.append("  [WRAP  ] canonical_stage_labels   always installed (skill-only labels)")
    lines.append("  [WRAP  ] cg_breakdown             always installed (skill-only lines)")
    return "\n".join(lines)


def stage_asset(sglang_src: str, asset_path: str,
                dst_name: str = "gpu_memory_tracker.py") -> str:
    candidates = [
        os.path.join(sglang_src, "python", "sglang", "srt", "utils"),
        os.path.join(sglang_src, "sglang", "srt", "utils"),
        os.path.join(sglang_src, "srt", "utils"),
    ]
    dst_dir = next((c for c in candidates if os.path.isdir(c)), None)
    if dst_dir is None:
        raise FileNotFoundError(f"could not locate sglang/srt/utils under {sglang_src}")
    dst = os.path.join(dst_dir, dst_name)
    shutil.copyfile(asset_path, dst)
    return dst


def render_inject_block() -> str:
    """Generate the self-resolving injection block (candidate-based wrapping)."""
    # Use repr() (a Python literal) -- NOT json.dumps, whose lowercase
    # true/false/null are invalid Python and would crash at import.
    block = _BLOCK_TEMPLATE.replace("__STAGE_SPEC__", repr(STAGE_SPEC))
    block = block.replace("__GLOBAL_WRAP_SPEC__", repr(GLOBAL_WRAP_SPEC))
    return block


_BLOCK_TEMPLATE = '''

# ==================== injected by memory-analysis skill (BEGIN) ====================
# Staged GPU-memory tracking (canonical target/draft stages) + one-shot param dump
# + fine-grained deepep/cuda-graph trace + [cg-breakdown] lines for the 5-bucket
# cuda-graph decomposition. Gated by SGLANG_TRACK_GPU_MEMORY=1; sub-features
# additionally gated by SGLANG_CAPTURE_MEM_LEDGER=1 and
# SGLANG_CAPTURE_MEM_SNAPSHOT_DIR=<dir>. Each stage resolves the FIRST present
# method from a candidate list; `{role}` in labels resolves to target/draft at
# call time. Line-identical features defer to forks that natively carry aiak
# commit 491ed25b (source-marker check). Reversible: delete this block.
import os as _mt_os


def _memtrack_install():
    if _mt_os.environ.get("SGLANG_TRACK_GPU_MEMORY") != "1":
        return
    import logging as _mt_log
    _lg = _mt_log.getLogger("memtrack")
    try:
        from sglang.srt.utils.gpu_memory_tracker import init_global_memory_tracker
        from sglang.srt.utils.param_memory_dump import dump_param_memory_stats
    except Exception as _e:
        _lg.warning(f"[memtrack] import failed: {_e}")
        return
    _tr = init_global_memory_tracker()
    try:
        _tr.snapshot("initial")
    except Exception:
        pass

    def _snap(lbl):
        try:
            _tr.snapshot(lbl)
        except Exception:
            pass

    def _role_of(obj):
        return "draft" if getattr(obj, "is_draft_worker", False) else "target"

    _spec = __STAGE_SPEC__
    _gspec = __GLOBAL_WRAP_SPEC__
    _mrg = globals()  # model_runner module namespace (block appended there)

    # ---------- fine-grained trace extras (deepep buffer / cuda graph) ----------

    def _x_deepep():
        """Log exact nvl/rdma sizes when the DeepEP Buffer is constructed."""
        import inspect as _ins
        from sglang.srt.layers.moe.token_dispatcher import deepep as _dpm
        try:
            if "Allocating DeepEP buffer" in _ins.getsource(_dpm):
                return "native"
        except Exception:
            pass
        _B = getattr(_dpm, "Buffer", None)
        if _B is None:
            return "no Buffer symbol"
        if getattr(_B, "_memtrack_wrapped", False):
            return "already wrapped"
        _oi = _B.__init__

        def _bi(self, group, num_nvl_bytes=0, num_rdma_bytes=0, *a, **k):
            try:
                _gs = group.size() if hasattr(group, "size") else -1
                _lg.warning(
                    "[memtrack] Allocating DeepEP buffer: "
                    "nvl=%.1f MiB, rdma=%.1f MiB (group_size=%d)"
                    % (num_nvl_bytes / 2**20, num_rdma_bytes / 2**20, _gs))
            except Exception:
                pass
            return _oi(self, group, num_nvl_bytes, num_rdma_bytes, *a, **k)

        _B.__init__ = _bi
        _B._memtrack_wrapped = True
        return "wrapped Buffer.__init__"

    def _x_graph_substages():
        """Split the CUDA-graph stage into shared-output/eager/prefill/decode
        sub-phases (same labels as the aiak commit)."""
        import inspect as _ins
        from sglang.srt.model_executor.model_runner_components import (
            cuda_graph_setup as _cgs,
        )
        try:
            if "before_create_for_model_runner" in _ins.getsource(_cgs):
                return "native"
        except Exception:
            pass
        done = []
        _gso = getattr(_cgs, "GraphSharedOutput", None)
        if _gso is not None and hasattr(_gso, "create_for_model_runner"):
            _o = _gso.create_for_model_runner

            def _w_gso(*a, **k):
                _snap("before_create_for_model_runner")
                r = _o(*a, **k)
                _snap("after_create_for_model_runner")
                return r

            _gso.create_for_model_runner = _w_gso
            done.append("create_for_model_runner")
        _er = getattr(_cgs, "EagerRunner", None)
        if _er is not None:
            _oe = _er.__init__

            def _w_er(self, *a, **k):
                r = _oe(self, *a, **k)
                _snap("after_EagerRunner")
                return r

            _er.__init__ = _w_er
            done.append("EagerRunner")
        for _fn, _lbl, _pos in (
            ("capture_prefill_graph", "after_capture_prefill_graph", "after"),
            ("capture_decode_graph", "after_DecodeGraphCapture", "before"),
        ):
            _of = getattr(_cgs, _fn, None)
            if _of is None:
                continue

            def _mk(_of=_of, _lbl=_lbl, _pos=_pos):
                def _w(*a, **k):
                    if _pos == "before":
                        _snap(_lbl)
                        return _of(*a, **k)
                    r = _of(*a, **k)
                    _snap(_lbl)
                    return r
                return _w

            setattr(_cgs, _fn, _mk())
            done.append(_fn)
        return "wrapped " + ",".join(done) if done else "nothing to wrap"

    def _x_eagle():
        """Draft-side canonical stages: draft_build_attention_backends +
        draft_cuda_graph on the eagle draft worker (labels are skill-only, so
        no native-marker deference needed)."""
        from sglang.srt.speculative import eagle_worker_v2 as _ew
        _cls = next((getattr(_ew, n, None) for n in
                     ("EagleDraftWorker", "EAGLEWorker", "EagleWorker")
                     if getattr(_ew, n, None) is not None), None)
        if _cls is None:
            return "no eagle worker class"
        done = []
        _mn = next((n for n in ("init_attention_backend",
                                "init_attention_backends")
                    if hasattr(_cls, n)), None)
        if _mn:
            _om = getattr(_cls, _mn)

            def _w_ab(self, *a, __om=_om, **k):
                _snap("before_draft_build_attention_backends")
                r = __om(self, *a, **k)
                _snap("after_draft_build_attention_backends")
                return r

            setattr(_cls, _mn, _w_ab)
            done.append(f"attn->{_mn}")
        if hasattr(_cls, "_capture_cuda_graphs"):
            _og = _cls._capture_cuda_graphs

            def _w_cg(self, *a, **k):
                _snap("before_draft_cuda_graph")
                r = _og(self, *a, **k)
                _snap("after_draft_cuda_graph")
                try:
                    _tr.print_summary()
                except Exception:
                    pass
                return r

            _cls._capture_cuda_graphs = _w_cg
            done.append("graphs->_capture_cuda_graphs")
        return "wrapped " + ",".join(done) if done else "nothing to wrap"

    def _x_capture_runner():
        """Per-runner-class instrumentation on decode/draft cuda-graph runners:
        [cg-breakdown] runner_init / torch_graph_pool / capture_total lines
        (always), per-bs ledger (env-gated, defers to native), allocator
        snapshot dump (env-gated, defers to native)."""
        import inspect as _ins
        import torch as _t

        def _tp_rank(self):
            try:
                from sglang.srt.runtime_context import get_parallel
                return get_parallel().tp_rank
            except Exception:
                return getattr(getattr(self, "model_runner", None), "tp_rank", 0)

        def _pool_bytes():
            # bytes held by PRIVATE allocator pools (cuda-graph pools)
            try:
                _tot = 0
                for _s in _t.cuda.memory_snapshot():
                    _pid = _s.get("segment_pool_id", (0, 0))
                    if tuple(_pid) != (0, 0):
                        _tot += _s.get("total_size", 0)
                return _tot
            except Exception:
                return None

        _classes = []
        for _mn, _cn in (
            ("sglang.srt.model_executor.runner.decode_cuda_graph_runner",
             "DecodeCudaGraphRunner"),
            ("sglang.srt.speculative.eagle_draft_cuda_graph_runner",
             "EAGLEDraftCudaGraphRunner"),
            ("sglang.srt.model_executor.cuda_graph_runner", "CudaGraphRunner"),
        ):
            try:
                _m = __import__(_mn, fromlist=[_cn])
                _c = getattr(_m, _cn, None)
                if _c is not None and _c not in _classes:
                    _classes.append(_c)
            except Exception:
                continue
        if not _classes:
            return "no runner class found"

        _want_ledger = _mt_os.environ.get("SGLANG_CAPTURE_MEM_LEDGER") == "1"
        _snapdir = _mt_os.environ.get("SGLANG_CAPTURE_MEM_SNAPSHOT_DIR", "")
        notes = []

        def _wrap_cls(_cls):
            _cn = _cls.__name__
            got = []
            try:
                _src = _ins.getsource(_cls)
            except Exception:
                _src = ""

            # --- [cg-breakdown] runner_init: attention graph state + static bufs
            _oi = _cls.__init__

            def _w_init(self, *a, __oi=_oi, __cn=_cn, **k):
                try:
                    _a0 = _t.cuda.memory_allocated()
                    _f0, _ = _t.cuda.mem_get_info()
                    _r0 = _t.cuda.memory_reserved()
                    _ok = True
                except Exception:
                    _ok = False
                r = __oi(self, *a, **k)
                if _ok:
                    try:
                        _a1 = _t.cuda.memory_allocated()
                        _f1, _ = _t.cuda.mem_get_info()
                        _r1 = _t.cuda.memory_reserved()
                        _lg.warning(
                            "[cg-breakdown] runner_init: torch_alloc +%.1f MiB, "
                            "non_torch +%.1f MiB (attention graph state + "
                            "static buffers, cls=%s)"
                            % ((_a1 - _a0) / 2**20,
                               ((_f0 - _f1) - (_r1 - _r0)) / 2**20, __cn))
                    except Exception:
                        pass
                return r

            _cls.__init__ = _w_init
            got.append("runner_init")

            # --- capture(): breakdown always; snapshot dump env-gated
            if hasattr(_cls, "capture"):
                _oc = _cls.capture
                _native_snap = "SGLANG_CAPTURE_MEM_SNAPSHOT_DIR" in _src
                _do_snap = bool(_snapdir) and not _native_snap

                def _w_cap(self, *a, __oc=_oc, __cn=_cn, __ds=_do_snap, **k):
                    try:
                        _f0, _ = _t.cuda.mem_get_info()
                        _a0 = _t.cuda.memory_allocated()
                        _r0 = _t.cuda.memory_reserved()
                        _p0 = _pool_bytes()
                        _ok = True
                    except Exception:
                        _ok = False
                    if __ds:
                        try:
                            _t.cuda.memory._record_memory_history(
                                max_entries=1_000_000)
                        except Exception as _e:
                            _lg.warning(
                                f"[memtrack] record_memory_history failed: {_e}")
                            __ds = False
                    try:
                        return __oc(self, *a, **k)
                    finally:
                        if _ok:
                            try:
                                _f1, _ = _t.cuda.mem_get_info()
                                _a1 = _t.cuda.memory_allocated()
                                _r1 = _t.cuda.memory_reserved()
                                _p1 = _pool_bytes()
                                if _p0 is not None and _p1 is not None:
                                    _lg.warning(
                                        "[cg-breakdown] torch_graph_pool: "
                                        "+%.1f MiB (private-pool segments, "
                                        "cls=%s)"
                                        % ((_p1 - _p0) / 2**20, __cn))
                                _lg.warning(
                                    "[cg-breakdown] capture_total: "
                                    "driver +%.1f MiB, torch_alloc +%.1f MiB, "
                                    "torch_reserved +%.1f MiB, "
                                    "non_torch +%.1f MiB (cls=%s)"
                                    % ((_f0 - _f1) / 2**20,
                                       (_a1 - _a0) / 2**20,
                                       (_r1 - _r0) / 2**20,
                                       ((_f0 - _f1) - (_r1 - _r0)) / 2**20,
                                       __cn))
                            except Exception:
                                pass
                        if __ds:
                            try:
                                _mt_os.makedirs(_snapdir, exist_ok=True)
                                _role = _role_of(
                                    getattr(self, "model_runner", None))
                                _p = _mt_os.path.join(
                                    _snapdir,
                                    f"capture_mem_{_role}_tp{_tp_rank(self)}"
                                    ".pickle")
                                _t.cuda.memory._dump_snapshot(_p)
                                _lg.warning(
                                    "[memtrack] dumped capture memory "
                                    f"snapshot to {_p}")
                            except Exception as _e:
                                _lg.warning(
                                    f"[memtrack] snapshot dump failed: {_e}")
                            try:
                                _t.cuda.memory._record_memory_history(
                                    enabled=None)
                            except Exception:
                                pass

                _cls.capture = _w_cap
                got.append("capture")

            # --- per-bs ledger (env-gated, defer to native)
            if _want_ledger:
                if "capture-mem-ledger" in _src:
                    got.append("ledger=native")
                else:
                    _one = next((n for n in ("capture_one_shape",
                                             "capture_one_batch_size")
                                 if hasattr(_cls, n)), None)
                    if _one:
                        _oo = getattr(_cls, _one)

                        def _w_one(self, size, *a, __oo=_oo, **k):
                            try:
                                _do = _tp_rank(self) == 0
                                if _do:
                                    _f0, _ = _t.cuda.mem_get_info()
                                    _r0 = _t.cuda.memory_reserved()
                            except Exception:
                                _do = False
                            r = __oo(self, size, *a, **k)
                            if _do:
                                try:
                                    _f1, _ = _t.cuda.mem_get_info()
                                    _r1 = _t.cuda.memory_reserved()
                                    _lg.warning(
                                        "[capture-mem-ledger] bs=%d: driver "
                                        "+%.1f MiB (torch reserved +%.1f MiB, "
                                        "non-torch +%.1f MiB)"
                                        % (size, (_f0 - _f1) / 2**20,
                                           (_r1 - _r0) / 2**20,
                                           ((_f0 - _f1) - (_r1 - _r0)) / 2**20))
                                except Exception:
                                    pass
                            return r

                        setattr(_cls, _one, _w_one)
                        got.append(f"ledger->{_one}")
            return f"{_cn}({','.join(got)})"

        for _cls in _classes:
            try:
                notes.append(_wrap_cls(_cls))
            except Exception as _e:
                notes.append(f"{_cls.__name__}(failed: {_e})")
        return "; ".join(notes)

    _extras = {"done": False}

    def _install_extras():
        # Deferred to the first wrapped-stage call so every sglang module is
        # importable (no import cycles at model_runner import time), yet still
        # earlier than deepep buffer alloc / cuda graph capture / eagle worker
        # construction.
        for _name, _fn in (("deepep", _x_deepep),
                           ("graph_substages", _x_graph_substages),
                           ("eagle_worker", _x_eagle),
                           ("capture_runner", _x_capture_runner)):
            try:
                _lg.warning(f"[memtrack] extras {_name}: {_fn()}")
            except Exception as _e:
                _lg.warning(f"[memtrack] extras {_name} failed: {_e}")

    # ---------------------------------------------------------------------------

    def _wrap(stage):
        name = next((m for m in stage["methods"] if hasattr(ModelRunner, m)), None)
        if name is None:
            _lg.warning(f"[memtrack] MISS stage {stage['before']} "
                        f"(none of {stage['methods']}), skipped")
            return
        orig = getattr(ModelRunner, name)
        before, after = stage["before"], stage["after"]
        dump_after = stage.get("dump_after"); summary_after = stage.get("summary_after")

        def w(self, *a, **k):
            if not _extras["done"]:
                _extras["done"] = True
                _install_extras()
            _role = _role_of(self)
            _snap(before.replace("{role}", _role))
            r = orig(self, *a, **k)
            _snap(after.replace("{role}", _role))
            if dump_after:
                try:
                    dump_param_memory_stats(self.model)
                except Exception as _e:
                    _lg.warning(f"[memtrack] dump failed: {_e}")
            if summary_after and _role == "target":
                try:
                    _tr.print_summary()
                except Exception:
                    pass
            return r

        w.__name__ = name
        setattr(ModelRunner, name, w)
        _lg.warning(f"[memtrack] OK stage {before}/{after} -> {name}()")

    def _wrap_global(gs):
        gname = gs["global"]
        fn = _mrg.get(gname)
        if not callable(fn):
            _lg.warning(f"[memtrack] MISS module-global {gname}, skipped")
            return False
        before, after = gs["before"], gs["after"]
        role_from_mr = gs.get("role_from_mr")

        def gw(*a, __fn=fn, **k):
            if role_from_mr:
                _mr = k.get("model_runner") or (a[0] if a else None)
                _role = _role_of(_mr)
            else:
                _role = "target"
            _snap(before.replace("{role}", _role))
            r = __fn(*a, **k)
            _snap(after.replace("{role}", _role))
            return r

        _mrg[gname] = gw
        _lg.warning(f"[memtrack] OK global {before}/{after} -> {gname}()")
        return True

    for _st in _spec:
        _wrap(_st)
    _g_res = {_gs["global"]: _wrap_global(_gs) for _gs in _gspec}
    if not _g_res.get("build_attention_backends"):
        # Older forks without the module-global split: fall back to wrapping the
        # whole init_attention_backends as the build stage.
        _wrap({"before": "before_{role}_build_attention_backends",
               "after": "after_{role}_build_attention_backends",
               "methods": ["init_attention_backends", "init_attention_backend"]})
    _lg.warning("[memtrack] startup tracking install complete")


_memtrack_install()
# ==================== injected by memory-analysis skill (END) ======================
'''


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "--validate":
        print(print_validation(validate_hooks(sys.argv[2])))
    elif len(sys.argv) >= 2 and sys.argv[1] == "--validate-extras":
        print(validate_extras(sys.argv[2]))
    elif len(sys.argv) >= 2 and sys.argv[1] == "--render":
        print(render_inject_block())
    else:
        print("usage: inject_hooks.py --validate <model_runner.py> | "
              "--validate-extras <sglang_src> | --render")
