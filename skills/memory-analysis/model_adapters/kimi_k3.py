"""Kimi-K3 adapter (multimodal; hybrid MLA + linear-attention; fp8 MoE).

This adapter classifies BOTH naming schemes into one shared, fusion-aware set of
categories so a HuggingFace checkpoint and a sglang runtime weight dump line up:

- HF checkpoint names: `language_model.model...block_sparse_moe.experts.{e}.w{1,2,3}`,
  MLA `q_a_proj`/`kv_a_proj_with_mqa` (separate), linear-attn `q/k/v/g_proj`
  (separate), dense `mlp.gate_proj`/`up_proj`.
- sglang runtime names: experts stacked+fused into `mlp.experts.w13_weight` /
  `w2_weight` (+ `_weight_scale`/`_weight_bias`/`gemmN_*`), MLA fused into
  `fused_qkv_a_proj_with_mqa`, linear-attn fused into `fused_qkvg_proj`, dense
  `mlp.gate_up_proj`, `block_sparse_moe.*` -> `mlp.*`.

Unified categories (gate+up collapsed to `w13`, q_a+kv_a to `mla.qkv_a_fused`,
etc.) let the per-category diff compare like with like. The language model
interleaves TWO attention types, so their projections live under separate
namespaces: `mla.*` (full/MLA layers) and `lin_attn.*` (gated-delta linear
layers). `o_proj` and `g_proj` are spelled identically in both, so a
whole-checkpoint prescan (`layer_type_map`) tags each layer and `disambiguate`
routes those two into `mla.o_proj`/`mla.g_proj` vs
`lin_attn.o_proj`/`lin_attn.g_proj`. Note: on the HF theory side the linear
`g_proj` is a SEPARATE tensor, so `lin_attn.qkv_fused` holds q+k+v only — at
runtime sglang may pack g as the 4th shard of `fused_qkvg_proj`
(`use_full_rank_gate`), but that is a runtime fusion, not part of the qkv total.
"""

from typing import Dict, List, Optional, Tuple

import re

from .base import MapEntry, ModelAdapter, register


# Per-layer attention type detection. Kimi-K3's language model interleaves two
# attention types; `o_proj` / `g_proj` are named identically in both, so we must
# know each layer's type to route them. These sub-names are UNIQUE to one type
# (in either HF or sglang-runtime spelling) and never appear in the other.
_MLA_MARKERS = frozenset({
    "q_a_proj", "kv_a_proj_with_mqa", "fused_qkv_a_proj_with_mqa",
    "q_b_proj", "kv_b_proj", "q_a_layernorm", "kv_a_layernorm",
})
_LIN_MARKERS = frozenset({
    "q_proj", "k_proj", "v_proj", "f_a_proj", "f_b_proj", "b_proj",
    "A_log", "dt_bias", "o_norm", "fused_qkvg_proj", "fused_qkvbfg_a_proj",
})
_SELF_ATTN_SUB = re.compile(r"\.layers\.(\d+)\.self_attn\.([A-Za-z0-9_]+)")

# o_proj / g_proj base categories that must be re-tagged per attention type.
_AMBIGUOUS = {"attn.o_proj": "o_proj", "attn.g_proj": "g_proj"}


