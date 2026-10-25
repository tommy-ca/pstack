#!/usr/bin/env python3
"""Tests for verdict reduction lattice, proof bar truth, and subprocess bounds.

Verifies:
- Explicit severity lattice: FAIL > BLOCKED > UNTESTED > PASS
- Failure is never masked by BLOCKED
- proof_bar plane and overall reduction truth
- Bounded subprocess execution and timeout handling
- Missing executable handling (BLOCKED, not crash)
- Evidence level preservation
- Adversarial negatives over the shipped stack: fake wire aliases, a shadowed
  `poteto-mode` route, an invented verdict token, a missing model route versus a
  genuine child defect, and an ambient-defined agent that a package may not claim
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
from dataclasses import replace
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.portable_verifier as verify_portable

import scripts.scan_host_boundary as scan_host_boundary

import scripts.prove_omp_vertical_slice as vertical_slice

import scripts.prove_omp_native_package as native_package

from scripts.drivers.omp import OMPDriver, _model_route_error  # noqa: E402
from scripts.drivers.opencode import OpenCodeDriver  # noqa: E402
from scripts.portability_schema import ChildSettlement  # noqa: E402
from scripts.route_resolver import resolve_primary_artifact, resolve_skill_order  # noqa: E402

reduce_verdicts = verify_portable.reduce_verdicts
ScenarioResult = verify_portable.ScenarioResult
PortableVerifier = verify_portable.PortableVerifier


# --- 1. Severity Lattice Invariants ---


def test_lattice_fail_beats_blocked() -> None:
    assert reduce_verdicts(["FAIL", "BLOCKED"]) == "FAIL"
    assert reduce_verdicts(["BLOCKED", "FAIL"]) == "FAIL"
    assert reduce_verdicts(["FAIL", "BLOCKED", "PASS"]) == "FAIL"
    assert reduce_verdicts(["BLOCKED", "PASS", "FAIL", "UNTESTED"]) == "FAIL"


def test_lattice_blocked_beats_untested_and_pass() -> None:
    assert reduce_verdicts(["BLOCKED", "PASS"]) == "BLOCKED"
    assert reduce_verdicts(["BLOCKED", "UNTESTED"]) == "BLOCKED"
    assert reduce_verdicts(["PASS", "BLOCKED"]) == "BLOCKED"


def test_lattice_untested_beats_pass() -> None:
    assert reduce_verdicts(["UNTESTED", "PASS"]) == "UNTESTED"
    assert reduce_verdicts(["PASS", "UNTESTED"]) == "UNTESTED"


def test_lattice_all_pass_is_pass() -> None:
    assert reduce_verdicts(["PASS"]) == "PASS"
    assert reduce_verdicts(["PASS", "PASS", "PASS"]) == "PASS"


def test_lattice_empty_is_untested() -> None:
    assert reduce_verdicts([]) == "UNTESTED"


def test_one_lattice_definition_serves_receipts_drivers_and_derivation() -> None:
    """#473: the receipt validator, the drivers and `check-evidence` reduce through one
    definition. A second copy is what let a declared plane float free of its scenarios."""
    from scripts.portability_schema import reduce_verdicts as schema_reduce
    from scripts.portability_schema import settle_planes as schema_settle

    assert reduce_verdicts is schema_reduce
    assert verify_portable.settle_planes is schema_settle
    assert reduce_verdicts(["LGTM", "PASS"]) == "FAIL"


# --- 2. proof_bar Mixed Outcomes ---


def test_proof_bar_fail_with_blocked_yields_fail(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    # Canonical plane: 1 PASS, 1 FAIL, 1 BLOCKED -> must be FAIL
    verifier.scenarios.extend([
        ScenarioResult("s1", "pass item", "canonical", "echo ok", 0, "ok", "PASS", 0.01),
        ScenarioResult("s2", "fail item", "canonical", "false", 1, "failed", "FAIL", 0.01),
        ScenarioResult("s3", "blocked item", "canonical", "none", 127, "blocked", "BLOCKED", 0.01),
        # Adapter plane: BLOCKED
        ScenarioResult("s4", "adapter blocked", "adapter", "none", 127, "blocked", "BLOCKED", 0.01),
        # Package plane: PASS
        ScenarioResult("s5", "package pass", "package", "echo ok", 0, "ok", "PASS", 0.01),
        # Runtime plane: PASS offline, which is not a live claim -> UNTESTED (#444)
        ScenarioResult("s6", "runtime pass", "runtime", "echo ok", 0, "ok", "PASS", 0.01),
    ])

    receipt = verifier.proof_bar()
    assert receipt.planes["canonical"] == "FAIL"
    assert receipt.planes["adapter"] == "BLOCKED"
    assert receipt.planes["package"] == "PASS"
    assert receipt.planes["runtime"] == "UNTESTED"
    # Overall must be FAIL, NOT BLOCKED!
    assert receipt.overall_verdict == "FAIL"


def test_proof_bar_blocked_with_pass_yields_blocked(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    verifier.scenarios.extend([
        ScenarioResult("s1", "pass item", "canonical", "echo ok", 0, "ok", "PASS", 0.01),
        ScenarioResult("s2", "blocked item", "adapter", "none", 127, "blocked", "BLOCKED", 0.01),
        ScenarioResult("s3", "pass item", "package", "echo ok", 0, "ok", "PASS", 0.01),
        ScenarioResult("s4", "pass item", "runtime", "echo ok", 0, "ok", "PASS", 0.01),
    ])

    receipt = verifier.proof_bar()
    assert receipt.overall_verdict == "BLOCKED"


def test_a_settlement_free_runtime_pass_is_demoted_to_untested(tmp_path: Path) -> None:
    """#444: five passing offline runtime checks are not a spawned child.

    Pins each edge of the gate: the settlement-free runtime PASS drops to UNTESTED
    (the host's overall verdict following it), a live typed settlement keeps the PASS
    — including a driver's raw dict, which is normalized before the gate reads it, and
    a live-labelled row whose child outcome failed is refused again — while FAIL and
    BLOCKED rows still reduce on their own severity.
    """

    def receipt_for(*scenarios: ScenarioResult):
        verifier = PortableVerifier(host="codex", evidence_root=tmp_path)
        verifier.launch()
        verifier.scenarios.extend(scenarios)
        return verifier.proof_bar()

    offline = tuple(
        ScenarioResult(
            f"offline-{i}", "offline runtime check", "runtime", "echo ok", 0, "ok", "PASS", 0.01
        )
        for i in range(5)
    )
    assert receipt_for(*offline).planes["runtime"] == "UNTESTED"
    assert receipt_for(*offline).overall_verdict == "UNTESTED"

    live = ScenarioResult(
        "live-child",
        "live runtime check",
        "runtime",
        "omp rpc child spawn",
        0,
        "child settled",
        "PASS",
        0.01,
        "observed_live",
        {"child_id": "c1", "terminal_outcome": "success", "model": "m", "transport": "rpc", "effective_rpc": "cfg"},
    )
    assert receipt_for(*offline, live).planes["runtime"] == "PASS"

    failed_child = replace(
        live,
        settlement=ChildSettlement(
            child_id="c1", terminal_outcome="error", model="m", transport="rpc", effective_rpc="cfg"
        ),
    )
    assert receipt_for(*offline, failed_child).planes["runtime"] == "UNTESTED"

    assert receipt_for(*offline[:-1], replace(offline[-1], verdict="FAIL")).planes["runtime"] == "FAIL"
    assert (
        receipt_for(*offline[:-1], replace(offline[-1], verdict="BLOCKED")).planes["runtime"] == "BLOCKED"
    )
    assert (
        receipt_for(*offline[:-1], replace(offline[-1], evidence_level="observed_live"))
        .planes["runtime"]
        == "UNTESTED"
    )


# --- 3. Subprocess Bounds, Timeouts, and Missing Binaries ---


def test_subprocess_timeout_produces_fail(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    res = verifier.run_command(
        "test-timeout",
        "Command exceeding timeout",
        "adapter",
        ["python3", "-c", "import time; time.sleep(2)"],
        timeout=0.1,
    )
    assert res.verdict == "FAIL"
    assert res.exit_code == 124
    assert "TIMEOUT" in res.stdout_snippet


def test_missing_binary_produces_blocked(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    res = verifier.run_command(
        "test-missing-bin",
        "Command with non-existent binary",
        "runtime",
        ["non_existent_binary_xyz_12345", "--version"],
    )
    assert res.verdict == "BLOCKED"
    assert res.exit_code == 127
    assert "NOT_FOUND" in res.stdout_snippet


def test_evidence_level_preservation(tmp_path: Path) -> None:
    verifier = PortableVerifier(host="grok", evidence_root=tmp_path)
    verifier.launch()

    res = verifier.run_command(
        "test-level",
        "Command with explicit evidence level",
        "canonical",
        ["echo", "static check"],
        evidence_level="static",
    )
    assert res.evidence_level == "static"

    receipt = verifier.proof_bar()
    scenario = next(s for s in receipt.scenarios if s.id == "test-level")
    assert scenario.evidence_level == "static"


# --- 4. Adversarial Negatives Over the Shipped Stack ---
#
# Each case attacks a shipped guardrail and asserts the refusal. The failure mode
# is a fake PASS: an alias that was never the wire, a shadowed route, an invented
# verdict token, a defect masked as BLOCKED, or an ambient-provided name the
# package credits to itself.


def _driver_with_contract(driver_cls, wire_alias: str):
    """A driver carrying a synthetic subagent contract, with availability forced on.

    The alias check is the shipped static contract; forcing availability keeps the
    negative offline-deterministic instead of skipping on a missing host binary.
    """
    driver = driver_cls(root=ROOT)
    driver._profile_data = {
        "tool_mappings": {"agent_spawn": "task"},
        "runtime_conventions": {
            "wire_aliases": {"task": wire_alias},
            "max_subagent_depth": 1,
        },
    }
    driver.is_available = lambda: (True, "static contract double")
    return driver


@pytest.mark.parametrize("driver_cls", [OMPDriver, OpenCodeDriver])
def test_fake_wire_alias_fails_the_native_subagent_contract(driver_cls, tmp_path: Path) -> None:
    honest = _driver_with_contract(driver_cls, "spawn_subagent").child_spawn(tmp_path)
    assert honest.verdict == "PASS", "the honest alias must pass or the negative is vacuous"

    # A real host primitive is not the portable wire name; the alias is fake.
    faked = _driver_with_contract(driver_cls, "pi_spawn").child_spawn(tmp_path)
    assert faked.verdict == "FAIL"
    assert faked.exit_code == 1


@pytest.mark.parametrize("driver_cls", [OMPDriver, OpenCodeDriver])
def test_a_missing_wire_alias_never_passes_by_default(driver_cls, tmp_path: Path) -> None:
    result = _driver_with_contract(driver_cls, "").child_spawn(tmp_path)
    assert result.verdict == "FAIL"


def test_an_aliased_host_primitive_stays_forbidden_in_shared_surfaces(tmp_path: Path) -> None:
    """A profile cannot legitimize a host primitive by aliasing it: the alias target
    still enters the forbidden vocabulary and is caught in a shared skill."""
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "omp.json").write_text(
        json.dumps({"host": "omp", "runtime_conventions": {"wire_aliases": {"task": "pi_spawn"}}}),
        encoding="utf-8",
    )
    vocab = scan_host_boundary.extract_forbidden_vocabulary(profiles)
    assert vocab["pi_spawn"] == "omp wire target", "the alias target must enter the vocabulary"

    shared = tmp_path / "skills" / "swarm" / "SKILL.md"
    shared.parent.mkdir(parents=True)
    shared.write_text("Start each lane with pi_spawn.\n", encoding="utf-8")
    _, violations, scanned = scan_host_boundary.run_scan(
        tmp_path, profiles, target_dirs=[tmp_path / "skills"]
    )
    assert scanned == 1
    assert [v.token for v in violations] == ["pi_spawn"]


def test_shadowed_poteto_mode_never_wins_the_canonical_route(tmp_path: Path) -> None:
    canonical = tmp_path / "skills" / "poteto-mode"
    (canonical / "playbooks").mkdir(parents=True)
    (canonical / "SKILL.md").write_text("canonical skill\n", encoding="utf-8")
    (canonical / "playbooks" / "orchestrate.md").write_text("canonical\n", encoding="utf-8")
    # Decoys a shadowing artifact could occupy at non-canonical locations.
    (tmp_path / "poteto-mode").mkdir()
    (tmp_path / "poteto-mode" / "SKILL.md").write_text("decoy\n", encoding="utf-8")
    (tmp_path / "orchestrate.md").write_text("decoy\n", encoding="utf-8")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "orchestrate.md").write_text("decoy\n", encoding="utf-8")

    assert resolve_primary_artifact("/poteto-mode", tmp_path) == canonical
    assert resolve_primary_artifact("poteto-mode", tmp_path) == canonical
    assert resolve_primary_artifact("orchestrate", tmp_path) == canonical / "playbooks" / "orchestrate.md"

    # A single row resolves; a second row claiming the same query is ambiguous,
    # so a shadow row cannot silently take the route.
    single = {"skill_order": [{"need": "/poteto-mode", "primary_pstack": "/poteto-mode"}]}
    matched = resolve_skill_order(single, "/poteto-mode", tmp_path)
    assert matched.status == "matched"
    assert matched.artifact == canonical

    shadowed = {
        "skill_order": [
            {"need": "/poteto-mode", "primary_pstack": "/poteto-mode"},
            {"need": "/poteto-mode", "primary_pstack": "/deslop"},
        ]
    }
    result = resolve_skill_order(shadowed, "/poteto-mode", tmp_path)
    assert result.status == "ambiguous"
    assert result.kind == "no-route"
    assert result.artifact is None

    # An identifier escaping the repository is refused outright.
    assert resolve_primary_artifact("/../../etc/passwd", tmp_path) is None
    assert resolve_primary_artifact("pstack:../../etc/passwd", tmp_path) is None


def test_an_invented_verdict_token_never_reduces_to_pass() -> None:
    assert reduce_verdicts(["PASS", "LGTM"]) == "FAIL"
    assert reduce_verdicts(["LGTM"]) == "FAIL"
    assert reduce_verdicts(["PASS", "PASS"]) == "PASS"


def test_a_missing_model_route_is_blocked_while_a_child_defect_is_not_masked() -> None:
    route_error = [
        {"type": "prompt_result", "status": "error", "error": {"message": "no route to provider"}}
    ]
    defect = [
        {
            "type": "prompt_result",
            "status": "error",
            "error": {"message": "model returned malformed JSON while running the tool"},
        }
    ]
    assert _model_route_error(route_error) != ""
    assert _model_route_error(defect) == "", "a genuine child defect must not become BLOCKED"

    blocked = vertical_slice.runtime_row(
        {"settlement": None, "failure": "", "route_error": "no model route", "exit_code": 1},
        "@review",
        0,
    )
    assert blocked.verdict == "BLOCKED"
    failed = vertical_slice.runtime_row(
        {"settlement": None, "failure": "", "route_error": "", "exit_code": 1}, "@review", 0
    )
    assert failed.verdict == "FAIL"


def test_an_ambient_defined_agent_is_flagged_so_the_package_cannot_claim_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ambient = tmp_path / "ambient-agents"
    ambient.mkdir()
    (ambient / "independent-verifier.md").write_text("ambient definition\n", encoding="utf-8")
    monkeypatch.setattr(native_package, "AMBIENT_AGENT_DIRS", (ambient,))

    assert native_package.ambient_defines_agent("independent-verifier") is True
    assert native_package.ambient_defines_agent("packaged-only") is False

    # The package proof credits a user-sourced start only when the ambient tree does
    # not already define the name; the two facts cannot be separated.
    source = inspect.getsource(native_package.spawn_named_agent)
    assert 'and not observation["ambient_defines_it"]' in source
