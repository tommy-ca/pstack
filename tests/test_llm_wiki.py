"""Tests for project-local LLM Wiki validator, compiler, and ingestion tool.

Validates acceptance criteria for Issue #866 (Epic #863):
- Structural validity of .llm-wiki/ on current tree
- Strict negative controls for broken links, missing files, unindexed pages, invalid config
- Deterministic ingestion with SHA-256 calculation and log appending
- CLI exit code contracts for CI integration
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.llm_wiki import (
    check_wiki,
    generate_index_markdown,
    ingest_file,
    compute_sha256,
    verify_sources,
    build_knowledge_graph,
    search_wiki,
)

WIKI_DIR = ROOT / ".llm-wiki"


def test_wiki_structure_passes_on_current_tree() -> None:
    errors = check_wiki(WIKI_DIR)
    assert not errors, f"Expected clean check on repository wiki, got errors: {errors}"


def test_wiki_config_schema() -> None:
    config_file = WIKI_DIR / "config.json"
    assert config_file.is_file()
    data = json.loads(config_file.read_text(encoding="utf-8"))
    for key in ("name", "mode", "topic", "version"):
        assert key in data
        assert isinstance(data[key], str)


def test_broken_link_in_index_fails_closed(tmp_path: Path) -> None:
    scratch_wiki = tmp_path / ".llm-wiki"
    shutil.copytree(WIKI_DIR, scratch_wiki)

    # Inject broken link in index.md
    index_file = scratch_wiki / "index.md"
    original = index_file.read_text(encoding="utf-8")
    index_file.write_text(original + "\n- [Broken](./wiki/concepts/nonexistent.md)\n", encoding="utf-8")

    errors = check_wiki(scratch_wiki)
    assert any("broken link" in e.lower() for e in errors)


def test_unindexed_page_fails_closed(tmp_path: Path) -> None:
    scratch_wiki = tmp_path / ".llm-wiki"
    shutil.copytree(WIKI_DIR, scratch_wiki)

    # Inject orphan page
    orphan = scratch_wiki / "wiki" / "concepts" / "orphan-concept.md"
    orphan.write_text("# Orphan\nUnindexed page content.", encoding="utf-8")

    errors = check_wiki(scratch_wiki)
    assert any("not listed in index.md" in e for e in errors)


def test_broken_relative_link_inside_page_fails_closed(tmp_path: Path) -> None:
    scratch_wiki = tmp_path / ".llm-wiki"
    shutil.copytree(WIKI_DIR, scratch_wiki)

    # Inject broken relative link in an indexed page
    target_page = scratch_wiki / "wiki" / "concepts" / "agentic-orchestrate.md"
    content = target_page.read_text(encoding="utf-8")
    target_page.write_text(content + "\n[Ghost](../entities/ghost.md)\n", encoding="utf-8")

    errors = check_wiki(scratch_wiki)
    assert any("broken relative link" in e.lower() for e in errors)


def test_corrupt_config_json_fails_closed(tmp_path: Path) -> None:
    scratch_wiki = tmp_path / ".llm-wiki"
    shutil.copytree(WIKI_DIR, scratch_wiki)

    (scratch_wiki / "config.json").write_text("{ corrupt json ...", encoding="utf-8")
    errors = check_wiki(scratch_wiki)
    assert any("invalid JSON" in e for e in errors)


def test_missing_required_file_fails_closed(tmp_path: Path) -> None:
    scratch_wiki = tmp_path / ".llm-wiki"
    shutil.copytree(WIKI_DIR, scratch_wiki)

    (scratch_wiki / "log.md").unlink()
    errors = check_wiki(scratch_wiki)
    assert any("Missing required top-level file: log.md" in e for e in errors)


def test_ingest_file_computes_sha256_and_appends_log(tmp_path: Path) -> None:
    scratch_wiki = tmp_path / ".llm-wiki"
    shutil.copytree(WIKI_DIR, scratch_wiki)

    test_source = tmp_path / "sample-spec.md"
    test_source.write_text("# Sample Spec\nDeterministic content.", encoding="utf-8")
    expected_sha = compute_sha256(test_source)

    dest, digest = ingest_file(test_source, scratch_wiki, label="Test Ingest")
    assert dest.is_file()
    assert dest.parent == scratch_wiki / "raw" / "sources"
    assert digest == expected_sha

    log_content = (scratch_wiki / "log.md").read_text(encoding="utf-8")
    assert "sample-spec.md" in log_content
    assert digest[:12] in log_content
    assert "Test Ingest" in log_content


def test_cli_subprocess_check_exit_code() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "llm_wiki.py"), "check", "--wiki-dir", str(WIKI_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "PASS:" in proc.stdout


def test_verify_sources_passes_on_current_wiki() -> None:
    errors = verify_sources(WIKI_DIR)
    assert not errors, f"Expected clean source verification on current wiki, got: {errors}"


def test_build_knowledge_graph_structure() -> None:
    graph = build_knowledge_graph(WIKI_DIR)
    assert "nodes" in graph
    assert "edges" in graph
    assert "inbound" in graph
    assert "outbound" in graph
    assert "orphans" in graph
    assert "metrics" in graph
    assert graph["metrics"]["total_pages"] == len(graph["nodes"])
    assert graph["metrics"]["total_links"] == len(graph["edges"])
    assert len(graph["nodes"]) > 0


def test_search_wiki_finds_relevant_matches() -> None:
    results = search_wiki(WIKI_DIR, "worktree protocol")
    assert len(results) > 0
    first = results[0]
    assert "path" in first
    assert "title" in first
    assert "score" in first
    assert "snippet" in first
    assert first["score"] > 0


def test_cli_subcommands_subprocess_exit_codes() -> None:
    cli_path = str(ROOT / "scripts" / "llm_wiki.py")
    wiki_arg = ["--wiki-dir", str(WIKI_DIR)]

    # verify-sources
    res_verify = subprocess.run([sys.executable, cli_path, "verify-sources", *wiki_arg], capture_output=True, text=True)
    assert res_verify.returncode == 0
    assert "PASS:" in res_verify.stdout

    # graph --json
    res_graph = subprocess.run([sys.executable, cli_path, "graph", "--json", *wiki_arg], capture_output=True, text=True)
    assert res_graph.returncode == 0
    parsed_graph = json.loads(res_graph.stdout)
    assert "metrics" in parsed_graph

    # search --json
    res_search = subprocess.run([sys.executable, cli_path, "search", "worktree", "--json", *wiki_arg], capture_output=True, text=True)
    assert res_search.returncode == 0
    parsed_search = json.loads(res_search.stdout)
    assert isinstance(parsed_search, list)
    assert len(parsed_search) > 0
