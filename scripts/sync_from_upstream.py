#!/usr/bin/env python3
"""Show how to refresh this port from official Cursor pstack.

Does not copy files. Prints the pin, the recipe, or `git log` since the
recorded tree. Copy + adapt + verify stay operator-owned so Grok-only files
and Cursor-only packaging are not overwritten blindly.

    python3 scripts/sync_from_upstream.py --pin
    python3 scripts/sync_from_upstream.py --recipe
    python3 scripts/sync_from_upstream.py --log
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


def primary_checkout_root(root: Path) -> Path:
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return root
    common = Path(proc.stdout.strip())
    if not common.is_absolute():
        common = (root / common).resolve()
    else:
        common = common.resolve()
    if common.name == ".git":
        return common.parent
    return common


def remote_cache(root: Path | None = None) -> Path:
    base = root if root is not None else ROOT
    return primary_checkout_root(base) / ".worktrees" / "upstream-cursor-plugins"


def pin(upstream_file: Path | None = None) -> str:
    target = upstream_file if upstream_file is not None else UPSTREAM
    text = target.read_text(encoding="utf-8")
    m = PIN_RE.search(text)
    if not m:
        raise SystemExit("UPSTREAM missing `tree <40-hex>` line")
    return m.group(1)


def recipe(upstream_file: Path | None = None) -> str:
    sha = pin(upstream_file)
    return f"""Refresh from official Cursor pstack (pin {sha}).

1. python3 scripts/sync_from_upstream.py --pin
   python3 scripts/sync_from_upstream.py --log
2. Review applicable intent from .worktrees/upstream-cursor-plugins/pstack/
   (`skills/`, `agents/`, and selected docs). Overlay last classification with
   skills/swarm/scripts/partition.py seed --cache .worktrees/upstream-cursor-plugins
   --out /tmp/pstack-refresh/overlay.tsv. Classify unclassified fragments with
   partition.py partition --table /tmp/pstack-refresh/overlay.tsv. Coverage is
   name-status only. Run partition.py print --coverage --cache .worktrees/upstream-cursor-plugins --table /tmp/pstack-refresh/overlay.tsv.
   port is shared intent, not a write permit.
   Copy with skills/swarm/scripts/apply.py --cache .worktrees/upstream-cursor-plugins --table /tmp/pstack-refresh/overlay.tsv.
   After adapt, run partition.py apply-check --cache .worktrees/upstream-cursor-plugins --table /tmp/pstack-refresh/overlay.tsv.
   Canonical table is
   skills/swarm/references/classification.tsv. Pack interrogate reviewer prompts
   with skills/interrogate/scripts/pack.py.
   Applied canonical source is whatever the UPSTREAM tree line records, not
   the latest observed release. Review docs/research/upstream-pstack-0.15.36-audit-2026-10-31.md
   and CHANGELOG.md for candidate 0.15.36, the source manifest, and explicit GAPs.
   Do not blindly copy `statechart/` and its test corpus, `make-bot-ui/`,
   `.cursor-plugin/`, `assets/logo.png`, or the separate `advisor/` plugin.
   Upstream 0.15.36 removes its `scripts/orch/` runtime; inspect local callers
   and migrate behavior before considering any local deletion. Do not overwrite
   host-owned profiles, tool references, manifests, README files, tests, scripts,
   or six-host agent/role projections. Audit Codex-compatible `watch-pr/`,
   `check-plan.mjs`, and `worktree-audit.sh` rather than blind-copying.
   Reject unverified Cursor Task calls and inferred model-family substitutions.

3. python3 scripts/adapt_harness.py
4. Hand-map depth-1 spawn (`pstack:<role>`) and persist-then-wake overnight
   (`/loop` → scheduler_create). Do not leave Cursor Task, same-run /loop,
   ~/.cursor/rules/*.mdc, or control-cli as live Grok calls.
5. python3 .grok/skills/verify-pstack/scripts/verify.py run --root .
   That is leftover doctor then Full sweep drive then cleanup on one run-id.
   Leftover doctor runs scripts/verify_harness.py then grok plugin validate.
   Evidence survives. Full sweep walks leftover-scanner, upstream-pin,
   absorbed-intent, upstream-recipe, refresh-hygiene, and release-tag.
6. Run python3 scripts/verify_portable.py doctor --host all,
   python3 scripts/verify_portable.py check-evidence --host all,
   python3 scripts/verify_portable.py check-staleness, targeted pytest and
   independent negative-control/model checks on the exact candidate head.
   Record host gaps separately from source-only/offline PASS in CHANGELOG.md.
7. ONLY after #850's verification gate, promote UPSTREAM, the package upstream_pin,
   canonical inventory, host versions and generated projections together.
   Do not claim release or live parity for an untested host.
"""


def ensure_remote(root: Path | None = None) -> Path:
    cache = remote_cache(root)
    cache.parent.mkdir(parents=True, exist_ok=True)
    if (cache / ".git").is_dir() or (cache / "HEAD").is_file():
        subprocess.run(
            ["git", "-C", str(cache), "fetch", "--quiet", "origin", "main"],
            check=True,
        )
    else:
        subprocess.run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--sparse",
                "--quiet",
                CURSOR_PLUGINS,
                str(cache),
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(cache), "sparse-checkout", "set", "pstack"],
            check=True,
        )
    subprocess.run(
        ["git", "-C", str(cache), "merge", "--ff-only", "--quiet", "origin/main"],
        check=True,
    )
    return cache


def show_log(root: Path | None = None) -> int:
    sha = pin(root / "UPSTREAM" if root else None)
    repo = ensure_remote(root)
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--pin", action="store_true", help="print the UPSTREAM tree SHA")
    group.add_argument("--recipe", action="store_true", help="print the refresh steps")
    group.add_argument(
        "--log",
        action="store_true",
        help="git log origin/main -- pstack since the recorded tree",
    )
    args = parser.parse_args(argv)
    if args.pin:
        print(pin())
        return
    if args.log:
        raise SystemExit(show_log())
    sys.stdout.write(recipe())


if __name__ == "__main__":
    main()
