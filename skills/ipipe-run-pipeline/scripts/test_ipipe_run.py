"""Offline checks for recipe resolution: python3 -m unittest test_ipipe_run (run inside scripts/)."""
from __future__ import annotations

import unittest

import ipipe_run as run


class RecipeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = run.load_config()

    def test_every_alias_points_to_a_scenario(self) -> None:
        for alias, key in self.cfg["aliases"].items():
            self.assertIn(key, self.cfg["scenarios"], alias)

    def test_fc_reports_missing_ask_keys(self) -> None:
        _, scn = run.pick_scenario(self.cfg, "FC")
        _, missing = run.resolve_plan(scn, {})
        self.assertEqual([m["key"] for m in missing], ["inference_model", "inference_model_lite"])

    def test_fc_fixed_pattern_and_override(self) -> None:
        _, scn = run.pick_scenario(self.cfg, "fc")
        sets = {"inference_model": "m", "inference_model_lite": "R1_0528", "inference_sampling": "10"}
        stages, missing = run.resolve_plan(scn, sets)
        params = stages[0]["params"]
        self.assertEqual(missing, [])
        self.assertEqual(params["evalscope_v2t_dataset"], "general_fc")
        self.assertEqual(params["inference_sampling"], "10")

    def test_unknown_key_and_bad_choice_fail_fast(self) -> None:
        _, scn = run.pick_scenario(self.cfg, "fc")
        with self.assertRaises(run.IpipeError):
            run.resolve_plan(scn, {"inferense_model": "typo"})
        with self.assertRaises(run.IpipeError):
            run.resolve_plan(scn, {"inference_model": "m", "inference_model_lite": "nope"})

    def test_multi_choice_validates_each_part(self) -> None:
        _, scn = run.pick_scenario(self.cfg, "evalscope")
        base = {"inference_model": "m", "inference_model_lite": "R1_0528"}
        ok, _ = run.resolve_plan(scn, {**base, "evalscope_llm_dataset": "gsm8k,math_500"})
        self.assertEqual(ok[0]["params"]["evalscope_llm_dataset"], "gsm8k,math_500")
        with self.assertRaises(run.IpipeError):
            run.resolve_plan(scn, {**base, "evalscope_llm_dataset": "gsm8k,bogus"})

    def test_second_stage_inherits_params(self) -> None:
        _, scn = run.pick_scenario(self.cfg, "kimi eval")
        stages, _ = run.resolve_plan(scn, {"model_id": "m", "dataset": "toolcall"})
        self.assertEqual(stages[0]["params"], stages[1]["params"])

    def test_mask_hides_bearer_and_auth(self) -> None:
        text = run.mask("--inference_auth Bearer abc123 x api_key=zzz")
        self.assertNotIn("abc123", text)
        self.assertNotIn("zzz", text)


if __name__ == "__main__":
    unittest.main()
