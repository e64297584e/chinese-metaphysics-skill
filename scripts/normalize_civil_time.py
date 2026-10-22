#!/usr/bin/env python3
"""Validate a local civil timestamp against a pinned IANA timezone.

This tool detects nonexistent spring-forward times and ambiguous fall-back times.
It normalizes an instant only; it does not choose a Bazi/Ziwei day-boundary school or
perform longitude/equation-of-time correction.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import zoneinfo
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


LOCAL_TIME_INPUT = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}(?::[0-9]{2})?$"
)
EXPECTED_TZDATA_PACKAGE = "2026.5"
EXPECTED_TZDB_VERSION = "2026e"


def pin_tzdata_package() -> Path | None:
    """Force ZoneInfo to use the reviewed Python tzdata wheel when installed."""
    try:
        import tzdata
    except ImportError:
        return None
    root = Path(tzdata.__file__).parent / "zoneinfo"
    zoneinfo.reset_tzpath([str(root)])
    ZoneInfo.clear_cache()
    return root


ACTIVE_TZDATA_ROOT = pin_tzdata_package()
UTC = timezone.utc
BEIJING = ZoneInfo("Asia/Shanghai")
FIXED_UTC_PLUS_8 = timezone(timedelta(hours=8))


def format_offset(value) -> str:
    total_seconds = int(value.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    suffix = f":{seconds:02d}" if seconds else ""
    return f"{sign}{hours:02d}:{minutes:02d}{suffix}"


def tzdb_version() -> str:
    for root in zoneinfo.TZPATH:
        try:
            first_line = (Path(root) / "tzdata.zi").read_text(encoding="utf-8").splitlines()[0]
        except (OSError, IndexError):
            continue
        if first_line.startswith("# version "):
            return first_line.removeprefix("# version ").strip()
    return "system-or-unknown"


def tzdata_package_version() -> str:
    try:
        return importlib.metadata.version("tzdata")
    except importlib.metadata.PackageNotFoundError:
        return "system-or-unknown"


def parse_local_time(value: str) -> datetime:
    if not LOCAL_TIME_INPUT.fullmatch(value):
        raise ValueError("--local must use YYYY-MM-DD HH:MM[:SS]")
    return datetime.fromisoformat(value)


def verify_tzdata_runtime() -> None:
    package_version = tzdata_package_version()
    active_version = tzdb_version()
    if (
        ACTIVE_TZDATA_ROOT is None
        or zoneinfo.TZPATH != (str(ACTIVE_TZDATA_ROOT),)
        or package_version != EXPECTED_TZDATA_PACKAGE
        or active_version != EXPECTED_TZDB_VERSION
    ):
        raise ValueError(
            "pinned timezone runtime unavailable: require "
            f"tzdata=={EXPECTED_TZDATA_PACKAGE} / tzdb {EXPECTED_TZDB_VERSION}"
        )


def local_candidates(local_time: datetime, zone_name: str) -> list[dict[str, object]]:
    if local_time.tzinfo is not None:
        raise ValueError("local_time must be naive; pass the timezone separately")
    zone = ZoneInfo(zone_name)
    candidates: list[dict[str, object]] = []
    seen_utc: set[str] = set()
    for fold in (0, 1):
        aware = local_time.replace(tzinfo=zone, fold=fold)
        try:
            instant = aware.astimezone(UTC)
            roundtrip = instant.astimezone(zone)
        except OverflowError as exc:
            raise ValueError("local time is outside the supported timezone conversion range") from exc
        if roundtrip.replace(tzinfo=None) != local_time:
            continue
        utc_key = instant.isoformat()
        if utc_key in seen_utc:
            continue
        seen_utc.add(utc_key)
        fixed_utc_plus_8 = instant.astimezone(FIXED_UTC_PLUS_8)
        candidates.append(
            {
                "fold": fold,
                "utc_offset": format_offset(aware.utcoffset()),
                "utc": instant.isoformat(),
                "localized": aware.isoformat(),
                "asia_shanghai": instant.astimezone(BEIJING).isoformat(),
                "fixed_utc_plus_8": fixed_utc_plus_8.isoformat(),
                "fixed_utc_plus_8_wall_clock": fixed_utc_plus_8.replace(tzinfo=None).isoformat(
                    sep=" "
                ),
            }
        )
    return candidates


def classify_local_time(local_time: datetime, zone_name: str) -> dict[str, object]:
    verify_tzdata_runtime()
    candidates = local_candidates(local_time, zone_name)
    status = "nonexistent" if not candidates else "ambiguous" if len(candidates) == 2 else "valid"
    result = {
        "status": status,
        "input": local_time.isoformat(sep=" "),
        "timezone": zone_name,
        "tzdata_package": tzdata_package_version(),
        "tzdb_version": tzdb_version(),
        "tzdb_source": "python-tzdata-package" if ACTIVE_TZDATA_ROOT else "system-zoneinfo",
        "candidates": candidates,
        "limitations": [
            "This validates civil time only.",
            "It does not apply longitude correction or equation of time.",
            "It does not select a metaphysics day-boundary or chart profile.",
            "Pre-1970 tzdb history can be incomplete and requires source review.",
        ],
    }
    if status == "valid":
        result["selected"] = candidates[0]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", required=True, help="Local wall time, YYYY-MM-DD HH:MM[:SS]")
    parser.add_argument("--timezone", required=True, help="IANA timezone, for example Asia/Shanghai")
    parser.add_argument("--fold", type=int, choices=(0, 1), help="Choose one side of an ambiguous time")
    args = parser.parse_args()

    try:
        local_time = parse_local_time(args.local)
        result = classify_local_time(local_time, args.timezone)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        parser.error(str(exc))

    if args.fold is not None:
        matches = [item for item in result["candidates"] if item["fold"] == args.fold]
        if not matches:
            result.pop("selected", None)
            result["error"] = f"fold={args.fold} is not valid for this local time"
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2
        result["selected"] = matches[0]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "nonexistent":
        return 2
    if result["status"] == "ambiguous" and args.fold is None:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
