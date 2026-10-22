#!/usr/bin/env python3
"""Audit one annual slice of the Renhuai Ziwei v4 JSONL dataset.

The script never emits interpretation text.  By default it checks only the
record structure and weak chart field ``ms``.  ``--scan-text`` additionally
computes aggregate duplication and rights-marker statistics.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import IO, BinaryIO, Iterable, Iterator


TOPICS = (
    "overview",
    "personality",
    "love",
    "career",
    "wealth",
    "health",
    "family",
    "children",
    "move",
    "friends",
    "home",
    "spirit",
    "parents",
)
EXPECTED_FIELDS = {"k", "y", "m", "d", "h", "g", "ms", "t", "c"}
MAJOR_STARS = {
    "紫微",
    "天机",
    "太阳",
    "武曲",
    "天同",
    "廉贞",
    "天府",
    "太阴",
    "贪狼",
    "巨门",
    "天相",
    "天梁",
    "七杀",
    "破军",
}
RIGHTS_MARKERS = ("倪师", "倪海厦", "《天纪》")
DEFAULT_MAX_INPUT_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_OUTPUT_BYTES = 1024 * 1024 * 1024
DEFAULT_MAX_LINE_BYTES = 1024 * 1024
DEFAULT_MAX_LINES = 10_000
DEFAULT_MAX_DISTINCT_HASHES = 1_000_000


class AuditInputError(ValueError):
    """Raised when an input violates a parser or resource boundary."""


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise AuditInputError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def utf16_code_units(text: str) -> int:
    """Match JavaScript String.length, which the dataset's ``t`` field uses."""

    return len(text.encode("utf-16-le")) // 2


def text_digest(text: str) -> bytes:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=16).digest()


def copy_and_sha256(source: BinaryIO, target: BinaryIO, *, max_bytes: int) -> str:
    """Copy a bounded input while hashing the exact bytes that will be parsed."""

    digest = hashlib.sha256()
    total = 0
    for chunk in iter(lambda: source.read(1024 * 1024), b""):
        total += len(chunk)
        if total > max_bytes:
            raise AuditInputError(f"input file exceeds {max_bytes} bytes")
        digest.update(chunk)
        target.write(chunk)
    target.flush()
    target.seek(0)
    return digest.hexdigest()


