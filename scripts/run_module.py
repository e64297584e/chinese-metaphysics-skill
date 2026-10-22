#!/usr/bin/env python3
"""Run one calculator through the unified skill entry point."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "references" / "upstreams.json"
QIMEN_RULESET = "mainline-cn-v1"
QIMEN_TIMEZONE = "Etc/GMT-8"
QIMEN_TIME_INPUT = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}(?::[0-9]{2})?$")
QIMEN_INPUT_FIELDS = {
    "question_type", "question_goal", "time_input", "calendar_type", "location", "ruleset",
}
QIMEN_LOCATION_FIELDS = {"country", "city", "timezone"}
ZIWEI_RULESET = "ziwei-sanhe-v1"
ZIWEI_TIME_INPUT = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$")
ZIWEI_CALENDAR_TYPES = {"solar", "lunar"}
ZIWEI_GENDERS = {"男", "女"}
ZIWEI_LATE_ZI_DESCRIPTIONS = {
    "next_day": "23:00 起视为次日子时，农历日期按次日计算（calculation.md 默认口径）",
    "same_day": "23:00 起取子时，但农历日期仍按当天（沿用用户既定口径时使用）",
}
ZIWEI_LATE_ZI_RULES = set(ZIWEI_LATE_ZI_DESCRIPTIONS)
ZIWEI_LEAP_MONTH_RULES = {"current", "next", "split_15"}
ZIWEI_INPUT_FIELDS = {
    "calendar_type",
    "birth_time",
    "is_leap_month",
    "gender",
    "late_zi_rule",
    "leap_month_rule",
    "query_year",
    "ruleset",
}
VERIFIED_CALENDAR_RANGE = (1901, 2100)
RUNTIME_DEPENDENCIES = {"lunar-python": "1.4.8"}
BRANCH_ORDER = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
BRANCHES = set(BRANCH_ORDER)
STEM_ORDER = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
STEMS = set(STEM_ORDER)
PALACE_NAMES = {
    "命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
    "迁移", "交友", "官禄", "田宅", "福德", "父母",
}
ZIWEI_MAJOR_STARS = {
    "紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府",
    "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军",
}
ZIWEI_MINOR_STARS = {
    "文昌", "文曲", "左辅", "右弼", "天魁", "天钺", "禄存", "擎羊", "陀罗",
    "火星", "铃星", "地空", "地劫", "天马",
}
ZIWEI_ADJECTIVE_STARS = {"天刑", "天姚", "红鸾", "天喜", "天哭", "天虚"}
ZIWEI_TRACKED_STARS = ZIWEI_MAJOR_STARS | ZIWEI_MINOR_STARS | ZIWEI_ADJECTIVE_STARS
SIHUA_TYPES = {"化禄", "化权", "化科", "化忌"}
WUXING_JU = {"水二局": 2, "木三局": 3, "金四局": 4, "土五局": 5, "火六局": 6}
QIMEN_GRID_ORDER = [4, 9, 2, 3, 5, 7, 8, 1, 6]
QIMEN_PALACES = {
    1: ("坎宫", "北", "坎", "水"),
    2: ("坤宫", "西南", "坤", "土"),
    3: ("震宫", "东", "震", "木"),
    4: ("巽宫", "东南", "巽", "木"),
    5: ("中宫", "中", "中", "土"),
    6: ("乾宫", "西北", "乾", "金"),
    7: ("兑宫", "西", "兑", "金"),
    8: ("艮宫", "东北", "艮", "土"),
    9: ("离宫", "南", "离", "火"),
}
QIMEN_DOORS = {"休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门"}
QIMEN_STARS = {"天蓬", "天任", "天冲", "天辅", "天英", "天芮", "天柱", "天心"}
QIMEN_GODS = {"值符", "螣蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"}
QIMEN_PLATE_STEMS = set(STEM_ORDER) - {"甲"}
QIMEN_XUNSHOU = {"甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"}
SOLAR_TERMS = {
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑",
    "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
}


def reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict:
    payload: dict = {}
    for key, value in pairs:
        if key in payload:
            raise ValueError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def load_json(path: Path) -> object:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_json_keys,
    )


def source_path(source_id: str) -> Path:
    payload = load_json(MANIFEST)
    for source in payload["sources"]:
        if source["id"] == source_id:
            path = ROOT / source["path"]
            if not path.exists():
                raise SystemExit(
                    f"Missing {source_id}. Run: python3 scripts/bootstrap_upstreams.py --install-deps"
                )
            if source.get("distribution") != "bundled":
                try:
                    head = subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=path, text=True
                    ).strip()
                    dirty = subprocess.check_output(
                        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                        cwd=path,
                        text=True,
                    ).strip()
                except (OSError, subprocess.CalledProcessError) as exc:
                    raise SystemExit(f"Cannot verify pinned source {source_id}: {exc}") from exc
                if head != source["commit"] or dirty:
                    state = f"HEAD={head}" + ("; dirty worktree" if dirty else "")
                    raise SystemExit(
                        f"Refusing unverified source {source_id} ({state}); run scripts/doctor.py"
                    )
            return path
    raise SystemExit(f"Unknown source id: {source_id}")


def run_python(script: Path, arguments: list[str]) -> int:
    return subprocess.run([sys.executable, str(script), *arguments], check=False).returncode


def verify_runtime_dependencies() -> None:
    for distribution, expected in RUNTIME_DEPENDENCIES.items():
        try:
            actual = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError as exc:
            raise SystemExit(f"Missing pinned runtime dependency {distribution}=={expected}") from exc
        if actual != expected:
            raise SystemExit(
                f"Refusing runtime dependency drift: {distribution}=={actual}; expected {expected}"
            )


def validate_qimen_input(input_path: Path) -> dict:
    """Fail closed before calling an upstream that accepts misleading labels/zones."""
    payload = load_json(input_path)
    if not isinstance(payload, dict):
        raise ValueError("Qimen input must be a JSON object")
    unknown = sorted(set(payload) - QIMEN_INPUT_FIELDS)
    if unknown:
        raise ValueError(
            "Qimen wrapper rejects unreviewed or silently ignored input fields: "
            + ", ".join(unknown)
        )
    if payload.get("ruleset") != QIMEN_RULESET:
        raise ValueError(f"Qimen wrapper accepts only the reviewed ruleset {QIMEN_RULESET}")
    if payload.get("calendar_type") != "solar":
        raise ValueError("Qimen wrapper accepts only calendar_type=solar")
    location = payload.get("location")
    if not isinstance(location, dict):
        raise ValueError("Qimen location must be an object")
    unknown_location = sorted(set(location) - QIMEN_LOCATION_FIELDS)
    if unknown_location:
        raise ValueError(
            "Qimen wrapper rejects unreviewed or silently ignored location fields: "
            + ", ".join(unknown_location)
        )
    timezone_name = location.get("timezone") if isinstance(location, dict) else None
    if timezone_name != QIMEN_TIMEZONE:
        raise ValueError(
            f"Qimen wrapper accepts only fixed UTC+8 ({QIMEN_TIMEZONE}); "
            "convert and validate other local civil times first"
        )
    time_input = payload.get("time_input")
    if not isinstance(time_input, str) or not QIMEN_TIME_INPUT.fullmatch(time_input):
        raise ValueError("Qimen time_input must use YYYY-MM-DD HH:MM[:SS]")
    try:
        parsed_time = datetime.fromisoformat(time_input)
    except ValueError as exc:
        raise ValueError("Qimen time_input must use YYYY-MM-DD HH:MM[:SS]") from exc
    if parsed_time.tzinfo is not None:
        raise ValueError(
            "Qimen time_input must be naive after conversion; use fixed_utc_plus_8_wall_clock"
        )
    if not VERIFIED_CALENDAR_RANGE[0] <= parsed_time.year <= VERIFIED_CALENDAR_RANGE[1]:
        raise ValueError(
            "Qimen reviewed runtime range is 1901-2100; outside dates are unsupported"
        )
    for field in ("question_type", "question_goal"):
        if not isinstance(payload.get(field), str) or not payload[field].strip():
            raise ValueError(f"Qimen {field} must be a non-empty string")
    for field in ("country", "city"):
        if not isinstance(location.get(field), str) or not location[field].strip():
            raise ValueError(f"Qimen location.{field} must be a non-empty string")
    return payload


def validate_ziwei_input(input_path: Path) -> dict:
    """Accept only the explicitly reviewed, timezone-neutral Ziwei contract."""
    payload = load_json(input_path)
    if not isinstance(payload, dict):
        raise ValueError("Ziwei input must be a JSON object")
    unknown = sorted(set(payload) - ZIWEI_INPUT_FIELDS)
    if unknown:
        raise ValueError(
            "Ziwei wrapper rejects unreviewed or silently ignored input fields: "
            + ", ".join(unknown)
        )
    if payload.get("ruleset") != ZIWEI_RULESET:
        raise ValueError(f"Ziwei wrapper accepts only the reviewed ruleset {ZIWEI_RULESET}")
    calendar_type = payload.get("calendar_type")
    if calendar_type not in ZIWEI_CALENDAR_TYPES:
        raise ValueError("Ziwei calendar_type must be solar or lunar")
    birth_time = payload.get("birth_time")
    if not isinstance(birth_time, str) or not ZIWEI_TIME_INPUT.fullmatch(birth_time):
        raise ValueError("Ziwei birth_time must use the naive civil format YYYY-MM-DD HH:MM")
    date_part, time_part = birth_time.split(" ")
    year, month, day = (int(value) for value in date_part.split("-"))
    hour, minute = (int(value) for value in time_part.split(":"))
    if calendar_type == "solar":
        try:
            datetime(year, month, day, hour, minute)
        except ValueError as exc:
            raise ValueError("Ziwei birth_time is not a valid Gregorian civil date and time") from exc
    elif not (1 <= month <= 12 and 1 <= day <= 30 and 0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Ziwei lunar birth_time must use month 1-12, day 1-30, and a valid time")
    if not VERIFIED_CALENDAR_RANGE[0] <= year <= VERIFIED_CALENDAR_RANGE[1]:
        raise ValueError("Ziwei reviewed runtime range is 1901-2100; outside dates are unsupported")
    if type(payload.get("is_leap_month")) is not bool:
        raise ValueError("Ziwei is_leap_month must be an explicit boolean")
    if calendar_type == "solar" and payload["is_leap_month"]:
        raise ValueError("Ziwei is_leap_month must be false for a solar birth_time")
    if payload.get("gender") not in ZIWEI_GENDERS:
        raise ValueError("Ziwei gender must be explicitly 男 or 女")
    if payload.get("late_zi_rule") not in ZIWEI_LATE_ZI_RULES:
        raise ValueError("Ziwei late_zi_rule must be explicitly next_day or same_day")
    if payload.get("leap_month_rule") not in ZIWEI_LEAP_MONTH_RULES:
        raise ValueError("Ziwei leap_month_rule must be explicitly current, next, or split_15")
    if "query_year" in payload:
        query_year = payload["query_year"]
        if type(query_year) is not int or not VERIFIED_CALENDAR_RANGE[0] <= query_year <= VERIFIED_CALENDAR_RANGE[1]:
            raise ValueError("Ziwei query_year must be an integer from 1901 through 2100")
    return payload


def validate_qimen_chart_structure(chart: dict, ganzhi: object) -> None:
    """Require the complete nine-palace surface consumed by routing instructions."""
    if not isinstance(ganzhi, dict):
        raise ValueError("Qimen output lacks Ganzhi metadata")
    for field in ("year", "month", "day", "time"):
        value = ganzhi.get(field)
        if (
            not isinstance(value, str)
            or len(value) != 2
            or value[0] not in STEMS
            or value[1] not in BRANCHES
        ):
            raise ValueError("Qimen output has incomplete Ganzhi pillars")
    if (
        ganzhi.get("day_xun_exact") not in QIMEN_XUNSHOU
        or ganzhi.get("time_xun") not in QIMEN_XUNSHOU
        or chart.get("xunshou") != ganzhi.get("time_xun")
    ):
        raise ValueError("Qimen Xunshou metadata is inconsistent")
    for field in ("day_xunkong_exact", "time_xunkong"):
        value = ganzhi.get(field)
        if not isinstance(value, str) or len(value) != 2 or any(branch not in BRANCHES for branch in value):
            raise ValueError("Qimen Xunkong metadata is incomplete")

    palaces = chart.get("palaces")
    grid_order = chart.get("grid_order")
    door_index = chart.get("door_index")
    star_index = chart.get("star_index")
    if (
        not isinstance(palaces, list)
        or len(palaces) != 9
        or any(not isinstance(palace, dict) for palace in palaces)
        or any(type(palace.get("palace")) is not int for palace in palaces)
        or {palace["palace"] for palace in palaces} != set(QIMEN_PALACES)
        or grid_order != QIMEN_GRID_ORDER
        or not isinstance(door_index, dict)
        or set(door_index) != QIMEN_DOORS
        or any(type(value) is not int or value not in QIMEN_PALACES or value == 5 for value in door_index.values())
        or not isinstance(star_index, dict)
        or set(star_index) != QIMEN_STARS | {"天禽"}
        or any(type(value) is not int or value not in QIMEN_PALACES or value == 5 for value in star_index.values())
    ):
        raise ValueError("Qimen output lacks a complete nine-palace grid and indexes")

    palace_by_number = {palace["palace"]: palace for palace in palaces}
    seen_earth_stems: list[str] = []
    seen_sky_stems: list[str] = []
    seen_doors: set[str] = set()
    seen_stars: set[str] = set()
    seen_gods: set[str] = set()
    for number, palace in palace_by_number.items():
        expected_name, expected_direction, expected_trigram, expected_element = QIMEN_PALACES[number]
        if (
            palace.get("name") != expected_name
            or palace.get("direction") != expected_direction
            or palace.get("trigram") != expected_trigram
            or palace.get("element") != expected_element
            or type(palace.get("is_center")) is not bool
            or type(palace.get("hosts_center")) is not bool
            or type(palace.get("hosts_center_sky")) is not bool
            or palace.get("earth_stem") not in QIMEN_PLATE_STEMS
        ):
            raise ValueError("Qimen palace identity or plate metadata is inconsistent")
        seen_earth_stems.append(palace["earth_stem"])
        sky_stems = palace.get("sky_stems")
        if not isinstance(sky_stems, list) or any(stem not in QIMEN_PLATE_STEMS for stem in sky_stems):
            raise ValueError("Qimen sky-plate stems are incomplete")
        seen_sky_stems.extend(sky_stems)
        if number == 5:
            if (
                not {"star", "door", "god", "sky_stem"}.issubset(palace)
                or palace["is_center"] is not True
                or palace.get("star") is not None
                or palace.get("door") is not None
                or palace.get("god") is not None
                or palace.get("sky_stem") is not None
                or sky_stems
            ):
                raise ValueError("Qimen center palace must remain the hosted empty center")
            continue
        if (
            palace["is_center"] is not False
            or palace.get("door") not in QIMEN_DOORS
            or palace.get("star") not in QIMEN_STARS
            or palace.get("god") not in QIMEN_GODS
            or palace.get("sky_stem") not in QIMEN_PLATE_STEMS
            or palace["sky_stem"] not in sky_stems
            or door_index.get(palace["door"]) != number
            or star_index.get(palace["star"]) != number
        ):
            raise ValueError("Qimen door, star, deity, or sky plate is inconsistent")
        seen_doors.add(palace["door"])
        seen_stars.add(palace["star"])
        seen_gods.add(palace["god"])

    if (
        set(seen_earth_stems) != QIMEN_PLATE_STEMS
        or len(seen_earth_stems) != len(set(seen_earth_stems))
        or set(seen_sky_stems) != QIMEN_PLATE_STEMS
        or len(seen_sky_stems) != len(set(seen_sky_stems))
        or seen_doors != QIMEN_DOORS
        or seen_stars != QIMEN_STARS
        or seen_gods != QIMEN_GODS
        or star_index.get("天禽") != star_index.get("天芮")
    ):
        raise ValueError("Qimen rotating plates are incomplete or duplicated")

    hosted_palace = palace_by_number[star_index["天禽"]]
    center_hosting = chart.get("center_hosting")
    earth_hosts = [palace for palace in palaces if palace.get("hosts_center") is True]
    sky_hosts = [palace for palace in palaces if palace.get("hosts_center_sky") is True]
    if (
        len(earth_hosts) != 1
        or len(sky_hosts) != 1
        or sky_hosts[0] is not hosted_palace
        or hosted_palace.get("hosted_star") != "天禽"
        or hosted_palace.get("hosted_sky_stem") != palace_by_number[5]["earth_stem"]
        or not isinstance(center_hosting, dict)
        or center_hosting.get("hosted_star") != "天禽"
        or center_hosting.get("center_stem") != palace_by_number[5]["earth_stem"]
        or center_hosting.get("earth_host_palace") != earth_hosts[0]["palace"]
        or center_hosting.get("sky_palace") != hosted_palace["palace"]
        or center_hosting.get("follows_star") != "天芮"
    ):
        raise ValueError("Qimen center-hosting metadata is inconsistent")

    zhifu = chart.get("zhifu")
    zhishi = chart.get("zhishi")
    if (
        not isinstance(zhifu, dict)
        or zhifu.get("star") not in QIMEN_STARS
        or zhifu.get("palace") != star_index.get(zhifu.get("star"))
        or not isinstance(zhishi, dict)
        or zhishi.get("door") not in QIMEN_DOORS
        or zhishi.get("palace") != door_index.get(zhishi.get("door"))
        or type(zhishi.get("raw_palace")) is not int
        or type(zhishi.get("hours_from_xunshou")) is not int
    ):
        raise ValueError("Qimen chief-star or chief-door metadata is incomplete")

    for field in ("day_stem", "year_stem", "month_stem"):
        item = chart.get(field)
        if (
            not isinstance(item, dict)
            or item.get("stem") not in QIMEN_PLATE_STEMS
            or type(item.get("raw_palace")) is not int
            or item["raw_palace"] not in QIMEN_PALACES
            or type(item.get("palace")) is not int
            or item["palace"] not in QIMEN_PALACES
        ):
            raise ValueError("Qimen stem-role metadata is incomplete")
    for field in ("hour_yima", "day_yima"):
        item = chart.get(field)
        if (
            not isinstance(item, dict)
            or item.get("branch") not in BRANCHES
            or item.get("source_branch") not in BRANCHES
            or type(item.get("palace")) is not int
            or item["palace"] not in QIMEN_PALACES
        ):
            raise ValueError("Qimen Yima metadata is incomplete")

    if chart.get("hidden_yi") not in QIMEN_PLATE_STEMS or chart.get("time_stem_visible") not in QIMEN_PLATE_STEMS:
        raise ValueError("Qimen hidden or visible stem metadata is incomplete")
    for field in ("kongwang", "day_kongwang"):
        values = chart.get(field)
        if not isinstance(values, list) or not values or any(branch not in BRANCHES for branch in values):
            raise ValueError("Qimen void branches are incomplete")
    for field in ("kongwang_palaces", "day_kongwang_palaces"):
        values = chart.get(field)
        if not isinstance(values, list) or any(type(value) is not int or value not in QIMEN_PALACES for value in values):
            raise ValueError("Qimen void-palace indexes are incomplete")
    patterns = chart.get("detected_patterns")
    if not isinstance(patterns, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("name"), str)
        or not item["name"]
        or type(item.get("palace")) is not int
        or item["palace"] not in QIMEN_PALACES
        or not isinstance(item.get("detail"), str)
        or item.get("nature") not in {"吉", "凶", "中"}
        for item in patterns
    ):
        raise ValueError("Qimen detected-pattern metadata is malformed")


def annotate_qimen_profile(output: Path, expected: dict) -> None:
    """Attach the locally reviewed effective profile to a successful Qimen result."""
    payload = load_json(output)
    ruleset = payload.get("ruleset")
    declared_ruleset = ruleset.get("id") if isinstance(ruleset, dict) else ruleset
    normalized = payload.get("normalized_input")
    normalized_ruleset = normalized.get("ruleset") if isinstance(normalized, dict) else None
    if declared_ruleset != QIMEN_RULESET or normalized_ruleset != QIMEN_RULESET:
        values = f"ruleset={declared_ruleset!r}, normalized_input.ruleset={normalized_ruleset!r}"
        raise ValueError(
            "Refusing to attach the fixed-solar-term-five-day-v1 review to "
            f"an unverified Qimen ruleset ({values})"
        )
    expected_normalized = {
        "question_type": expected["question_type"].strip(),
        "question_goal": expected["question_goal"].strip(),
        "calendar_type": expected["calendar_type"],
        "ruleset": expected["ruleset"],
        "timezone": expected["location"]["timezone"],
        "country": expected["location"]["country"].strip(),
        "city": expected["location"]["city"].strip(),
        "original_time_input": expected["time_input"],
        "used_now": False,
    }
    if not isinstance(normalized, dict) or any(
        normalized.get(key) != value for key, value in expected_normalized.items()
    ):
        raise ValueError(
            "Refusing to annotate a Qimen output whose normalized input differs from the request"
        )
    calendar = payload.get("calendar")
    solar = calendar.get("solar") if isinstance(calendar, dict) else None
    lunar = calendar.get("lunar") if isinstance(calendar, dict) else None
    jieqi = calendar.get("jieqi") if isinstance(calendar, dict) else None
    ganzhi = payload.get("ganzhi")
    chart = payload.get("chart")
    if (
        normalized.get("timezone") != QIMEN_TIMEZONE
        or normalized.get("calendar_type") != "solar"
        or not isinstance(solar, dict)
        or solar.get("timezone") != QIMEN_TIMEZONE
        or not isinstance(lunar, dict)
    ):
        raise ValueError("Refusing to annotate a Qimen output outside the reviewed fixed UTC+8 solar profile")
    original_time = normalized.get("original_time_input")
    calculated_time = solar.get("ymd_hms")
    try:
        time_matches = (
            isinstance(original_time, str)
            and isinstance(calculated_time, str)
            and QIMEN_TIME_INPUT.fullmatch(original_time) is not None
            and QIMEN_TIME_INPUT.fullmatch(calculated_time) is not None
            and datetime.fromisoformat(original_time) == datetime.fromisoformat(calculated_time)
        )
    except ValueError:
        time_matches = False
    if not time_matches:
        raise ValueError("Refusing to annotate Qimen output whose calculated wall clock differs from input")
    if (
        not isinstance(jieqi, dict)
        or jieqi.get("active_jie") not in SOLAR_TERMS
        or jieqi.get("next_jie") not in SOLAR_TERMS
        or not isinstance(jieqi.get("active_jie_started_at"), str)
        or QIMEN_TIME_INPUT.fullmatch(jieqi["active_jie_started_at"]) is None
        or not isinstance(jieqi.get("next_jie_at"), str)
        or QIMEN_TIME_INPUT.fullmatch(jieqi["next_jie_at"]) is None
        or not isinstance(chart, dict)
        or chart.get("dun_type") not in {"阳遁", "阴遁"}
        or chart.get("yuan") not in {"上元", "中元", "下元"}
        or type(chart.get("ju_number")) is not int
        or not 1 <= chart["ju_number"] <= 9
    ):
        raise ValueError("Refusing to annotate incomplete Qimen calendar/chart output")
    if (
        type(lunar.get("year")) is not int
        or type(lunar.get("month")) is not int
        or not 1 <= lunar["month"] <= 12
        or type(lunar.get("day")) is not int
        or not 1 <= lunar["day"] <= 30
        or type(lunar.get("is_leap_month")) is not bool
        or not isinstance(lunar.get("month_text"), str)
        or not lunar["month_text"]
        or not isinstance(lunar.get("day_text"), str)
        or not lunar["day_text"]
    ):
        raise ValueError("Refusing to annotate incomplete Qimen lunar-calendar output")
    validate_qimen_chart_structure(chart, ganzhi)

    warnings = payload.setdefault("warnings", [])
    if not isinstance(warnings, list):
        raise ValueError("Qimen output warnings must be a list")
    payload["profile_review"] = {
        "schema_version": 1,
        "declared_ruleset": "mainline-cn-v1",
        "effective_profile_id": "fixed-solar-term-five-day-v1",
        "input_time_basis": "fixed UTC+8 wall clock (Etc/GMT-8)",
        "iana_timezone_conversion_supported_by_engine": False,
        "source_civil_time_conversion_verified": False,
        "output_schema_completeness_verified": True,
        "algorithmic_correctness_independently_verified": False,
        "reviewed_calendar_range": [1901, 2100],
        "evidence_tier": "C",
        "full_zhirun_implemented": False,
        "audit_reference": "references/qimen-profile-audit.md",
    }
    warnings.append(
        "口径提示：mainline-cn-v1 是“当前节气 + 五日三元 + 固定局表”的工程 profile，"
        "尚未实现完整超神/接气/置闰调度；不得把本盘标作完整置闰法。"
    )
    warnings.append(
        "时间提示：上游元数据中的 Asia/Shanghai 不代表已正确处理 IANA 历史时区或 DST；"
        "本适配层只审核转换后的固定 UTC+8 壁钟（Etc/GMT-8）。"
    )
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_sihua_entries(
    entries: object,
    star_index: dict,
    palace_by_branch: dict,
) -> bool:
    if (
        not isinstance(entries, list)
        or len(entries) != 4
        or any(not isinstance(item, dict) for item in entries)
        or any(not isinstance(item.get("type"), str) for item in entries)
        or {item.get("type") for item in entries} != SIHUA_TYPES
    ):
        return False
    for item in entries:
        star = item.get("star")
        branch = item.get("branch")
        palace = palace_by_branch.get(branch)
        if (
            not isinstance(star, str)
            or star not in star_index
            or star_index[star] != branch
            or not isinstance(palace, dict)
            or item.get("palace") != palace.get("name")
        ):
            return False
    return True


def validate_ziwei_chart_structure(chart: dict) -> tuple[dict, list[tuple[int, int, dict]]]:
    """Validate all chart surfaces that downstream instructions tell a caller to consume."""
    palaces = chart.get("palaces")
    star_index = chart.get("star_index")
    self_check = chart.get("self_check")
    if (
        not isinstance(palaces, list)
        or len(palaces) != 12
        or any(not isinstance(palace, dict) for palace in palaces)
        or any(not isinstance(palace.get("name"), str) for palace in palaces)
        or any(not isinstance(palace.get("branch"), str) for palace in palaces)
        or {palace.get("name") for palace in palaces} != PALACE_NAMES
        or {palace.get("branch") for palace in palaces} != BRANCHES
        or not isinstance(star_index, dict)
        or set(star_index) != ZIWEI_TRACKED_STARS
        or any(not isinstance(branch, str) or branch not in BRANCHES for branch in star_index.values())
        or not isinstance(self_check, dict)
        or self_check.get("passed") is not True
        or type(self_check.get("major_star_count")) is not int
        or self_check.get("major_star_count") != 14
    ):
        raise ValueError("Refusing to annotate an incomplete or self-check-failing Ziwei chart")

    palace_by_branch = {palace["branch"]: palace for palace in palaces}
    palace_by_name = {palace["name"]: palace for palace in palaces}
    seen_stars: dict[str, str] = {}
    seen_major: set[str] = set()
    decadal_spans: list[tuple[int, int, dict]] = []
    shen_palaces: list[dict] = []
    for palace in palaces:
        branch = palace["branch"]
        stem = palace.get("stem")
        if stem not in STEMS or palace.get("ganzhi") != stem + branch:
            raise ValueError("Ziwei palace stem/branch metadata is incomplete")
        if type(palace.get("is_shen_gong")) is not bool:
            raise ValueError("Ziwei palace body-palace flag must be Boolean")
        if palace["is_shen_gong"]:
            shen_palaces.append(palace)

        decadal = palace.get("decadal")
        start = decadal.get("start_age") if isinstance(decadal, dict) else None
        end = decadal.get("end_age") if isinstance(decadal, dict) else None
        if type(start) is not int or type(end) is not int or end - start != 9 or start < 1:
            raise ValueError("Ziwei palace decadal span is incomplete")
        decadal_spans.append((start, end, palace))

        for field in ("major_stars", "minor_stars"):
            stars = palace.get(field)
            if not isinstance(stars, list) or any(not isinstance(star, dict) for star in stars):
                raise ValueError("Ziwei palace star lists are incomplete")
            for star in stars:
                name = star.get("name")
                if not isinstance(name, str) or name not in ZIWEI_TRACKED_STARS or name in seen_stars:
                    raise ValueError("Ziwei chart contains a missing, unknown, or duplicate star")
                seen_stars[name] = branch
                if field == "major_stars":
                    seen_major.add(name)
                    if name not in ZIWEI_MAJOR_STARS:
                        raise ValueError("Ziwei major-star list contains a non-major star")
                elif name not in ZIWEI_MINOR_STARS:
                    raise ValueError("Ziwei minor-star list contains a non-minor star")
        adjectives = palace.get("adjective_stars")
        if not isinstance(adjectives, list) or any(
            not isinstance(name, str) or name not in ZIWEI_TRACKED_STARS or name in seen_stars
            for name in adjectives
        ) or len(set(adjectives)) != len(adjectives):
            raise ValueError("Ziwei palace adjective-star list is incomplete")
        for name in adjectives:
            if name not in ZIWEI_ADJECTIVE_STARS:
                raise ValueError("Ziwei adjective-star list contains another star class")
            seen_stars[name] = branch

    if seen_major != ZIWEI_MAJOR_STARS or seen_stars != star_index:
        raise ValueError("Ziwei palace star placements do not match the complete star index")
    spans = sorted(decadal_spans, key=lambda item: item[0])
    if any(current[0] != previous[1] + 1 for previous, current in zip(spans, spans[1:])):
        raise ValueError("Ziwei decadal spans are not contiguous")
    if len(shen_palaces) != 1:
        raise ValueError("Ziwei chart must identify exactly one body palace")

    ming = chart.get("ming_gong")
    shen = chart.get("shen_gong")
    wuxing = chart.get("wuxing_ju")
    ming_palace = palace_by_name["命宫"]
    shen_palace = shen_palaces[0]
    if (
        not isinstance(ming, dict)
        or ming.get("branch") != ming_palace["branch"]
        or ming.get("ganzhi") != ming_palace["ganzhi"]
        or not isinstance(shen, dict)
        or shen.get("branch") != shen_palace["branch"]
        or shen.get("palace") != shen_palace["name"]
        or not isinstance(wuxing, dict)
        or not isinstance(wuxing.get("name"), str)
        or WUXING_JU.get(wuxing.get("name")) != wuxing.get("number")
        or chart.get("decadal_direction") not in {"顺行", "逆行"}
        or not isinstance(chart.get("ming_zhu"), str)
        or not chart["ming_zhu"]
        or not isinstance(chart.get("shen_zhu"), str)
        or not chart["shen_zhu"]
        or self_check.get("ziwei_branch") != star_index["紫微"]
        or not validate_sihua_entries(chart.get("year_sihua"), star_index, palace_by_branch)
    ):
        raise ValueError("Ziwei chart identity, bureau, rulers, or natal transformations are incomplete")
    partner = self_check.get("ziwei_partner")
    if partner is not None and (
        not isinstance(partner, str)
        or partner not in ZIWEI_MAJOR_STARS
        or star_index[partner] != star_index["紫微"]
    ):
        raise ValueError("Ziwei self-check partner metadata is inconsistent")
    return palace_by_branch, spans


def validate_ziwei_horoscope_structure(
    horoscope: object,
    query_year: int,
    nominal_age: int,
    star_index: dict,
    palace_by_branch: dict,
    decadal_spans: list[tuple[int, int, dict]],
) -> bool:
    if not isinstance(horoscope, dict):
        return False
    yearly = horoscope.get("yearly")
    if not isinstance(yearly, dict):
        return False
    expected_year_branch = BRANCH_ORDER[(query_year - 4) % 12]
    expected_year_ganzhi = STEM_ORDER[(query_year - 4) % 10] + expected_year_branch
    yearly_palaces = yearly.get("palaces")
    if (
        horoscope.get("query_lunar_year") != query_year
        or type(horoscope.get("nominal_age")) is not int
        or horoscope.get("nominal_age") != nominal_age
        or yearly.get("ganzhi") != expected_year_ganzhi
        or yearly.get("ming_branch") != expected_year_branch
        or yearly.get("ming_on_natal_palace") != palace_by_branch[expected_year_branch]["name"]
        or not isinstance(yearly_palaces, list)
        or len(yearly_palaces) != 12
        or any(not isinstance(item, dict) for item in yearly_palaces)
        or any(not isinstance(item.get("name"), str) for item in yearly_palaces)
        or any(not isinstance(item.get("branch"), str) for item in yearly_palaces)
        or {item.get("name") for item in yearly_palaces} != PALACE_NAMES
        or {item.get("branch") for item in yearly_palaces} != BRANCHES
        or any(
            item.get("natal_palace") != palace_by_branch[item.get("branch")]["name"]
            for item in yearly_palaces
        )
        or not validate_sihua_entries(yearly.get("sihua"), star_index, palace_by_branch)
    ):
        return False

    matching = [span for span in decadal_spans if span[0] <= nominal_age <= span[1]]
    decadal = horoscope.get("decadal")
    if not matching:
        return decadal is None
    if len(matching) != 1 or not isinstance(decadal, dict):
        return False
    start, end, palace = matching[0]
    return (
        decadal.get("branch") == palace["branch"]
        and decadal.get("ganzhi") == palace["ganzhi"]
        and decadal.get("natal_palace") == palace["name"]
        and decadal.get("start_age") == start
        and decadal.get("end_age") == end
        and validate_sihua_entries(decadal.get("sihua"), star_index, palace_by_branch)
    )


def annotate_ziwei_profile(output: Path, expected: dict) -> None:
    """Verify the Ziwei result before attaching the local Tier C profile review."""
    from lunar_python import Lunar, Solar

    payload = load_json(output)
    if not isinstance(payload, dict):
        raise ValueError("Ziwei output must be a JSON object")
    normalized = payload.get("normalized_input")
    ruleset = payload.get("ruleset")
    calendar = payload.get("calendar")
    chart = payload.get("chart")
    warnings = payload.get("warnings")
    if not all(isinstance(item, dict) for item in (normalized, ruleset, calendar, chart)):
        raise ValueError("Refusing to annotate an incomplete Ziwei output")
    if warnings is None:
        warnings = []
        payload["warnings"] = warnings
    if not isinstance(warnings, list):
        raise ValueError("Ziwei output warnings must be a list")
    if ruleset.get("id") != ZIWEI_RULESET:
        raise ValueError("Refusing to attach the Ziwei review to an unverified ruleset")

    expected_fields = {
        "calendar_type": expected["calendar_type"],
        "original_birth_time": expected["birth_time"],
        "gender": expected["gender"],
        "leap_month_rule": expected["leap_month_rule"],
        "late_zi_rule": expected["late_zi_rule"],
    }
    if any(normalized.get(key) != value for key, value in expected_fields.items()):
        raise ValueError("Refusing to annotate Ziwei output whose normalized input differs from the request")
    if normalized.get("leap_month_rule_source") != "explicit":
        raise ValueError("Refusing a Ziwei output that silently defaulted the leap-month convention")
    civil_solar = normalized.get("civil_solar_datetime")
    if not isinstance(civil_solar, str) or not ZIWEI_TIME_INPUT.fullmatch(civil_solar):
        raise ValueError("Ziwei output lacks a strict normalized civil solar datetime")
    try:
        normalized_time = datetime.strptime(civil_solar, "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise ValueError("Ziwei output has an invalid normalized civil solar datetime") from exc
    if not VERIFIED_CALENDAR_RANGE[0] <= normalized_time.year <= VERIFIED_CALENDAR_RANGE[1]:
        raise ValueError("Ziwei normalized date is outside the reviewed 1901-2100 range")

    leap_rule = ruleset.get("leap_month_rule")
    if (
        ruleset.get("late_zi_rule") != ZIWEI_LATE_ZI_DESCRIPTIONS[expected["late_zi_rule"]]
        or not isinstance(leap_rule, dict)
        or leap_rule.get("id") != expected["leap_month_rule"]
        or leap_rule.get("source") != "explicit"
    ):
        raise ValueError("Ziwei ruleset metadata does not preserve the selected conventions")
    if type(calendar.get("is_leap_month")) is not bool or leap_rule.get("applied") is not calendar["is_leap_month"]:
        raise ValueError("Ziwei leap-month application metadata is inconsistent")

    birth_hour = int(expected["birth_time"][11:13])
    birth_minute = int(expected["birth_time"][14:16])
    expected_rollover = expected["late_zi_rule"] == "next_day" and birth_hour == 23
    if calendar.get("day_rollover_applied") is not expected_rollover:
        raise ValueError("Ziwei output does not preserve the selected late-Zi rollover rule")
    if normalized_time.hour != birth_hour or normalized_time.minute != birth_minute:
        raise ValueError("Ziwei normalized clock time differs from the request")
    if expected["calendar_type"] == "solar":
        expected_civil_solar = expected["birth_time"]
    else:
        lunar_year, lunar_month, lunar_day = (
            int(value) for value in expected["birth_time"][:10].split("-")
        )
        lunar = Lunar.fromYmd(
            lunar_year,
            -lunar_month if expected["is_leap_month"] else lunar_month,
            lunar_day,
        )
        solar = lunar.getSolar()
        expected_civil_solar = (
            f"{solar.getYear():04d}-{solar.getMonth():02d}-{solar.getDay():02d} "
            f"{birth_hour:02d}:{birth_minute:02d}"
        )
    if civil_solar != expected_civil_solar:
        raise ValueError("Ziwei normalized civil date does not match the requested calendar input")
    expected_hour_branch = BRANCH_ORDER[((birth_hour + 1) // 2) % 12] + "时"
    if calendar.get("hour_branch") != expected_hour_branch:
        raise ValueError("Ziwei output hour branch differs from the supplied civil clock")
    palace_by_branch, decadal_spans = validate_ziwei_chart_structure(chart)
    chart_solar_date = calendar.get("chart_solar_date")
    try:
        chart_date = datetime.strptime(chart_solar_date, "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise ValueError("Ziwei output has an invalid chart solar date") from exc
    if not VERIFIED_CALENDAR_RANGE[0] <= chart_date.year <= VERIFIED_CALENDAR_RANGE[1]:
        raise ValueError("Ziwei chart date is outside the reviewed 1901-2100 range")
    expected_chart_date = normalized_time.date() + timedelta(days=1 if expected_rollover else 0)
    if chart_date.date() != expected_chart_date:
        raise ValueError("Ziwei chart date does not match the selected late-Zi rollover rule")

    recalculated_lunar = Solar.fromYmd(
        chart_date.year,
        chart_date.month,
        chart_date.day,
    ).getLunar()
    recalculated_month = abs(recalculated_lunar.getMonth())
    recalculated_day = recalculated_lunar.getDay()
    recalculated_is_leap = recalculated_lunar.getMonth() < 0
    recalculated_chart_month = recalculated_month
    if recalculated_is_leap and (
        expected["leap_month_rule"] == "next"
        or (expected["leap_month_rule"] == "split_15" and recalculated_day > 15)
    ):
        recalculated_chart_month = recalculated_month % 12 + 1
    recalculated_fields = {
        "lunar_year": recalculated_lunar.getYear(),
        "lunar_month": recalculated_month,
        "lunar_day": recalculated_day,
        "is_leap_month": recalculated_is_leap,
        "chart_month": recalculated_chart_month,
        "year_ganzhi": recalculated_lunar.getYearInGanZhi(),
    }
    if any(calendar.get(key) != value for key, value in recalculated_fields.items()):
        raise ValueError("Ziwei calendar metadata does not match the pinned calendar conversion")

    horoscope = payload.get("horoscope")
    if "query_year" in expected:
        expected_nominal_age = expected["query_year"] - calendar["lunar_year"] + 1
        if expected_nominal_age < 1 or not validate_ziwei_horoscope_structure(
            horoscope,
            expected["query_year"],
            expected_nominal_age,
            chart["star_index"],
            palace_by_branch,
            decadal_spans,
        ):
            raise ValueError("Ziwei horoscope output does not match the requested query_year")
    elif horoscope is not None:
        raise ValueError("Ziwei output contains an unrequested horoscope overlay")

    payload["profile_review"] = {
        "schema_version": 1,
        "declared_ruleset": ZIWEI_RULESET,
        "effective_profile_id": "fixed-civil-date-sanhe-v1",
        "input_time_basis": (
            "caller-supplied naive solar civil wall clock"
            if expected["calendar_type"] == "solar"
            else "caller-supplied lunar calendar date with a naive wall clock"
        ),
        "iana_timezone_conversion_supported_by_engine": False,
        "longitude_or_true_solar_time_supported_by_engine": False,
        "minute_precision_role": "two-hour branch selection and boundary warning only",
        "reviewed_calendar_range": [1901, 2100],
        "requested_is_leap_month": expected["is_leap_month"],
        "selected_late_zi_rule": expected["late_zi_rule"],
        "selected_leap_month_rule": expected["leap_month_rule"],
        "query_year": expected.get("query_year"),
        "evidence_tier": "C",
        "independently_validated": False,
        "output_schema_completeness_verified": True,
        "calendar_fields_recomputed_with_pinned_dependency": True,
        "school_algorithm_recomputed_independently": False,
        "audit_reference": "references/ziwei-runtime-audit.md",
    }
    warnings.append(
        "口径提示：本结果只是 ziwei-sanhe-v1 固定三合工程 profile 的可复现输出，"
        "尚无独立权威引擎或成组历书金标准验证，不得表述为通行各派的唯一正确命盘。"
    )
    warnings.append(
        "时间提示：引擎不处理 IANA 时区、历史 DST、经度或真太阳时；分钟只用于时辰归属和交界提醒。"
        "若输入来自异地或历史民用时间，必须先独立核验转换并保留记录。"
    )
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_calculator_atomically(
    script: Path,
    input_path: Path,
    output_path: Path,
    annotator: Callable[[Path], None],
) -> int:
    """Publish a calculator result only after upstream success and local review."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
        delete=False,
    ) as handle:
        temporary_output = Path(handle.name)
    try:
        result = run_python(
            script,
            ["--input", str(input_path), "--output", str(temporary_output)],
        )
        if result != 0:
            try:
                diagnostic = temporary_output.read_text(encoding="utf-8").strip()
            except OSError:
                diagnostic = ""
            if diagnostic:
                print(diagnostic, file=sys.stderr)
            return result
        annotator(temporary_output)
        temporary_output.replace(output_path)
        return 0
    finally:
        temporary_output.unlink(missing_ok=True)