@register
class KimiK3Adapter(ModelAdapter):
    name = "kimi_k3"

    def layer_type_map(self, names: List[str]) -> Dict[int, str]:
        """Prescan every tensor name to tag each layer 'mla' or 'lin'. Works on
        both HF checkpoint names and sglang runtime names (marker sets cover
        both spellings). A conv1d sub (`q_conv1d` etc.) also marks a linear
        layer."""
        tags: Dict[int, str] = {}
        for n in names:
            m = _SELF_ATTN_SUB.search(n)
            if not m:
                continue
            layer, sub = int(m.group(1)), m.group(2)
            if sub in _MLA_MARKERS:
                tags[layer] = "mla"
            elif sub in _LIN_MARKERS or "conv" in sub:
                tags.setdefault(layer, "lin")
        return tags

    def disambiguate(self, name: str, category: str, layer_tag: Optional[str]) -> str:
        """Route the type-shared o_proj/g_proj into the per-attention-type
        category (mla.* vs lin_attn.*) using the prescanned layer tag."""
        suffix = _AMBIGUOUS.get(category)
        if suffix and layer_tag in ("mla", "lin"):
            prefix = "mla" if layer_tag == "mla" else "lin_attn"
            return f"{prefix}.{suffix}"
        return category

    def extra_rules(self) -> List[Tuple[str, str]]:
        return [
            # --- MoE expert auxiliary tensors (must precede weight rules) ---
            # fp8 block scales -> same .__quant__ bucket as the HF .weight_scale
            # companions, so theory and runtime scales compare directly.
            (r"mlp\.experts\.w13_weight_scale", "moe.expert.w13.__quant__"),
            (r"mlp\.experts\.w2_weight_scale", "moe.expert.w2.__quant__"),
            # per-expert bias / activation params are genuinely runtime-only state
            (r"mlp\.experts\.w\d*_weight_bias", "moe.expert.bias"),
            (r"mlp\.experts\.gemm\d*_(alpha|beta|clamp)", "moe.expert.aux"),
            # --- MoE expert weights (unified: gate+up -> w13, down -> w2) ---
            (r"block_sparse_moe\.experts\.\d+\.w1(?:\.|$)", "moe.expert.w13"),
            (r"block_sparse_moe\.experts\.\d+\.w3(?:\.|$)", "moe.expert.w13"),
            (r"block_sparse_moe\.experts\.\d+\.w2(?:\.|$)", "moe.expert.w2"),
            (r"mlp\.experts\.w13_weight\b", "moe.expert.w13"),
            (r"mlp\.experts\.w2_weight\b", "moe.expert.w2"),
            # --- router (both schemes) ---
            (r"(block_sparse_moe|mlp)\.gate\.", "moe.router"),
            # --- shared experts (gate+up unified) ---
            (r"shared_experts\.gate_up_proj", "moe.shared.gate_up"),
            (r"shared_experts\.gate_proj", "moe.shared.gate_up"),
            (r"shared_experts\.up_proj", "moe.shared.gate_up"),
            (r"shared_experts\.down_proj", "moe.shared.down"),
            # --- grouped routed expert ---
            (r"routed_expert_up_proj", "moe.routed.up_proj"),
            (r"routed_expert_down_proj", "moe.routed.down_proj"),
            (r"routed_expert_norm", "moe.routed.norm"),
            # --- dense MLP (gate+up unified) ---
            (r"(^|\.)mlp\.gate_up_proj", "mlp.gate_up"),
            (r"(^|\.)mlp\.gate_proj", "mlp.gate_up"),
            (r"(^|\.)mlp\.up_proj", "mlp.gate_up"),
            (r"(^|\.)mlp\.down_proj", "mlp.down"),
            # --- MLA attention (q_a + kv_a fused at runtime) ---
            (r"self_attn\.fused_qkv_a_proj_with_mqa", "mla.qkv_a_fused"),
            (r"self_attn\.q_a_proj", "mla.qkv_a_fused"),
            (r"self_attn\.kv_a_proj_with_mqa", "mla.qkv_a_fused"),
            (r"self_attn\.q_b_proj", "mla.q_b_proj"),
            (r"self_attn\.kv_b_proj", "mla.kv_b_proj"),
            (r"self_attn\.q_a_layernorm", "mla.q_a_layernorm"),
            (r"self_attn\.kv_a_layernorm", "mla.kv_a_layernorm"),
            # g_proj / o_proj exist in BOTH attention types in HF (93 each). Emit a
            # neutral base category here; `disambiguate()` re-tags per layer type
            # into mla.* vs lin_attn.* using the whole-checkpoint layer prescan.
            (r"self_attn\.g_proj", "attn.g_proj"),
            # --- linear / gated-delta attention (q/k/v fused at runtime; g is a
            # SEPARATE shard, so this category holds q+k+v only) ---
            (r"self_attn\.fused_qkvg_proj", "lin_attn.qkv_fused"),
            (r"self_attn\.qkv_proj\.", "lin_attn.qkv_fused"),  # runtime fused q/k/v
            (r"self_attn\.[qkv]_proj\.", "lin_attn.qkv_fused"),  # HF split q/k/v
            (r"self_attn\.f_a_proj", "lin_attn.f_a_proj"),
            (r"self_attn\.f_b_proj", "lin_attn.f_b_proj"),
            (r"self_attn\.b_proj", "lin_attn.b_proj"),
            (r"self_attn\.[qkv]*_?conv", "lin_attn.conv"),
            (r"self_attn\.A_log", "lin_attn.A_log"),
            (r"self_attn\.dt_bias", "lin_attn.dt_bias"),
            (r"self_attn\.o_norm", "lin_attn.o_norm"),
            # --- residual proj / norm (incl. runtime output_attn_res_*) ---
            (r"(self_attention|output_attn)_res_proj", "res.attn_proj"),
            (r"(self_attention|output_attn)_res_norm", "res.attn_norm"),
            (r"mlp_res_proj", "res.mlp_proj"),
            (r"mlp_res_norm", "res.mlp_norm"),
            # --- vision tower + mm projector ---
            (r"^vision_tower\..*wqkv", "vision.attn_qkv"),
            (r"^vision_tower\..*\.wo\.", "vision.attn_o"),
            (r"^vision_tower\..*mlp\.fc", "vision.mlp"),
            (r"^vision_tower\..*(patch_embed|pos_emb)", "vision.patch_embed"),
            (r"^vision_tower\..*(norm|layernorm)", "vision.norm"),
            (r"^vision_tower\.", "vision.other"),
            (r"^mm_projector", "mm_projector"),
        ]

    def mapping(self) -> Dict[str, MapEntry]:
        # `tp` here is the STRUCTURAL shard axis (resolved to a numeric degree
        # from the launch config, never from a dump): moe_ep / attn_tp / tensor /
        # replicated. Values marked "hypothesis" are structural guesses to be
        # confirmed against config/source -- if the diff shows a MISMATCH, that is
        # a real finding, not something to fit away by editing the axis.
        m = super().mapping()
        m.update({
            "moe.expert.w13": MapEntry("mlp.experts.w13_weight (stacked fp8)",
                                       "stacked", "moe_ep", note="HF w1(gate)+w3(up)"),
            "moe.expert.w2": MapEntry("mlp.experts.w2_weight (stacked fp8)",
                                      "stacked", "moe_ep", note="HF w2(down)"),
            "moe.expert.aux": MapEntry("experts.gemm*_{alpha,beta,clamp}", tp="replicated",
                                       note="per-expert activation scalars (runtime only)"),
            "moe.expert.bias": MapEntry("experts.w*_weight_bias", tp="moe_ep",
                                        note="per-expert output bias (runtime only, f32)"),
            "moe.shared.gate_up": MapEntry("shared_experts.gate_up_proj", "fused",
                                           "tensor", note="hypothesis: TP-sharded"),
            "moe.shared.down": MapEntry("shared_experts.down_proj", tp="tensor",
                                        note="hypothesis: TP-sharded"),
            "moe.routed.up_proj": MapEntry("routed_expert_up_proj", tp="tensor",
                                           note="hypothesis: verify axis vs source"),
            "moe.routed.down_proj": MapEntry("routed_expert_down_proj", tp="tensor",
                                             note="hypothesis: verify axis vs source"),
            "moe.routed.norm": MapEntry("routed_expert_norm.weight", tp="replicated"),
            "moe.router": MapEntry("mlp.gate.weight", tp="replicated",
                                   note="+e_score_correction_bias"),
            "mlp.gate_up": MapEntry("mlp.gate_up_proj", "fused", "tensor"),
            "mlp.down": MapEntry("mlp.down_proj", tp="tensor"),
            "mla.qkv_a_fused": MapEntry("fused_qkv_a_proj_with_mqa", "fused",
                                        "attn_tp", note="HF q_a_proj+kv_a_proj_with_mqa"),
            "mla.q_b_proj": MapEntry("q_b_proj", tp="attn_tp"),
            "mla.kv_b_proj": MapEntry("kv_b_proj", tp="attn_tp"),
            "mla.g_proj": MapEntry("g_proj (MLA layers)", tp="attn_tp",
                                   note="gated-attn output gate, MLA layers only"),
            "mla.o_proj": MapEntry("o_proj (MLA layers)", tp="attn_tp"),
            "mla.q_a_layernorm": MapEntry("q_a_layernorm.weight", tp="replicated"),
            "mla.kv_a_layernorm": MapEntry("kv_a_layernorm.weight", tp="replicated"),
            "lin_attn.qkv_fused": MapEntry("fused_qkvg_proj[q,k,v]", "fused", "attn_tp",
                                           note="HF q+k+v; g is a separate shard "
                                                "(fused_qkvg_proj[3]) -> lin_attn.g_proj"),
            "lin_attn.g_proj": MapEntry("g_proj / fused_qkvg_proj[3] (linear layers)",
                                        tp="attn_tp",
                                        note="gated-delta output gate, linear layers"),
            "lin_attn.o_proj": MapEntry("o_proj (linear layers)", tp="attn_tp"),
            "lin_attn.f_a_proj": MapEntry("f_a_proj", tp="attn_tp"),
            "lin_attn.f_b_proj": MapEntry("f_b_proj", tp="attn_tp"),
            "lin_attn.b_proj": MapEntry("b_proj", tp="attn_tp"),
            "lin_attn.conv": MapEntry("qkv_convNd", tp="attn_tp"),
            "lin_attn.A_log": MapEntry("A_log", tp="replicated"),
            "lin_attn.dt_bias": MapEntry("dt_bias", tp="replicated"),
            "lin_attn.o_norm": MapEntry("o_norm.weight", tp="replicated"),
            "res.attn_proj": MapEntry("self_attention_res_proj", tp="replicated"),
            "res.mlp_proj": MapEntry("mlp_res_proj", tp="replicated"),
            "res.attn_norm": MapEntry("self_attention_res_norm.weight", tp="replicated"),
            "res.mlp_norm": MapEntry("mlp_res_norm.weight", tp="replicated"),
            "mm_projector": MapEntry("mm_projector.*", tp="replicated"),
            "vision.patch_embed": MapEntry("vision_tower.patch_embed.*", tp="replicated"),
            "vision.attn_qkv": MapEntry("vision_tower...wqkv.weight", tp="replicated"),
            "vision.attn_o": MapEntry("vision_tower...wo.weight", tp="replicated"),
            "vision.mlp": MapEntry("vision_tower...mlp.fc*", tp="replicated"),
            "vision.norm": MapEntry("vision_tower...norm", tp="replicated"),
        })
        return m
