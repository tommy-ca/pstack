"""Pi PStack candidate profile verification; no native Pi runtime required."""
from __future__ import annotations

import copy
import json

import pytest

from scripts.portability_types import PORTABLE_CAPABILITY_UNIVERSE
from scripts.verify_pi_candidate import ROOT, CandidateContractError, bounded_negative_controls, check_contract, from_disk, smoke


def test_candidate_profile_all_17():
    p, m, s = from_disk()
    check_contract(p, m, s)
    assert p["host"] == "pstack:pi"
    assert p["support_state"] == "candidate"
    assert {r["capability"] for r in p["bindings"]} == set(PORTABLE_CAPABILITY_UNIVERSE)
    assert not any(r["verification_status"] == "verified" for r in p["bindings"])


def test_three_interactive_four_research_and_no_auto_install():
    _, m, s = from_disk()
    assert [e["name"] for e in m["engineering"]] == ["pi-subagents", "pi-better-sandbox", "pi-ask-user"]
    assert [e["name"] for e in m["research_addon"]] == ["pi-web-access"]
    assert [e["name"] for e in m["transitional"]] == ["@zenspc/pi-pstack"]
    assert s["skills"] == ["../skills"] and not s.get("packages")


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
    with pytest.raises(CandidateContractError, match="exactly 3"):
        check_contract(p, m, s)


def test_no_auto_installed_extensions():
    p, m, s = copy.deepcopy(from_disk())
    s["packages"] = ["npm:pi-subagents"]
    with pytest.raises(CandidateContractError, match="automatic"):
        check_contract(p, m, s)


def test_bounded_mutants_rejected():
    assert bounded_negative_controls() == 43


def test_normative_profile_json_schema():
    import jsonschema
    import referencing
    schema_dir = ROOT / "schemas/portability"
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