def run_qimen_atomically(
    script: Path,
    input_path: Path,
    output_path: Path,
    expected: dict,
) -> int:
    return run_calculator_atomically(
        script,
        input_path,
        output_path,
        lambda path: annotate_qimen_profile(path, expected),
    )


def run_ziwei_atomically(
    script: Path,
    input_path: Path,
    output_path: Path,
    expected: dict,
) -> int:
    return run_calculator_atomically(
        script,
        input_path,
        output_path,
        lambda path: annotate_ziwei_profile(path, expected),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="module", required=True)

    bazi = subparsers.add_parser("bazi", help="Run the bundled Bazi calculator")
    bazi.add_argument("arguments", nargs=argparse.REMAINDER)

    for name in ("qimen", "ziwei"):
        command = subparsers.add_parser(name, help=f"Run the pinned {name} calculator")
        command.add_argument("--input", required=True)
        command.add_argument("--output", required=True)

    subparsers.add_parser("fengshui-source", help="Print the pinned Feng Shui SKILL.md path")
    args = parser.parse_args()

    if args.module == "bazi":
        verify_runtime_dependencies()
        remainder = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        script = source_path("bazi-skill") / "scripts" / "pai_pan.py"
        return run_python(script, remainder)

    if args.module == "qimen":
        input_path = Path(args.input)
        output_path = Path(args.output)
        try:
            expected = validate_qimen_input(input_path)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parser.error(str(exc))
        verify_runtime_dependencies()
        script = source_path("numerologist-skills") / "qimen-dunjia" / "scripts" / "qimen_cli.py"
        try:
            return run_qimen_atomically(script, input_path, output_path, expected)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parser.error(str(exc))

    if args.module == "ziwei":
        input_path = Path(args.input)
        output_path = Path(args.output)
        try:
            expected = validate_ziwei_input(input_path)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parser.error(str(exc))
        verify_runtime_dependencies()
        script = source_path("numerologist-skills") / "ziwei-doushu" / "scripts" / "ziwei_cli.py"
        try:
            return run_ziwei_atomically(script, input_path, output_path, expected)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parser.error(str(exc))

    skill_file = source_path("fengshui-skill") / "SKILL.md"
    print(skill_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
