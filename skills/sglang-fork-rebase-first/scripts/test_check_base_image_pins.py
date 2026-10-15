"""python3 -m unittest test_check_base_image_pins  (inside scripts/)"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import check_base_image_pins as pins

PYPROJECT = """
[build-system]
requires = ["setuptools>=61.0", "torch==2.14.1", "wheel"]
[project]
name = "sglang"
dependencies = [
  "aiohttp",
  "flashinfer_python[cu13]==0.7.1",  # keep aligned
  "kernels>=0.14.1,<0.15",
  "av==16.1.0 ; sys_platform == 'linux' and platform_machine == 'aarch64'",
  "sglang-kernel==0.4.9",
]
"""


class PinsTest(unittest.TestCase):
    def setUp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pyproject.toml"
            path.write_text(PYPROJECT, encoding="utf-8")
            self.pins = pins.read_pins(path)

    def test_reads_pins_skips_markers_and_unpinned(self) -> None:
        self.assertEqual(self.pins["torch"], [("==", "2.14.1")])
        self.assertEqual(self.pins["flashinfer-python"], [("==", "0.7.1")])
        self.assertEqual(self.pins["kernels"], [(">=", "0.14.1"), ("<", "0.15")])
        self.assertNotIn("av", self.pins)
        self.assertNotIn("aiohttp", self.pins)

    def test_old_dev_image_fails_on_enforced_pins(self) -> None:
        old = {"torch": "2.13.0+cu130", "sglang-kernel": "0.4.6.post1", "flashinfer-python": "0.6.18", "kernels": "0.14.2"}
        rows = pins.check(self.pins, old, {"torch", "sglang-kernel"})
        self.assertEqual({r[1] for r in rows if r[0] == "FAIL"}, {"torch", "sglang-kernel"})
        self.assertIn("flashinfer-python", {r[1] for r in rows if r[0] == "WARN"})

    def test_matching_image_passes_and_local_tag_is_ignored(self) -> None:
        good = {"torch": "2.14.1+cu130", "sglang-kernel": "0.4.9", "flashinfer-python": "0.7.1", "kernels": "0.14.2"}
        self.assertEqual(pins.check(self.pins, good, {"torch", "sglang-kernel"}), [])

    def test_post_release_is_not_equal_to_the_pin(self) -> None:
        rows = pins.check(self.pins, {"torch": "2.14.1", "sglang-kernel": "0.4.9.post1"}, {"sglang-kernel"})
        self.assertIn(("FAIL", "sglang-kernel", "==0.4.9", "0.4.9.post1"), rows)

    def test_missing_enforced_package_fails(self) -> None:
        rows = pins.check(self.pins, {"torch": "2.14.1"}, {"torch", "sglang-kernel"})
        self.assertIn(("FAIL", "sglang-kernel", "==0.4.9", "missing"), rows)


if __name__ == "__main__":
    unittest.main()
