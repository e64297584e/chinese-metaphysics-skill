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
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    if not (target / ".git").exists():
        run(["git", "clone", "--no-checkout", repository, str(target)])
    else:
        remote = output(["git", "remote", "get-url", "origin"], cwd=target)
        if remote.rstrip("/") != repository.rstrip("/"):
            raise RuntimeError(f"unexpected origin for {target}: {remote}")

    run(["git", "fetch", "--depth", "1", "origin", commit], cwd=target)
    run(["git", "checkout", "--detach", commit], cwd=target)
    verify_commit(target, commit)
    return target


def install_requirements(source: dict[str, object], target: Path) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-deps", action="store_true", help="Install pinned modules' Python requirements")
    parser.add_argument("--offline", action="store_true", help="Verify existing checkouts without network access")
    args = parser.parse_args()

    for source in load_sources():
        target = fetch_source(source, offline=args.offline)
        if args.install_deps and source.get("requirements"):
            install_requirements(source, target)
        print(f"OK {source['id']} {source['commit']} -> {target.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
