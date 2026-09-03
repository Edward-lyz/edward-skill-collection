# 模块分类规则 (taxonomy_rules)

`scripts/module_taxonomy.py` 的 `DEFAULT_RULES` 是有序 (regex, category) 列表，
自上而下匹配、首个命中即止。适配器可通过 `extra_rules()` 在前面插入自定义规则。

## 类别一览
- `embedding` / `lm_head`
- MLA 注意力：`attn.q_a_proj` / `attn.q_b_proj` / `attn.q_a_layernorm` /
  `attn.kv_a_proj` / `attn.kv_a_layernorm` / `attn.kv_b_proj` / `attn.q_proj`
- 经典注意力：`attn.k_proj` / `attn.v_proj` / `attn.o_proj` / `attn.layernorm`
- MoE：`moe.router` / `moe.shared.{gate,up,down}_proj` / `moe.expert.{gate,up,down}_proj`
- dense MLP：`mlp.{gate,up,down}_proj`
- norm：`norm.input` / `norm.post_attn` / `norm.final` / `norm.other`
- 兜底：`other`

## 量化伴随张量
后缀命中 `QUANT_SUFFIXES`（`.weight_scale_inv`、`.scale` 等）的张量归入
`<category>.__quant__` 子桶，不污染权重本体字节统计。

## 新增模型
1. 若命名与上表一致：无需改动，直接用 `--model` 指定或用 base 启发式。
2. 若命名特殊：在 `model_adapters/<name>.py` 的 `extra_rules()` 里加规则；
   或补充 `DEFAULT_RULES`（影响所有模型，需谨慎）。
