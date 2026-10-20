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
                        "time_input": "2026-10-19 15:30",
                        "calendar_type": "solar",
                        "location": {
                            "country": "China",
                            "city": "Shanghai",
                            "timezone": "Asia/Shanghai",
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
            self.assertIn("chart", json.loads(qimen_output.read_text(encoding="utf-8")))

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
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            subprocess.run(
                [sys.executable, str(RUNNER), "ziwei", "--input", str(ziwei_input), "--output", str(ziwei_output)],
                check=True,
            )
            self.assertIn("chart", json.loads(ziwei_output.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
