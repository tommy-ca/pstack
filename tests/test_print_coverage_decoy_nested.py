from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "swarm" / "scripts" / "partition.py"
_PARTITION_TAIL = Path("skills") / "swarm" / "scripts" / "partition.py"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", "main", str(path)],
        check=True,
        capture_output=True,
    )
    _git(path, "config", "user.email", "t@example.com")
    _git(path, "config", "user.name", "t")


def _overlay_cache(cache: Path, extra: str) -> tuple[str, str]:
    _init_repo(cache)
    how = cache / "pstack" / "skills" / "how" / "SKILL.md"
    how.parent.mkdir(parents=True)
    how.write_text("old how\n", encoding="utf-8")
    (cache / "pstack" / "skills" / "x.md").write_text("old x\n", encoding="utf-8")
    _git(cache, "add", "pstack")
    _git(cache, "commit", "-m", "pin")
    pin = _git(cache, "rev-parse", "HEAD").stdout.strip()
    how.write_text("new how\n", encoding="utf-8")
    (cache / "pstack" / "skills" / "x.md").write_text("new x\n", encoding="utf-8")
    (cache / "pstack" / "skills" / "extra.md").write_text(extra, encoding="utf-8")
    _git(cache, "add", "pstack")
    _git(cache, "commit", "-m", "tip")
    tip = _git(cache, "rev-parse", "HEAD").stdout.strip()
    return pin, tip


def _print_coverage(
    script: Path, cwd: Path, cache: str, table: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(script),
            "print",
            "--coverage",
            "--cache",
            cache,
            "--table",
            str(table),
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_print_coverage_relative_cache_uses_primary_not_decoy_nested_clone(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    (repo / "README").write_text("root\n", encoding="utf-8")
    script_in_repo = repo / _PARTITION_TAIL
    script_in_repo.parent.mkdir(parents=True)
    shutil.copy2(SCRIPT, script_in_repo)
    _git(repo, "add", "README", "skills")
    _git(repo, "commit", "-m", "init")

    worktree = repo / ".worktrees" / "feat" / "demo"
    worktree.parent.mkdir(parents=True)
    _git(repo, "worktree", "add", "--detach", str(worktree))
    wt_script = worktree / _PARTITION_TAIL
    assert wt_script.is_file()
    assert wt_script.resolve().parents[3] == worktree.resolve()

    primary_cache = repo / ".worktrees" / "upstream-cursor-plugins"
    decoy = worktree / ".worktrees" / "upstream-cursor-plugins"
    pin, tip = _overlay_cache(primary_cache, "primary-extra\n")
    _, decoy_tip = _overlay_cache(decoy, "decoy-extra\n")
    assert tip != decoy_tip
    assert _git(decoy, "cat-file", "-e", tip, check=False).returncode != 0
    assert (primary_cache / "pstack" / "skills" / "extra.md").read_text(
        encoding="utf-8"
    ) == "primary-extra\n"
    assert (decoy / "pstack" / "skills" / "extra.md").read_text(
        encoding="utf-8"
    ) == "decoy-extra\n"

    table = tmp_path / "overlay.tsv"
    table.write_text(
        f"# pin={pin}\n"
        f"# tip={tip}\n"
        "path\tchange\tbucket\tnote\n"
        "skills/how/SKILL.md\tM\tport\tkeep\n"
        "skills/x.md\tM\tport\tkeep\n"
        "skills/extra.md\tA\tport\tkeep\n",
        encoding="utf-8",
    )

    from_primary = _print_coverage(
        wt_script, worktree, str(primary_cache.resolve()), table
    )
    assert from_primary.returncode == 0, from_primary.stderr
    assert from_primary.stdout == "coverage ok\n"

    from_decoy = _print_coverage(wt_script, worktree, str(decoy.resolve()), table)
    assert from_decoy.returncode != 0
    assert tip in from_decoy.stderr
    assert from_decoy.stdout != "coverage ok\n"

    relative = _print_coverage(
        wt_script, worktree, ".worktrees/upstream-cursor-plugins", table
    )
    assert relative.returncode == 0, relative.stderr
    assert relative.stdout == "coverage ok\n"
