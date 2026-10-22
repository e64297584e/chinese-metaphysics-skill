#!/usr/bin/env python3
"""Integration smoke tests for the unified entry point."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "scripts" / "run_module.py"
NORMALIZER = ROOT / "scripts" / "normalize_civil_time.py"


class IntegrationTests(unittest.TestCase):
    def test_bazi_known_chart(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "bazi",
                "--",
                "--solar",
                "1991-06-15",
                "--hour",
                "15:18",
                "--sex",
                "男",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("| 天干 | 辛 | 甲 | 丙 | 丙 |", result.stdout)
        self.assertIn("| 地支 | 未 | 午 | 辰 | 申 |", result.stdout)

    def test_external_calculators_when_bootstrapped(self) -> None:
        if not (ROOT / ".upstream" / "Numerologist_skills").exists():
            self.skipTest("runtime upstreams are not bootstrapped")

        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            qimen_input = temp / "qimen.json"
            qimen_output = temp / "qimen-output.json"
            qimen_input.write_text(
                json.dumps(
                    {
                        "question_type": "career",
                        "question_goal": "test",
                        "time_input": "2024-12-25 12:00",
                        "calendar_type": "solar",
                        "location": {
                            "country": "China",
                            "city": "Shanghai",
                            "timezone": "Etc/GMT-8",
                        },
                        "ruleset": "mainline-cn-v1",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(RUNNER), "qimen", "--input", str(qimen_input), "--output", str(qimen_output)],
                check=True,
            )
            qimen_payload = json.loads(qimen_output.read_text(encoding="utf-8"))
            self.assertIn("chart", qimen_payload)
            self.assertEqual(
                qimen_payload["profile_review"]["effective_profile_id"],
                "fixed-solar-term-five-day-v1",
            )
            self.assertFalse(qimen_payload["profile_review"]["full_zhirun_implemented"])
            self.assertTrue(any("不得把本盘标作完整置闰法" in item for item in qimen_payload["warnings"]))
            self.assertEqual(qimen_payload["calendar"]["jieqi"]["active_jie"], "冬至")
            self.assertEqual(qimen_payload["chart"]["dun_type"], "阳遁")
            self.assertEqual(qimen_payload["chart"]["ju_number"], 4)
            self.assertEqual(qimen_payload["chart"]["yuan"], "下元")

            ziwei_input = temp / "ziwei.json"
            ziwei_output = temp / "ziwei-output.json"
            ziwei_input.write_text(
                json.dumps(
                    {
                        "calendar_type": "solar",
                        "birth_time": "1991-06-15 15:18",
                        "is_leap_month": False,
                        "gender": "男",
                        "late_zi_rule": "next_day",
                        "leap_month_rule": "split_15",
                        "query_year": 2026,
                        "ruleset": "ziwei-sanhe-v1",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(RUNNER), "ziwei", "--input", str(ziwei_input), "--output", str(ziwei_output)],
                check=True,
            )
            ziwei_payload = json.loads(ziwei_output.read_text(encoding="utf-8"))
            self.assertIn("chart", ziwei_payload)
            self.assertEqual(
                ziwei_payload["profile_review"]["effective_profile_id"],
                "fixed-civil-date-sanhe-v1",
            )
            self.assertEqual(ziwei_payload["profile_review"]["evidence_tier"], "C")
            self.assertFalse(ziwei_payload["profile_review"]["independently_validated"])

            lunar_ziwei_input = temp / "ziwei-lunar.json"
            lunar_ziwei_output = temp / "ziwei-lunar-output.json"
            lunar_ziwei_input.write_text(
                json.dumps(
                    {
                        "calendar_type": "lunar",
                        "birth_time": "2023-02-30 12:00",
                        "is_leap_month": False,
                        "gender": "女",
                        "late_zi_rule": "next_day",
                        "leap_month_rule": "current",
                        "query_year": 2026,
                        "ruleset": "ziwei-sanhe-v1",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "ziwei",
                    "--input",
                    str(lunar_ziwei_input),
                    "--output",
                    str(lunar_ziwei_output),
                ],
                check=True,
            )
            lunar_payload = json.loads(lunar_ziwei_output.read_text(encoding="utf-8"))
            self.assertEqual(
                lunar_payload["normalized_input"]["civil_solar_datetime"],
                "2023-03-21 12:00",
            )
            self.assertFalse(lunar_payload["profile_review"]["requested_is_leap_month"])

    def test_qimen_iana_input_is_converted_before_fixed_utc_plus_8_engine(self) -> None:
        if not (ROOT / ".upstream" / "Numerologist_skills").exists():
            self.skipTest("runtime upstreams are not bootstrapped")

        normalized = subprocess.run(
            [
                sys.executable,
                str(NORMALIZER),
                "--local",
                "2024-12-21 05:00:00",
                "--timezone",
                "America/New_York",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        wall_clock = json.loads(normalized.stdout)["candidates"][0][
            "fixed_utc_plus_8_wall_clock"
        ]
        self.assertEqual(wall_clock, "2024-12-21 18:00:00")

        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            input_path = temp / "qimen-converted.json"
            output_path = temp / "qimen-converted-output.json"
            input_path.write_text(
                json.dumps(
                    {
                        "question_type": "timing",
                        "question_goal": "timezone regression",
                        "time_input": wall_clock,
                        "calendar_type": "solar",
                        "location": {
                            "country": "United States",
                            "city": "New York",
                            "timezone": "Etc/GMT-8",
                        },
                        "ruleset": "mainline-cn-v1",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "qimen",
                    "--input",
                    str(input_path),
                    "--output",
                    str(output_path),
                ],
                check=True,
            )
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["calendar"]["solar"]["ymd_hms"], wall_clock)
            self.assertEqual(payload["calendar"]["jieqi"]["active_jie"], "冬至")
            self.assertEqual(
                payload["profile_review"]["input_time_basis"],
                "fixed UTC+8 wall clock (Etc/GMT-8)",
            )


if __name__ == "__main__":
    unittest.main()
