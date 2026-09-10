from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "swarm" / "scripts" / "partition.py"


def load_partition():
    spec = importlib.util.spec_from_file_location("swarm_partition", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_table(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_table_round_trip(tmp_path: Path) -> None:
    mod = load_partition()
    src = tmp_path / "t.tsv"
    write_table(
        src,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "# tip=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
        "path\tchange\tbucket\tnote\n"
        "skills/how/SKILL.md\tM\tport\tkeep critics\n",
    )
    table = mod.read_table(src)
    assert table.pin.endswith("a")
    assert table.rows[0].path == "skills/how/SKILL.md"
    again = mod.read_table(src)
    src.write_text(mod.format_table(table), encoding="utf-8")
    assert mod.read_table(src) == again


def test_parse_rejects_duplicate_unknown_and_dotdot(tmp_path: Path) -> None:
    mod = load_partition()
    dup = tmp_path / "dup.tsv"
    write_table(
        dup,
        "path\tchange\tbucket\tnote\n"
        "a.md\tM\tport\tx\n"
        "a.md\tM\tskip\ty\n",
    )
    try:
        mod.read_table(dup)
        raise AssertionError("duplicate path must fail")
    except SystemExit as exc:
        assert "duplicate" in str(exc)

    bad = tmp_path / "bad.tsv"
    write_table(bad, "path\tchange\tbucket\tnote\n../secret\tM\tport\tx\n")
    try:
        mod.read_table(bad)
        raise AssertionError(".. path must fail")
    except SystemExit as exc:
        assert "invalid path" in str(exc)

    unk = tmp_path / "unk.tsv"
    write_table(unk, "path\tchange\tbucket\tnote\na.md\tM\tcopy\tx\n")
    try:
        mod.read_table(unk)
        raise AssertionError("unknown bucket must fail")
    except SystemExit as exc:
        assert "invalid bucket" in str(exc)


def test_pstack_prefix_stripped() -> None:
    mod = load_partition()
    row = mod.parse_row(["pstack/skills/how/SKILL.md", "M", "port", "n"])
    assert row.path == "skills/how/SKILL.md"


def test_skeleton_unclassified() -> None:
    mod = load_partition()
    table = mod.skeleton_table(
        "pin",
        "tip",
        (("A", "skills/new/SKILL.md"), ("M", "README.md")),
    )
    assert table.comments["pin"] == "pin"
    assert all(row.bucket == "unclassified" for row in table.rows)
    assert len(table.rows) == 2


def test_coverage_fails_on_gap_and_unclassified() -> None:
    mod = load_partition()
    table = mod.Table(
        {"pin": "p", "tip": "t"},
        (mod.Row("a.md", "M", "port", ""),),
    )
    errors = mod.coverage_errors(table, (("M", "a.md"), ("A", "b.md")))
    assert any("missing diff path: b.md" in e for e in errors)
    table2 = mod.Table(
        {},
        (mod.Row("a.md", "M", "unclassified", ""),),
    )
    errors2 = mod.coverage_errors(table2, (("M", "a.md"),))
    assert any("unclassified: a.md" in e for e in errors2)
    table3 = mod.Table({}, (mod.Row("a.md", "M", "port", ""),))
    assert mod.coverage_errors(table3, (("M", "a.md"),)) == ()


def test_partition_keeps_how_together_and_is_disjoint(tmp_path: Path) -> None:
    mod = load_partition()
    rows = (
        mod.Row("skills/how/SKILL.md", "M", "port", ""),
        mod.Row("skills/how/references/explainer-prompt.md", "M", "port", ""),
        mod.Row("skills/how/references/explorer-prompt.md", "M", "port", ""),
        mod.Row("skills/how/references/x.md", "M", "port", ""),
        mod.Row("skills/unslop/SKILL.md", "M", "port", ""),
        mod.Row("docs/guide/08-principles.md", "M", "port", ""),
    )
    first = mod.partition_rows(rows, 2)
    second = mod.partition_rows(rows, 2)
    assert first == second
    how_workers = {
        i
        for i, slice_rows in enumerate(first)
        if any(r.path.startswith("skills/how/") for r in slice_rows)
    }
    assert how_workers == {0} or how_workers == {1}
    seen: set[str] = set()
    for slice_rows in first:
        for row in slice_rows:
            assert row.path not in seen
            seen.add(row.path)
    leftover = tmp_path / "worker-9.paths"
    leftover.write_text("stale\n", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("ok\n", encoding="utf-8")
    mod.write_worker_paths(tmp_path, first)
    assert not leftover.exists()
    assert (tmp_path / "keep.txt").read_text(encoding="utf-8") == "ok\n"
    assert (tmp_path / "worker-0.paths").is_file()
    assert (tmp_path / "worker-1.paths").is_file()
    mod.write_worker_paths(tmp_path, first)
    assert (tmp_path / "worker-0.paths").is_file()


def test_partition_cli_refuses_fence_bucket(tmp_path: Path) -> None:
    mod = load_partition()
    table = tmp_path / "t.tsv"
    write_table(
        table,
        "path\tchange\tbucket\tnote\n"
        ".cursor-plugin/plugin.json\tM\tskip\tx\n"
        "skills/how/SKILL.md\tM\tport\ty\n",
    )
    try:
        mod.partition_main(
            [
                "partition",
                "--workers",
                "1",
                "--out",
                str(tmp_path / "out"),
                "--table",
                str(table),
                "--bucket",
                "skip",
            ]
        )
        raise AssertionError("skip partition must fail")
    except SystemExit as exc:
        assert "fences" in str(exc)

    write_table(
        table,
        "path\tchange\tbucket\tnote\n"
        "skills/how/SKILL.md\tM\taudit\tx\n",
    )
    try:
        mod.partition_main(
            [
                "partition",
                "--workers",
                "1",
                "--out",
                str(tmp_path / "out-audit"),
                "--table",
                str(table),
                "--bucket",
                "audit",
            ]
        )
        raise AssertionError("audit partition must fail")
    except SystemExit as exc:
        assert "fences" in str(exc)


def test_merge_fails_on_duplicate_and_pin_mismatch(tmp_path: Path) -> None:
    mod = load_partition()
    a = tmp_path / "a.tsv"
    b = tmp_path / "b.tsv"
    write_table(
        a,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "path\tchange\tbucket\tnote\n"
        "a.md\tM\tport\tx\n",
    )
    write_table(
        b,
        "# pin=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
        "path\tchange\tbucket\tnote\n"
        "b.md\tM\tport\ty\n",
    )
    try:
        mod.merge_tables([mod.read_table(a), mod.read_table(b)])
        raise AssertionError("pin mismatch must fail")
    except SystemExit as exc:
        assert "pin mismatch" in str(exc)
    write_table(
        b,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "path\tchange\tbucket\tnote\n"
        "a.md\tM\tskip\ty\n",
    )
    try:
        mod.merge_tables([mod.read_table(a), mod.read_table(b)])
        raise AssertionError("duplicate merge must fail")
    except SystemExit as exc:
        assert "duplicate" in str(exc)


def test_overlay_seed_keeps_classified_and_drops_stale() -> None:
    mod = load_partition()
    prior = mod.Table(
        {"pin": "oldpin", "tip": "oldtip"},
        (
            mod.Row("skills/how/SKILL.md", "M", "audit", "keep critics"),
            mod.Row("stale.md", "M", "port", "gone"),
            mod.Row("skills/x.md", "M", "unclassified", "old note"),
        ),
    )
    table = mod.overlay_seed(
        prior,
        (
            ("A", "skills/how/SKILL.md"),
            ("A", "skills/brand.md"),
            ("M", "skills/x.md"),
        ),
        "newpin",
        "newtip",
    )
    by_path = {row.path: row for row in table.rows}
    assert "stale.md" not in by_path
    assert by_path["skills/how/SKILL.md"] == mod.Row(
        "skills/how/SKILL.md", "A", "audit", "keep critics"
    )
    assert by_path["skills/brand.md"].bucket == "unclassified"
    assert by_path["skills/brand.md"].change == "A"
    assert by_path["skills/x.md"] == mod.Row(
        "skills/x.md", "M", "unclassified", "old note"
    )
    assert table.pin == "newpin"
    assert table.tip == "newtip"


def test_apply_check_fails_on_leftover_and_skips_name_status(
    tmp_path: Path, monkeypatch
) -> None:
    mod = load_partition()

    def boom(*_args, **_kwargs):
        raise AssertionError("git_name_status must not run")

    monkeypatch.setattr(mod, "git_name_status", boom)
    dest = tmp_path / "dest"
    skill = dest / "skills" / "live"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("run /deslop on this tree\n", encoding="utf-8")
    (dest / "skills" / "swarm" / "references").mkdir(parents=True)
    (dest / "skills" / "swarm" / "references" / "classification.tsv").write_text(
        "note names /deslop and cursor-team-kit as negatives\n",
        encoding="utf-8",
    )
    hits = mod.leftover_hits(dest)
    assert any(hit.token == "/deslop" and "SKILL.md" in hit.relpath for hit in hits)
    assert all(hit.relpath.endswith("classification.tsv") is False for hit in hits)
    table_path = tmp_path / "t.tsv"
    write_table(
        table_path,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "path\tchange\tbucket\tnote\n",
    )
    cache = tmp_path / "cache"
    cache.mkdir()
    try:
        mod.partition_main(
            [
                "apply-check",
                "--cache",
                str(cache),
                "--table",
                str(table_path),
                "--dest",
                str(dest),
                "--tip",
                "deadbeef",
            ]
        )
        raise AssertionError("leftover apply-check must fail")
    except SystemExit as exc:
        assert exc.code == 2


def test_leftover_askquestion_after_there_is_no_is_live(tmp_path: Path) -> None:
    mod = load_partition()
    dest = tmp_path / "dest"
    skill = dest / "skills" / "live"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "There is no setup. Call AskQuestion for the fork.\n",
        encoding="utf-8",
    )
    (skill / "OK.md").write_text(
        "There is no `cursor-team-kit` here.\n",
        encoding="utf-8",
    )
    hits = mod.leftover_hits(dest)
    assert any(hit.token == "AskQuestion" and hit.relpath.endswith("SKILL.md") for hit in hits)
    assert all(hit.relpath.endswith("OK.md") is False for hit in hits)


def _git(cache: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cache), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def _init_cache_with_origin_main(cache: Path) -> tuple[str, str]:
    subprocess.run(["git", "init", "-b", "main", str(cache)], check=True, capture_output=True)
    _git(cache, "config", "user.email", "t@example.com")
    _git(cache, "config", "user.name", "t")
    how = cache / "pstack" / "skills" / "how" / "SKILL.md"
    x_md = cache / "pstack" / "skills" / "x.md"
    how.parent.mkdir(parents=True)
    how.write_text("old how\n", encoding="utf-8")
    x_md.write_text("old x\n", encoding="utf-8")
    _git(cache, "add", "pstack")
    _git(cache, "commit", "-m", "pin")
    pin = _git(cache, "rev-parse", "HEAD").stdout.strip()
    how.write_text("new how\n", encoding="utf-8")
    x_md.write_text("new x\n", encoding="utf-8")
    (cache / "pstack" / "skills" / "brand.md").write_text("brand\n", encoding="utf-8")
    _git(cache, "add", "pstack")
    _git(cache, "commit", "-m", "tip")
    tip = _git(cache, "rev-parse", "HEAD").stdout.strip()
    _git(cache, "update-ref", "refs/remotes/origin/main", tip)
    return pin, tip


def test_classified_range_uses_table_comments_not_origin_main() -> None:
    mod = load_partition()
    table = mod.Table(
        {
            "pin": "1111111111111111111111111111111111111111",
            "tip": "2222222222222222222222222222222222222222",
        },
        (),
    )
    pin, tip = mod.classified_range(table, None, None)
    assert pin == "1111111111111111111111111111111111111111"
    assert tip == "2222222222222222222222222222222222222222"
    pin2, tip2 = mod.classified_range(table, "cli-pin", "cli-tip")
    assert pin2 == "cli-pin"
    assert tip2 == "cli-tip"


def test_seed_main_uses_upstream_and_origin_main(tmp_path: Path) -> None:
    mod = load_partition()
    cache = tmp_path / "cache"
    pin_sha, tip_sha = _init_cache_with_origin_main(cache)
    root = tmp_path / "root"
    root.mkdir()
    (root / "UPSTREAM").write_text(f"tree {pin_sha}\n", encoding="utf-8")
    table_path = tmp_path / "prior.tsv"
    write_table(
        table_path,
        "# pin=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n"
        "# tip=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n"
        "path\tchange\tbucket\tnote\n"
        "skills/how/SKILL.md\tM\taudit\tkeep critics\n"
        "stale.md\tM\tport\tgone\n"
        "skills/x.md\tM\tunclassified\told note\n",
    )
    out = tmp_path / "overlay.tsv"
    pin, tip = mod.next_refresh_range(root, cache, None, None)
    assert pin == pin_sha
    assert tip == tip_sha
    mod.seed_main(
        argparse.Namespace(
            cache=cache,
            table=table_path,
            out=out,
            pin=None,
            tip=None,
        ),
        root,
    )
    overlay = mod.read_table(out)
    assert overlay.pin == pin_sha
    assert overlay.tip == tip_sha
    by_path = {row.path: row for row in overlay.rows}
    assert "stale.md" not in by_path
    assert by_path["skills/how/SKILL.md"] == mod.Row(
        "skills/how/SKILL.md", "M", "audit", "keep critics"
    )
    assert by_path["skills/brand.md"].bucket == "unclassified"
    assert by_path["skills/x.md"] == mod.Row(
        "skills/x.md", "M", "unclassified", "old note"
    )


def test_read_upstream_blob_skips_workdir_when_tip_is_git_object(
    tmp_path: Path,
) -> None:
    mod = load_partition()
    cache = tmp_path / "cache"
    pin_sha, tip_sha = _init_cache_with_origin_main(cache)
    missing = cache / "pstack" / "skills" / "ghost.md"
    missing.write_text("only on disk\n", encoding="utf-8")
    assert mod.read_upstream_blob(cache, tip_sha, "skills/ghost.md") is None
    assert (
        mod.read_upstream_blob(cache, tip_sha, "skills/how/SKILL.md") == b"new how\n"
    )
    loose = tmp_path / "loose"
    put = loose / "pstack" / "skills" / "ghost.md"
    put.parent.mkdir(parents=True)
    put.write_text("workdir fallback\n", encoding="utf-8")
    assert (
        mod.read_upstream_blob(loose, "not-a-git-object", "skills/ghost.md")
        == b"workdir fallback\n"
    )
    assert pin_sha != tip_sha


def test_dest_looks_raw_cursor_ignores_allowed_negation() -> None:
    mod = load_partition()
    assert mod.dest_looks_raw_cursor("There is no `cursor-team-kit` here.\n") is False
    assert mod.live_leftover_tokens("There is no `cursor-team-kit` here.\n") == ()
    assert mod.dest_looks_raw_cursor("there is no /deslop in this port\n") is False
    assert mod.dest_looks_raw_cursor("run /deslop on this tree\n") is True
    assert mod.live_leftover_tokens("run /deslop on this tree\n") == ("/deslop",)
    assert mod.dest_looks_raw_cursor("Call AskQuestion for the fork.\n") is True


def test_mixed_deslop_negation_and_call_on_same_line_is_live(tmp_path: Path) -> None:
    mod = load_partition()
    mixed = "there is no /deslop; run /deslop anyway\n"
    dest = tmp_path / "dest"
    skill = dest / "skills" / "live"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(mixed, encoding="utf-8")
    assert mod.leftover_hits(dest) == (
        mod.LeftoverHit("skills/live/SKILL.md", "/deslop"),
    )
    assert mod.dest_looks_raw_cursor(mixed) is True
    assert mod.live_leftover_tokens(mixed) == ("/deslop",)


def test_mixed_cursor_team_kit_negation_and_call_on_same_line_is_live(
    tmp_path: Path,
) -> None:
    mod = load_partition()
    mixed = "There is no `cursor-team-kit`; run cursor-team-kit anyway\n"
    first = mixed.find("cursor-team-kit")
    second = mixed.find("cursor-team-kit", first + 1)
    assert mod.leftover_mention_allowed(mixed, "cursor-team-kit", first) is True
    assert mod.leftover_mention_allowed(mixed, "cursor-team-kit", second) is False
    dest = tmp_path / "dest"
    skill = dest / "skills" / "live"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(mixed, encoding="utf-8")
    assert mod.leftover_hits(dest) == (
        mod.LeftoverHit("skills/live/SKILL.md", "cursor-team-kit"),
    )
    assert mod.dest_looks_raw_cursor(mixed) is True
    assert mod.live_leftover_tokens(mixed) == ("cursor-team-kit",)


def test_resolve_cache_relative_joins_primary_from_feat_worktree() -> None:
    mod = load_partition()
    feat_root = Path(
        "/home/tommyk/projects/pstack/.worktrees/feat/pstack-upstream-sync-apply"
    )
    got = mod.resolve_cache(feat_root, Path(".worktrees/upstream-cursor-plugins"))
    assert got == Path(
        "/home/tommyk/projects/pstack/.worktrees/upstream-cursor-plugins"
    ).resolve()


def test_resolve_cache_absolute_existing_is_resolved_not_rewritten(
    tmp_path: Path,
) -> None:
    mod = load_partition()
    cache = tmp_path / "elsewhere" / "cache"
    cache.mkdir(parents=True)
    feat_root = Path(
        "/home/tommyk/projects/pstack/.worktrees/feat/pstack-upstream-sync-apply"
    )
    got = mod.resolve_cache(feat_root, cache)
    assert got == cache.resolve()
    assert got != Path(
        "/home/tommyk/projects/pstack/.worktrees/upstream-cursor-plugins"
    ).resolve()


def test_resolve_cache_missing_relative_exits() -> None:
    mod = load_partition()
    feat_root = Path(
        "/home/tommyk/projects/pstack/.worktrees/feat/pstack-upstream-sync-apply"
    )
    try:
        mod.resolve_cache(feat_root, Path(".worktrees/no-such-cache"))
        raise AssertionError("missing cache must fail")
    except SystemExit as exc:
        assert (
            str(exc)
            == "missing cache: /home/tommyk/projects/pstack/.worktrees/no-such-cache"
        )


def test_print_coverage_uses_classified_comments_not_refresh_range(
    tmp_path: Path, capsys
) -> None:
    mod = load_partition()
    cache = tmp_path / "cache"
    pin_sha, tip_sha = _init_cache_with_origin_main(cache)
    extra = cache / "pstack" / "skills" / "extra.md"
    extra.write_text("extra\n", encoding="utf-8")
    _git(cache, "add", "pstack")
    _git(cache, "commit", "-m", "ahead")
    ahead = _git(cache, "rev-parse", "HEAD").stdout.strip()
    _git(cache, "update-ref", "refs/remotes/origin/main", ahead)
    root = tmp_path / "root"
    root.mkdir()
    (root / "UPSTREAM").write_text(f"tree {pin_sha}\n", encoding="utf-8")
    table_path = tmp_path / "overlay.tsv"
    write_table(
        table_path,
        f"# pin={pin_sha}\n"
        f"# tip={tip_sha}\n"
        "path\tchange\tbucket\tnote\n"
        "skills/how/SKILL.md\tM\tport\tkeep\n"
        "skills/x.md\tM\tport\tkeep\n"
        "skills/brand.md\tA\tport\tkeep\n",
    )
    refresh_pin, refresh_tip = mod.next_refresh_range(root, cache, None, None)
    assert (refresh_pin, refresh_tip) == (pin_sha, ahead)
    assert (refresh_pin, refresh_tip) != (pin_sha, tip_sha)
    refresh_errors = mod.coverage_errors(
        mod.read_table(table_path),
        mod.git_name_status(cache, pin_sha, ahead),
    )
    assert "missing diff path: skills/extra.md" in refresh_errors
    mod.partition_main(
        [
            "print",
            "--coverage",
            "--cache",
            str(cache),
            "--table",
            str(table_path),
        ]
    )
    captured = capsys.readouterr()
    assert captured.out == "coverage ok\n"
