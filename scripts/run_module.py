#!/usr/bin/env python3
"""Run one calculator through the unified skill entry point."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "references" / "upstreams.json"


def source_path(source_id: str) -> Path:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for source in payload["sources"]:
        if source["id"] == source_id:
            path = ROOT / source["path"]
            if not path.exists():
                raise SystemExit(
                    f"Missing {source_id}. Run: python3 scripts/bootstrap_upstreams.py --install-deps"
                )
            return path
    raise SystemExit(f"Unknown source id: {source_id}")


def run_python(script: Path, arguments: list[str]) -> int:
    return subprocess.run([sys.executable, str(script), *arguments], check=False).returncode


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
        remainder = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
        script = source_path("bazi-skill") / "scripts" / "pai_pan.py"
        return run_python(script, remainder)

    if args.module == "qimen":
        script = source_path("numerologist-skills") / "qimen-dunjia" / "scripts" / "qimen_cli.py"
        return run_python(script, ["--input", args.input, "--output", args.output])

    if args.module == "ziwei":
        script = source_path("numerologist-skills") / "ziwei-doushu" / "scripts" / "ziwei_cli.py"
        return run_python(script, ["--input", args.input, "--output", args.output])

    skill_file = source_path("fengshui-skill") / "SKILL.md"
    print(skill_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
