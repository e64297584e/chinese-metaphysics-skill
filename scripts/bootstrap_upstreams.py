#!/usr/bin/env python3
"""Fetch pinned, non-vendored upstream skills for local runtime use."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "references" / "upstreams.json"
ROOT_REQUIREMENTS = ROOT / "requirements.txt"


def run(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def output(command: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True).strip()


def load_sources() -> list[dict[str, object]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return list(payload["sources"])


def verify_commit(target: Path, commit: str) -> None:
    actual = output(["git", "rev-parse", "HEAD"], cwd=target)
    if actual != commit:
        raise RuntimeError(f"commit verification failed for {target}: {actual} != {commit}")


def verify_clean(target: Path) -> None:
    status = output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=target)
    if status:
        raise RuntimeError(f"pinned checkout has local changes: {target}")


def fetch_source(source: dict[str, object], *, offline: bool) -> Path:
    target = ROOT / str(source["path"])
    commit = str(source["commit"])
    repository = str(source["repository"])

    if source["distribution"] == "bundled":
        if not target.exists():
            raise RuntimeError(f"bundled source is missing: {target}")
        return target

    if offline:
        if not (target / ".git").exists():
            raise RuntimeError(f"runtime source is not installed: {source['id']}")
        verify_commit(target, commit)
        verify_clean(target)
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    if not (target / ".git").exists():
        run(["git", "clone", "--no-checkout", repository, str(target)])
    else:
        remote = output(["git", "remote", "get-url", "origin"], cwd=target)
        if remote.rstrip("/") != repository.rstrip("/"):
            raise RuntimeError(f"unexpected origin for {target}: {remote}")
        verify_clean(target)

    run(["git", "fetch", "--depth", "1", "origin", commit], cwd=target)
    run(["git", "checkout", "--detach", commit], cwd=target)
    verify_commit(target, commit)
    verify_clean(target)
    return target


def install_dependencies(source: dict[str, object], target: Path) -> None:
    seen: set[str] = set()
    for relative in source.get("requirements", []):
        requirements = target / str(relative)
        if not requirements.exists():
            raise RuntimeError(f"requirements file is missing: {requirements}")
        key = requirements.read_text(encoding="utf-8")
        if key in seen:
            continue
        seen.add(key)
        run([sys.executable, "-m", "pip", "install", "-r", str(requirements)])

    installer = source.get("install")
    if installer is None:
        return
    if installer == "npm-ci-ignore-scripts":
        if not (target / "package-lock.json").exists():
            raise RuntimeError(f"package-lock.json is missing: {target}")
        run(["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=target)
        return
    raise RuntimeError(f"unsupported dependency installer for {source['id']}: {installer}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies for selected pinned sources")
    parser.add_argument("--offline", action="store_true", help="Verify existing checkouts without network access")
    parser.add_argument(
        "--include-audit",
        action="store_true",
        help="Fetch optional external audit sources; they are never used as primary calculators",
    )
    args = parser.parse_args()

    if args.offline and args.install_deps:
        parser.error("--offline cannot be combined with --install-deps because installers may access package indexes")

    if args.install_deps:
        run([sys.executable, "-m", "pip", "install", "-r", str(ROOT_REQUIREMENTS)])

    for source in load_sources():
        if source.get("optional") and not args.include_audit:
            print(f"SKIP optional {source['id']} (use --include-audit)")
            continue
        target = fetch_source(source, offline=args.offline)
        if args.install_deps and (source.get("requirements") or source.get("install")):
            install_dependencies(source, target)
        print(f"OK {source['id']} {source['commit']} -> {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
