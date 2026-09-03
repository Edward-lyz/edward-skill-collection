"""Model adapters: encode how a specific model's HuggingFace tensor names map to
the parameter names sglang actually holds at runtime, plus any taxonomy rule
overrides.

Why an adapter layer: sglang fuses and sometimes shards weights while loading
(q/k/v -> qkv_proj, gate/up -> gate_up_proj, per-expert gate/up/down -> stacked
`w13_weight`/`w2_weight`), and tensor-parallel splits certain dims across ranks.
These transforms differ per architecture, so hard-coding them in the analysis
pipeline would not generalise. Instead the pipeline asks an adapter, and new
models are supported by adding one file here (or falling back to the heuristic
base adapter).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class MapEntry:
    """How a taxonomy category relates to sglang runtime params."""

    sglang_hint: str          # runtime param name / group it lands in
    fusion: str = "none"      # none | fused | stacked
    tp: str = "replicated"    # replicated | col_parallel | row_parallel | ep
    note: str = ""


class ModelAdapter:
    """Heuristic default. Works for common Llama/DeepSeek-ish naming; specific
    models subclass to correct the uncertain parts."""

    name = "base"

    # Extra taxonomy rules, tried before DEFAULT_RULES. Override if a model uses
    # unusual tensor names.
    def extra_rules(self) -> List[Tuple[str, str]]:
        return []

    # Tensor-parallel degree; only affects the "expected measured = theory/tp"
    # reasoning in the diff. 1 = no TP.
    def __init__(self, tp: int = 1):
        self.tp = tp

    def mapping(self) -> Dict[str, MapEntry]:
        """category -> MapEntry. Heuristic, best-effort; unknown categories are
        reported as `uncertain` by the diff step."""
        col = "col_parallel"
        row = "row_parallel"
        return {
            "embedding": MapEntry("embed_tokens.weight", tp="col_parallel",
                                  note="vocab-parallel"),
            "lm_head": MapEntry("lm_head.weight", tp="col_parallel",
                                note="tied with embedding if config.tie_word_embeddings"),
            # classic attention -> fused qkv
            "attn.q_proj": MapEntry("qkv_proj (fused)", "fused", col),
            "attn.k_proj": MapEntry("qkv_proj (fused)", "fused", col),
            "attn.v_proj": MapEntry("qkv_proj (fused)", "fused", col),
            "attn.o_proj": MapEntry("o_proj", tp=row),
            # dense mlp -> fused gate_up
            "mlp.gate_proj": MapEntry("gate_up_proj (fused)", "fused", col),
            "mlp.up_proj": MapEntry("gate_up_proj (fused)", "fused", col),
            "mlp.down_proj": MapEntry("down_proj", tp=row),
            # MoE experts -> stacked expert weights, expert-parallel
            "moe.expert.gate_proj": MapEntry("w13_weight (stacked)", "stacked",
                                             "ep", note="gate+up stacked per expert"),
            "moe.expert.up_proj": MapEntry("w13_weight (stacked)", "stacked", "ep"),
            "moe.expert.down_proj": MapEntry("w2_weight (stacked)", "stacked", "ep"),
            "moe.shared.gate_proj": MapEntry("shared_experts.gate_up_proj (fused)",
                                             "fused", col),
            "moe.shared.up_proj": MapEntry("shared_experts.gate_up_proj (fused)",
                                           "fused", col),
            "moe.shared.down_proj": MapEntry("shared_experts.down_proj", tp=row),
            "moe.router": MapEntry("gate.weight", note="router, replicated"),
            # norms replicated
            "norm.input": MapEntry("input_layernorm.weight"),
            "norm.post_attn": MapEntry("post_attention_layernorm.weight"),
            "norm.final": MapEntry("norm.weight"),
        }

    def lookup(self, category: str) -> Optional[MapEntry]:
        base = category[: -len(".__quant__")] if category.endswith(".__quant__") else category
        return self.mapping().get(base)


_REGISTRY: Dict[str, type] = {}


def register(cls):
    _REGISTRY[cls.name] = cls
    return cls


def get_adapter(name: Optional[str], tp: int = 1) -> ModelAdapter:
    if not name:
        return ModelAdapter(tp=tp)
    # allow lazy import of sibling modules
    if name not in _REGISTRY:
        try:
            __import__(f"model_adapters.{name}")
        except Exception:
            try:
                __import__(name)  # when scripts/ and model_adapters/ on path
            except Exception:
                pass
    cls = _REGISTRY.get(name, ModelAdapter)
    return cls(tp=tp)
