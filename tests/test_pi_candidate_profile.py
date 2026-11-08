"""Pi PStack candidate profile verification; no native Pi runtime required."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_types import PORTABLE_CAPABILITY_UNIVERSE
from scripts.verify_pi_candidate import CandidateContractError, bounded_negative_controls, check_contract, check_verdict_template, from_disk, smoke


def test_candidate_profile_all_17():
    p, m, s = from_disk()
    check_contract(p, m, s)
    assert p["host"] == "pstack:pi"
    assert p["support_state"] == "candidate"
    assert {r["capability"] for r in p["bindings"]} == set(PORTABLE_CAPABILITY_UNIVERSE)
    assert not any(r["verification_status"] == "verified" for r in p["bindings"])


def test_four_interactive_five_research_and_no_auto_install():
    _, m, s = from_disk()
    assert [e["name"] for e in m["engineering"]] == ["pi-subagents", "pi-better-sandbox", "pi-verdict", "pi-ask-user"]
    assert [e["name"] for e in m["research_addon"]] == ["pi-web-access"]
    assert [e["name"] for e in m["transitional"]] == ["@zenspc/pi-pstack"]
    assert s["skills"] == ["../skills"] and not s.get("packages")
    assert s["subagents"] == {"projectRootResolution":"git-root","agentScanDirs":["../agents"]}


@pytest.mark.parametrize("state", ["mapped","packaged","verified","supported"])
def test_no_premature_host_promotion(state):
    p, m, s = copy.deepcopy(from_disk())
    p["support_state"] = state
    with pytest.raises(CandidateContractError, match="candidate"):
        check_contract(p, m, s)


@pytest.mark.parametrize("capability", PORTABLE_CAPABILITY_UNIVERSE)
def test_false_capability_proof_rejected(capability):
    p, m, s = copy.deepcopy(from_disk())
    next(r for r in p["bindings"] if r["capability"] == capability)["verification_status"] = "verified"
    with pytest.raises(CandidateContractError):
        check_contract(p, m, s)


@pytest.mark.parametrize("key", ["stored_credentials","outside_project"])
def test_sandbox_credentials_fail_closed(key):
    p, m, s = copy.deepcopy(from_disk())
    m["policies"][key] = "write"
    with pytest.raises(CandidateContractError, match="Credential"):
        check_contract(p, m, s)


def test_operator_ask_not_native_hard_gate():
    p, m, s = copy.deepcopy(from_disk())
    next(r for r in p["bindings"] if r["capability"] == "human.gate")["implementation_status"] = "native"
    with pytest.raises(CandidateContractError, match="human.gate"):
        check_contract(p, m, s)


def test_extra_orchestration_engine_rejected():
    p, m, s = copy.deepcopy(from_disk())
    m["engineering"].append({"name":"pi-dynamic-workflows","version":"1.0.0"})
    with pytest.raises(CandidateContractError, match="exactly 4"):
        check_contract(p, m, s)


def test_no_auto_installed_extensions():
    p, m, s = copy.deepcopy(from_disk())
    s["packages"] = ["npm:pi-subagents"]
    with pytest.raises(CandidateContractError, match="automatic"):
        check_contract(p, m, s)


def test_bounded_mutants_rejected():
    assert bounded_negative_controls() == 59


def test_pi_package_manifest_contract():
    from scripts.verify_pi_candidate import load_package, _check_package_contract
    pkg = load_package()
    _check_package_contract(pkg)
    assert pkg["name"] == "pstack"
    assert pkg["private"] is True
    assert "pi-package" in pkg["keywords"]
    assert pkg["pi"]["skills"] == ["./skills"]
    assert pkg["pi"]["subagents"]["agents"] == ["./agents"]
    assert "extensions" not in pkg["pi"]


def test_normative_profile_json_schema():
    import jsonschema
    import referencing
    schema_dir = ROOT / "schemas"
    registry = referencing.Registry()
    for path in schema_dir.glob("*.json"):
        content = json.loads(path.read_text(encoding="utf-8"))
        resource = referencing.Resource.from_contents(content)
        registry = registry.with_resource(path.name, resource)
        registry = registry.with_resource(content.get("$id", path.name), resource)
    schema = json.loads((schema_dir / "profile.schema.json").read_text(encoding="utf-8"))
    errors = list(jsonschema.Draft202012Validator(schema, registry=registry).iter_errors(from_disk()[0]))
    assert not errors, [e.message for e in errors]


def test_pi_smoke_does_not_pretend_runtime_pass(monkeypatch, capsys):
    import scripts.verify_pi_candidate as v
    monkeypatch.setattr(v.shutil,"which",lambda _:None)
    assert smoke() == 2
    assert "BLOCKED" in capsys.readouterr().out


def test_autonomous_authorization_is_not_os_sandbox_or_hard_gate():
    p, m, s = from_disk()
    assert m["active_security_policy"] == "pi-better-sandbox"
    assert m["active_authorization_policy"] == "pi-verdict"
    assert m["authorization"]["child_tool_interception"] == "unverified"
    assert m["authorization"]["classifier_allow_can_authorize_human_gate"] is False
    assert m["authorization"]["audit_covers_all_actions"] is False
    assert next(b for b in p["bindings"] if b["capability"] == "human.gate")["implementation_status"] == "gap"
    check_verdict_template()


@pytest.mark.parametrize("mutation", ["default_on_required", "builtin_deny_floor_required",
    "headless_ask_must_deny", "gate_disable_fails_closed_externally", "requires_os_isolation"])
def test_verdict_policy_flags_fail_closed(mutation):
    p, m, s = copy.deepcopy(from_disk())
    m["authorization"][mutation] = False
    with pytest.raises(CandidateContractError, match="Authorization restriction"):
        check_contract(p, m, s)


@pytest.mark.parametrize("field", ["fallback_rescue_allowed",
    "classifier_allow_can_authorize_human_gate", "audit_covers_all_actions"])
def test_autonomous_classifier_may_not_be_promoted_to_proof(field):
    p, m, s = copy.deepcopy(from_disk())
    m["authorization"][field] = True
    with pytest.raises(CandidateContractError, match="Unproven authorization bypass"):
        check_contract(p, m, s)


def test_subagent_launch_may_not_be_ignored_by_verdict():
    p, m, s = copy.deepcopy(from_disk())
    m["authorization"]["ignore_tools_for_permission_sensitive_actions"] = ["subagent_launch"]
    with pytest.raises(CandidateContractError, match="Permission-sensitive"):
        check_contract(p, m, s)
