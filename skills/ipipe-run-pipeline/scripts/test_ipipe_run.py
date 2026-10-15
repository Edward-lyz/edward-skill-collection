"""Offline checks for recipe resolution: python3 -m unittest test_ipipe_run (run inside scripts/)."""
from __future__ import annotations

import unittest

import ipipe_run as run
import stress_history


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


class StressRecipeTest(unittest.TestCase):
    def setUp(self) -> None:
        _, self.scn = run.pick_scenario(run.load_config(), "长稳")
        self.sets = {"model_id": "m", "prefill_job_name": "x-prefill", "specific_model_path": "/p", "qps": "1"}

    def test_asks_are_collected_across_both_stages(self) -> None:
        _, missing = run.resolve_plan(self.scn, {})
        self.assertEqual([m["key"] for m in missing], ["model_id", "prefill_job_name", "specific_model_path", "qps"])

    def test_each_stage_gets_only_its_own_keys(self) -> None:
        stages, missing = run.resolve_plan(self.scn, self.sets)
        self.assertEqual(missing, [])
        check, bench = stages[0]["params"], stages[1]["params"]
        self.assertNotIn("qps", check)
        self.assertEqual(check["skip_deploy_env"], "true")
        self.assertEqual(stages[0]["expect_skipped"], "新建或扩缩容")
        self.assertEqual(bench["qps"], "1")

    def test_defaults_are_12h_prefill_pod_and_modal_dataset(self) -> None:
        bench = run.resolve_plan(self.scn, self.sets)[0][1]["params"]
        self.assertEqual(bench["run_time_second"], "43200")
        self.assertEqual(bench["specific_k8s_pod"], "NA")  # NA = first prefill pod of prefill_job_name
        self.assertEqual(bench["dataset_name"], "deepseek_v4数据集##output_glm5-260331.jsonl")

    def test_unknown_key_still_fails_fast(self) -> None:
        with self.assertRaises(run.IpipeError):
            run.resolve_plan(self.scn, {**self.sets, "skip_deploy_envv": "false"})


class StressHistoryTest(unittest.TestCase):
    LINE = ("2026-10-10 23:57:19 + command='python3 /ws/ds_test/common/common_class/aiak_perf.py   --run_time_second 43200 "
            '--host "http://10.178.29.70:80" --model "m" --n "8000000" --qps "0.8" --of 8092 '
            "--k8s_pod a-prefill-x-0 --k8s_mode True --dataset_type \"chat\" --enable_thinking \"false\" --per_qps 15'")

    def test_parse_perf_command(self) -> None:
        p = stress_history.parse_perf_command(self.LINE)
        self.assertEqual((p["run_time_second"], p["num_requests"], p["qps"], p["k8s_mode"]), ("43200", "8000000", "0.8", "True"))
        self.assertEqual((p["port"], p["thinking_budget"], p["pod_role"]), ("1", "NA", "prefill"))

    def test_mode_prefers_count_then_newest(self) -> None:
        self.assertEqual(stress_history.pick_mode(["a", "b", "b", "a", "c"]), ("a", 2))  # tie -> newest first
        self.assertEqual(stress_history.pick_mode(["a", "b", "b"]), ("b", 2))

    def test_dataset_label_regex(self) -> None:
        line = "echo 'dataset: '\\''deepseek_v4数据集##output_glm5-260331.jsonl'\\'''"
        self.assertEqual(stress_history.DATASET_RE.search(line).group(1), "deepseek_v4数据集##output_glm5-260331.jsonl")


if __name__ == "__main__":
    unittest.main()
