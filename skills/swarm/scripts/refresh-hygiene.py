#!/usr/bin/env python3
"""Report pstack overlay-refresh leftovers. Delete nested overlay caches only.

Default is dry-run. Prints TSV and exits 2 when a nested-cache would-delete
row remains. --apply removes nested clones at
<worktree>/.worktrees/upstream-cursor-plugins after Guard. It never removes
the primary cache or a path listed by git worktree list. Squash worktrees
and Claude-shaped ~/.grok/skills/reflect are report rows.

    python3 refresh-hygiene.py --root /path/to/pstack
    python3 refresh-hygiene.py --root /path/to/pstack --apply
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

PARTITION_SCRIPT = Path(__file__).resolve().with_name("partition.py")
CACHE_TAIL = (".worktrees", "upstream-cursor-plugins")
CLAUDE_MARKERS = (
    "~/.claude/projects",
    "plugin-dev:skill-development",
    'subagent_type: "general-purpose"',
)
KIND_NESTED = "nested-cache"
KIND_SQUASH = "squash-worktree"
KIND_SKILL = "stale-skill"
KIND_ORDER = {KIND_NESTED: 0, KIND_SQUASH: 1, KIND_SKILL: 2}
PR_SUBJECT_RE = re.compile(r"\(#(\d+)\)\s*$")


def _load_partition():
    spec = importlib.util.spec_from_file_location("swarm_partition", PARTITION_SCRIPT)
    if spec is None or spec.loader is None:
        raise SystemExit(f"missing partition.py: {PARTITION_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P = _load_partition()


@dataclass(frozen=True)
class Row:
    kind: str
    action: str
    path: Path
    note: str


@dataclass(frozen=True)
class Guard:
    primary_cache: Path
    worktrees: frozenset[Path]


@dataclass(frozen=True)
class Worktree:
    path: Path
    head: str
    note: str


def overlay_cache(worktree: Path) -> Path:
    return worktree.joinpath(*CACHE_TAIL)


def is_overlay_cache_path(path: Path) -> bool:
    return path.parts[-2:] == CACHE_TAIL


def git_run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def parse_worktrees(text: str) -> tuple[Worktree, ...]:
    records: list[Worktree] = []
    fields: dict[str, str | bool] = {}

    def flush() -> None:
        raw = fields.get("path")
        if not isinstance(raw, str) or not raw:
            fields.clear()
            return
        head = fields.get("head")
        records.append(
            Worktree(
                Path(raw).resolve(),
                head if isinstance(head, str) else "",
                _worktree_note(fields),
            )
        )
        fields.clear()

    for line in text.splitlines():
        if line == "":
            flush()
            continue
        if line.startswith("worktree "):
            fields["path"] = line[len("worktree ") :]
        elif line.startswith("HEAD "):
            fields["head"] = line[len("HEAD ") :]
        elif line.startswith("branch "):
            fields["branch"] = line[len("branch ") :]
        elif line == "detached":
            fields["detached"] = True
        elif line.startswith("prunable"):
            fields["prunable"] = True
    flush()
    return tuple(records)


def _worktree_note(fields: dict[str, str | bool]) -> str:
    if fields.get("prunable"):
        return "prunable"
    if fields.get("detached"):
        return "detached"
    branch = fields.get("branch")
    if isinstance(branch, str) and branch:
        prefix = "refs/heads/"
        if branch.startswith(prefix):
            branch = branch[len(prefix) :]
        return f"branch={branch}"
    return "ok"


def list_worktrees(root: Path) -> tuple[Worktree, ...]:
    proc = git_run(root, "worktree", "list", "--porcelain")
    if proc.returncode != 0:
        err = proc.stderr.strip() or f"git worktree list failed in {root}"
        raise SystemExit(err)
    return parse_worktrees(proc.stdout)


def rmtree_git_clone(path: Path) -> None:
    def onexc(func: object, p: str, exc: BaseException) -> None:
        if isinstance(exc, FileNotFoundError):
            return
        os.chmod(p, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        if not callable(func):
            raise exc
        func(p)

    try:
        shutil.rmtree(path, onexc=onexc)
    except FileNotFoundError:
        return


def guarded_delete(path: Path, guard: Guard) -> None:
    resolved = path.resolve()
    if path.is_symlink() or resolved.is_symlink():
        raise RuntimeError(f"refusing symlink: {path}")
    if resolved == guard.primary_cache:
        raise RuntimeError(f"refusing primary cache: {resolved}")
    if resolved in guard.worktrees:
        raise RuntimeError(f"refusing git worktree: {resolved}")
    if not is_overlay_cache_path(resolved):
        raise RuntimeError(f"refusing non-cache path: {resolved}")
    rmtree_git_clone(resolved)


def skill_shape(text: str) -> str:
    if any(marker in text for marker in CLAUDE_MARKERS):
        return "claude-shaped"
    return "ok"


def scan_skills(skills_root: Path) -> tuple[Row, ...]:
    skill = skills_root.expanduser() / "reflect" / "SKILL.md"
    if not skill.is_absolute():
        skill = skill.resolve()
    try:
        if not skill.is_file():
            return ()
        text = skill.read_text(encoding="utf-8")
    except PermissionError:
        return ()
    if skill_shape(text) != "claude-shaped":
        return ()
    return (Row(KIND_SKILL, "report", skill, "claude-shaped"),)


def take_overlay(cand: Path, guard: Guard, *, apply: bool) -> Row:
    resolved = cand.resolve()
    if resolved == guard.primary_cache:
        return Row(KIND_NESTED, "keep", resolved, "primary overlay cache")
    if resolved in guard.worktrees:
        return Row(KIND_NESTED, "keep", resolved, "in git worktree list")
    if cand.is_symlink():
        return Row(KIND_NESTED, "keep", resolved, "symlink")
    if not is_overlay_cache_path(resolved):
        return Row(KIND_NESTED, "keep", resolved, "not an overlay cache path")
    if apply:
        guarded_delete(cand, guard)
        return Row(KIND_NESTED, "deleted", resolved, "nested overlay clone")
    return Row(KIND_NESTED, "would-delete", resolved, "nested overlay clone")


def load_base_ref(root: Path) -> str:
    for ref in ("origin/main", "main"):
        proc = git_run(root, "rev-parse", "--verify", "--quiet", ref)
        if proc.returncode == 0:
            return ref
    return ""


def is_ancestor(root: Path, sha: str, base: str) -> bool:
    if not base or not sha:
        return False
    proc = git_run(root, "merge-base", "--is-ancestor", sha, base)
    return proc.returncode == 0


def subject_of(root: Path, sha: str) -> str:
    proc = git_run(root, "log", "-1", "--format=%s", sha)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def load_subjects(root: Path, base: str) -> tuple[str, ...]:
    if not base:
        return ()
    proc = git_run(root, "log", "--format=%s", base)
    if proc.returncode != 0:
        return ()
    return tuple(line for line in proc.stdout.splitlines() if line)


def squash_from_log(head_subject: str, main_subjects: Sequence[str]) -> str:
    if not head_subject:
        return ""
    for subj in main_subjects:
        match = PR_SUBJECT_RE.search(subj)
        if not match:
            continue
        numbered = f"{head_subject} (#{match.group(1)})"
        if subj == numbered or subj == head_subject:
            return f"#{match.group(1)} MERGED; HEAD not on main"
    return ""


def squash_rows(worktrees: Sequence[Worktree], git_root: Path) -> tuple[Row, ...]:
    base = load_base_ref(git_root)
    subjects = load_subjects(git_root, base)
    git_key = git_root.resolve()
    rows: list[Row] = []
    for index, wt in enumerate(worktrees):
        if index == 0 or not wt.head:
            continue
        try:
            if wt.path.resolve() == git_key:
                continue
        except OSError:
            pass
        if is_ancestor(git_root, wt.head, base):
            continue
        detail = squash_from_log(subject_of(git_root, wt.head), subjects)
        if detail:
            rows.append(Row(KIND_SQUASH, "report", wt.path, detail))
    return tuple(rows)


def format_rows(rows: Sequence[Row]) -> str:
    lines = ["kind\taction\tpath\tnote"]
    ordered = sorted(
        rows, key=lambda row: (KIND_ORDER.get(row.kind, 9), str(row.path))
    )
    for row in ordered:
        lines.append(f"{row.kind}\t{row.action}\t{row.path}\t{row.note}")
    return "\n".join(lines) + "\n"


def refresh(root: Path, skills: Path, *, apply: bool) -> tuple[Row, ...]:
    root = root.expanduser().resolve()
    primary = P.primary_checkout_root(root)
    worktrees = list_worktrees(primary)
    primary_cache = overlay_cache(primary).resolve()
    guard = Guard(
        primary_cache,
        frozenset(wt.path.resolve() for wt in worktrees),
    )
    rows: list[Row] = []
    seen_primary = False
    for wt in worktrees:
        cand = overlay_cache(wt.path)
        try:
            visible = cand.exists() or cand.is_symlink()
        except PermissionError:
            rows.append(Row(KIND_NESTED, "keep", cand, "unreadable"))
            continue
        if not visible:
            continue
        row = take_overlay(cand, guard, apply=apply)
        if row.path == guard.primary_cache:
            seen_primary = True
        rows.append(row)
    if not seen_primary and overlay_cache(primary).exists():
        rows.append(
            Row(KIND_NESTED, "keep", primary_cache, "primary overlay cache")
        )
    rows.extend(squash_rows(worktrees, primary))
    rows.extend(scan_skills(skills))
    return tuple(rows)


def nested_would_delete(rows: Sequence[Row]) -> bool:
    return any(
        row.kind == KIND_NESTED and row.action == "would-delete" for row in rows
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument(
        "--skills",
        type=Path,
        default=Path.home() / ".grok" / "skills",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="delete nested overlay caches; default is dry-run",
    )
    args = parser.parse_args(None if argv is None else list(argv))
    rows = refresh(args.root, args.skills, apply=args.apply)
    sys.stdout.write(format_rows(rows))
    if not args.apply and nested_would_delete(rows):
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            sys.stderr.write(exc.code + "\n")
            raise SystemExit(2) from None
        raise
