from __future__ import annotations

import importlib.util
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "swarm" / "scripts" / "refresh-hygiene.py"


def load():
    spec = importlib.util.spec_from_file_location("refresh_hygiene", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


def _repo(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main", str(repo)], check=True, capture_output=True
    )
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "README").write_text("root\n", encoding="utf-8")
    _git(repo, "add", "README")
    _git(repo, "commit", "-m", "init")
    sample = repo / ".worktrees" / "fix" / "sample"
    sample.parent.mkdir(parents=True)
    _git(repo, "worktree", "add", "--detach", str(sample))
    primary = repo / ".worktrees" / "upstream-cursor-plugins"
    primary.mkdir()
    (primary / "marker").write_text("primary\n", encoding="utf-8")
    nested = sample / ".worktrees" / "upstream-cursor-plugins"
    nested.mkdir(parents=True)
    (nested / "marker").write_text("nested\n", encoding="utf-8")
    ro = nested / "objects" / "pack"
    ro.parent.mkdir(parents=True)
    ro.write_text("blob\n", encoding="utf-8")
    ro.chmod(stat.S_IRUSR)
    skills = tmp_path / "skills"
    skill = skills / "reflect" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "transcripts live in ~/.claude/projects/encoded\n", encoding="utf-8"
    )
    return repo, primary, nested, skills


def test_nested_clone_under_worktree_is_would_delete_primary_is_keep(
    tmp_path: Path, capsys
) -> None:
    mod = load()
    repo, primary, nested, skills = _repo(tmp_path)
    skill = skills / "reflect" / "SKILL.md"
    assert mod.main(["--root", str(repo), "--skills", str(skills)]) == 2
    assert (nested / "marker").read_text(encoding="utf-8") == "nested\n"
    assert (primary / "marker").read_text(encoding="utf-8") == "primary\n"
    assert capsys.readouterr().out == (
        "kind\taction\tpath\tnote\n"
        f"nested-cache\twould-delete\t{nested.resolve()}\tnested overlay clone\n"
        f"nested-cache\tkeep\t{primary.resolve()}\tprimary overlay cache\n"
        f"stale-skill\treport\t{skill.resolve()}\tclaude-shaped\n"
    )


def test_apply_removes_nested_not_primary(tmp_path: Path, capsys) -> None:
    mod = load()
    repo, primary, nested, skills = _repo(tmp_path)
    sample = repo / ".worktrees" / "fix" / "sample"
    skill = skills / "reflect" / "SKILL.md"
    assert (
        mod.main(["--root", str(repo), "--skills", str(skills), "--apply"]) == 0
    )
    assert not nested.exists()
    assert (primary / "marker").read_text(encoding="utf-8") == "primary\n"
    assert (sample / "README").read_text(encoding="utf-8") == "root\n"
    assert skill.read_text(encoding="utf-8") == (
        "transcripts live in ~/.claude/projects/encoded\n"
    )
    assert capsys.readouterr().out == (
        "kind\taction\tpath\tnote\n"
        f"nested-cache\tdeleted\t{nested.resolve()}\tnested overlay clone\n"
        f"nested-cache\tkeep\t{primary.resolve()}\tprimary overlay cache\n"
        f"stale-skill\treport\t{skill.resolve()}\tclaude-shaped\n"
    )


def test_second_apply_is_noop(tmp_path: Path, capsys) -> None:
    mod = load()
    repo, primary, nested, skills = _repo(tmp_path)
    skill = skills / "reflect" / "SKILL.md"
    assert (
        mod.main(["--root", str(repo), "--skills", str(skills), "--apply"]) == 0
    )
    capsys.readouterr()
    assert (
        mod.main(["--root", str(repo), "--skills", str(skills), "--apply"]) == 0
    )
    assert not nested.exists()
    assert (primary / "marker").read_text(encoding="utf-8") == "primary\n"
    assert capsys.readouterr().out == (
        "kind\taction\tpath\tnote\n"
        f"nested-cache\tkeep\t{primary.resolve()}\tprimary overlay cache\n"
        f"stale-skill\treport\t{skill.resolve()}\tclaude-shaped\n"
    )


def test_registered_worktree_path_is_not_deleted(tmp_path: Path, capsys) -> None:
    mod = load()
    repo, primary, nested, skills = _repo(tmp_path)
    mod.rmtree_git_clone(nested)
    nested.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", "--detach", str(nested))
    (nested / "marker").write_text("registered\n", encoding="utf-8")
    assert (
        mod.main(["--root", str(repo), "--skills", str(skills), "--apply"]) == 0
    )
    assert (nested / "marker").read_text(encoding="utf-8") == "registered\n"
    assert (primary / "marker").read_text(encoding="utf-8") == "primary\n"
    out = capsys.readouterr().out
    assert (
        f"nested-cache\tkeep\t{nested.resolve()}\tin git worktree list" in out
    )
    assert f"nested-cache\tdeleted\t{nested.resolve()}" not in out


def test_squash_worktree_cli_tsv_literal(tmp_path: Path, capsys) -> None:
    mod = load()
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--initial-branch=main", str(repo)],
        check=True,
        capture_output=True,
    )
    _git(repo, "config", "user.name", "Hygiene Test")
    _git(repo, "config", "user.email", "hygiene@example.com")
    (repo / "f.txt").write_text("a\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "main")
    worktree = tmp_path / "demo"
    _git(repo, "worktree", "add", "-b", "feat/demo", str(worktree))
    (worktree / "f.txt").write_text("b\n", encoding="utf-8")
    _git(worktree, "add", ".")
    _git(worktree, "commit", "-m", "feat: demo")
    _git(repo, "merge", "--squash", "feat/demo")
    _git(repo, "commit", "-m", "feat: demo (#1)")
    skills = tmp_path / "skills"
    skill = skills / "reflect" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("GROK_SESSION_ID only\n", encoding="utf-8")
    assert mod.main(["--root", str(repo), "--skills", str(skills)]) == 0
    assert capsys.readouterr().out == (
        "kind\taction\tpath\tnote\n"
        f"squash-worktree\treport\t{worktree.resolve()}\t"
        "#1 MERGED; HEAD not on main\n"
    )


def test_squash_from_log_rejects_subject_prefix() -> None:
    mod = load()
    assert (
        mod.squash_from_log(
            "fix(pstack)",
            ("fix(pstack): resolve relative overlay cache on the primary checkout (#11)",),
        )
        == ""
    )
    assert (
        mod.squash_from_log("feat: demo", ("feat: demo (#1)",))
        == "#1 MERGED; HEAD not on main"
    )


def test_sync_remote_cache_is_primary_checkout() -> None:
    script = ROOT / "scripts" / "sync-from-upstream.py"
    spec = importlib.util.spec_from_file_location("sync_from_upstream", script)
    assert spec is not None and spec.loader is not None
    sync = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sync)
    got = sync.remote_cache().resolve()
    assert got == Path(
        "/home/tommyk/projects/pstack/.worktrees/upstream-cursor-plugins"
    ).resolve()
    feat_script = Path(
        "/home/tommyk/projects/pstack/.worktrees/feat/pstack-upstream-sync-apply"
        "/scripts/sync-from-upstream.py"
    )
    if feat_script.is_file():
        feat_root = feat_script.resolve().parents[1]
        assert feat_root != Path("/home/tommyk/projects/pstack").resolve()
        assert got != (feat_root / ".worktrees" / "upstream-cursor-plugins").resolve()
