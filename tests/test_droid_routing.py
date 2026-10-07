#!/usr/bin/env python3
"""Droid advisory skill_order routing regressions (S7).

Reproduces the route_playbook defects on the real profiles/droid.json rows:
the canonical prove-it-works identifier, the annotated droid identifier, the
null-primary declared fallback, native droid-definition and skill-directory
resolution, and the honest no-route report for unknown queries. Also pins the
corrected droid-tools.md plan-tool wording for explicit role tool allowlists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.drivers.droid import DroidDriver, resolve_skill_order


def _profile() -> dict:
    return json.loads((ROOT / "profiles" / "droid.json").read_text(encoding="utf-8"))


def _rows() -> list[dict]:
    return _profile()["skill_order"]


def _row(need: str) -> dict:
    return next(r for r in _rows() if r["need"] == need)


def _offline_driver() -> DroidDriver:
    driver = DroidDriver(ROOT)
    # The routing scenario is an offline profile check (no CLI invocation);
    # pin availability so the verdict mapping is tested without the binary.
    driver.is_available = lambda: (True, "test")
    return driver


# --- VAL-SHIP-005(a): every enumerated row resolves honestly ---


def test_every_skill_order_row_resolves() -> None:
    rows = _rows()
    assert len(rows) == 7, "re-enumerate profiles/droid.json skill_order when the population changes"
    for row in rows:
        route = resolve_skill_order(_profile(), row["need"], ROOT)
        assert route.kind != "no-route", f"row {row['need']!r} does not match its own need"
        if row["primary_pstack"] is None:
            assert route.kind == "declared-fallback", row["need"]
            assert route.target == (row["fallback_builtin"] or row["secondary_user"]), row["need"]
        else:
            assert route.kind in {"skill", "playbook", "droid-definition"}, row["need"]
            assert route.artifact is not None and route.artifact.exists(), row["need"]


def test_default_feature_query_still_routes() -> None:
    route = resolve_skill_order(_profile(), "feature", ROOT)
    assert route.artifact == ROOT / "skills" / "poteto-mode" / "playbooks" / "feature.md"
    assert route.artifact.exists()


# --- VAL-SHIP-005(b): the three reproduced row defects ---


def test_prove_it_works_row_uses_canonical_identifier() -> None:
    row = _row("Prove work is done")
    assert row["primary_pstack"] == "/principle-prove-it-works"
    route = resolve_skill_order(_profile(), row["need"], ROOT)
    assert route.artifact == ROOT / "skills" / "principle-prove-it-works"
    assert route.artifact.is_dir()


def test_read_only_spawn_row_routes_to_native_droid_definition() -> None:
    row = _row("Read-only spawn")
    assert row["primary_pstack"] == "pstack-how-explorer"
    assert "(" not in row["primary_pstack"], "annotation must live in notes, never in the identifier"
    assert "allowlist restricts" in row["notes"]
    route = resolve_skill_order(_profile(), row["need"], ROOT)
    assert route.kind == "droid-definition"
    assert route.artifact == ROOT / "droids" / "pstack-how-explorer.md"
    assert route.artifact.is_file()


def test_null_primary_worktree_row_resolves_declared_fallback() -> None:
    row = _row("Worktree isolation")
    assert row["primary_pstack"] is None
    route = resolve_skill_order(_profile(), row["need"], ROOT)
    assert route.kind == "declared-fallback"
    assert route.target == "session-worktree (droid -w)"


def test_identifiers_carry_no_annotation() -> None:
    for row in _rows():
        primary = row["primary_pstack"]
        if primary is not None:
            assert "(" not in primary and ")" not in primary, row["need"]


# --- VAL-SHIP-005(c): unknown queries never claim a route ---


def test_unknown_playbook_reports_no_route() -> None:
    route = resolve_skill_order(_profile(), "make-coffee", ROOT)
    assert route.kind == "no-route"
    assert route.target is None


def test_unknown_playbook_scenario_never_claims_success() -> None:
    result = _offline_driver().route_playbook("make-coffee", ROOT)
    assert result.verdict == "FAIL"
    assert result.exit_code != 0
    assert "None" not in result.stdout, "must not present None as a routed target"
    assert "skill_order row matches" in result.stdout


def test_substring_queries_do_not_false_match_rows() -> None:
    for query in ("spawn", "worktree", "explore", "route", "plan", "prove"):
        route = resolve_skill_order(_profile(), query, ROOT)
        assert route.kind == "no-route", f"{query!r} false-matched a row by substring"


# --- VAL-SHIP-005(b): route_playbook verdict mapping over the defect rows ---


def test_route_playbook_passes_for_default_and_defect_rows() -> None:
    driver = _offline_driver()
    for query in ("feature", "Prove work is done", "Read-only spawn", "Worktree isolation"):
        result = driver.route_playbook(query, ROOT)
        assert result.verdict == "PASS", (query, result.stdout)
        assert "None" not in result.stdout, query


def test_route_playbook_fails_honestly_for_missing_artifact() -> None:
    broken = dict(_profile())
    broken["skill_order"] = [dict(_row("TDD"), primary_pstack="/no-such-skill")]
    driver = DroidDriver(ROOT)
    driver._profile_data = broken
    driver.is_available = lambda: (True, "test")
    result = driver.route_playbook("TDD", ROOT)
    assert result.verdict == "FAIL"
    assert "no artifact exists" in result.stdout


# --- VAL-SHIP-005(e): plan-tool availability follows the tools allowlist ---


def test_droid_tools_md_plan_tool_claim_is_allowlist_scoped() -> None:
    text = (ROOT / "skills" / "poteto-mode" / "references" / "droid-tools.md").read_text(encoding="utf-8")
    assert "Always included in every droid" not in text
    assert "todo_write" in text
    assert "allowlist" in text
