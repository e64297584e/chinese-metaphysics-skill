#!/usr/bin/env python3
"""Verify bundled files, pinned upstream checkouts, and runtime dependencies."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "references" / "upstreams.json"


def git_state(path: Path) -> tuple[str | None, bool]:
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path, text=True).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=path, text=True
        ).strip()
        return head, not status
    except (OSError, subprocess.CalledProcessError):
        return None, False


def npm_dependencies_ok(path: Path) -> bool:
    if shutil.which("npm") is None or not (path / "node_modules").is_dir():
        return False
    try:
        lock = json.loads((path / "package-lock.json").read_text(encoding="utf-8"))
        for relative, metadata in lock.get("packages", {}).items():
            if not relative.startswith("node_modules/") or metadata.get("link"):
                continue
            package_json = path / relative / "package.json"
            if not package_json.exists():
                if metadata.get("optional"):
                    continue
                return False
            installed = json.loads(package_json.read_text(encoding="utf-8"))
            if installed.get("version") != metadata.get("version"):
                return False
        subprocess.run(
            ["npm", "ls", "--depth=0", "--ignore-scripts", "--json"],
            cwd=path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-audit",
        action="store_true",
        help="Require optional external audit sources to be installed at their pinned commits",
    )
    args = parser.parse_args()

    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    dirty_sources: list[str] = []
    manual_sources: list[str] = []
    bootstrap_repairable = False
    for source in payload["sources"]:
        if source.get("optional") and not args.include_audit:
            print(f"SKIP optional {source['id']}")
            continue
        path = ROOT / source["path"]
        if source["distribution"] == "bundled":
            ok = (path / "SKILL.md").exists() and (path / "LICENSE").exists()
            actual = "bundled" if ok else "missing"
            if not ok:
                manual_sources.append(source["id"])
        else:
            actual, clean = git_state(path)
            ok = actual == source["commit"] and clean
            if actual is not None and not clean:
                actual = f"{actual} (dirty)"
                dirty_sources.append(source["id"])
            elif not ok:
                bootstrap_repairable = True
        status = "OK" if ok else "FAIL"
        print(f"{status} {source['id']}: {actual}")
        if not ok:
            failures.append(source["id"])
        if source.get("install") == "npm-ci-ignore-scripts":
            deps_ok = npm_dependencies_ok(path)
            print(f"{'OK' if deps_ok else 'FAIL'} node dependencies: {source['id']}")
            if not deps_ok:
                failures.append(f"{source['id']}-node-dependencies")
                bootstrap_repairable = True

    if args.include_audit:
        zstd_ok = shutil.which("zstd") is not None
        print(f"{'OK' if zstd_ok else 'FAIL'} executable: zstd")
        if not zstd_ok:
            failures.append("zstd")

    for module in ("lunar_python", "zoneinfo"):
        ok = importlib.util.find_spec(module) is not None
        print(f"{'OK' if ok else 'FAIL'} python module: {module}")
        if not ok:
            failures.append(module)
            bootstrap_repairable = True

    if failures:
        if dirty_sources:
            print(f"Resolve local changes before bootstrap: {', '.join(dirty_sources)}")
        if manual_sources:
            print(f"Restore bundled sources from this repository: {', '.join(manual_sources)}")
        if "zstd" in failures:
            print("Install the zstd executable with the system package manager before auditing .zst files")
        if bootstrap_repairable:
            audit_flag = " --include-audit" if args.include_audit else ""
            print(f"Repair missing pins/dependencies with: python3 scripts/bootstrap_upstreams.py{audit_flag} --install-deps")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
