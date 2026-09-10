#!/usr/bin/env python3
"""Report leftover overlay caches and skills. Dry-run TSV; --apply deletes nested clones; --host-script prints cp.

    python3 refresh-hygiene.py --root /path/to/pstack
    python3 refresh-hygiene.py --root /path/to/pstack --apply
    python3 refresh-hygiene.py --root /path/to/pstack --host-script
    python3 refresh-hygiene.py --root /path/to/pstack --apply-skills
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shlex
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
KIND_LEFTOVER_WT = "leftover-worktree"
KIND_SKILL = "stale-skill"
KIND_ORDER = {
    KIND_NESTED: 0,
    KIND_SQUASH: 1,
    KIND_LEFTOVER_WT: 2,
    KIND_SKILL: 3,
}
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


@dataclass(frozen=True)
class SkillCopy:
    source: Path
    dest: Path


def overlay_cache(worktree: Path) -> Path:
    return worktree.joinpath(*CACHE_TAIL)


def is_overlay_cache_path(path: Path) -> bool:
    return path.parts[-2:] == CACHE_TAIL


def abs_unresolved(path: Path) -> Path:
    path = path.expanduser()
    if path.is_absolute():
        return path
    return Path.cwd() / path


def load_plan(root: Path, skills: Path) -> SkillCopy:
    source = abs_unresolved(root) / "skills" / "reflect" / "SKILL.md"
    dest = abs_unresolved(skills) / "reflect" / "SKILL.md"
    return SkillCopy(source, dest)


def host_copy_command(plan: SkillCopy) -> str:
    return shlex.join(["cp", "--", str(plan.source), str(plan.dest)])


def apply_skill_copy(plan: SkillCopy) -> Row:
    dest = plan.dest
    if dest.is_symlink() or has_symlink_parent(dest):
        return Row(KIND_SKILL, "eperm", dest, "EPERM")
    try:
        if not dest.is_file():
            return Row(KIND_SKILL, "not-stale", dest, "not-stale")
        text = dest.read_text(encoding="utf-8")
    except PermissionError:
        return Row(KIND_SKILL, "eperm", dest, "EPERM")
    if skill_shape(text) != "claude-shaped":
        return Row(KIND_SKILL, "not-stale", dest, "not-stale")
    try:
        shutil.copyfile(plan.source, dest)
    except PermissionError:
        return Row(KIND_SKILL, "eperm", dest, "EPERM")
    return Row(KIND_SKILL, "copied", dest, "ok")


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


def has_symlink_parent(path: Path) -> bool:
    return any(parent.is_symlink() for parent in path.parents)


def guarded_delete(path: Path, guard: Guard) -> None:
    if path.is_symlink() or has_symlink_parent(path):
        raise RuntimeError(f"refusing symlink: {path}")
    resolved = path.resolve()
    if resolved.is_symlink():
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
    skill = abs_unresolved(skills_root) / "reflect" / "SKILL.md"
    try:
        if not skill.is_file():
            return ()
        text = skill.read_text(encoding="utf-8")
    except PermissionError:
        return (Row(KIND_SKILL, "report", skill, "unread"),)
    if skill_shape(text) != "claude-shaped":
        return ()
    return (Row(KIND_SKILL, "report", skill, "claude-shaped"),)


def take_overlay(cand: Path, guard: Guard) -> Row:
    if cand.is_symlink() or has_symlink_parent(cand):
        return Row(KIND_NESTED, "keep", cand, "symlink")
    resolved = cand.resolve()
    if resolved == guard.primary_cache:
        return Row(KIND_NESTED, "keep", resolved, "primary overlay cache")
    if resolved in guard.worktrees:
        return Row(KIND_NESTED, "keep", resolved, "in git worktree list")
    if not is_overlay_cache_path(resolved):
        return Row(KIND_NESTED, "keep", resolved, "not an overlay cache path")
    return Row(KIND_NESTED, "would-delete", resolved, "nested overlay clone")


def apply_nested_deletes(rows: Sequence[Row], guard: Guard) -> tuple[Row, ...]:
    out: list[Row] = []
    for row in rows:
        if row.kind != KIND_NESTED or row.action != "would-delete":
            out.append(row)
            continue
        try:
            guarded_delete(row.path, guard)
        except (RuntimeError, OSError) as exc:
            out.append(Row(row.kind, "error", row.path, str(exc)))
            continue
        try:
            gone = not row.path.exists() and not row.path.is_symlink()
        except OSError:
            gone = False
        if gone:
            out.append(Row(row.kind, "deleted", row.path, row.note))
        else:
            out.append(Row(row.kind, "error", row.path, "still present"))
    return tuple(out)


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
        if not base or is_ancestor(git_root, wt.head, base):
            continue
        detail = squash_from_log(subject_of(git_root, wt.head), subjects)
        if detail:
            rows.append(Row(KIND_SQUASH, "report", wt.path, detail))
        else:
            rows.append(
                Row(
                    KIND_LEFTOVER_WT,
                    "report",
                    wt.path,
                    f"HEAD not ancestor of {base}",
                )
            )
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
        row = take_overlay(cand, guard)
        if row.path == guard.primary_cache:
            seen_primary = True
        rows.append(row)
    if not seen_primary and overlay_cache(primary).exists():
        rows.append(
            Row(KIND_NESTED, "keep", primary_cache, "primary overlay cache")
        )
    rows.extend(squash_rows(worktrees, primary))
    rows.extend(scan_skills(skills))
    planned = tuple(rows)
    if apply:
        return apply_nested_deletes(planned, guard)
    return planned


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
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="delete nested overlay caches; default is dry-run",
    )
    mode.add_argument(
        "--host-script",
        action="store_true",
        help="print cp -- git-tracked SKILL.md overlay SKILL.md; write nothing",
    )
    mode.add_argument(
        "--apply-skills",
        action="store_true",
        help="copy in-process; fail closed on EPERM without chmod",
    )
    args = parser.parse_args(None if argv is None else list(argv))
    if args.host_script:
        plan = load_plan(args.root, args.skills)
        if not plan.source.is_file():
            raise SystemExit(f"missing git-tracked skill: {plan.source}")
        sys.stdout.write(host_copy_command(plan) + "\n")
        return 0
    if args.apply_skills:
        plan = load_plan(args.root, args.skills)
        if not plan.source.is_file():
            raise SystemExit(f"missing git-tracked skill: {plan.source}")
        row = apply_skill_copy(plan)
        sys.stdout.write(format_rows((row,)))
        return 2 if row.action == "eperm" else 0
    rows = refresh(args.root, args.skills, apply=args.apply)
    sys.stdout.write(format_rows(rows))
    if args.apply and any(row.action == "error" for row in rows):
        return 2
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