@contextlib.contextmanager
def open_dataset(path: str, source: BinaryIO | None = None) -> Iterator[IO[str]]:
    if path == "-":
        yield sys.stdin
        return

    if source is None:
        raise AuditInputError("an opened binary source is required for file input")
    if Path(path).suffix != ".zst":
        text_source = io.TextIOWrapper(source, encoding="utf-8")
        try:
            yield text_source
        finally:
            text_source.detach()
        return

    if shutil.which("zstd") is None:
        raise RuntimeError("zstd is required to read .zst files")
    process = subprocess.Popen(
        ["zstd", "-dc", "--long=27"],
        stdin=source,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    assert process.stdout is not None
    assert process.stderr is not None
    fully_consumed = False
    try:
        yield process.stdout
        fully_consumed = True
    finally:
        process.stdout.close()
        stderr = process.stderr.read().strip()
        return_code = process.wait()
        if return_code and fully_consumed:
            raise RuntimeError(f"zstd failed with exit {return_code}: {stderr}")


def bounded_lines(
    source: IO[str],
    *,
    max_output_bytes: int,
    max_line_bytes: int,
    max_lines: int,
) -> Iterator[str]:
    """Yield UTF-8 lines while enforcing annual-slice resource limits."""

    output_bytes = 0
    for line_number in range(1, max_lines + 2):
        # The character bound also caps decoder allocation.  UTF-8 byte length
        # is checked separately because non-ASCII characters use multiple bytes.
        line = source.readline(max_line_bytes + 1)
        if not line:
            return
        encoded_bytes = len(line.encode("utf-8"))
        if len(line) > max_line_bytes or encoded_bytes > max_line_bytes:
            raise AuditInputError(f"line {line_number} exceeds {max_line_bytes} UTF-8 bytes")
        output_bytes += encoded_bytes
        if output_bytes > max_output_bytes:
            raise AuditInputError(f"decompressed input exceeds {max_output_bytes} bytes")
        if line_number > max_lines:
            raise AuditInputError(f"input exceeds {max_lines} lines")
        yield line


def days_in_year(year: int) -> int:
    return (dt.date(year + 1, 1, 1) - dt.date(year, 1, 1)).days


def calendar_year(value: str) -> int:
    year = int(value)
    if not 1 <= year <= 9998:
        raise argparse.ArgumentTypeError("year must be between 1 and 9998")
    return year


def audit_lines(
    lines: Iterable[str],
    *,
    expected_year: int | None = None,
    scan_text: bool = False,
    max_distinct_hashes: int = DEFAULT_MAX_DISTINCT_HASHES,
) -> dict[str, object]:
    if expected_year is not None and not 1 <= expected_year <= 9998:
        raise AuditInputError("expected year must be between 1 and 9998")
    if max_distinct_hashes <= 0:
        raise AuditInputError("max_distinct_hashes must be positive")

    violations: collections.Counter[str] = collections.Counter()
    records = 0
    seen_keys: set[str] = set()
    combinations: set[tuple[int, int, int, int, str]] = set()
    valid_dates: set[str] = set()
    years: set[int] = set()
    hours: collections.Counter[int] = collections.Counter()
    genders: collections.Counter[str] = collections.Counter()
    main_stars: collections.Counter[str] = collections.Counter()
    topic_presence: collections.Counter[str] = collections.Counter()

    topic_chars: collections.Counter[str] = collections.Counter()
    topic_hashes = {topic: set() for topic in TOPICS}
    whole_content_hashes: set[bytes] = set()
    line_hashes: set[bytes] = set()
    paragraph_hashes: set[bytes] = set()
    total_nonempty_lines = 0
    total_paragraphs = 0
    rights_marker_records = 0
    rights_marker_topic_texts = 0
    quanshu_marker_topic_texts = 0

    def remember_digest(collection: set[bytes], digest: bytes) -> None:
        if digest in collection:
            return
        retained_hashes = (
            sum(len(values) for values in topic_hashes.values())
            + len(whole_content_hashes)
            + len(line_hashes)
            + len(paragraph_hashes)
        )
        if retained_hashes >= max_distinct_hashes:
            raise AuditInputError(f"distinct text hashes exceed {max_distinct_hashes}")
        collection.add(digest)

    for raw in lines:
        if not raw.strip():
            violations["blank_line"] += 1
            continue
        try:
            record = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
        except (ValueError, UnicodeDecodeError):
            violations["invalid_json"] += 1
            continue
        records += 1
        if not isinstance(record, dict):
            violations["non_object_record"] += 1
            continue
        if set(record) != EXPECTED_FIELDS:
            violations["schema_mismatch"] += 1

        year = record.get("y")
        month = record.get("m")
        day = record.get("d")
        hour = record.get("h")
        gender = record.get("g")
        if not all(isinstance(value, int) and not isinstance(value, bool) for value in (year, month, day, hour)):
            violations["invalid_numeric_field"] += 1
            continue
        assert isinstance(year, int) and isinstance(month, int) and isinstance(day, int) and isinstance(hour, int)
        if not isinstance(gender, str) or gender not in {"male", "female"}:
            violations["invalid_gender"] += 1
            continue
        if not 0 <= hour <= 11:
            violations["invalid_hour"] += 1
        try:
            date = dt.date(year, month, day)
        except (ValueError, OverflowError):
            violations["invalid_date"] += 1
            continue

        years.add(year)
        if expected_year is not None and year != expected_year:
            violations["unexpected_year"] += 1
        date_text = date.isoformat()
        valid_dates.add(date_text)
        hours[hour] += 1
        genders[gender] += 1
        combinations.add((year, month, day, hour, gender))

        key = record.get("k")
        expected_key = f"{date_text}-{hour}-{gender}"
        if not isinstance(key, str) or key != expected_key:
            violations["key_mismatch"] += 1
        elif key in seen_keys:
            violations["duplicate_key"] += 1
        else:
            seen_keys.add(key)

        main_star = record.get("ms")
        if main_star is None:
            main_stars["null"] += 1
        elif isinstance(main_star, str) and main_star in MAJOR_STARS:
            main_stars[main_star] += 1
        else:
            violations["invalid_main_star"] += 1
            main_stars["<invalid>"] += 1

        contents = record.get("c")
        lengths = record.get("t")
        if not isinstance(contents, dict) or not isinstance(lengths, dict):
            violations["invalid_topic_container"] += 1
            continue
        if set(contents) != set(TOPICS) or set(lengths) != set(TOPICS):
            violations["topic_shape_mismatch"] += 1

        record_has_rights_marker = False
        if scan_text:
            remember_digest(
                whole_content_hashes,
                text_digest(json.dumps(contents, ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
            )
        for topic in TOPICS:
            text = contents.get(topic)
            declared_length = lengths.get(topic)
            if not isinstance(text, str):
                violations["non_string_topic"] += 1
                continue
            if not isinstance(declared_length, int) or isinstance(declared_length, bool) or declared_length < 0:
                violations["invalid_topic_length"] += 1
            topic_presence[topic] += 1
            if not scan_text:
                continue
            topic_chars[topic] += len(text)
            remember_digest(topic_hashes[topic], text_digest(text))
            if declared_length != utf16_code_units(text):
                violations["length_mismatch"] += 1
            if any(marker in text for marker in RIGHTS_MARKERS):
                rights_marker_topic_texts += 1
                record_has_rights_marker = True
            if "《紫微斗数全书》" in text or "《全书》" in text:
                quanshu_marker_topic_texts += 1
            for raw_line in text.splitlines():
                normalized_line = " ".join(raw_line.split())
                if normalized_line:
                    total_nonempty_lines += 1
                    remember_digest(line_hashes, text_digest(normalized_line))
            for raw_paragraph in text.split("\n\n"):
                normalized_paragraph = " ".join(raw_paragraph.split())
                if normalized_paragraph:
                    total_paragraphs += 1
                    remember_digest(paragraph_hashes, text_digest(normalized_paragraph))
        if record_has_rights_marker:
            rights_marker_records += 1

    coverage: dict[str, object] = {}
    if expected_year is not None:
        expected_combinations = {
            (date.year, date.month, date.day, hour, gender)
            for offset in range(days_in_year(expected_year))
            for date in (dt.date(expected_year, 1, 1) + dt.timedelta(days=offset),)
            for hour in range(12)
            for gender in ("male", "female")
        }
        expected_records = len(expected_combinations)
        missing = len(expected_combinations - combinations)
        extra = len(combinations - expected_combinations)
        coverage = {
            "expected_year": expected_year,
            "expected_records": expected_records,
            "observed_combinations": len(combinations),
            "missing_combinations": missing,
            "extra_combinations": extra,
        }
        if records != expected_records:
            violations["record_count_mismatch"] += abs(records - expected_records)
        if missing:
            violations["coverage_missing"] += missing
        if extra:
            violations["coverage_extra"] += extra

    result: dict[str, object] = {
        "ok": not violations,
        "records": records,
        "unique_keys": len(seen_keys),
        "unique_dates": len(valid_dates),
        "date_min": min(valid_dates) if valid_dates else None,
        "date_max": max(valid_dates) if valid_dates else None,
        "years": sorted(years),
        "hours": dict(sorted(hours.items())),
        "genders": dict(sorted(genders.items())),
        "main_stars": dict(sorted(main_stars.items())),
        "topic_presence": dict(topic_presence),
        "coverage": coverage,
        "violations": dict(sorted(violations.items())),
    }
    if scan_text:
        topic_texts = sum(topic_presence.values())
        unique_topic_texts = sum(len(values) for values in topic_hashes.values())
        result["text_metrics"] = {
            "topic_texts": topic_texts,
            "topic_characters": dict(topic_chars),
            "distinct_topic_text_hashes": {topic: len(values) for topic, values in topic_hashes.items()},
            "distinct_topic_text_hash_ratio": unique_topic_texts / topic_texts if topic_texts else None,
            "distinct_whole_content_hashes": len(whole_content_hashes),
            "distinct_whole_content_hash_ratio": len(whole_content_hashes) / records if records else None,
            "nonempty_lines": total_nonempty_lines,
            "distinct_normalized_line_hashes": len(line_hashes),
            "distinct_normalized_line_hash_ratio": len(line_hashes) / total_nonempty_lines if total_nonempty_lines else None,
            "paragraphs": total_paragraphs,
            "distinct_normalized_paragraph_hashes": len(paragraph_hashes),
            "distinct_normalized_paragraph_hash_ratio": len(paragraph_hashes) / total_paragraphs if total_paragraphs else None,
            "records_with_rights_markers": rights_marker_records,
            "topic_texts_with_rights_markers": rights_marker_topic_texts,
            "topic_texts_with_quanshu_markers": quanshu_marker_topic_texts,
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", help="Annual .jsonl/.jsonl.zst file, or - for stdin")
    parser.add_argument("--expected-year", type=calendar_year, help="Require complete Gregorian coverage for this year")
    parser.add_argument("--expected-sha256", help="Verify the compressed or plain input file before parsing")
    parser.add_argument(
        "--scan-text",
        action="store_true",
        help="Compute aggregate duplication and rights-marker metrics without emitting text",
    )
    parser.add_argument(
        "--max-input-bytes",
        type=int,
        default=DEFAULT_MAX_INPUT_BYTES,
        help=f"Maximum compressed file size (default: {DEFAULT_MAX_INPUT_BYTES})",
    )
    parser.add_argument(
        "--max-output-bytes",
        type=int,
        default=DEFAULT_MAX_OUTPUT_BYTES,
        help=f"Maximum decompressed UTF-8 bytes (default: {DEFAULT_MAX_OUTPUT_BYTES})",
    )
    parser.add_argument(
        "--max-line-bytes",
        type=int,
        default=DEFAULT_MAX_LINE_BYTES,
        help=f"Maximum UTF-8 bytes per JSONL record (default: {DEFAULT_MAX_LINE_BYTES})",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=DEFAULT_MAX_LINES,
        help=f"Maximum input lines (default: {DEFAULT_MAX_LINES})",
    )
    parser.add_argument(
        "--max-distinct-hashes",
        type=int,
        default=DEFAULT_MAX_DISTINCT_HASHES,
        help=f"Maximum retained distinct text hashes (default: {DEFAULT_MAX_DISTINCT_HASHES})",
    )
    args = parser.parse_args()

    for option in ("max_input_bytes", "max_output_bytes", "max_line_bytes", "max_lines", "max_distinct_hashes"):
        if getattr(args, option) <= 0:
            parser.error(f"--{option.replace('_', '-')} must be positive")

    checksum: dict[str, object] | None = None
    if args.dataset == "-" and args.expected_sha256:
        parser.error("--expected-sha256 cannot be used with stdin")
    expected_sha256 = args.expected_sha256.lower() if args.expected_sha256 else None
    if expected_sha256 is not None and re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        parser.error("--expected-sha256 must be exactly 64 hexadecimal characters")

    try:
        with contextlib.ExitStack() as stack:
            parse_source: BinaryIO | None = None
            if args.dataset != "-":
                path = Path(args.dataset)
                if path.suffix == ".zst" and expected_sha256 is None:
                    parser.error(".zst inputs require --expected-sha256 from the pinned release manifest")
                open_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
                open_flags |= getattr(os, "O_NOFOLLOW", 0)
                descriptor = os.open(path, open_flags)
                source_stat = os.fstat(descriptor)
                if not stat.S_ISREG(source_stat.st_mode):
                    os.close(descriptor)
                    raise AuditInputError("file input must be a regular file")
                opened_source = stack.enter_context(os.fdopen(descriptor, "rb"))
                input_limit = args.max_input_bytes if path.suffix == ".zst" else args.max_output_bytes
                if source_stat.st_size > input_limit:
                    raise AuditInputError(f"input file exceeds {input_limit} bytes")

                input_snapshot = stack.enter_context(tempfile.TemporaryFile(mode="w+b"))
                actual = copy_and_sha256(opened_source, input_snapshot, max_bytes=input_limit)
                parse_source = input_snapshot
                if expected_sha256 is not None:
                    checksum_mismatch = actual.lower() != expected_sha256
                    checksum = {
                        "expected_sha256": expected_sha256,
                        "actual_sha256": actual,
                        "ok": not checksum_mismatch,
                    }
                    if checksum_mismatch:
                        print(
                            json.dumps(
                                {
                                    "ok": False,
                                    "checksum": checksum,
                                    "violations": {"checksum_mismatch": 1},
                                    "error": "checksum mismatch; input was not parsed",
                                },
                                ensure_ascii=False,
                                indent=2,
                                sort_keys=True,
                            )
                        )
                        return 1

            with open_dataset(args.dataset, parse_source) as lines:
                limited_lines = bounded_lines(
                    lines,
                    max_output_bytes=args.max_output_bytes,
                    max_line_bytes=args.max_line_bytes,
                    max_lines=args.max_lines,
                )
                result = audit_lines(
                    limited_lines,
                    expected_year=args.expected_year,
                    scan_text=args.scan_text,
                    max_distinct_hashes=args.max_distinct_hashes,
                )
    except (OSError, RuntimeError, UnicodeError, AuditInputError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False, indent=2))
        return 2

    if checksum is not None:
        result["checksum"] = checksum
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
