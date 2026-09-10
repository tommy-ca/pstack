from __future__ import annotations

import importlib.util
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "swarm" / "scripts" / "refresh-hygiene.py"
CLAUDE = "transcripts live in ~/.claude/projects/encoded\n"
GROK = "GROK_SESSION_ID\n"


def load():
    spec = importlib.util.spec_from_file_location("refresh_hygiene", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _src_dest(tmp_path: Path, dest_text: str) -> tuple[Path, Path, Path, Path]:
    root = tmp_path / "pstack"
    src = root / "skills" / "reflect" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_text(GROK, encoding="utf-8")
    skills = tmp_path / "skills"
    dest = skills / "reflect" / "SKILL.md"
    dest.parent.mkdir(parents=True)
    dest.write_text(dest_text, encoding="utf-8")
    return root, src, skills, dest


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


def test_host_script_literal_and_apply_skills_eperm(tmp_path: Path, capsys) -> None:
    mod = load()
    root = tmp_path / "pstack"
    root.mkdir()
    subprocess.run(
        ["git", "init", "-b", "main", str(root)], check=True, capture_output=True
    )
    src = root / "skills" / "reflect" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_text("GROK_SESSION_ID\n", encoding="utf-8")
    skills = tmp_path / "skills"
    dest = skills / "reflect" / "SKILL.md"
    dest.parent.mkdir(parents=True)
    dest.write_text(
        "transcripts live in ~/.claude/projects/encoded\n", encoding="utf-8"
    )

    assert mod.main(["--root", str(root), "--skills", str(skills)]) == 0
    assert dest.read_text(encoding="utf-8") == (
        "transcripts live in ~/.claude/projects/encoded\n"
    )
    assert capsys.readouterr().out == (
        "kind\taction\tpath\tnote\n"
        f"stale-skill\treport\t{dest}\tclaude-shaped\n"
    )

    assert (
        mod.main(
            ["--root", str(root), "--skills", str(skills), "--host-script"]
        )
        == 0
    )
    assert capsys.readouterr().out == f"cp -- {src} {dest}\n"
    assert dest.read_text(encoding="utf-8") == (
        "transcripts live in ~/.claude/projects/encoded\n"
    )

    dest.chmod(0o444)
    try:
        assert (
            mod.main(
                ["--root", str(root), "--skills", str(skills), "--apply-skills"]
            )
            == 2
        )
        assert capsys.readouterr().out == (
            "kind\taction\tpath\tnote\n"
            f"stale-skill\teperm\t{dest}\tEPERM\n"
        )
        assert dest.read_text(encoding="utf-8") == (
            "transcripts live in ~/.claude/projects/encoded\n"
        )
        assert stat.S_IMODE(dest.stat().st_mode) == 0o444
    finally:
        dest.chmod(0o644)


def test_host_script_dest_is_overlay_not_symlink_target(
    tmp_path: Path, capsys
) -> None:
    mod = load()
    root = tmp_path / "pstack"
    src = root / "skills" / "reflect" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_text("GROK_SESSION_ID\n", encoding="utf-8")
    agents = tmp_path / "agents" / "skills" / "reflect"
    agents.mkdir(parents=True)
    (agents / "SKILL.md").write_text(
        "transcripts live in ~/.claude/projects/encoded\n", encoding="utf-8"
    )
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "reflect").symlink_to(agents)
    dest = skills / "reflect" / "SKILL.md"
    assert dest.resolve() == (agents / "SKILL.md").resolve()
    assert (
        mod.main(
            ["--root", str(root), "--skills", str(skills), "--host-script"]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert out == f"cp -- {src} {dest}\n"
    assert str(agents) not in out
    assert dest.read_text(encoding="utf-8") == (
        "transcripts live in ~/.claude/projects/encoded\n"
    )


def test_apply_skills_symlink_parent_is_eperm_dest_unchanged(
    tmp_path: Path, capsys
) -> None:
    mod = load()
    root = tmp_path / "pstack"
    src = root / "skills" / "reflect" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_text(GROK, encoding="utf-8")
    agents = tmp_path / "agents" / "skills" / "reflect"
    agents.mkdir(parents=True)
    target = agents / "SKILL.md"
    target.write_text(CLAUDE, encoding="utf-8")
    skills = tmp_path / "skills"
    skills.mkdir()
    (skills / "reflect").symlink_to(agents)
    dest = skills / "reflect" / "SKILL.md"
    assert dest.parent.is_symlink()
    assert not dest.is_symlink()
    before_mode = stat.S_IMODE(dest.stat().st_mode)

    assert (
        mod.main(["--root", str(root), "--skills", str(skills), "--apply-skills"])
        == 2
    )
    out = capsys.readouterr().out
    assert out == (
        "kind\taction\tpath\tnote\n"
        f"stale-skill\teperm\t{dest}\tEPERM\n"
    )
    assert str(agents) not in out
    assert dest.read_text(encoding="utf-8") == CLAUDE
    assert dest.parent.is_symlink()
    assert stat.S_IMODE(dest.stat().st_mode) == before_mode
    assert target.read_text(encoding="utf-8") == CLAUDE


def test_apply_skills_symlink_ancestor_is_eperm_dest_unchanged(
    tmp_path: Path, capsys
) -> None:
    mod = load()
    root = tmp_path / "pstack"
    src = root / "skills" / "reflect" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_text(GROK, encoding="utf-8")
    real_skills = tmp_path / "real_skills"
    real_dest = real_skills / "reflect" / "SKILL.md"
    real_dest.parent.mkdir(parents=True)
    real_dest.write_text(CLAUDE, encoding="utf-8")
    overlay = tmp_path / "overlay"
    overlay.mkdir()
    (overlay / "skills").symlink_to(real_skills)
    skills = overlay / "skills"
    dest = skills / "reflect" / "SKILL.md"
    assert not dest.is_symlink()
    assert not dest.parent.is_symlink()
    assert mod.has_symlink_parent(dest)
    before_mode = stat.S_IMODE(dest.stat().st_mode)

    assert (
        mod.main(["--root", str(root), "--skills", str(skills), "--apply-skills"])
        == 2
    )
    out = capsys.readouterr().out
    assert out == (
        "kind\taction\tpath\tnote\n"
        f"stale-skill\teperm\t{dest}\tEPERM\n"
    )
    assert str(real_skills) not in out
    assert dest.read_text(encoding="utf-8") == CLAUDE
    assert stat.S_IMODE(dest.stat().st_mode) == before_mode


def test_apply_skills_dest_symlink_is_eperm_even_when_target_is_grok_shaped(
    tmp_path: Path, capsys
) -> None:
    mod = load()
    root = tmp_path / "pstack"
    src = root / "skills" / "reflect" / "SKILL.md"
    src.parent.mkdir(parents=True)
    src.write_text(GROK, encoding="utf-8")
    agents = tmp_path / "agents" / "skills" / "reflect"
    agents.mkdir(parents=True)
    target = agents / "SKILL.md"
    target.write_text(GROK, encoding="utf-8")
    skills = tmp_path / "skills"
    dest = skills / "reflect" / "SKILL.md"
    dest.parent.mkdir(parents=True)
    dest.symlink_to(target)
    assert dest.is_symlink()
    before_mode = stat.S_IMODE(target.stat().st_mode)

    assert (
        mod.main(["--root", str(root), "--skills", str(skills), "--apply-skills"])
        == 2
    )
    out = capsys.readouterr().out
    assert out == (
        "kind\taction\tpath\tnote\n"
        f"stale-skill\teperm\t{dest}\tEPERM\n"
    )
    assert str(agents) not in out
    assert dest.is_symlink()
    assert dest.read_text(encoding="utf-8") == GROK
    assert target.read_text(encoding="utf-8") == GROK
    assert stat.S_IMODE(target.stat().st_mode) == before_mode


def test_apply_skills_grok_shaped_dest_is_not_stale_dest_unchanged(
    tmp_path: Path, capsys
) -> None:
    mod = load()
    root, src, skills, dest = _src_dest(tmp_path, GROK)
    before_mode = stat.S_IMODE(dest.stat().st_mode)
    src.write_text("GROK_SESSION_ID plus extra\n", encoding="utf-8")

    assert (
        mod.main(["--root", str(root), "--skills", str(skills), "--apply-skills"])
        == 0
    )
    out = capsys.readouterr().out
    assert out == (
        "kind\taction\tpath\tnote\n"
        f"stale-skill\tnot-stale\t{dest}\tnot-stale\n"
    )
    assert dest.read_text(encoding="utf-8") == GROK
    assert stat.S_IMODE(dest.stat().st_mode) == before_mode
    assert src.read_text(encoding="utf-8") == "GROK_SESSION_ID plus extra\n"


def test_apply_skills_claude_shaped_writable_dest_copies(
    tmp_path: Path, capsys
) -> None:
    mod = load()
    root, src, skills, dest = _src_dest(tmp_path, CLAUDE)

    assert (
        mod.main(["--root", str(root), "--skills", str(skills), "--apply-skills"])
        == 0
    )
    out = capsys.readouterr().out
    assert out == (
        "kind\taction\tpath\tnote\n"
        f"stale-skill\tcopied\t{dest}\tok\n"
    )
    assert dest.read_text(encoding="utf-8") == GROK
    assert src.read_text(encoding="utf-8") == GROK
    assert not dest.is_symlink()


def test_apply_skills_second_copy_is_not_stale(tmp_path: Path, capsys) -> None:
    mod = load()
    root, src, skills, dest = _src_dest(tmp_path, CLAUDE)
    assert (
        mod.main(["--root", str(root), "--skills", str(skills), "--apply-skills"])
        == 0
    )
    assert dest.read_text(encoding="utf-8") == GROK
    capsys.readouterr()
    src.write_text("GROK_SESSION_ID plus extra\n", encoding="utf-8")
    assert (
        mod.main(["--root", str(root), "--skills", str(skills), "--apply-skills"])
        == 0
    )
    out = capsys.readouterr().out
    assert out == (
        "kind\taction\tpath\tnote\n"
        f"stale-skill\tnot-stale\t{dest}\tnot-stale\n"
    )
    assert dest.read_text(encoding="utf-8") == GROK
    assert src.read_text(encoding="utf-8") == "GROK_SESSION_ID plus extra\n"


def test_parent_symlink_cache_is_keep_not_deleted(tmp_path: Path, capsys) -> None:
    mod = load()
    repo, primary, nested, skills = _repo(tmp_path)
    sample = repo / ".worktrees" / "fix" / "sample"
    elsewhere = tmp_path / "elsewhere" / ".worktrees" / "upstream-cursor-plugins"
    elsewhere.mkdir(parents=True)
    (elsewhere / "marker").write_text("via-symlink\n", encoding="utf-8")
    mod.rmtree_git_clone(nested)
    nested.parent.rmdir()
    (sample / ".worktrees").symlink_to(elsewhere.parent)
    cand = sample / ".worktrees" / "upstream-cursor-plugins"
    assert cand.is_dir()
    assert (sample / ".worktrees").is_symlink()
    assert (
        mod.main(["--root", str(repo), "--skills", str(skills), "--apply"]) == 0
    )
    assert (elsewhere / "marker").read_text(encoding="utf-8") == "via-symlink\n"
    out = capsys.readouterr().out
    assert f"nested-cache\tkeep\t{cand}\tsymlink" in out
    assert f"nested-cache\tdeleted\t{elsewhere.resolve()}" not in out


def test_apply_collects_then_records_error_and_still_present(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    mod = load()
    repo, primary, nested, skills = _repo(tmp_path)
    skill = skills / "reflect" / "SKILL.md"

    def boom(path: Path, guard: object) -> None:
        assert nested.exists()
        raise OSError("nope")

    monkeypatch.setattr(mod, "guarded_delete", boom)
    assert (
        mod.main(["--root", str(repo), "--skills", str(skills), "--apply"]) == 2
    )
    assert nested.exists()
    assert (primary / "marker").read_text(encoding="utf-8") == "primary\n"
    assert capsys.readouterr().out == (
        "kind\taction\tpath\tnote\n"
        f"nested-cache\terror\t{nested.resolve()}\tnope\n"
        f"nested-cache\tkeep\t{primary.resolve()}\tprimary overlay cache\n"
        f"stale-skill\treport\t{skill.resolve()}\tclaude-shaped\n"
    )

    def silent(path: Path, guard: object) -> None:
        return None

    monkeypatch.setattr(mod, "guarded_delete", silent)
    assert (
        mod.main(["--root", str(repo), "--skills", str(skills), "--apply"]) == 2
    )
    assert nested.exists()
    out = capsys.readouterr().out
    assert f"nested-cache\tdeleted\t{nested.resolve()}" not in out
    assert f"nested-cache\terror\t{nested.resolve()}\tstill present" in out


def test_leftover_worktree_when_squash_from_log_empty(
    tmp_path: Path, capsys
) -> None:
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
    skills = tmp_path / "skills"
    skill = skills / "reflect" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("GROK_SESSION_ID only\n", encoding="utf-8")
    assert mod.main(["--root", str(repo), "--skills", str(skills)]) == 0
    assert capsys.readouterr().out == (
        "kind\taction\tpath\tnote\n"
        f"leftover-worktree\treport\t{worktree.resolve()}\t"
        "HEAD not ancestor of main\n"
    )


def test_scan_skills_permission_error_emits_unread(
    tmp_path: Path, monkeypatch
) -> None:
    mod = load()
    skills = tmp_path / "skills"
    skill = skills / "reflect" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("secret\n", encoding="utf-8")
    real = Path.read_text

    def deny(self: Path, *args: object, **kwargs: object) -> str:
        if Path(self) == skill:
            raise PermissionError("denied")
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny)
    rows = mod.scan_skills(skills)
    assert rows == (mod.Row(mod.KIND_SKILL, "report", skill, "unread"),)
