#!/usr/bin/env python3
"""Comprehensive test suite for pure typed route resolver across six hosts.

Verifies:
- Exact matching invariants (never substring)
- Canonical skill resolution (/principle-prove-it-works)
- Agent identifier resolution (pstack:how-explorer -> agents/how-explorer.md)
- Droid definition resolution (pstack-how-explorer -> droids/pstack-how-explorer.md)
- Three-tier declared fallback resolution
- Unknown and empty query handling
- Ambiguity detection
- Path traversal defense
- Exhaustive six-host profile resolution (zero unmapped primaries)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.route_resolver import RouteResolution, resolve_skill_order, resolve_primary_artifact


def load_profile(host: str) -> dict:
    return json.loads((ROOT / "profiles" / f"{host}.json").read_text(encoding="utf-8"))


# --- 1. Substring Rejection & Exact Matching ---


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity", "droid"])
def test_substring_queries_do_not_match(host: str) -> None:
    profile = load_profile(host)
    # "spawn" must not match "Read-only spawn"
    res = resolve_skill_order(profile, "spawn", ROOT)
    assert not res.is_matched
    assert res.kind == "no-route"

    # "work" must not match "Prove work is done" or "Worktree isolation"
    res = resolve_skill_order(profile, "work", ROOT)
    assert not res.is_matched
    assert res.kind == "no-route"

    # "playbook" must not match "playbooks/*.md"
    res = resolve_skill_order(profile, "playbook", ROOT)
    assert not res.is_matched
    assert res.kind == "no-route"


# --- 2. Case Normalization & Stem Matching ---


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity", "droid"])
def test_case_insensitive_and_stem_matching(host: str) -> None:
    profile = load_profile(host)
    for q in ["feature", "Feature", "FEATURE"]:
        res = resolve_skill_order(profile, q, ROOT)
        assert res.is_matched, f"Failed for {q} on {host}"
        assert res.kind == "playbook"
        assert res.artifact is not None
        assert res.artifact.exists()
        assert res.artifact.name == "feature.md"


# --- 3. Canonical Principle Prove-It-Works Resolution ---


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity", "droid"])
def test_prove_it_works_resolves_canonical_skill(host: str) -> None:
    profile = load_profile(host)
    res = resolve_skill_order(profile, "Prove work is done", ROOT)
    assert res.is_matched, f"Failed for {host}"
    assert res.kind == "skill"
    assert res.target == "/principle-prove-it-works"
    assert res.artifact is not None
    assert res.artifact.exists()
    assert res.artifact.is_dir()
    assert (res.artifact / "SKILL.md").exists()


# --- 4. Read-Only Spawn / Agent Resolution ---


def test_grok_and_codex_read_only_spawn_resolves_agent() -> None:
    for host in ["grok", "codex"]:
        profile = load_profile(host)
        res = resolve_skill_order(profile, "Read-only spawn", ROOT)
        assert res.is_matched, f"Failed on {host}"
        assert res.kind == "agent"
        assert res.target == "pstack:how-explorer"
        assert res.artifact == ROOT / "agents" / "how-explorer.md"
        assert res.artifact.is_file()


def test_droid_read_only_spawn_resolves_droid_definition() -> None:
    profile = load_profile("droid")
    res = resolve_skill_order(profile, "Read-only spawn", ROOT)
    assert res.is_matched
    assert res.kind == "droid-definition"
    assert res.target == "pstack-how-explorer"
    assert res.artifact == ROOT / "droids" / "pstack-how-explorer.md"
    assert res.artifact.is_file()


# --- 5. Declared Fallbacks (Null Primaries) ---


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity", "droid"])
def test_null_primaries_resolve_declared_fallbacks(host: str) -> None:
    profile = load_profile(host)
    for row in profile.get("skill_order", []):
        if row.get("primary_pstack") is None:
            res = resolve_skill_order(profile, row["need"], ROOT)
            assert res.is_matched
            assert res.kind == "declared-fallback"
            expected = row.get("secondary_user") or row.get("fallback_builtin")
            assert res.target == expected
            assert res.artifact is None


# --- 6. Exhaustive Six-Host Profile Resolution ---


@pytest.mark.parametrize("host", ["grok", "codex", "omp", "opencode", "antigravity", "droid"])
def test_all_profile_skill_order_rows_resolve_to_existing_artifacts(host: str) -> None:
    profile = load_profile(host)
    rows = profile.get("skill_order", [])
    assert len(rows) > 0, f"Profile {host} has empty skill_order"

    for row in rows:
        need = row["need"]
        res = resolve_skill_order(profile, need, ROOT)
        assert res.is_matched, f"Row '{need}' in {host} failed to match itself"
        if row.get("primary_pstack") is not None:
            assert res.artifact is not None, f"Row '{need}' ({res.target}) in {host} has None artifact"
            assert res.artifact.exists(), f"Row '{need}' target '{res.target}' artifact '{res.artifact}' does not exist on disk"


# --- 7. Ambiguity, Empty and Traversal Defenses ---


def test_empty_query_returns_unmatched() -> None:
    profile = load_profile("grok")
    for q in ["", "   ", "\t\n"]:
        res = resolve_skill_order(profile, q, ROOT)
        assert not res.is_matched
        assert res.status == "unmatched"
        assert res.kind == "no-route"


def test_ambiguous_query_detection() -> None:
    mock_profile = {
        "skill_order": [
            {"need": "Duplicate test query", "primary_pstack": "playbooks/feature.md"},
            {"need": "Duplicate test query", "primary_pstack": "playbooks/bug-fix.md"},
        ]
    }
    res = resolve_skill_order(mock_profile, "Duplicate test query", ROOT)
    assert res.status == "ambiguous"
    assert res.kind == "no-route"
    assert len(res.matched_rows) == 2


def test_path_traversal_defense() -> None:
    profile = load_profile("grok")
    res = resolve_skill_order(profile, "../../etc/passwd", ROOT)
    assert not res.is_matched
    assert res.kind == "no-route"

    # Direct helper defense
    art = resolve_primary_artifact("../../etc/passwd", ROOT)
    assert art is None or not art.is_file() or not str(art.resolve()).startswith("/etc")
