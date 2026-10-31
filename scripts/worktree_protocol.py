#!/usr/bin/env python3
"""PStack Worktree Confinement and Consistency Protocol.

Adheres strictly to SOLID, KISS, DRY, and YAGNI:
- Pure Python 3.10+ standard library (zero external dependencies).
- Single responsibility: enforce worktree confinement within <repo_root>/.worktrees/<slug>.
- Never allow arbitrary worktree or workspace paths (e.g., /tmp, home dir, external paths).
- Deterministic, headless verification for CI, scripts, and agent workflows.

Usage:
    python3 scripts/worktree_protocol.py check [--repo <dir>]
    python3 scripts/worktree_protocol.py get-path <branch> [--repo <dir>]
    python3 scripts/worktree_protocol.py add <branch> [--repo <dir>] [--base <base>]
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


def find_repo_root(start_dir: Path | None = None) -> Path:
    """Find the root of the git repository."""
    current = (start_dir or Path.cwd()).resolve()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=current,
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(res.stdout.strip()).resolve()
    except subprocess.CalledProcessError:
        raise ValueError(f"Not inside a git repository: {current}")


def slugify_branch_name(branch: str) -> str:
    """Convert a git branch name into a safe directory slug.
    
    Replaces slashes, colons, spaces, and unsafe chars with hyphens.
    Strips leading/trailing hyphens and collapses consecutive hyphens.
    """
    clean = re.sub(r"[^a-zA-Z0-9._-]+", "-", branch.strip())
    clean = re.sub(r"-+", "-", clean).strip("-")
    if not clean or clean in (".", ".."):
        raise ValueError(f"Invalid branch name for worktree: {branch!r}")
    return clean


def get_allowed_worktree_root(repo_root: Path) -> Path:
    """Return the designated .worktrees directory in the repo."""
    return (repo_root / ".worktrees").resolve()


def validate_worktree_path(repo_root: Path, target_path: Path) -> tuple[bool, str]:
    """Validate that target_path is strictly confined within <repo_root>/.worktrees/.
    
    Returns (is_valid, reason).
    """
    allowed_root = get_allowed_worktree_root(repo_root)
    resolved_target = target_path.resolve()
    
    # Must be under allowed_root
    try:
        rel = resolved_target.relative_to(allowed_root)
    except ValueError:
        return False, (
            f"Worktree path '{resolved_target}' is outside designated worktree root "
            f"'{allowed_root}'. Arbitrary worktree locations are strictly prohibited."
        )
    
    # Cannot be allowed_root itself (must be inside a dedicated subdirectory)
    if rel == Path("."):
        return False, f"Worktree cannot be the root .worktrees directory itself."
    
    # Check for escaping patterns in relative path parts
    if ".." in rel.parts:
        return False, f"Worktree path '{resolved_target}' contains directory traversal elements."
    
    return True, "Valid worktree path"


def get_canonical_worktree_path(repo_root: Path, branch: str) -> Path:
    """Return the canonical path for a branch worktree."""
    slug = slugify_branch_name(branch)
    allowed_root = get_allowed_worktree_root(repo_root)
    return allowed_root / slug


def list_registered_worktrees(repo_root: Path) -> list[tuple[Path, str, str]]:
    """Query git for registered worktrees via porcelain format.
    
    Returns list of (worktree_path, head_sha, branch_or_detached).
    """
    res = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    worktrees: list[tuple[Path, str, str]] = []
    current_path: Path | None = None
    current_head: str = ""
    current_branch: str = ""

    for line in res.stdout.splitlines():
        line = line.strip()
        if not line:
            if current_path:
                worktrees.append((current_path, current_head, current_branch or "detached"))
                current_path = None
                current_head = ""
                current_branch = ""
            continue
        if line.startswith("worktree "):
            current_path = Path(line[len("worktree "):].strip()).resolve()
        elif line.startswith("HEAD "):
            current_head = line[len("HEAD "):].strip()
        elif line.startswith("branch "):
            current_branch = line[len("branch "):].strip()

    if current_path:
        worktrees.append((current_path, current_head, current_branch or "detached"))

    return worktrees


def check_worktrees(repo_root: Path) -> list[str]:
    """Audit all registered worktrees for protocol conformance.
    
    Returns list of error messages (empty on pass).
    """
    errors: list[str] = []
    registered = list_registered_worktrees(repo_root)
    if not registered:
        return ["No worktrees reported by git."]

    # First entry is always the main worktree (must match repo_root)
    main_wt, _, _ = registered[0]
    if main_wt != repo_root:
        errors.append(
            f"Main worktree mismatch: expected '{repo_root}', got '{main_wt}'."
        )

    # All subsequent worktrees must be confined within .worktrees/
    for wt_path, head_sha, branch in registered[1:]:
        valid, reason = validate_worktree_path(repo_root, wt_path)
        if not valid:
            errors.append(f"VIOLATION in worktree [{branch} at {wt_path}]: {reason}")

    return errors


def add_worktree(repo_root: Path, branch: str, base_ref: str | None = None) -> Path:
    """Create a new worktree strictly following the confinement protocol."""
    target_path = get_canonical_worktree_path(repo_root, branch)
    valid, reason = validate_worktree_path(repo_root, target_path)
    if not valid:
        raise ValueError(reason)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "worktree", "add", "-b", branch, str(target_path)]
    if base_ref:
        cmd.append(base_ref)

    subprocess.run(cmd, cwd=repo_root, check=True)
    return target_path


def main() -> int:
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--repo", type=Path, default=None, help="Repository root directory")

    parser = argparse.ArgumentParser(
        description="PStack Worktree Confinement and Consistency Protocol validator.",
        parents=[parent_parser],
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: check
    subparsers.add_parser("check", parents=[parent_parser], help="Verify all registered worktrees adhere to confinement.")

    # Subcommand: get-path
    get_path_p = subparsers.add_parser("get-path", parents=[parent_parser], help="Get canonical worktree path for branch.")
    get_path_p.add_argument("branch", help="Branch name")

    # Subcommand: add
    add_p = subparsers.add_parser("add", parents=[parent_parser], help="Add a worktree strictly within .worktrees/.")
    add_p.add_argument("branch", help="Branch name to create and checkout")
    add_p.add_argument("--base", default=None, help="Base commit or branch to branch from")

    args = parser.parse_args()

    try:
        repo_root = find_repo_root(args.repo)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.subcommand == "check":
        violations = check_worktrees(repo_root)
        if violations:
            print(f"FAIL: {len(violations)} worktree protocol violation(s) found:", file=sys.stderr)
            for v in violations:
                print(f"  - {v}", file=sys.stderr)
            return 1
        print(f"PASS: All registered worktrees adhere to PStack worktree confinement protocol.")
        return 0

    elif args.subcommand == "get-path":
        try:
            path = get_canonical_worktree_path(repo_root, args.branch)
            print(str(path))
            return 0
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

    elif args.subcommand == "add":
        try:
            created = add_worktree(repo_root, args.branch, args.base)
            print(f"SUCCESS: Created confined worktree for '{args.branch}' at {created}")
            return 0
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
