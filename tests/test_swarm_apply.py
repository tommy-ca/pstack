from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "swarm" / "scripts" / "apply.py"


def load_apply():
    spec = importlib.util.spec_from_file_location("swarm_apply", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_table(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def put_blob(cache: Path, relpath: str, content: bytes) -> None:
    dest = cache / "pstack" / relpath
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)


def test_dry_run_refuses_fence_and_writes_nothing(tmp_path: Path) -> None:
    mod = load_apply()
    cache = tmp_path / "cache"
    dest = tmp_path / "dest"
    dest.mkdir()
    put_blob(cache, "skills/how/SKILL.md", b"upstream how\n")
    table = tmp_path / "t.tsv"
    write_table(
        table,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "# tip=not-a-git-object\n"
        "path\tchange\tbucket\tnote\n"
        "skills/how/SKILL.md\tM\taudit\tfence\n",
    )
    report = mod.apply_main(
        [
            "--cache",
            str(cache),
            "--table",
            str(table),
            "--dest",
            str(dest),
            "--dry-run",
        ]
    )
    assert report.dry_run is True
    assert report.copied == ()
    assert any(d.reason == "fence" for d in report.refused)
    assert not (dest / "skills" / "how" / "SKILL.md").exists()


def test_copy_port_and_skip_equal_dest(tmp_path: Path) -> None:
    mod = load_apply()
    cache = tmp_path / "cache"
    dest = tmp_path / "dest"
    rel = "skills/why/SKILL.md"
    put_blob(cache, rel, b"portable why\n")
    table = tmp_path / "t.tsv"
    write_table(
        table,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "# tip=not-a-git-object\n"
        "path\tchange\tbucket\tnote\n"
        f"{rel}\tM\tport\tkeep\n",
    )
    report = mod.apply_main(
        ["--cache", str(cache), "--table", str(table), "--dest", str(dest)]
    )
    written = dest / rel
    assert report.copied == (rel,)
    assert written.read_bytes() == b"portable why\n"
    first_mtime = written.stat().st_mtime_ns
    again = mod.apply_main(
        ["--cache", str(cache), "--table", str(table), "--dest", str(dest)]
    )
    assert again.copied == ()
    assert again.skipped == (rel,)
    assert written.stat().st_mtime_ns == first_mtime


def test_refuse_remapped_dest(tmp_path: Path) -> None:
    mod = load_apply()
    cache = tmp_path / "cache"
    dest = tmp_path / "dest"
    rel = "skills/why/SKILL.md"
    put_blob(cache, rel, b"AskQuestion leftover\n")
    dest_file = dest / rel
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    dest_file.write_text("spawn_subagent pstack:why-investigators\n", encoding="utf-8")
    before = dest_file.read_bytes()
    table = tmp_path / "t.tsv"
    write_table(
        table,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "# tip=not-a-git-object\n"
        "path\tchange\tbucket\tnote\n"
        f"{rel}\tM\tport\thost map\n",
    )
    report = mod.apply_main(
        ["--cache", str(cache), "--table", str(table), "--dest", str(dest)]
    )
    assert report.copied == ()
    assert any(d.reason == "already-remapped" for d in report.refused)
    assert dest_file.read_bytes() == before


def test_refuse_host_keep_when_dest_differs_without_cursor_tokens(tmp_path: Path) -> None:
    mod = load_apply()
    cache = tmp_path / "cache"
    dest = tmp_path / "dest"
    rel = "skills/recall/SKILL.md"
    put_blob(cache, rel, b"Transcripts live at ~/.cursor/projects/x\n")
    dest_file = dest / rel
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    dest_file.write_text("Transcripts live where this session says.\n", encoding="utf-8")
    before = dest_file.read_bytes()
    table = tmp_path / "t.tsv"
    write_table(
        table,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "# tip=not-a-git-object\n"
        "path\tchange\tbucket\tnote\n"
        f"{rel}\tM\tport\thost keep\n",
    )
    report = mod.apply_main(
        ["--cache", str(cache), "--table", str(table), "--dest", str(dest)]
    )
    assert report.copied == ()
    assert any(d.reason == "host-keep" for d in report.refused)
    assert dest_file.read_bytes() == before


def test_host_keep_when_dest_only_has_allowed_leftover_mention(tmp_path: Path) -> None:
    mod = load_apply()
    cache = tmp_path / "cache"
    dest = tmp_path / "dest"
    rel = "skills/recall/SKILL.md"
    put_blob(cache, rel, b"install cursor-team-kit then /deslop\n")
    dest_file = dest / rel
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    dest_file.write_text(
        "There is no `cursor-team-kit` here.\nthere is no /deslop in this port\n",
        encoding="utf-8",
    )
    before = dest_file.read_bytes()
    table = tmp_path / "t.tsv"
    write_table(
        table,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "# tip=not-a-git-object\n"
        "path\tchange\tbucket\tnote\n"
        f"{rel}\tM\tport\thost keep\n",
    )
    report = mod.apply_main(
        ["--cache", str(cache), "--table", str(table), "--dest", str(dest)]
    )
    assert report.copied == ()
    assert any(d.reason == "host-keep" for d in report.refused)
    assert dest_file.read_bytes() == before


def test_plugin_has_no_grok_workflows() -> None:
    assert not (ROOT / ".grok" / "workflows").exists()
    rhai = ROOT / "skills" / "swarm" / "references" / "pstack-upstream-refresh.rhai"
    assert rhai.is_file()
    text = rhai.read_text(encoding="utf-8")
    assert "capability_mode" not in text
    assert 'name: "pstack-upstream-refresh"' in text
