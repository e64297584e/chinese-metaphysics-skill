#!/usr/bin/env python3
"""Unit tests for local output adapters in the unified runner."""

from __future__ import annotations

import importlib.util
import json
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("run_module.py")
SPEC = importlib.util.spec_from_file_location("run_module", SCRIPT)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(RUNNER)


class QimenProfileAnnotationTests(unittest.TestCase):
    def valid_input(self) -> dict:
        return {
            "question_type": "综合",
            "question_goal": "测试请求",
            "time_input": "2024-12-25 12:00:00",
            "calendar_type": "solar",
            "location": {
                "country": "中国",
                "city": "北京",
                "timezone": "Etc/GMT-8",
            },
            "ruleset": "mainline-cn-v1",
        }

    def write_payload(self, directory: str, payload: dict) -> Path:
        earth_stems = dict(zip(range(1, 10), ("乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")))
        noncenter = (1, 2, 3, 4, 6, 7, 8, 9)
        doors = dict(zip(noncenter, ("休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门")))
        stars = dict(zip(noncenter, ("天蓬", "天任", "天冲", "天辅", "天英", "天柱", "天心", "天芮")))
        gods = dict(zip(noncenter, ("值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天")))
        sky_stems = dict(zip(noncenter, ("乙", "丙", "丁", "戊", "庚", "辛", "壬", "癸")))
        palaces = []
        for number in range(1, 10):
            name, direction, trigram, element = RUNNER.QIMEN_PALACES[number]
            is_center = number == 5
            sky_stem = None if is_center else sky_stems[number]
            sky_stem_list = [] if is_center else [sky_stem]
            hosted_sky_stem = "己" if number == 9 else None
            if hosted_sky_stem:
                sky_stem_list.append(hosted_sky_stem)
            palaces.append(
                {
                    "palace": number,
                    "name": name,
                    "direction": direction,
                    "trigram": trigram,
                    "element": element,
                    "earth_stem": earth_stems[number],
                    "sky_stem": sky_stem,
                    "sky_stems": sky_stem_list,
                    "stem_relation": None,
                    "hosted_sky_stem": hosted_sky_stem,
                    "hosted_stem_relation": None,
                    "star": None if is_center else stars[number],
                    "hosted_star": "天禽" if number == 9 else None,
                    "star_element": None,
                    "star_palace_relation": None,
                    "door": None if is_center else doors[number],
                    "door_element": None,
                    "door_palace_relation": None,
                    "god": None if is_center else gods[number],
                    "is_center": is_center,
                    "hosts_center": number == 2,
                    "hosts_center_sky": number == 9,
                    "hosting_note": None,
                }
            )
        complete = {
            "normalized_input": {
                "question_type": "综合",
                "question_goal": "测试请求",
                "ruleset": "mainline-cn-v1",
                "timezone": "Etc/GMT-8",
                "calendar_type": "solar",
                "country": "中国",
                "city": "北京",
                "used_now": False,
                "original_time_input": "2024-12-25 12:00:00",
            },
            "ruleset": {"id": "mainline-cn-v1"},
            "calendar": {
                "solar": {"ymd_hms": "2024-12-25 12:00:00", "timezone": "Etc/GMT-8"},
                "lunar": {
                    "year": 2024,
                    "month": 11,
                    "day": 25,
                    "month_text": "冬",
                    "day_text": "廿五",
                    "is_leap_month": False,
                },
                "jieqi": {
                    "active_jie": "冬至",
                    "active_jie_started_at": "2024-12-21 17:20:35",
                    "next_jie": "小寒",
                    "next_jie_at": "2025-01-05 10:32:47",
                },
            },
            "ganzhi": {
                "year": "甲辰",
                "month": "丙子",
                "day": "癸亥",
                "time": "戊午",
                "day_xun_exact": "甲寅",
                "day_xunkong_exact": "子丑",
                "time_xun": "甲寅",
                "time_xunkong": "子丑",
            },
            "chart": {
                "dun_type": "阳遁",
                "yuan": "下元",
                "ju_number": 4,
                "xunshou": "甲寅",
                "hidden_yi": "癸",
                "kongwang": ["子", "丑"],
                "kongwang_palaces": [1, 8],
                "day_kongwang": ["子", "丑"],
                "day_kongwang_palaces": [1, 8],
                "time_stem_visible": "戊",
                "day_stem": {"stem": "癸", "raw_palace": 9, "palace": 9, "note": None},
                "year_stem": {"stem": "戊", "raw_palace": 4, "palace": 4, "note": None},
                "month_stem": {"stem": "丙", "raw_palace": 2, "palace": 2, "note": None},
                "hour_yima": {"branch": "申", "palace": 2, "source_branch": "午"},
                "day_yima": {"branch": "巳", "palace": 4, "source_branch": "亥"},
                "zhifu": {"star": "天辅", "palace": 4},
                "zhishi": {"door": "杜门", "palace": 4, "raw_palace": 4, "hours_from_xunshou": 4},
                "center_hosting": {
                    "hosted_star": "天禽",
                    "center_stem": "己",
                    "earth_host_palace": 2,
                    "sky_palace": 9,
                    "follows_star": "天芮",
                },
                "door_index": {door: number for number, door in doors.items()},
                "star_index": {
                    **{star: number for number, star in stars.items()},
                    "天禽": 9,
                },
                "detected_patterns": [
                    {"name": "测试结构", "palace": 1, "detail": "schema fixture", "nature": "中"}
                ],
                "grid_order": list(RUNNER.QIMEN_GRID_ORDER),
                "palaces": palaces,
            },
            "warnings": [],
        }

        def deep_update(target: dict, changes: dict) -> None:
            for key, value in changes.items():
                if isinstance(value, dict) and isinstance(target.get(key), dict):
                    deep_update(target[key], value)
                else:
                    target[key] = value

        deep_update(complete, payload)
        output = Path(directory) / "qimen-output.json"
        output.write_text(json.dumps(complete, ensure_ascii=False), encoding="utf-8")
        return output

    def test_annotates_only_reviewed_ruleset(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(
                directory,
                {
                    "normalized_input": {"ruleset": "mainline-cn-v1"},
                    "ruleset": {"id": "mainline-cn-v1"},
                    "warnings": [],
                },
            )
            RUNNER.annotate_qimen_profile(output, self.valid_input())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["profile_review"]["effective_profile_id"],
                "fixed-solar-term-five-day-v1",
            )
            self.assertTrue(any("不得把本盘标作完整置闰法" in item for item in payload["warnings"]))

    def test_input_gate_accepts_only_explicit_fixed_utc_plus_8_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "qimen-input.json"
            input_path.write_text(
                json.dumps(
                    self.valid_input()
                ),
                encoding="utf-8",
            )
            RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_arbitrary_ruleset_label(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "qimen-input.json"
            input_path.write_text(
                json.dumps(
                    {
                        "ruleset": "totally-unreviewed",
                        "calendar_type": "solar",
                        "location": {"timezone": "Etc/GMT-8"},
                        "time_input": "2024-12-25 12:00:00",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "only the reviewed ruleset"):
                RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "qimen-input.json"
            input_path.write_text(
                '{"ruleset":"mainline-cn-v1","ruleset":"forged"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_unconverted_iana_wall_clock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "qimen-input.json"
            input_path.write_text(
                json.dumps(
                    {
                        "ruleset": "mainline-cn-v1",
                        "calendar_type": "solar",
                        "location": {"timezone": "America/New_York"},
                        "time_input": "2024-12-25 12:00:00",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "only fixed UTC\\+8"):
                RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_offset_bearing_time_string(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "qimen-input.json"
            input_path.write_text(
                json.dumps(
                    {
                        "ruleset": "mainline-cn-v1",
                        "calendar_type": "solar",
                        "location": {"timezone": "Etc/GMT-8"},
                        "time_input": "2024-12-25T12:00:00+08:00",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_truncated_hour(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "qimen-input.json"
            input_path.write_text(
                json.dumps(
                    {
                        "ruleset": "mainline-cn-v1",
                        "calendar_type": "solar",
                        "location": {"timezone": "Etc/GMT-8"},
                        "time_input": "2024-12-25 12",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_unicode_digits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "qimen-input.json"
            input_path.write_text(
                json.dumps(
                    {
                        "ruleset": "mainline-cn-v1",
                        "calendar_type": "solar",
                        "location": {"timezone": "Etc/GMT-8"},
                        "time_input": "２０２４-１２-２５ １２:００",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_silently_ignored_fields(self) -> None:
        invalid_payloads = (
            {"longitude": 121.47},
            {"true_solar_time": True},
            {"use_now": True},
            {"is_leap_month": True},
            {"location": {"timezone": "Etc/GMT-8", "longitude": 121.47}},
        )
        for extra in invalid_payloads:
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as directory:
                payload = {
                    "ruleset": "mainline-cn-v1",
                    "calendar_type": "solar",
                    "location": {"timezone": "Etc/GMT-8"},
                    "time_input": "2024-12-25 12:00:00",
                }
                if "location" in extra:
                    payload["location"] = extra["location"]
                else:
                    payload.update(extra)
                input_path = Path(directory) / "qimen-input.json"
                input_path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "silently ignored"):
                    RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_lunar_or_now_modes(self) -> None:
        for calendar_type in ("lunar", "now"):
            with self.subTest(calendar_type=calendar_type), tempfile.TemporaryDirectory() as directory:
                input_path = Path(directory) / "qimen-input.json"
                input_path.write_text(
                    json.dumps(
                        {
                            "ruleset": "mainline-cn-v1",
                            "calendar_type": calendar_type,
                            "location": {"timezone": "Etc/GMT-8"},
                            "time_input": "2024-12-25 12:00:00",
                        }
                    ),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "calendar_type=solar"):
                    RUNNER.validate_qimen_input(input_path)

    def test_input_gate_rejects_dates_outside_reviewed_range(self) -> None:
        for wall_clock in ("1800-01-01 12:00:00", "2200-01-01 12:00:00"):
            with self.subTest(wall_clock=wall_clock), tempfile.TemporaryDirectory() as directory:
                input_path = Path(directory) / "qimen-input.json"
                input_path.write_text(
                    json.dumps(
                        {
                            "ruleset": "mainline-cn-v1",
                            "calendar_type": "solar",
                            "location": {"timezone": "Etc/GMT-8"},
                            "time_input": wall_clock,
                        }
                    ),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "1901-2100"):
                    RUNNER.validate_qimen_input(input_path)

    def test_runtime_dependency_version_is_exact(self) -> None:
        with patch.object(RUNNER.importlib.metadata, "version", return_value="9.9.9"):
            with self.assertRaisesRegex(SystemExit, "dependency drift"):
                RUNNER.verify_runtime_dependencies()

    def test_rejects_unreviewed_ruleset_without_mutating_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(
                directory,
                {
                    "normalized_input": {"ruleset": "future-rules-v2"},
                    "ruleset": {"id": "future-rules-v2"},
                    "warnings": [],
                },
            )
            before = output.read_bytes()
            with self.assertRaisesRegex(ValueError, "unverified Qimen ruleset"):
                RUNNER.annotate_qimen_profile(output, self.valid_input())
            self.assertEqual(output.read_bytes(), before)

    def test_rejects_disagreeing_ruleset_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(
                directory,
                {
                    "normalized_input": {"ruleset": "future-rules-v2"},
                    "ruleset": {"id": "mainline-cn-v1"},
                    "warnings": [],
                },
            )
            with self.assertRaisesRegex(ValueError, "unverified Qimen ruleset"):
                RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_rejects_missing_ruleset_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(
                directory,
                {
                    "ruleset": None,
                },
            )
            with self.assertRaisesRegex(ValueError, "unverified Qimen ruleset"):
                RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_rejects_missing_normalized_ruleset_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(
                directory,
                {
                    "normalized_input": {"ruleset": None},
                },
            )
            with self.assertRaisesRegex(ValueError, "unverified Qimen ruleset"):
                RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_rejects_non_list_warnings_without_mutating_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(
                directory,
                {
                    "normalized_input": {"ruleset": "mainline-cn-v1"},
                    "ruleset": {"id": "mainline-cn-v1"},
                    "warnings": "not-a-list",
                },
            )
            before = output.read_bytes()
            with self.assertRaisesRegex(ValueError, "warnings must be a list"):
                RUNNER.annotate_qimen_profile(output, self.valid_input())
            self.assertEqual(output.read_bytes(), before)

    def test_rejects_output_timezone_or_calendar_mode_relabel(self) -> None:
        for normalized_patch in (
            {"timezone": "America/New_York"},
            {"calendar_type": "lunar"},
        ):
            with self.subTest(normalized_patch=normalized_patch), tempfile.TemporaryDirectory() as directory:
                output = self.write_payload(directory, {"normalized_input": normalized_patch})
                with self.assertRaises(ValueError):
                    RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_rejects_output_wall_clock_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(
                directory,
                {
                    "calendar": {
                        "solar": {
                            "ymd_hms": "2024-12-25 00:00:00",
                            "timezone": "Etc/GMT-8",
                        },
                        "jieqi": {"active_jie": "冬至"},
                    }
                },
            )
            with self.assertRaisesRegex(ValueError, "calculated wall clock differs"):
                RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_rejects_output_bound_to_a_different_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(
                directory,
                {"normalized_input": {"question_goal": "另一个请求"}},
            )
            with self.assertRaisesRegex(ValueError, "differs from the request"):
                RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_rejects_missing_nullable_center_schema_field(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(directory, {})
            payload = json.loads(output.read_text(encoding="utf-8"))
            center = next(item for item in payload["chart"]["palaces"] if item["palace"] == 5)
            del center["sky_stem"]
            output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_rejects_aware_output_time_boolean_bureau_or_unknown_term(self) -> None:
        invalid_payloads = (
            {
                "normalized_input": {"original_time_input": "2024-12-25T12:00:00+08:00"},
                "calendar": {
                    "solar": {
                        "ymd_hms": "2024-12-25T12:00:00+08:00",
                        "timezone": "Etc/GMT-8",
                    },
                    "jieqi": {"active_jie": "冬至"},
                },
            },
            {"chart": {"dun_type": "阳遁", "yuan": "下元", "ju_number": True}},
            {"calendar": {
                "solar": {"ymd_hms": "2024-12-25 12:00:00", "timezone": "Etc/GMT-8"},
                "jieqi": {"active_jie": ""},
            }},
        )
        for invalid in invalid_payloads:
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as directory:
                output = self.write_payload(directory, invalid)
                with self.assertRaises(ValueError):
                    RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_rejects_minimal_forged_chart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_payload(directory, {})
            payload = json.loads(output.read_text(encoding="utf-8"))
            payload["chart"] = {"dun_type": "阳遁", "yuan": "下元", "ju_number": 4}
            output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                RUNNER.annotate_qimen_profile(output, self.valid_input())

    def test_atomic_runner_creates_parent_and_forwards_error_without_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            script = temp / "fake_qimen.py"
            script.write_text(
                """import argparse, json, pathlib
p = argparse.ArgumentParser()
p.add_argument('--input')
p.add_argument('--output')
a = p.parse_args()
pathlib.Path(a.output).write_text(json.dumps({'error': 'synthetic failure'}), encoding='utf-8')
raise SystemExit(1)
""",
                encoding="utf-8",
            )
            input_path = temp / "input.json"
            input_path.write_text("{}", encoding="utf-8")
            output_path = temp / "new" / "nested" / "output.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                result = RUNNER.run_qimen_atomically(
                    script,
                    input_path,
                    output_path,
                    self.valid_input(),
                )
            self.assertEqual(result, 1)
            self.assertIn("synthetic failure", stderr.getvalue())
            self.assertFalse(output_path.exists())
            self.assertTrue(output_path.parent.is_dir())


class ZiweiProfileAnnotationTests(unittest.TestCase):
    def valid_input(self) -> dict:
        return {
            "calendar_type": "solar",
            "birth_time": "1991-06-15 15:18",
            "is_leap_month": False,
            "gender": "男",
            "late_zi_rule": "next_day",
            "leap_month_rule": "split_15",
            "query_year": 2026,
            "ruleset": "ziwei-sanhe-v1",
        }

    def write_input(self, directory: str, patch: dict | None = None) -> Path:
        payload = self.valid_input()
        if patch:
            payload.update(patch)
        path = Path(directory) / "ziwei-input.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def write_output(self, directory: str, patch: dict | None = None) -> Path:
        names = ("命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "交友", "官禄", "田宅", "福德", "父母")
        branches = tuple(RUNNER.BRANCH_ORDER)
        palaces = []
        for index, (name, branch) in enumerate(zip(names, branches)):
            stem = RUNNER.STEM_ORDER[index % len(RUNNER.STEM_ORDER)]
            start_age = 3 + index * 10
            palaces.append(
                {
                    "name": name,
                    "branch": branch,
                    "stem": stem,
                    "ganzhi": stem + branch,
                    "is_shen_gong": name == "官禄",
                    "major_stars": [],
                    "minor_stars": [],
                    "adjective_stars": [],
                    "decadal": {"start_age": start_age, "end_age": start_age + 9},
                }
            )

        star_index = {}
        for index, name in enumerate(sorted(RUNNER.ZIWEI_MAJOR_STARS)):
            palace = palaces[index % 12]
            palace["major_stars"].append({"name": name, "brightness": "平", "sihua": None})
            star_index[name] = palace["branch"]
        for index, name in enumerate(sorted(RUNNER.ZIWEI_MINOR_STARS)):
            palace = palaces[(index + 2) % 12]
            palace["minor_stars"].append({"name": name, "sihua": None})
            star_index[name] = palace["branch"]
        for index, name in enumerate(sorted(RUNNER.ZIWEI_ADJECTIVE_STARS)):
            palace = palaces[(index + 4) % 12]
            palace["adjective_stars"].append(name)
            star_index[name] = palace["branch"]

        palace_by_branch = {palace["branch"]: palace for palace in palaces}
        sihua_stars = sorted(RUNNER.ZIWEI_TRACKED_STARS)[:4]
        sihua = [
            {
                "type": transformation,
                "star": star,
                "branch": star_index[star],
                "palace": palace_by_branch[star_index[star]]["name"],
            }
            for transformation, star in zip(
                ("化禄", "化权", "化科", "化忌"),
                sihua_stars,
            )
        ]
        query_year = 2026
        year_branch = RUNNER.BRANCH_ORDER[(query_year - 4) % 12]
        year_ganzhi = RUNNER.STEM_ORDER[(query_year - 4) % 10] + year_branch
        yearly_palaces = [
            {
                "name": name,
                "branch": branch,
                "natal_palace": palace_by_branch[branch]["name"],
            }
            for name, branch in zip(names, branches)
        ]
        active_decadal = next(
            palace for palace in palaces
            if palace["decadal"]["start_age"] <= 36 <= palace["decadal"]["end_age"]
        )
        payload = {
            "normalized_input": {
                "calendar_type": "solar",
                "original_birth_time": "1991-06-15 15:18",
                "civil_solar_datetime": "1991-06-15 15:18",
                "gender": "男",
                "leap_month_rule": "split_15",
                "leap_month_rule_source": "explicit",
                "late_zi_rule": "next_day",
            },
            "ruleset": {
                "id": "ziwei-sanhe-v1",
                "late_zi_rule": RUNNER.ZIWEI_LATE_ZI_DESCRIPTIONS["next_day"],
                "leap_month_rule": {"id": "split_15", "source": "explicit", "applied": False},
            },
            "calendar": {
                "chart_solar_date": "1991-06-15",
                "day_rollover_applied": False,
                "is_leap_month": False,
                "lunar_year": 1991,
                "lunar_month": 5,
                "lunar_day": 4,
                "chart_month": 5,
                "year_ganzhi": "辛未",
                "hour_branch": "申时",
            },
            "chart": {
                "ming_gong": {"branch": "子", "ganzhi": "甲子"},
                "shen_gong": {"branch": "申", "palace": "官禄"},
                "wuxing_ju": {"name": "木三局", "number": 3},
                "ming_zhu": "禄存",
                "shen_zhu": "天相",
                "decadal_direction": "顺行",
                "year_sihua": sihua,
                "star_index": star_index,
                "palaces": palaces,
                "self_check": {
                    "passed": True,
                    "major_star_count": 14,
                    "ziwei_branch": star_index["紫微"],
                    "ziwei_partner": None,
                },
            },
            "warnings": [],
            "horoscope": {
                "query_lunar_year": 2026,
                "nominal_age": 36,
                "yearly": {
                    "ganzhi": year_ganzhi,
                    "ming_branch": year_branch,
                    "ming_on_natal_palace": palace_by_branch[year_branch]["name"],
                    "palaces": yearly_palaces,
                    "sihua": sihua,
                },
                "decadal": {
                    "branch": active_decadal["branch"],
                    "ganzhi": active_decadal["ganzhi"],
                    "natal_palace": active_decadal["name"],
                    "start_age": active_decadal["decadal"]["start_age"],
                    "end_age": active_decadal["decadal"]["end_age"],
                    "sihua": sihua,
                },
            },
        }

        def deep_update(target: dict, changes: dict) -> None:
            for key, value in changes.items():
                if isinstance(value, dict) and isinstance(target.get(key), dict):
                    deep_update(target[key], value)
                else:
                    target[key] = value

        if patch:
            deep_update(payload, patch)
        path = Path(directory) / "ziwei-output.json"
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return path

    def test_input_gate_accepts_only_explicit_reviewed_profile(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = RUNNER.validate_ziwei_input(self.write_input(directory))
            self.assertEqual(payload["ruleset"], "ziwei-sanhe-v1")

    def test_input_gate_accepts_a_valid_lunar_date_not_valid_in_gregorian_calendar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            payload = RUNNER.validate_ziwei_input(
                self.write_input(
                    directory,
                    {"calendar_type": "lunar", "birth_time": "2023-02-30 12:00"},
                )
            )
            self.assertEqual(payload["birth_time"], "2023-02-30 12:00")

    def test_input_gate_rejects_missing_or_unreviewed_conventions(self) -> None:
        invalid_values = {
            "ruleset": "another-school",
            "late_zi_rule": None,
            "leap_month_rule": None,
            "gender": "male",
            "is_leap_month": 0,
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    RUNNER.validate_ziwei_input(self.write_input(directory, {field: value}))

    def test_input_gate_rejects_duplicate_json_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "ziwei-input.json"
            input_path.write_text(
                '{"ruleset":"ziwei-sanhe-v1","ruleset":"forged"}',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                RUNNER.validate_ziwei_input(input_path)

    def test_input_gate_rejects_loose_or_offset_time(self) -> None:
        for birth_time in (
            "1991/06/15 15:18",
            "1991-06-15T15:18",
            "1991-06-15 15",
            "1991-06-15 15:18:00",
            "1991-06-15 15:18+08:00",
            "１９９１-０６-１５ １５:１８",
        ):
            with self.subTest(birth_time=birth_time), tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(ValueError, "naive civil format"):
                    RUNNER.validate_ziwei_input(self.write_input(directory, {"birth_time": birth_time}))

    def test_input_gate_rejects_range_unknown_fields_and_solar_leap_flag(self) -> None:
        invalid_patches = (
            {"birth_time": "1800-01-01 12:00"},
            {"birth_time": "2200-01-01 12:00"},
            {"calendar_type": "lunar", "birth_time": "2023-02-31 12:00"},
            {"query_year": True},
            {"query_year": 2200},
            {"timezone": "Asia/Shanghai"},
            {"longitude": 121.47},
            {"is_leap_month": True},
        )
        for patch in invalid_patches:
            with self.subTest(patch=patch), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    RUNNER.validate_ziwei_input(self.write_input(directory, patch))

    def test_annotation_adds_tier_c_profile_disclosure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_output(directory)
            RUNNER.annotate_ziwei_profile(output, self.valid_input())
            payload = json.loads(output.read_text(encoding="utf-8"))
            review = payload["profile_review"]
            self.assertEqual(review["effective_profile_id"], "fixed-civil-date-sanhe-v1")
            self.assertEqual(review["evidence_tier"], "C")
            self.assertFalse(review["independently_validated"])
            self.assertFalse(review["iana_timezone_conversion_supported_by_engine"])
            self.assertTrue(any("不得表述为" in warning for warning in payload["warnings"]))

    def test_annotation_accepts_first_nominal_year_before_a_decadal_period(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_output(
                directory,
                {
                    "horoscope": {
                        "query_lunar_year": 1991,
                        "nominal_age": 1,
                        "yearly": {
                            "ganzhi": "辛未",
                            "ming_branch": "未",
                            "ming_on_natal_palace": "交友",
                        },
                        "decadal": None,
                    }
                },
            )
            expected = self.valid_input()
            expected["query_year"] = 1991
            RUNNER.annotate_ziwei_profile(output, expected)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertIsNone(payload["horoscope"]["decadal"])

    def test_annotation_rejects_relabelled_input_or_ruleset(self) -> None:
        invalid_patches = (
            {"normalized_input": {"calendar_type": "lunar"}},
            {"normalized_input": {"late_zi_rule": "same_day"}},
            {"normalized_input": {"leap_month_rule_source": "default"}},
            {"ruleset": {"id": "unreviewed-v2"}},
            {"ruleset": {"late_zi_rule": ""}},
            {"ruleset": {"late_zi_rule": "same_day"}},
        )
        for patch in invalid_patches:
            with self.subTest(patch=patch), tempfile.TemporaryDirectory() as directory:
                output = self.write_output(directory, patch)
                with self.assertRaises(ValueError):
                    RUNNER.annotate_ziwei_profile(output, self.valid_input())

    def test_annotation_rejects_minimal_forged_chart_and_empty_horoscope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = self.write_output(directory)
            payload = json.loads(output.read_text(encoding="utf-8"))
            payload["chart"] = {
                "palaces": [
                    {"name": name, "branch": branch}
                    for name, branch in zip(
                        ("命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "交友", "官禄", "田宅", "福德", "父母"),
                        RUNNER.BRANCH_ORDER,
                    )
                ],
                "self_check": {"passed": True, "major_star_count": 14},
            }
            payload["horoscope"]["yearly"] = {}
            payload["horoscope"]["decadal"] = {}
            output.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(ValueError):
                RUNNER.annotate_ziwei_profile(output, self.valid_input())

    def test_annotation_rejects_incomplete_or_failed_chart(self) -> None:
        invalid_patches = (
            {"chart": {"palaces": []}},
            {"chart": {"self_check": {"passed": False, "major_star_count": 14}}},
            {"chart": {"self_check": {"passed": True, "major_star_count": True}}},
            {"calendar": {"chart_solar_date": "not-a-date"}},
            {"calendar": {"day_rollover_applied": True}},
            {"calendar": {"hour_branch": "酉时"}},
            {"ruleset": {"leap_month_rule": {"id": "split_15", "source": "explicit", "applied": True}}},
            {"horoscope": {"query_lunar_year": 2025, "nominal_age": 35, "yearly": {}, "decadal": {}}},
            {
                "calendar": {"is_leap_month": True},
                "ruleset": {
                    "leap_month_rule": {
                        "id": "split_15",
                        "source": "explicit",
                        "applied": True,
                    }
                },
            },
            {
                "calendar": {"lunar_year": 1990},
                "horoscope": {
                    "query_lunar_year": 2026,
                    "nominal_age": 37,
                    "yearly": {},
                    "decadal": {},
                },
            },
        )
        for patch in invalid_patches:
            with self.subTest(patch=patch), tempfile.TemporaryDirectory() as directory:
                output = self.write_output(directory, patch)
                with self.assertRaises(ValueError):
                    RUNNER.annotate_ziwei_profile(output, self.valid_input())

    def test_atomic_runner_does_not_replace_existing_output_on_review_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            script = temp / "fake_ziwei.py"
            script.write_text(
                """import argparse, json, pathlib
p = argparse.ArgumentParser()
p.add_argument('--input')
p.add_argument('--output')
a = p.parse_args()
pathlib.Path(a.output).write_text(json.dumps({'ruleset': {'id': 'forged'}}), encoding='utf-8')
""",
                encoding="utf-8",
            )
            input_path = temp / "input.json"
            input_path.write_text("{}", encoding="utf-8")
            output_path = temp / "output.json"
            output_path.write_text('{"preserved": true}', encoding="utf-8")
            with self.assertRaises(ValueError):
                RUNNER.run_ziwei_atomically(script, input_path, output_path, self.valid_input())
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8")), {"preserved": True})


if __name__ == "__main__":
    unittest.main()
