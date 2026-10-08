"""Behavioral tests proving loss-aware worktree audit and safe drop (#203)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_SCRIPT = ROOT / "skills" / "poteto-mode" / "scripts" / "worktree-audit.sh"
DROP_SCRIPT = ROOT / "skills" / "poteto-mode" / "scripts" / "worktree-drop.sh"


def _run_cmd(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def _init_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_cmd(["git", "init", "-b", "main"], cwd=repo)
    _run_cmd(["git", "config", "user.name", "Test User"], cwd=repo)
    _run_cmd(["git", "config", "user.email", "test@example.com"], cwd=repo)

    (repo / "README.md").write_text("# Repo\n", encoding="utf-8")
    _run_cmd(["git", "add", "README.md"], cwd=repo)
    _run_cmd(["git", "commit", "-m", "initial commit"], cwd=repo)

    wt = tmp_path / "wt-branch"
    _run_cmd(["git", "worktree", "add", "-b", "feature", str(wt)], cwd=repo)
    return repo, wt


def test_worktree_audit_classifies_untracked_files_as_hold_untracked(tmp_path: Path) -> None:
    repo, wt = _init_repo(tmp_path)
    (wt / "untracked.txt").write_text("precious untracked data\n", encoding="utf-8")

    proc = _run_cmd([str(AUDIT_SCRIPT), str(repo)])
    assert proc.returncode == 0, proc.stderr
    lines = [ln for ln in proc.stdout.splitlines() if str(wt) in ln]
    assert len(lines) == 1, proc.stdout
    row = lines[0].split("\t")
    bucket = row[7]
    dirty = row[3]
    assert "scratch:1" in dirty
    assert bucket == "hold-untracked"
    assert bucket != "safe"


def test_worktree_audit_classifies_tracked_wip_as_hold_wip(tmp_path: Path) -> None:
    repo, wt = _init_repo(tmp_path)
    (wt / "README.md").write_text("# Modified\n", encoding="utf-8")

    proc = _run_cmd([str(AUDIT_SCRIPT), str(repo)])
    assert proc.returncode == 0, proc.stderr
    lines = [ln for ln in proc.stdout.splitlines() if str(wt) in ln]
    assert len(lines) == 1
    row = lines[0].split("\t")
    bucket = row[7]
    dirty = row[3]
    assert "wip:1" in dirty
    assert bucket == "hold-wip"
    assert bucket != "safe"


def test_worktree_audit_classifies_unpushed_branch_as_hold_unpushed(tmp_path: Path) -> None:
    repo, wt = _init_repo(tmp_path)
    # Commit to feature branch without remote
    (wt / "committed.txt").write_text("committed\n", encoding="utf-8")
    _run_cmd(["git", "add", "committed.txt"], cwd=wt)
    _run_cmd(["git", "commit", "-m", "feature work"], cwd=wt)

    proc = _run_cmd([str(AUDIT_SCRIPT), str(repo)])
    assert proc.returncode == 0, proc.stderr
    lines = [ln for ln in proc.stdout.splitlines() if str(wt) in ln]
    assert len(lines) == 1
    row = lines[0].split("\t")
    remote = row[4]
    bucket = row[7]
    assert remote == "no-remote"
    assert bucket == "hold-unpushed"
    assert bucket != "safe"


def test_worktree_drop_refuses_force_and_preserves_uncommitted_state(tmp_path: Path) -> None:
    repo, wt = _init_repo(tmp_path)
    (wt / "uncommitted.txt").write_text("important scratch\n", encoding="utf-8")

    proc = _run_cmd(
        [
            str(DROP_SCRIPT),
            "--repo", str(repo),
            "--apply",
            "--expect-registered", "1",
            "--expect-leftover", "0",
            "--path", str(wt),
        ],
        cwd=repo,
    )
    # Normal git worktree remove refuses because of untracked files
    assert proc.returncode != 0
    # The worktree and its untracked file must survive intact
    assert wt.is_dir()
    assert (wt / "uncommitted.txt").is_file()
    assert (wt / "uncommitted.txt").read_text(encoding="utf-8") == "important scratch\n"
