#!/usr/bin/env python3
"""Verify bundled files, pinned upstream checkouts, and Python dependencies."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "references" / "upstreams.json"


def git_head(path: Path) -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    for source in payload["sources"]:
        path = ROOT / source["path"]
        if source["distribution"] == "bundled":
            ok = (path / "SKILL.md").exists() and (path / "LICENSE").exists()
            actual = "bundled" if ok else "missing"
        else:
            actual = git_head(path)
            ok = actual == source["commit"]
        status = "OK" if ok else "FAIL"
        print(f"{status} {source['id']}: {actual}")
        if not ok:
            failures.append(source["id"])

    for module in ("lunar_python", "zoneinfo"):
        ok = importlib.util.find_spec(module) is not None
        print(f"{'OK' if ok else 'FAIL'} python module: {module}")
        if not ok:
            failures.append(module)

    if failures:
        print("Repair with: python3 scripts/bootstrap_upstreams.py --install-deps")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
