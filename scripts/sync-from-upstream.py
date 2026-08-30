#!/usr/bin/env python3
"""Show how to refresh this port from official Cursor pstack.

Does not copy files. Prints the pin, the recipe, or `git log` since the
recorded tree. Copy + adapt + verify stay operator-owned so grok-only
files (HARNESS.md, plugin.json, README) are not overwritten blindly.

    python3 scripts/sync-from-upstream.py --pin
    python3 scripts/sync-from-upstream.py --recipe
    python3 scripts/sync-from-upstream.py --log
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "UPSTREAM"
CURSOR_PLUGINS = "https://github.com/cursor/plugins.git"
PIN_RE = re.compile(r"^tree ([0-9a-f]{40})$", re.M)
REMOTE_CACHE = ROOT / ".worktrees" / "upstream-cursor-plugins"


def pin() -> str:
    text = UPSTREAM.read_text(encoding="utf-8")
    m = PIN_RE.search(text)
    if not m:
        raise SystemExit("UPSTREAM missing `tree <40-hex>` line")
    return m.group(1)


def recipe() -> str:
    sha = pin()
    return f"""Refresh from official Cursor pstack (pin {sha}).

1. python3 scripts/sync-from-upstream.py --log
2. Copy intent from that tree's pstack/ into this repo (`skills/`, `agents/`). Skip make-bot-ui. Do not overwrite HARNESS.md, plugin.json, README.md, README.zh-CN.md, tests/, or scripts/.
3. python3 scripts/adapt-harness.py
4. Hand-map depth-1 spawn (`pstack:<role>`) and persist-then-wake overnight (`/loop` → scheduler_create). Do not leave Cursor Task, same-run /loop, ~/.cursor/rules/*.mdc, or control-cli as live Grok calls.
5. python3 scripts/verify-harness.py && python3 tests/test_verify_harness.py
6. Update the `tree` line in UPSTREAM to the new pstack/ commit.
"""


def ensure_remote() -> Path:
    REMOTE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if (REMOTE_CACHE / ".git").is_dir() or (REMOTE_CACHE / "HEAD").is_file():
        subprocess.run(
            ["git", "-C", str(REMOTE_CACHE), "fetch", "--quiet", "origin", "main"],
            check=True,
        )
        return REMOTE_CACHE
    subprocess.run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--sparse",
            "--quiet",
            CURSOR_PLUGINS,
            str(REMOTE_CACHE),
        ],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(REMOTE_CACHE), "sparse-checkout", "set", "pstack"],
        check=True,
    )
    return REMOTE_CACHE


def show_log() -> int:
    sha = pin()
    repo = ensure_remote()
    tip = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--short", "origin/main"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    log = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "log",
            "--oneline",
            f"{sha}..origin/main",
            "--",
            "pstack",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if log.returncode != 0:
        sys.stderr.write(log.stderr)
        return log.returncode
    lines = [ln for ln in log.stdout.splitlines() if ln.strip()]
    print(f"pin {sha}")
    print(f"tip origin/main {tip}")
    print(f"pstack commits after pin: {len(lines)}")
    if not lines:
        print("up to date (no pstack commits after pin).")
        return 0
    print(log.stdout, end="" if log.stdout.endswith("\n") else "\n")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pin", action="store_true", help="print the UPSTREAM tree SHA")
    group.add_argument("--recipe", action="store_true", help="print the refresh steps")
    group.add_argument(
        "--log",
        action="store_true",
        help="git log origin/main -- pstack since the recorded tree",
    )
    args = parser.parse_args()
    if args.pin:
        print(pin())
        return
    if args.log:
        raise SystemExit(show_log())
    sys.stdout.write(recipe())


if __name__ == "__main__":
    main()
