"""GLM-5.2-FP8 (GlmMoeDsaForCausalLM) adapter -- refined from the auto skeleton
against the real runtime dump of the d8 decode deployment.

Architecture: MLA-style attention (q_a/q_b + kv_a_with_mqa/kv_b) + DSA indexer
+ MoE (76 MoE layers x 256 routed experts + shared experts; first 3 layers
dense) + MTP (NextN) tail weights that are loaded by the DRAFT model only.

Sharding facts (from launch config + sglang source, NEVER from the dump):
- --enable-dp-attention with dp == tp  => attention TP-group size tp/dp = 1,
  so ALL attention weights (and embedding) are replicated per rank.
- --enable-dp-lm-head                  => lm_head replicated per rank.
- --moe-dense-tp-size 1                => dense-layer MLP + shared experts
  replicated per rank.
- --moe-a2a-backend deepep (no --ep-size) => server_args sets
  ep_size = tp_size, so routed experts shard on the ep axis.
- SGLANG_DEL_MLA_DEAD_WEIGHT=1         => kv_b_proj.weight is DELETED at
  runtime after w_kc/w_vc extraction (only its fp32 scale survives), so
  attn.kv_b measures ~0 by design.
- MTP weights (eh_proj/enorm/hnorm/shared_head + final NextN layer) belong to
  the separate draft ModelRunner (DeepseekV3ForCausalLMNextN dump); they are
  expected to be ABSENT from the target-model dump.
"""

from typing import Dict, List, Tuple

from .base import MapEntry, ModelAdapter, register


@register
class Glm52Fp820260616Adapter(ModelAdapter):
    name = "glm_5_2_fp8_20260616"

    def extra_rules(self) -> List[Tuple[str, str]]:
        # Order matters (first match wins): specific submodules before the
        # generic patterns that their names contain (indexer.k_norm before
        # norms, shared_experts before experts, experts before mlp.gate/up).
        return [
            # --- MTP / NextN tail: draft-model-only weights ---------------
            (r"\beh_proj\b", "mtp.draft_only"),
            (r"\benorm\b", "mtp.draft_only"),
            (r"\bhnorm\b", "mtp.draft_only"),
            (r"shared_head", "mtp.draft_only"),
            # --- DSA indexer (covers wq_b/wk/weights_proj/k_norm) ---------
            (r"self_attn\.indexer\.", "attn.indexer"),
            (r"\.indexer\.", "attn.indexer"),
            # --- MoE ------------------------------------------------------
            (r"shared_experts\.", "moe.shared_experts"),
            # runtime stacked-expert scales lack the dot before weight_scale
            # ("w13_weight_scale_inv"), so the generic quant-suffix routing
            # misses them; route them into the __quant__ bucket explicitly
            (r"experts\.w13_weight_scale_inv", "moe.experts.w13.__quant__"),
            (r"experts\.w2_weight_scale_inv", "moe.experts.w2.__quant__"),
            (r"experts\.w13_weight", "moe.experts.w13"),
            (r"experts\.w2_weight", "moe.experts.w2"),
            (r"experts\.\d+\.(gate|up)_proj", "moe.experts.w13"),
            (r"experts\.\d+\.down_proj", "moe.experts.w2"),
            (r"mlp\.gate\.(weight|e_score_correction_bias)", "moe.router"),
            # --- MLA attention (runtime fuses q_a + kv_a into one) --------
            (r"fused_qkv_a_proj_with_mqa", "attn.fused_qkv_a"),
            (r"self_attn\.q_a_proj", "attn.fused_qkv_a"),
            (r"kv_a_proj_with_mqa", "attn.fused_qkv_a"),
            (r"self_attn\.q_b_proj", "attn.q_b"),
            (r"self_attn\.kv_b_proj", "attn.kv_b"),
            (r"self_attn\.o_proj", "attn.o_proj"),
            # runtime-only attention-backend scalars
            (r"attn_m(qa|ha)\.(k|v)_scale", "runtime.kv_scale"),
            # --- dense-layer MLP (after expert/shared rules) ---------------
            (r"mlp\.gate_up_proj", "dense_mlp.gate_up"),
            (r"mlp\.(gate|up)_proj", "dense_mlp.gate_up"),
            (r"mlp\.down_proj", "dense_mlp.down"),
            # --- embeddings / head ----------------------------------------
            (r"embed_tokens", "embedding"),
            (r"lm_head", "lm_head"),
            # --- norms ------------------------------------------------------
            (r"q_a_layernorm|kv_a_layernorm", "norms"),
            (r"input_layernorm|post_attention_layernorm", "norms"),
            (r"model\.norm\.weight", "norms"),
        ]

    def mapping(self) -> Dict[str, MapEntry]:
        rep = "replicated"
        return {
            "embedding": MapEntry(
                "model.embed_tokens.weight", "none", rep,
                note="dp-attention (dp==tp) -> attn TP group=1, replicated"),
            "lm_head": MapEntry(
                "lm_head.weight", "none", rep,
                note="--enable-dp-lm-head -> replicated per rank"),
            "attn.fused_qkv_a": MapEntry(
                "self_attn.fused_qkv_a_proj_with_mqa", "fused", rep,
                note="HF q_a_proj + kv_a_proj_with_mqa fused at load"),
            "attn.q_b": MapEntry("self_attn.q_b_proj", "none", rep,
                                 note="dp-attention -> replicated"),
            "attn.kv_b": MapEntry(
                "self_attn.kv_b_proj", "none", rep,
                note="SGLANG_DEL_MLA_DEAD_WEIGHT=1 deletes the weight at "
                     "runtime (w_kc/w_vc extracted); only fp32 scale remains "
                     "-> measured ~0 is EXPECTED"),
            "attn.o_proj": MapEntry("self_attn.o_proj", "none", rep,
                                    note="dp-attention -> replicated"),
            "attn.indexer": MapEntry("self_attn.indexer.*", "none", rep,
                                     note="DSA indexer, replicated"),
            "dense_mlp.gate_up": MapEntry(
                "mlp.gate_up_proj", "fused", rep,
                note="--moe-dense-tp-size 1 -> replicated (3 dense layers)"),
            "dense_mlp.down": MapEntry("mlp.down_proj", "none", rep,
                                       note="--moe-dense-tp-size 1"),
            "moe.experts.w13": MapEntry(
                "mlp.experts.w13_weight", "stacked", "ep",
                note="gate+up stacked; deepep -> ep_size=tp_size "
                     "(server_args), 256/ep experts per rank"),
            "moe.experts.w2": MapEntry(
                "mlp.experts.w2_weight", "stacked", "ep",
                note="down stacked; deepep -> ep_size=tp_size"),
            "moe.shared_experts": MapEntry(
                "mlp.shared_experts.*", "fused", rep,
                note="shared experts replicated per rank"),
            "moe.router": MapEntry("mlp.gate.weight", "none", rep,
                                   note="router + e_score bias, replicated"),
            "norms": MapEntry("*_layernorm / model.norm", "none", rep),
            "mtp.draft_only": MapEntry(
                "(draft ModelRunner)", "none", rep,
                note="NextN/MTP weights load in the DRAFT model dump "
                     "(DeepseekV3ForCausalLMNextN); absent from the target "
                     "dump by design"),
            "runtime.kv_scale": MapEntry(
                "attn_mqa/attn_mha k_scale,v_scale", "none", rep,
                note="runtime-only fp8 KV-cache scalars, no HF counterpart"),
        }
