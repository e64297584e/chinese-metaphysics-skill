#!/usr/bin/env python3
"""Tests for strict civil-time normalization."""

from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import sys
import unittest
from unittest.mock import patch
import zoneinfo
from datetime import datetime
from pathlib import Path


SCRIPT = Path(__file__).with_name("normalize_civil_time.py")
SPEC = importlib.util.spec_from_file_location("normalize_civil_time", SCRIPT)
NORMALIZER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(NORMALIZER)


class CivilTimeTests(unittest.TestCase):
    def test_new_york_spring_gap_is_rejected(self) -> None:
        result = NORMALIZER.classify_local_time(datetime(2024, 3, 10, 2, 30), "America/New_York")
        self.assertEqual(result["status"], "nonexistent")
        self.assertEqual(result["candidates"], [])

    def test_new_york_fall_fold_requires_choice(self) -> None:
        result = NORMALIZER.classify_local_time(datetime(2024, 11, 3, 1, 30), "America/New_York")
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual([item["utc_offset"] for item in result["candidates"]], ["-04:00", "-05:00"])

    def test_china_1990_spring_gap_is_rejected(self) -> None:
        result = NORMALIZER.classify_local_time(datetime(1990, 4, 15, 2, 30), "Asia/Shanghai")
        self.assertEqual(result["status"], "nonexistent")

    def test_china_1990_fall_fold_requires_choice(self) -> None:
        result = NORMALIZER.classify_local_time(datetime(1990, 9, 16, 1, 30), "Asia/Shanghai")
        self.assertEqual(result["status"], "ambiguous")
        self.assertEqual([item["utc_offset"] for item in result["candidates"]], ["+09:00", "+08:00"])

    def test_ordinary_time_is_unique(self) -> None:
        result = NORMALIZER.classify_local_time(datetime(2026, 10, 22, 12, 0), "Asia/Shanghai")
        self.assertEqual(result["status"], "valid")
        self.assertEqual(len(result["candidates"]), 1)
        self.assertTrue(result["candidates"][0]["fixed_utc_plus_8"].endswith("+08:00"))
        self.assertEqual(
            result["candidates"][0]["fixed_utc_plus_8_wall_clock"],
            "2026-10-22 12:00:00",
        )
        self.assertEqual(result["selected"], result["candidates"][0])
        self.assertEqual(result["tzdb_version"], "2026e")
        self.assertEqual(result["tzdb_source"], "python-tzdata-package")

    def test_active_zoneinfo_path_is_the_pinned_tzdata_wheel(self) -> None:
        self.assertIsNotNone(NORMALIZER.ACTIVE_TZDATA_ROOT)
        self.assertEqual(zoneinfo.TZPATH, (str(NORMALIZER.ACTIVE_TZDATA_ROOT),))

    def test_strict_local_parser_rejects_truncated_or_fractional_inputs(self) -> None:
        for value in (
            "2024-12-25",
            "2024-12-25 15",
            "2024-12-25 15:00:00.500",
            "２０２４-１２-２５ １５:００",
        ):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                NORMALIZER.parse_local_time(value)

    def test_historical_second_offset_is_not_truncated(self) -> None:
        result = NORMALIZER.classify_local_time(datetime(1900, 1, 1, 12, 0), "Asia/Shanghai")
        self.assertEqual(result["candidates"][0]["utc_offset"], "+08:05:43")

    def test_invalid_fold_error_does_not_expose_a_selected_candidate(self) -> None:
        stdout = io.StringIO()
        argv = [
            "normalize_civil_time.py",
            "--local",
            "2026-10-22 12:00:00",
            "--timezone",
            "Asia/Shanghai",
            "--fold",
            "1",
        ]
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
            self.assertEqual(NORMALIZER.main(), 2)
        payload = json.loads(stdout.getvalue())
        self.assertNotIn("selected", payload)
        self.assertIn("error", payload)

    def test_extreme_timezone_overflow_becomes_validation_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the supported"):
            NORMALIZER.classify_local_time(datetime(1, 1, 1, 0, 0), "Etc/GMT-14")

    def test_missing_tzdata_metadata_falls_back_to_system_marker(self) -> None:
        with patch.object(
            NORMALIZER.importlib.metadata,
            "version",
            side_effect=NORMALIZER.importlib.metadata.PackageNotFoundError,
        ):
            self.assertEqual(NORMALIZER.tzdata_package_version(), "system-or-unknown")

    def test_classifier_fails_closed_without_exact_pinned_tzdata(self) -> None:
        with patch.object(NORMALIZER, "ACTIVE_TZDATA_ROOT", None):
            with self.assertRaisesRegex(ValueError, "pinned timezone runtime unavailable"):
                NORMALIZER.classify_local_time(datetime(2026, 10, 22, 12, 0), "Asia/Shanghai")
        with patch.object(NORMALIZER.importlib.metadata, "version", return_value="9999.0"):
            with self.assertRaisesRegex(ValueError, "pinned timezone runtime unavailable"):
                NORMALIZER.classify_local_time(datetime(2026, 10, 22, 12, 0), "Asia/Shanghai")


if __name__ == "__main__":
    unittest.main()
