#!/usr/bin/env python3
"""Tests for the optional Ziwei v4 dataset auditor."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("audit_ziwei_dataset.py")
SPEC = importlib.util.spec_from_file_location("audit_ziwei_dataset", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
AUDITOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDITOR)


def record(
    *,
    key: str = "1991-06-15-8-male",
    year: int = 1991,
    month: int = 6,
    day: int = 15,
    hour: int = 8,
    gender: str = "male",
    main_star: str | None = None,
    text: str = "结构化测试🙂",
) -> dict[str, object]:
    contents = {topic: text for topic in AUDITOR.TOPICS}
    lengths = {topic: AUDITOR.utf16_code_units(text) for topic in AUDITOR.TOPICS}
    return {
        "k": key,
        "y": year,
        "m": month,
        "d": day,
        "h": hour,
        "g": gender,
        "ms": main_star,
        "t": lengths,
        "c": contents,
    }


def json_lines(*records: dict[str, object]) -> list[str]:
    return [json.dumps(item, ensure_ascii=False) + "\n" for item in records]


class AuditZiweiDatasetTests(unittest.TestCase):
    def test_valid_record_and_utf16_lengths(self) -> None:
        result = AUDITOR.audit_lines(json_lines(record()), scan_text=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["records"], 1)
        self.assertEqual(result["violations"], {})
        metrics = result["text_metrics"]
        self.assertEqual(metrics["topic_texts"], 13)
        self.assertEqual(metrics["distinct_whole_content_hashes"], 1)

    def test_invalid_date_and_key_are_rejected(self) -> None:
        invalid_date = record(key="1991-02-30-0-male", month=2, day=30, hour=0)
        mismatched_key = record(key="wrong-key")
        result = AUDITOR.audit_lines(json_lines(invalid_date, mismatched_key))
        self.assertFalse(result["ok"])
        self.assertEqual(result["violations"]["invalid_date"], 1)
        self.assertEqual(result["violations"]["key_mismatch"], 1)

    def test_duplicate_key_and_invalid_main_star_are_rejected(self) -> None:
        secret = "PRIVATE INTERPRETATION TEXT"
        first = record(main_star=secret)
        second = record()
        result = AUDITOR.audit_lines(json_lines(first, second))
        self.assertFalse(result["ok"])
        self.assertEqual(result["violations"]["duplicate_key"], 1)
        self.assertEqual(result["violations"]["invalid_main_star"], 1)
        self.assertEqual(result["main_stars"], {"<invalid>": 1, "null": 1})
        self.assertNotIn(secret, json.dumps(result))

    def test_unhashable_main_star_is_redacted(self) -> None:
        invalid = record()
        invalid["ms"] = ["PRIVATE"]
        result = AUDITOR.audit_lines(json_lines(invalid))
        self.assertFalse(result["ok"])
        self.assertEqual(result["violations"]["invalid_main_star"], 1)
        self.assertEqual(result["main_stars"], {"<invalid>": 1})

    def test_expected_year_requires_full_coverage(self) -> None:
        result = AUDITOR.audit_lines(json_lines(record()), expected_year=1991)
        self.assertFalse(result["ok"])
        self.assertEqual(result["coverage"]["expected_records"], 8760)
        self.assertEqual(result["coverage"]["missing_combinations"], 8759)

    def test_coverage_uses_exact_domain_not_only_cardinality(self) -> None:
        outside = record(key="1992-06-15-8-male", year=1992)
        result = AUDITOR.audit_lines(json_lines(outside), expected_year=1991)
        self.assertFalse(result["ok"])
        self.assertEqual(result["coverage"]["missing_combinations"], 8760)
        self.assertEqual(result["coverage"]["extra_combinations"], 1)

    def test_duplicate_json_keys_are_rejected(self) -> None:
        raw = '{"k":"first","k":"second"}\n'
        result = AUDITOR.audit_lines([raw])
        self.assertFalse(result["ok"])
        self.assertEqual(result["violations"]["invalid_json"], 1)

    def test_oversized_json_integer_is_rejected_without_traceback(self) -> None:
        raw = '{"y":' + "9" * 5000 + "}\n"
        result = AUDITOR.audit_lines([raw])
        self.assertFalse(result["ok"])
        self.assertEqual(result["violations"]["invalid_json"], 1)

    def test_stream_resource_limits(self) -> None:
        with self.assertRaises(AUDITOR.AuditInputError):
            list(
                AUDITOR.bounded_lines(
                    io.StringIO("12345\n"),
                    max_output_bytes=100,
                    max_line_bytes=4,
                    max_lines=10,
                )
            )
        with self.assertRaises(AUDITOR.AuditInputError):
            list(
                AUDITOR.bounded_lines(
                    io.StringIO("{}\n{}\n"),
                    max_output_bytes=100,
                    max_line_bytes=10,
                    max_lines=1,
                )
            )

    def test_text_hash_budget_is_enforced(self) -> None:
        with self.assertRaises(AUDITOR.AuditInputError):
            AUDITOR.audit_lines(json_lines(record()), scan_text=True, max_distinct_hashes=1)

    def test_checksum_mismatch_stops_before_decompression(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            dataset = Path(directory) / "invalid.jsonl.zst"
            dataset.write_bytes(b"this is deliberately not a zstd frame")
            output = io.StringIO()
            argv = [str(SCRIPT), str(dataset), "--expected-sha256", "0" * 64]
            with mock.patch.object(sys, "argv", argv), redirect_stdout(output):
                return_code = AUDITOR.main()
        payload = json.loads(output.getvalue())
        self.assertEqual(return_code, 1)
        self.assertEqual(payload["violations"], {"checksum_mismatch": 1})
        self.assertEqual(payload["error"], "checksum mismatch; input was not parsed")


if __name__ == "__main__":
    unittest.main()
