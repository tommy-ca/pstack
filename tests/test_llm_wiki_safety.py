"""Security and replay contract tests for the PStack project-local wiki.

The baseline is intentionally structural; these tests do not prove semantic
extraction, arbitrary Markdown parsing, or a cross-file transaction.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.llm_wiki import check_wiki, generate_index_markdown, ingest_file

BASE_WIKI = ROOT / ".llm-wiki"


@pytest.fixture
def wiki(tmp_path: Path) -> Path:
    dest = tmp_path / ".llm-wiki"
    shutil.copytree(BASE_WIKI, dest)
    return dest


def _source(folder: Path, text: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / "spec.md"
    file.write_text(text, encoding="utf-8")
    return file


def test_immutable_raw_basename_conflict_is_rejected(wiki: Path, tmp_path: Path) -> None:
    first = _source(tmp_path / "first", "one")
    second = _source(tmp_path / "second", "two")
    dest, _ = ingest_file(first, wiki)
    log_before = (wiki / "log.md").read_bytes()
    with pytest.raises(FileExistsError, match="Immutable raw source collision"):
        ingest_file(second, wiki)
    assert dest.read_bytes() == b"one"
    assert (wiki / "log.md").read_bytes() == log_before


def test_exact_replay_does_not_duplicate_log(wiki: Path, tmp_path: Path) -> None:
    source = _source(tmp_path / "in", "identical")
    first = ingest_file(source, wiki)
    previous = (wiki / "log.md").read_bytes()
    second = ingest_file(source, wiki)
    assert first == second
    assert (wiki / "log.md").read_bytes() == previous


def test_concurrent_conflicting_ingest_has_single_winner(wiki: Path, tmp_path: Path) -> None:
    first = _source(tmp_path / "first", "A")
    second = _source(tmp_path / "second", "B")
    with ThreadPoolExecutor(max_workers=2) as pool:
        runs = list(pool.map(lambda p: _capture_ingest(p, wiki), (first, second)))
    assert sorted(runs) == ["collision", "success"]
    assert (wiki / "raw/sources/spec.md").read_text() in {"A", "B"}


def _capture_ingest(source: Path, wiki: Path) -> str:
    try:
        ingest_file(source, wiki)
        return "success"
    except FileExistsError:
        return "collision"


def _make_symlink(link: Path, target: Path, is_dir: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=is_dir)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlinks unavailable: {exc}")


def test_symlink_raw_source_directory_is_rejected(wiki: Path, tmp_path: Path) -> None:
    source = _source(tmp_path / "in", "safe")
    outside = tmp_path / "outside"
    outside.mkdir()
    sources = wiki / "raw/sources"
    shutil.rmtree(sources)
    _make_symlink(sources, outside, is_dir=True)
    with pytest.raises(ValueError, match="Symlink wiki source directory"):
        ingest_file(source, wiki)
    assert not list(outside.iterdir())


def test_symlink_raw_target_cannot_be_overwritten(wiki: Path, tmp_path: Path) -> None:
    source = _source(tmp_path / "in", "safe")
    outside = tmp_path / "outside.md"
    outside.write_text("secret")
    _make_symlink(wiki / "raw/sources/spec.md", outside)
    with pytest.raises(FileExistsError, match="Immutable raw source collision"):
        ingest_file(source, wiki)
    assert outside.read_text() == "secret"


def test_symlink_log_refuses_write_before_creating_raw(wiki: Path, tmp_path: Path) -> None:
    source = _source(tmp_path / "in", "safe")
    outside = tmp_path / "outside.md"
    outside.write_text("unchanged")
    (wiki / "log.md").unlink()
    _make_symlink(wiki / "log.md", outside)
    with pytest.raises(ValueError, match="Symlink wiki log"):
        ingest_file(source, wiki)
    assert outside.read_text() == "unchanged"
    assert not (wiki / "raw/sources/spec.md").exists()


def test_index_escape_is_rejected(wiki: Path, tmp_path: Path) -> None:
    (tmp_path / "outside.md").write_text("outside")
    idx = wiki / "index.md"
    idx.write_text(idx.read_text() + "\n- [Escape](../outside.md)\n")
    assert any("out-of-root link" in e for e in check_wiki(wiki))


def test_page_escape_is_rejected(wiki: Path) -> None:
    page = wiki / "wiki/concepts/agentic-orchestrate.md"
    page.write_text(page.read_text() + "\n[Escape](../../../../outside.md)\n")
    assert any("out-of-root link" in e for e in check_wiki(wiki))


def test_nested_pages_are_included_by_index_generator(wiki: Path) -> None:
    page = wiki / "wiki/concepts/nested/detail.md"
    page.parent.mkdir()
    page.write_text("# Nested Detail\nBounded test fixture.\n")
    generated = generate_index_markdown(wiki)
    assert "(wiki/concepts/nested/detail.md)" in generated


def test_config_required_value_is_nonempty_string(wiki: Path) -> None:
    cfg = wiki / "config.json"
    import json
    content = json.loads(cfg.read_text())
    content["mode"] = []
    cfg.write_text(json.dumps(content))
    assert any("must be a nonempty string" in e for e in check_wiki(wiki))


def test_cli_conflicting_ingest_returns_nonzero(wiki: Path, tmp_path: Path) -> None:
    first = _source(tmp_path / "first", "one")
    second = _source(tmp_path / "second", "two")
    command = [sys.executable, str(ROOT / "scripts/llm_wiki.py"), "ingest"]
    ok = subprocess.run(command + [str(first), "--wiki-dir", str(wiki)], capture_output=True, text=True, check=False)
    bad = subprocess.run(command + [str(second), "--wiki-dir", str(wiki)], capture_output=True, text=True, check=False)
    assert ok.returncode == 0
    assert bad.returncode != 0
    assert "Immutable raw source collision" in bad.stderr
