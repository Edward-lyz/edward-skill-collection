"""Auto-derive a model_adapters/<name>.py skeleton from a sglang source tree.

For precise theory<->runtime alignment each new model needs an adapter that maps
BOTH the HF component names and the sglang fused/runtime names onto one shared
category. The ground truth for the fusion is the model class' `stacked_params_
mapping` (fused_param <- [source components]). This tool scans that mapping and
emits an adapter skeleton: for every fused param it creates a unified category
and rules for the fused name AND each source component, with a best-effort `tp`
guess. The result is a STARTING POINT to refine against a real runtime dump.
"""

import os
import re
import sys

from sglang_name_map import scan_sglang_stacked_mapping


def _guess_tp(name: str) -> str:
    """Best-effort STRUCTURAL axis guess from the name (a hypothesis to verify
    against config/source -- never against a dump). Returns a logical axis token."""
    n = name.lower()
    if "expert" in n or n.startswith("w13") or n.startswith("w2"):
        return "moe_ep"
    if "norm" in n or "bias" in n or "scale" in n or "rotary" in n:
        return "replicated"
    if "self_attn" in n or "attention" in n or n.startswith("attn"):
        return "attn_tp"
    return "tensor"


def _cat_for(fused: str) -> str:
    base = fused.strip(".").split(".")[-1].replace("_weight", "").replace("_proj", "")
    base = re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_") or "misc"
    if "expert" in fused.lower() or base in ("w13", "w2"):
        return f"moe.expert.{base}"
    return f"attn_mlp.{base}"


def derive(sglang_src: str, model_hint: str, out_name: str) -> str:
    fused = scan_sglang_stacked_mapping(sglang_src, model_hint=model_hint)
    if not fused:
        raise SystemExit(f"no stacked_params_mapping found under {sglang_src} "
                         f"(hint={model_hint})")
    rules, mapping, seen = [], [], set()
    for fused_name, sources in sorted(fused.items()):
        cat = _cat_for(fused_name)
        tp = _guess_tp(fused_name)
        # runtime fused name
        rules.append(f'            (r"{re.escape(fused_name.strip("."))}", "{cat}"),')
        # HF source components
        for s in sources:
            rules.append(f'            (r"{re.escape(s.strip("."))}", "{cat}"),')
        if cat not in seen:
            seen.add(cat)
            mapping.append(f'            "{cat}": MapEntry("{fused_name.strip(".")}", '
                           f'"fused", "{tp}", note="auto-derived; verify"),')
    cls = "".join(p.capitalize() for p in re.split(r"[^a-z0-9]+", out_name.lower()) if p)
    text = _TEMPLATE.replace("__NAME__", out_name).replace("__CLASS__", cls) \
        .replace("__RULES__", "\n".join(rules)).replace("__MAPPING__", "\n".join(mapping))
    return text


_TEMPLATE = '''"""Auto-derived adapter for __NAME__ (from sglang stacked_params_mapping).

GENERATED SKELETON -- refine `tp` per category against a real runtime weight dump
(look for `size mismatch` / `only in ...` rows in the diff), and split any
runtime-only tensors (bias/scale) into their own categories.
"""

from typing import Dict, List, Tuple

from .base import MapEntry, ModelAdapter, register


@register
class __CLASS__Adapter(ModelAdapter):
    name = "__NAME__"

    def extra_rules(self) -> List[Tuple[str, str]]:
        return [
__RULES__
        ]

    def mapping(self) -> Dict[str, MapEntry]:
        m = super().mapping()
        m.update({
__MAPPING__
        })
        return m
'''


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("usage: derive_adapter.py <sglang_src> <model_hint> <out_name> "
              "[out_dir]")
        sys.exit(1)
    src, hint, name = sys.argv[1:4]
    out_dir = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model_adapters")
    text = derive(src, hint, name)
    out = os.path.join(out_dir, f"{name}.py")
    with open(out, "w") as f:
        f.write(text)
    print(f"[written] {out}")
