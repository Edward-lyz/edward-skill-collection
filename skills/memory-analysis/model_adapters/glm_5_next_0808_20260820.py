"""GLM-5-Next-0808-20260820 adapter (multimodal; hybrid MLA/DSA + gated-delta
linear attention; fp8 MoE with 288 routed + 1 shared expert; NextN/MTP layer).

Refined from the auto-derived skeleton against a real runtime dump
(`K3_param_memory_stats_gpu0_Glm5NextForConditionalGeneration_*.log`, tp=ep=8).
Only the NAME mapping was corrected from that dump; every shard AXIS below is
read off the sglang source in the running image, never fitted to the measured
bytes:

  * `models/deepseek_v2.py` DeepseekV2AttentionMLA -- fused_qkv_a_proj_with_mqa
    = ReplicatedLinear, q_b_proj / kv_b_proj = ColumnParallelLinear,
    o_proj = RowParallelLinear.
  * `models/glm5_next.py` linear-attn layer -- qkv_proj = QKVParallelLinear,
    qkv_conv1d = MergedColumnParallelLinear, f_b/g_b/b_proj = Column,
    f_a/g_a_proj = ReplicatedLinear, hc_* = nn.Parameter(float32).
  * `layers/attention/dsa/dsa_indexer_kpool.py` -- wq_b / weights_proj /
    index_kpool_* replicated.
  * `models/glm4v.py` vision tower -- mlp.gate_up = MergedColumnParallel,
    mlp.down = RowParallel, merger.proj = Replicated, patch_embed = Conv3d.
  * routed experts go through FusedMoE with ep_size from the launch (EP axis);
    shared experts are a plain DeepseekV2MLP (TP axis) because the launch passes
    --disable-shared-experts-fusion.

Naming: HF prefixes the LM with `model.language_model.` and the tower with
`model.visual.`; the runtime drops those to `model.` / `visual.`. Rules below are
prefix-agnostic so both sides land in the same category.

MTP/NextN: the HF checkpoint carries one extra decoder layer (eh_proj / enorm /
hnorm / shared_head, plus its own attention + 288 experts). The launch sets no
speculative algorithm, so sglang never loads it. `layer_type_map` tags that
layer and `disambiguate` folds ALL of its tensors into `mtp.nextn_layer`, so it
shows up as one honest "only in HF" row instead of skewing every other category.
"""

from typing import Dict, List, Optional, Tuple

import re

from .base import MapEntry, ModelAdapter, register

# Sub-names unique to one attention type; `o_proj` exists in BOTH and is routed
# per layer by disambiguate().
_MLA_MARKERS = frozenset({
    "q_a_proj", "kv_a_proj_with_mqa", "fused_qkv_a_proj_with_mqa",
    "q_b_proj", "kv_b_proj", "q_a_layernorm", "kv_a_layernorm", "indexer",
})
_LIN_MARKERS = frozenset({
    "q_proj", "k_proj", "v_proj", "f_a_proj", "f_b_proj", "g_a_proj",
    "g_b_proj", "b_proj", "A_log", "dt_bias", "o_norm", "qkv_proj",
})
_SELF_ATTN_SUB = re.compile(r"\.layers\.(\d+)\.self_attn\.([A-Za-z0-9_]+)")
_LAYER_RE = re.compile(r"\.layers\.(\d+)\.")
# Tensors that only exist in the NextN/MTP layer of the checkpoint.
_MTP_MARKERS = ("eh_proj", "enorm", "hnorm", "shared_head")


