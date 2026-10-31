"""Tests for PStack Worktree Confinement and Consistency Protocol."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.worktree_protocol import (
    find_repo_root,
    slugify_branch_name,
    get_allowed_worktree_root,
    validate_worktree_path,
    get_canonical_worktree_path,
    check_worktrees,
    add_worktree,
    remove_worktree,
    list_confined_worktrees,
)


def _run_git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )


def test_slugify_branch_name() -> None:
    assert slugify_branch_name("feat/add-login") == "feat-add-login"
    assert slugify_branch_name("fix/issue-123_part2") == "fix-issue-123_part2"
    assert slugify_branch_name("chore/clean-up/v2.0") == "chore-clean-up-v2.0"
    assert slugify_branch_name("   feat/spaces   ") == "feat-spaces"
    assert slugify_branch_name("weird!@#$%^&*()name") == "weird-name"

    with pytest.raises(ValueError, match="Invalid branch name"):
        slugify_branch_name("")
    with pytest.raises(ValueError, match="Invalid branch name"):
        slugify_branch_name("---")
    with pytest.raises(ValueError, match="Invalid branch name"):
        slugify_branch_name("..")


def test_validate_worktree_path_accepts_confined_paths(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    allowed_root = repo / ".worktrees"
    allowed_root.mkdir()

    valid_wt = allowed_root / "feature-1"
    ok, reason = validate_worktree_path(repo, valid_wt)
    assert ok is True
    assert "Valid" in reason


def test_validate_worktree_path_rejects_arbitrary_locations(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".worktrees").mkdir()

    # Outside root: in /tmp or sibling directory
    arbitrary_external = tmp_path / "external-wt"
    ok, reason = validate_worktree_path(repo, arbitrary_external)
    assert ok is False
    assert "outside designated worktree root" in reason

    # Escape attempt via traversal
    traversal_wt = repo / ".worktrees" / ".." / "escaped-wt"
    ok, reason = validate_worktree_path(repo, traversal_wt)
    assert ok is False

    # Root .worktrees directory itself cannot be a worktree checkout
    ok, reason = validate_worktree_path(repo, repo / ".worktrees")
    assert ok is False
    assert "cannot be the root .worktrees directory itself" in reason


def test_check_worktrees_detects_arbitrary_unconfined_worktrees(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-b", "main"], cwd=repo)
    _run_git(["config", "user.name", "Tester"], cwd=repo)
    _run_git(["config", "user.email", "tester@example.com"], cwd=repo)

    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    _run_git(["add", "README.md"], cwd=repo)
    _run_git(["commit", "-m", "init"], cwd=repo)

    # 1. Clean repo with only main worktree
    violations = check_worktrees(repo)
    assert violations == []

    # 2. Add compliant worktree under .worktrees/
    compliant_wt = repo / ".worktrees" / "compliant-feat"
    _run_git(["worktree", "add", "-b", "compliant", str(compliant_wt)], cwd=repo)
    violations = check_worktrees(repo)
    assert violations == []

    # 3. Add unconfined arbitrary worktree outside .worktrees/
    arbitrary_wt = tmp_path / "arbitrary-wt"
    _run_git(["worktree", "add", "-b", "arbitrary", str(arbitrary_wt)], cwd=repo)
    violations = check_worktrees(repo)
    assert len(violations) == 1
    assert "VIOLATION in worktree" in violations[0]
    assert "arbitrary-wt" in violations[0]
    assert "outside designated worktree root" in violations[0]


def test_add_worktree_enforces_canonical_confinement(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-b", "main"], cwd=repo)
    _run_git(["config", "user.name", "Tester"], cwd=repo)
    _run_git(["config", "user.email", "tester@example.com"], cwd=repo)

    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    _run_git(["add", "README.md"], cwd=repo)
    _run_git(["commit", "-m", "init"], cwd=repo)

    created_path = add_worktree(repo, "feat/user-auth")
    expected_path = (repo / ".worktrees" / "feat-user-auth").resolve()
    assert created_path.resolve() == expected_path
    assert created_path.is_dir()
    assert (created_path / ".git").is_file()

    # Confirmed by check_worktrees
    assert check_worktrees(repo) == []


def test_cli_check_command_on_current_repo() -> None:
    root = find_repo_root()
    res = subprocess.run(
        [sys.executable, "scripts/worktree_protocol.py", "check", "--repo", str(root)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "PASS: All registered worktrees adhere" in res.stdout


def test_add_worktree_checks_out_existing_branch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-b", "main"], cwd=repo)
    _run_git(["config", "user.name", "Tester"], cwd=repo)
    _run_git(["config", "user.email", "tester@example.com"], cwd=repo)
    (repo / "README.md").write_text("# Repo\n", encoding="utf-8")
    _run_git(["add", "README.md"], cwd=repo)
    _run_git(["commit", "-m", "init"], cwd=repo)

    # Pre-create branch locally
    _run_git(["branch", "existing-feature"], cwd=repo)

    created_path = add_worktree(repo, "existing-feature")
    assert created_path.is_dir()
    assert (created_path / ".git").is_file()
    assert check_worktrees(repo) == []


def test_remove_worktree_and_list_confined(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-b", "main"], cwd=repo)
    _run_git(["config", "user.name", "Tester"], cwd=repo)
    _run_git(["config", "user.email", "tester@example.com"], cwd=repo)
    (repo / "README.md").write_text("# Repo\n", encoding="utf-8")
    _run_git(["add", "README.md"], cwd=repo)
    _run_git(["commit", "-m", "init"], cwd=repo)

    # Add worktree
    wt = add_worktree(repo, "feat/cleanup-target")
    confined = list_confined_worktrees(repo)
    assert len(confined) == 1
    assert confined[0]["slug"] == "feat-cleanup-target"
    assert "feat/cleanup-target" in confined[0]["branch"]

    # Remove worktree by slug/branch
    remove_worktree(repo, "feat/cleanup-target")
    assert not wt.exists()
    assert list_confined_worktrees(repo) == []


def test_remove_worktree_refuses_unconfined_target(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    unconfined_target = tmp_path / "external-wt"

    with pytest.raises(ValueError, match="outside designated worktree root"):
        remove_worktree(repo, unconfined_target)


def test_cli_list_and_remove_commands(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(["init", "-b", "main"], cwd=repo)
    _run_git(["config", "user.name", "Tester"], cwd=repo)
    _run_git(["config", "user.email", "tester@example.com"], cwd=repo)
    (repo / "README.md").write_text("# Repo\n", encoding="utf-8")
    _run_git(["add", "README.md"], cwd=repo)
    _run_git(["commit", "-m", "init"], cwd=repo)

    # Add worktree via CLI
    res_add = subprocess.run(
        [sys.executable, "scripts/worktree_protocol.py", "add", "cli-test", "--repo", str(repo)],
        capture_output=True,
        text=True,
    )
    assert res_add.returncode == 0
    assert "SUCCESS: Created confined worktree" in res_add.stdout

    # List worktrees via CLI (--json)
    res_list = subprocess.run(
        [sys.executable, "scripts/worktree_protocol.py", "list", "--json", "--repo", str(repo)],
        capture_output=True,
        text=True,
    )
    assert res_list.returncode == 0
    import json
    parsed = json.loads(res_list.stdout)
    assert len(parsed) == 1
    assert parsed[0]["slug"] == "cli-test"

    # Remove worktree via CLI
    res_rm = subprocess.run(
        [sys.executable, "scripts/worktree_protocol.py", "remove", "cli-test", "--repo", str(repo)],
        capture_output=True,
        text=True,
    )
    assert res_rm.returncode == 0
    assert "SUCCESS: Removed confined worktree" in res_rm.stdout
