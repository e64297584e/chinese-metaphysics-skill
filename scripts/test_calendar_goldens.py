#!/usr/bin/env python3
"""Execute every machine-routed authority-backed calendar golden."""

from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BAZI_SCRIPTS = ROOT / "modules" / "bazi" / "scripts"
sys.path.insert(0, str(BAZI_SCRIPTS))
import pai_pan  # noqa: E402


class CalendarGoldenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(
            (ROOT / "references" / "calendar-goldens.json").read_text(encoding="utf-8")
        )["cases"]

    def test_every_machine_routed_case(self) -> None:
        executed = 0
        for case in self.cases:
            adapter = case["execution"]["adapter"]
            if adapter == "manual-only":
                continue
            with self.subTest(case=case["id"], adapter=adapter):
                executed += 1
                if adapter == "bazi.day-ganzhi":
                    solar = date.fromisoformat(case["input"]["solar_date"])
                    actual = "".join(
                        pai_pan.gz_from_index(
                            pai_pan.day_gz_index(solar.year, solar.month, solar.day)
                        )
                    )
                    self.assertEqual(actual, case["expected"]["ganzhi_day"])
                elif adapter == "bazi.solar-to-lunar":
                    solar = date.fromisoformat(case["input"]["solar_date"])
                    actual = pai_pan.solar_to_lunar(solar.year, solar.month, solar.day)
                    expected = case["expected"]
                    self.assertEqual(
                        actual,
                        (
                            expected["lunar_year"],
                            expected["lunar_month"],
                            expected["lunar_day"],
                            expected["is_leap_month"],
                        ),
                    )
                elif adapter == "bazi.jie-event-minute":
                    expected_time = case["expected"]["published_time"]
                    event = case["expected"]["event"]
                    actual = pai_pan._lunar_python_jie(int(expected_time[:4]), event)
                    self.assertEqual(actual.strftime("%Y-%m-%d %H:%M"), expected_time)
                else:  # guarded by validate_evidence.py; retained as a test fail-safe
                    self.fail(f"unsupported calendar adapter: {adapter}")
        self.assertEqual(executed, 5)


if __name__ == "__main__":
    unittest.main()
