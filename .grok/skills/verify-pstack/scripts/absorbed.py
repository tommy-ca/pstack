#!/usr/bin/env python3
"""Fail when pstack commits follow the recorded pin, or absorbed lines are missing."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PIN_RE = re.compile(r"^tree ([0-9a-f]{40})$", re.M)

PRESENT = (
    ("docs/guide/07-overnight.md", "starts a round at the owner"),
    ("docs/guide/07-overnight.md", "scheduler_create"),
    ("docs/guide/07-overnight.md", "pstack:comment-sicko"),
    ("skills/show-me-your-work/scripts/log.sh", '[ ! -s "$logfile" ]'),
    ("skills/show-me-your-work/scripts/log.sh", '>> "$logfile"'),
    ("skills/poteto-mode/scripts/check-plan.mjs", "Ten lanes on `[^`<>]+`"),
    ("skills/poteto-mode/scripts/check-plan.mjs", "scheduler_create"),
    ("skills/poteto-mode/scripts/check-plan.mjs", "LANES.test"),
    (
        "skills/principle-outcome-oriented-execution/SKILL.md",
        "Require full static and runtime verification",
    ),
    ("skills/poteto-mode/SKILL.md", "agent.spawn"),
    ("skills/poteto-mode/SKILL.md", "grok-tools.md"),
    ("skills/poteto-mode/references/grok-tools.md", "spawn_subagent"),
    ("skills/poteto-mode/references/grok-tools.md", "scheduler_create"),
    ("skills/poteto-mode/references/grok-tools.md", "gh pr"),
    ("plugin.json", "grokbuild"),
)

ABSENT = (
    ("skills/interrogate/references/reviewer-prompt.md", "Only include nits if they"),
    (
        "skills/principle-outcome-oriented-execution/SKILL.md",
        "Always run final verification before declaring done",
    ),
    ("plugin.json", '"version": "0.15.5"'),
)


def read_pin(root: Path) -> str | None:
    path = root / "UPSTREAM"
    if not path.is_file():
        return None
    match = PIN_RE.search(path.read_text(encoding="utf-8"))
    if match is None:
        return None
    return match.group(1)


def commit_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def commits_after_pin(cache: Path, pin: str) -> tuple[list[str], str | None]:
    if not cache.is_dir():
        return [], f"cache missing: {cache}"
    proc = subprocess.run(
        ["git", "-C", str(cache), "log", "--oneline", f"{pin}..HEAD", "--", "pstack"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip() or f"exit {proc.returncode}"
        return [], f"git log failed: {detail}"
    return commit_lines(proc.stdout), None


def line_errors(root: Path) -> list[str]:
    errors: list[str] = []
    seen: dict[Path, str] = {}
    for rel, _needle in (*PRESENT, *ABSENT):
        path = root / rel
        if path in seen:
            continue
        if not path.is_file():
            seen[path] = ""
            errors.append(f"missing {rel}")
            continue
        seen[path] = path.read_text(encoding="utf-8")
    for rel, needle in PRESENT:
        path = root / rel
        if path in seen and needle not in seen[path]:
            errors.append(f"missing {rel}: {needle}")
    for rel, needle in ABSENT:
        path = root / rel
        if path in seen and needle in seen[path]:
            errors.append(f"forbidden {rel}: {needle}")
    return errors


def check(root: Path, commits: list[str], commit_error: str | None) -> list[str]:
    errors: list[str] = []
    if read_pin(root) is None:
        errors.append("UPSTREAM has no tree line")
    if commit_error is not None:
        errors.append(commit_error)
    if commits:
        errors.append("pstack commits after pin")
        errors.extend(commits)
    errors.extend(line_errors(root))
    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check",))
    parser.add_argument("--root", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--commits-file", type=Path)
    group.add_argument("--cache", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"root missing: {root}")
        return 1
    pin = read_pin(root)
    if args.commits_file is not None:
        if not args.commits_file.is_file():
            print(f"commits file missing: {args.commits_file}")
            return 1
        commits = commit_lines(args.commits_file.read_text(encoding="utf-8"))
        commit_error = None
    else:
        if pin is None:
            commits = []
            commit_error = None
        else:
            commits, commit_error = commits_after_pin(args.cache, pin)
    errors = check(root, commits, commit_error)
    if errors:
        print("\n".join(errors))
        return 1
    print("PASS absorbed-intent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
