"""Generic module taxonomy for transformer weight tensors.

The goal is to bucket individual tensors (from a HuggingFace checkpoint or a
sglang runtime dump) into a small, stable set of *module categories* so that a
DeepSeek/Kimi style MLA+MoE model and a vanilla Llama style MHA+dense model can
be compared with the same vocabulary.

Classification is rule driven so new architectures only need a new rule row (or
a per-model adapter override) instead of touching the analysis pipeline. Rules
are matched top to bottom; the first matching regex wins, so put the specific
patterns (MLA projections, MoE experts) before the generic ones.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class TensorInfo:
    """One physical tensor as it exists on disk / in memory."""

    name: str
    shape: List[int]
    dtype: str
    nbytes: int

    @property
    def numel(self) -> int:
        n = 1
        for d in self.shape:
            n *= d
        return n


# (compiled_regex, category). Order matters: first match wins.
# Categories are intentionally coarse -- fine grained per-layer detail is kept
# separately via the layer index extracted below.
DEFAULT_RULES: List[Tuple[str, str]] = [
    # --- embeddings / head ---
    (r"(^|\.)embed_tokens\.", "embedding"),
    (r"(^|\.)lm_head\.", "lm_head"),
    # --- MLA (DeepSeek / Kimi) attention projections ---
    (r"self_attn\.q_a_proj\.", "attn.q_a_proj"),
    (r"self_attn\.q_b_proj\.", "attn.q_b_proj"),
    (r"self_attn\.q_a_layernorm\.", "attn.q_a_layernorm"),
    (r"self_attn\.kv_a_proj_with_mqa\.", "attn.kv_a_proj"),
    (r"self_attn\.kv_a_layernorm\.", "attn.kv_a_layernorm"),
    (r"self_attn\.kv_b_proj\.", "attn.kv_b_proj"),
    (r"self_attn\.q_proj\.", "attn.q_proj"),  # MLA w/o LoRA q
    # --- classic MHA / GQA attention projections ---
    (r"self_attn\.(k_proj)\.", "attn.k_proj"),
    (r"self_attn\.(v_proj)\.", "attn.v_proj"),
    (r"self_attn\.(o_proj)\.", "attn.o_proj"),
    (r"self_attn\..*layernorm", "attn.layernorm"),
    # --- MoE ---
    (r"mlp\.gate\.(weight|e_score_correction_bias)", "moe.router"),
    (r"mlp\.shared_experts?\..*gate_proj", "moe.shared.gate_proj"),
    (r"mlp\.shared_experts?\..*up_proj", "moe.shared.up_proj"),
    (r"mlp\.shared_experts?\..*down_proj", "moe.shared.down_proj"),
    (r"mlp\.experts\.\d+\..*gate_proj", "moe.expert.gate_proj"),
    (r"mlp\.experts\.\d+\..*up_proj", "moe.expert.up_proj"),
    (r"mlp\.experts\.\d+\..*down_proj", "moe.expert.down_proj"),
    # --- dense MLP ---
    (r"mlp\.gate_proj\.", "mlp.gate_proj"),
    (r"mlp\.up_proj\.", "mlp.up_proj"),
    (r"mlp\.down_proj\.", "mlp.down_proj"),
    # --- norms ---
    (r"input_layernorm\.", "norm.input"),
    (r"post_attention_layernorm\.", "norm.post_attn"),
    (r"(^|\.)norm\.weight$", "norm.final"),
    (r"layernorm|layer_norm|\.norm\.", "norm.other"),
]

# Suffixes that mark a quantization companion tensor rather than the weight
# itself. We keep them in their own sub-bucket so a category's byte total is not
# polluted by fp8 scales.
QUANT_SUFFIXES = (
    ".weight_scale_inv",
    ".weight_scale",
    ".scale",
    ".input_scale",
    ".weight_zero_point",
)

_LAYER_RE = re.compile(r"\.layers\.(\d+)\.")

# Substitutions to collapse the *repeated* dimensions (per-layer, per-expert,
# per-encoder-block) of an HF tensor name into a single module template, so a
# stack of identical layers / experts / vision blocks is de-duplicated to one row.
_LAYER_SUB = re.compile(r"\.layers\.\d+\.")
_EXPERT_SUB = re.compile(r"\.experts\.\d+\.")
_BLOCK_SUB = re.compile(r"\.blocks\.\d+\.")


def module_template(name: str) -> str:
    """Normalize an HF tensor name to a module template by collapsing the layer,
    expert and encoder-block indices (e.g.
    `model.layers.3.self_attn.q_a_proj.weight` ->
    `model.layers.{L}.self_attn.q_a_proj.weight`, and
    `vision_tower.encoder.blocks.9.wo.weight` ->
    `vision_tower.encoder.blocks.{B}.wo.weight`). Names that repeat only in one of
    these indices therefore map to a single template."""
    t = _LAYER_SUB.sub(".layers.{L}.", name)
    t = _EXPERT_SUB.sub(".experts.{E}.", t)
    t = _BLOCK_SUB.sub(".blocks.{B}.", t)
    return t


@dataclass
class CategoryAgg:
    category: str
    count: int = 0
    total_bytes: int = 0
    dtypes: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    layers: set = field(default_factory=set)
    example: str = ""
    shapes: set = field(default_factory=set)

    def add(self, t: TensorInfo, layer: Optional[int]):
        self.count += 1
        self.total_bytes += t.nbytes
        self.dtypes[t.dtype] += t.nbytes
        if layer is not None:
            self.layers.add(layer)
        if not self.example:
            self.example = t.name
        if len(self.shapes) < 4:
            self.shapes.add(tuple(t.shape))

    def shape_repr(self) -> str:
        """One representative shape, noting if the category holds several."""
        if not self.shapes:
            return ""
        shown = sorted(self.shapes)
        s = str(list(shown[0]))
        if len(self.shapes) > 1:
            s += f" (+{len(self.shapes) - 1})"
        return s


class Taxonomy:
    """Rule based classifier. `extra_rules` (from an adapter) are tried first.

    Some tensors cannot be classified from their name alone -- e.g. `o_proj` /
    `g_proj` exist in BOTH the MLA and the linear-attention layers of a hybrid
    model and must land in different categories per layer type. For those, an
    `adapter` may provide two optional hooks:
      - `layer_type_map(names) -> {layer_idx: tag}`  (a whole-checkpoint prescan)
      - `disambiguate(base_name, category, layer_tag) -> category`
    When present, classification becomes context-aware; otherwise it stays a pure
    per-name regex.
    """

    def __init__(self, extra_rules: Optional[List[Tuple[str, str]]] = None,
                 adapter=None):
        rules = list(extra_rules or []) + DEFAULT_RULES
        self._rules = [(re.compile(p), c) for p, c in rules]
        self._adapter = adapter

    @staticmethod
    def is_quant_companion(name: str) -> bool:
        return any(name.endswith(s) for s in QUANT_SUFFIXES)

    @staticmethod
    def layer_of(name: str) -> Optional[int]:
        m = _LAYER_RE.search(name)
        return int(m.group(1)) if m else None

    def _layer_types(self, tensors: List[TensorInfo]) -> Dict[int, str]:
        """Prescan the tensor list for the adapter's per-layer type tags. Returns
        an empty map when the adapter offers no `layer_type_map` hook."""
        fn = getattr(self._adapter, "layer_type_map", None)
        if not fn:
            return {}
        try:
            return fn([t.name for t in tensors]) or {}
        except Exception:
            return {}

    def classify(self, name: str, layer_types: Optional[Dict[int, str]] = None) -> str:
        base = name
        for suf in QUANT_SUFFIXES:
            if base.endswith(suf):
                base = base[: -len(suf)]
                break
        for rx, cat in self._rules:
            if rx.search(base):
                cat_out = cat
                break
        else:
            cat_out = "other"
        dis = getattr(self._adapter, "disambiguate", None)
        if dis:
            tag = (layer_types or {}).get(self.layer_of(base))
            try:
                cat_out = dis(base, cat_out, tag) or cat_out
            except Exception:
                pass
        if base != name:  # was a quant companion
            cat_out += ".__quant__"
        return cat_out

    def aggregate(self, tensors: List[TensorInfo]) -> Dict[str, CategoryAgg]:
        lt = self._layer_types(tensors)
        out: Dict[str, CategoryAgg] = {}
        for t in tensors:
            cat = self.classify(t.name, lt)
            agg = out.setdefault(cat, CategoryAgg(cat))
            agg.add(t, self.layer_of(t.name))
        return out

    def aggregate_detailed(self, tensors: List[TensorInfo]) -> Dict[tuple, list]:
        """Group by (category, shape, dtype) -> [count, total_bytes, {layers}] for
        the non-aggregated (shape-listing) table."""
        lt = self._layer_types(tensors)
        out: Dict[tuple, list] = {}
        for t in tensors:
            key = (self.classify(t.name, lt), tuple(t.shape), t.dtype)
            e = out.setdefault(key, [0, 0, set()])
            e[0] += 1
            e[1] += t.nbytes
            lay = self.layer_of(t.name)
            if lay is not None:
                e[2].add(lay)
        return out

    def aggregate_by_module(self, tensors: List[TensorInfo]) -> Dict[str, dict]:
        """Group tensors by their HF module template (layer/expert indices
        collapsed), de-duplicating repeated layers/experts into one row.

        Each value carries: count (#instances), total_bytes (across all
        instances), a representative shape/dtype, the set of distinct layers, and
        the taxonomy category the module falls in."""
        lt = self._layer_types(tensors)
        out: Dict[str, dict] = {}
        for t in tensors:
            key = module_template(t.name)
            e = out.setdefault(key, {
                "count": 0, "total_bytes": 0, "shapes": set(),
                "dtypes": defaultdict(int), "layers": set(),
                "category": self.classify(t.name, lt),
            })
            e["count"] += 1
            e["total_bytes"] += t.nbytes
            e["shapes"].add(tuple(t.shape))
            e["dtypes"][t.dtype] += t.nbytes
            lay = self.layer_of(t.name)
            if lay is not None:
                e["layers"].add(lay)
        return out
