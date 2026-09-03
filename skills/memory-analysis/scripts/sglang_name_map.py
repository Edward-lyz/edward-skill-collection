"""Build the HF-category -> sglang-runtime-name mapping.

The mapping primarily comes from the model adapter (see model_adapters/). When a
sglang source tree is available we additionally scan the target model class for
its `stacked_params_mapping` declaration -- the ground truth for how HF weights
are fused at load time -- and surface it so the adapter's assumptions can be
sanity-checked during verification.
"""

import glob
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class MappingRow:
    category: str
    sglang_hint: str
    fusion: str
    tp: str
    note: str


def build_mapping(categories: List[str], adapter) -> List[MappingRow]:
    rows: List[MappingRow] = []
    for cat in sorted(set(categories)):
        is_scale = cat.endswith(".__quant__")
        entry = adapter.lookup(cat)  # resolves the base category for .__quant__
        if entry is None:
            rows.append(MappingRow(cat, "?", "uncertain", "uncertain",
                                   "no adapter rule; verify manually"))
        else:
            hint = entry.sglang_hint + (" (scale)" if is_scale else "")
            note = "fp8 block scale" if is_scale else entry.note
            rows.append(MappingRow(cat, hint, entry.fusion, entry.tp, note))
    return rows


# Match rows of a stacked_params_mapping list, e.g.
#   ("qkv_proj", "q_proj", "q"),
_STACKED_RE = re.compile(
    r"\(\s*[\"']([^\"']+)[\"']\s*,\s*[\"']([^\"']+)[\"']\s*,"
)


def scan_sglang_stacked_mapping(sglang_src: str,
                                model_hint: Optional[str] = None) -> Dict[str, List[str]]:
    """Best-effort scan of sglang model files for stacked_params_mapping.

    Returns {fused_param: [source_suffixes...]}. `model_hint` narrows the file
    search (e.g. 'deepseek', 'kimi'). Purely informational: used to validate the
    adapter, never required for the pipeline to run.
    """
    if not sglang_src or not os.path.isdir(sglang_src):
        return {}
    patterns = ["**/models/*.py"]
    if model_hint:
        patterns.insert(0, f"**/models/*{model_hint.lower()}*.py")
    files: List[str] = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(sglang_src, p), recursive=True))
    fused: Dict[str, List[str]] = {}
    for fp in sorted(set(files)):
        try:
            with open(fp, "r", errors="ignore") as f:
                txt = f.read()
        except OSError:
            continue
        if "stacked_params_mapping" not in txt:
            continue
        # capture the region after the assignment
        idx = txt.find("stacked_params_mapping")
        region = txt[idx: idx + 2000]
        for fused_name, src in _STACKED_RE.findall(region):
            fused.setdefault(fused_name, [])
            if src not in fused[fused_name]:
                fused[fused_name].append(src)
    return fused