@register
class Glm5Next080820260820Adapter(ModelAdapter):
    name = "glm_5_next_0808_20260820"

    def layer_type_map(self, names: List[str]) -> Dict[int, str]:
        """Tag every decoder layer 'mla' / 'lin' / 'mtp'. Works on both naming
        schemes; 'mtp' wins because the NextN layer is itself an MLA layer."""
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
        for n in names:
            if any(k in n for k in _MTP_MARKERS):
                m = _LAYER_RE.search(n)
                if m:
                    tags[int(m.group(1))] = "mtp"
        return tags

    def disambiguate(self, name: str, category: str,
                     layer_tag: Optional[str]) -> str:
        if layer_tag == "mtp":
            return "mtp.nextn_layer"
        if category == "attn.o_proj_amb":
            if layer_tag == "mla":
                return "mla.o_proj"
            if layer_tag == "lin":
                return "lin.o_proj"
            return "attn.o_proj"
        return category

    def extra_rules(self) -> List[Tuple[str, str]]:
        # First match wins, so the order is: MTP markers -> vision tower ->
        # MoE -> attention -> dense MLP. The vision block also owns
        # `mlp.gate_proj`/`down_proj` names, hence it must precede the LM MLP.
        return [
            # --- NextN / MTP layer (HF only under this launch) ---
            (r"\.eh_proj|\.enorm\.|\.hnorm\.|shared_head\.", "mtp.nextn_layer"),
            # --- vision tower ---
            (r"visual\.rotary_pos_emb", "visual.rotary_cache"),
            (r"visual\.patch_embed", "visual.patch_embed"),
            (r"visual\.downsample\.bias", "visual.bias_replicated"),
            (r"visual\.downsample\.weight", "visual.downsample"),
            (r"visual\.merger\.post_projection_norm\.bias",
             "visual.bias_replicated"),
            (r"visual\.merger\.post_projection_norm", "visual.norm"),
            (r"visual\.merger\.(gate_up_proj|gate_proj|up_proj)",
             "visual.merger_gate_up"),
            (r"visual\.merger\.down_proj", "visual.merger_down"),
            (r"visual\.merger\.proj", "visual.merger_proj"),
            (r"visual\.post_layernorm", "visual.norm"),
            (r"visual\.blocks\.\d+\.attn\.(qkv|qkv_proj)\.", "visual.attn_qkv"),
            (r"visual\.blocks\.\d+\.attn\.proj\.bias", "visual.bias_replicated"),
            (r"visual\.blocks\.\d+\.attn\.proj\.weight", "visual.attn_out"),
            (r"visual\.blocks\.\d+\.attn\.[qk]_norm", "visual.norm"),
            (r"visual\.blocks\.\d+\.mlp\.(gate_up_proj|gate_proj|up_proj)",
             "visual.mlp_gate_up"),
            (r"visual\.blocks\.\d+\.mlp\.down_proj\.bias",
             "visual.bias_replicated"),
            (r"visual\.blocks\.\d+\.mlp\.down_proj\.weight", "visual.mlp_down"),
            (r"visual\.blocks\.\d+\.norm\d", "visual.norm"),
            # --- MoE: fp8 block scales share the weight's .__quant__ bucket ---
            (r"experts\.w13_weight_scale", "moe.expert.w13.__quant__"),
            (r"experts\.w2_weight_scale", "moe.expert.w2.__quant__"),
            (r"mlp\.experts\.w13_weight", "moe.expert.w13"),
            (r"mlp\.experts\.w2_weight", "moe.expert.w2"),
            (r"mlp\.experts\.\d+\.(gate_proj|up_proj)", "moe.expert.w13"),
            (r"mlp\.experts\.\d+\.down_proj", "moe.expert.w2"),
            (r"mlp\.(gate|experts)\.e_score_correction_bias", "moe.router"),
            (r"mlp\.gate\.weight", "moe.router"),
            (r"shared_experts\.(gate_up_proj|gate_proj|up_proj)",
             "moe.shared.gate_up"),
            (r"shared_experts\.down_proj", "moe.shared.down"),
            # --- MLA / DSA attention ---
            (r"self_attn\.fused_qkv_a_proj_with_mqa", "mla.qkv_a_fused"),
            (r"self_attn\.q_a_proj", "mla.qkv_a_fused"),
            (r"self_attn\.kv_a_proj_with_mqa", "mla.qkv_a_fused"),
            (r"self_attn\.q_b_proj", "mla.q_b_proj"),
            (r"self_attn\.kv_b_proj", "mla.kv_b_proj"),
            (r"self_attn\.(q_a_layernorm|kv_a_layernorm)", "mla.norm"),
            (r"self_attn\.indexer\.", "mla.indexer"),
            (r"self_attn\.attn_m(ha|qa)\.[kv]_scale", "attn.kv_scale"),
            # --- gated-delta linear attention ---
            (r"self_attn\.[qkv]*_?conv1d", "lin.conv"),
            (r"self_attn\.qkv_proj\.", "lin.qkv_fused"),
            (r"self_attn\.[qkv]_proj\.", "lin.qkv_fused"),
            (r"self_attn\.(f_a_proj|g_a_proj)", "lin.a_proj"),
            (r"self_attn\.(f_b_proj|g_b_proj|b_proj)", "lin.b_proj"),
            (r"self_attn\.(A_log|dt_bias)", "lin.state_bias"),
            (r"self_attn\.o_norm", "lin.norm"),
            # o_proj lives in both attention types -> routed by disambiguate()
            (r"self_attn\.o_proj", "attn.o_proj_amb"),
            # --- hybrid-connection mixers (nn.Parameter, fp32 at runtime) ---
            (r"\.hc_(attn|ffn)_(fn|base|scale)", "hc.mixer"),
            # --- dense (non-MoE) LM MLP layers ---
            (r"mlp\.gate_up_proj", "mlp.gate_up"),
            (r"mlp\.(gate_proj|up_proj)", "mlp.gate_up"),
            (r"mlp\.down_proj", "mlp.down"),
        ]

    def mapping(self) -> Dict[str, MapEntry]:
        # `tp` is the STRUCTURAL shard axis (tensor -> tp, moe_ep -> ep,
        # replicated -> 1); the numeric degree comes from the launch config.
        # Every axis below is taken from the sglang classes cited in the module
        # docstring, NOT from the measured dump.
        m = super().mapping()
        m.update({
            "embedding": MapEntry("model.embed_tokens.weight", tp="tensor",
                                  note="VocabParallelEmbedding"),
            "lm_head": MapEntry("lm_head.weight", tp="tensor",
                                note="ParallelLMHead"),
            # --- MoE ---
            "moe.expert.w13": MapEntry("mlp.experts.w13_weight (stacked fp8)",
                                       "stacked", "moe_ep",
                                       note="HF gate_proj+up_proj per expert"),
            "moe.expert.w2": MapEntry("mlp.experts.w2_weight (stacked fp8)",
                                      "stacked", "moe_ep",
                                      note="HF down_proj per expert"),
            "moe.router": MapEntry("mlp.gate.weight (+e_score_correction_bias)",
                                   tp="replicated"),
            "moe.shared.gate_up": MapEntry("shared_experts.gate_up_proj",
                                           "fused", "tensor",
                                           note="MergedColumnParallel "
                                                "(--disable-shared-experts-fusion)"),
            "moe.shared.down": MapEntry("shared_experts.down_proj", tp="tensor",
                                        note="RowParallel"),
            # --- dense MLP ---
            "mlp.gate_up": MapEntry("mlp.gate_up_proj", "fused", "tensor",
                                    note="MergedColumnParallel, 3 dense layers"),
            "mlp.down": MapEntry("mlp.down_proj", tp="tensor",
                                 note="RowParallel"),
            # --- MLA / DSA attention (11 layers at runtime) ---
            "mla.qkv_a_fused": MapEntry("fused_qkv_a_proj_with_mqa", "fused",
                                        "replicated",
                                        note="ReplicatedLinear (deepseek_v2.py)"),
            "mla.q_b_proj": MapEntry("q_b_proj", tp="tensor",
                                     note="ColumnParallel"),
            "mla.kv_b_proj": MapEntry("kv_b_proj", tp="tensor",
                                      note="ColumnParallel"),
            "mla.o_proj": MapEntry("o_proj (MLA layers)", tp="tensor",
                                   note="RowParallel"),
            "mla.norm": MapEntry("q_a_layernorm / kv_a_layernorm",
                                 tp="replicated"),
            "mla.indexer": MapEntry("indexer.{wq_b,wk,weights_proj,k_norm,"
                                    "index_kpool_*}", tp="replicated",
                                    note="dsa_indexer_kpool.py; weights_proj "
                                         "upcast to fp32 at runtime"),
            "attn.kv_scale": MapEntry("attn_m{ha,qa}.{k,v}_scale",
                                      tp="replicated",
                                      note="runtime-only fp8 KV scales"),
            # --- gated-delta linear attention (34 layers) ---
            "lin.qkv_fused": MapEntry("qkv_proj", "fused", "tensor",
                                      note="QKVParallelLinear; HF q+k+v"),
            "lin.conv": MapEntry("qkv_conv1d", "fused", "tensor",
                                 note="MergedColumnParallel; fp32 at runtime"),
            "lin.a_proj": MapEntry("f_a_proj / g_a_proj", tp="replicated",
                                   note="ReplicatedLinear"),
            "lin.b_proj": MapEntry("f_b_proj / g_b_proj / b_proj", tp="tensor",
                                   note="ColumnParallel"),
            "lin.state_bias": MapEntry("A_log / dt_bias", tp="tensor",
                                       note="per-head state, sharded with heads"),
            "lin.norm": MapEntry("o_norm.weight", tp="replicated"),
            "lin.o_proj": MapEntry("o_proj (linear layers)", tp="tensor",
                                   note="RowParallel"),
            # --- hybrid connection mixers ---
            "hc.mixer": MapEntry("hc_{attn,ffn}_{fn,base,scale}",
                                 tp="replicated",
                                 note="nn.Parameter(float32); HF stores bf16"),
            # --- NextN / MTP layer, not loaded under this launch ---
            "mtp.nextn_layer": MapEntry("(not loaded)", tp="replicated",
                                        note="whole NextN layer: no "
                                             "speculative algorithm in launch"),
            # --- vision tower ---
            "visual.attn_qkv": MapEntry("visual...attn.qkv_proj", "fused",
                                        "tensor", note="QKVParallelLinear"),
            "visual.attn_out": MapEntry("visual...attn.proj.weight",
                                        tp="tensor", note="RowParallel"),
            "visual.mlp_gate_up": MapEntry("visual...mlp.gate_up_proj", "fused",
                                           "tensor",
                                           note="MergedColumnParallel (+bias)"),
            "visual.mlp_down": MapEntry("visual...mlp.down_proj.weight",
                                        tp="tensor", note="RowParallel"),
            "visual.merger_gate_up": MapEntry("visual.merger.gate_up_proj",
                                              "fused", "tensor"),
            "visual.merger_down": MapEntry("visual.merger.down_proj",
                                           tp="tensor"),
            "visual.merger_proj": MapEntry("visual.merger.proj",
                                           tp="replicated",
                                           note="ReplicatedLinear"),
            "visual.patch_embed": MapEntry("visual.patch_embed.proj",
                                           tp="replicated", note="Conv3d"),
            "visual.downsample": MapEntry("visual.downsample.weight",
                                          tp="replicated", note="Conv2d"),
            "visual.bias_replicated": MapEntry("row-parallel biases",
                                               tp="replicated",
                                               note="bias of RowParallel/"
                                                    "Replicated layers"),
            "visual.norm": MapEntry("visual norms", tp="replicated"),
            "visual.rotary_cache": MapEntry("visual.rotary_pos_emb."
                                            "cos_sin_cache", tp="replicated",
                                            note="runtime-only buffer"),
        })
        return m
