"""Model role profile planning, catalog states, host mappings, and pure resolution."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaError

from scripts import model_role_policy
from scripts.model_role_policy import check_model_role_policy
from scripts.model_role_resolver import (
    CompiledPolicy,
    compile_policy,
    model_plan_to_wire,
    plan_role,
    resolve_role_source,
)
from scripts.portability_schema import ValidationError
from tests.model_role_helpers import (
    EXAMPLE,
    PACKAGE,
    ROOT,
    catalog_plan_policy,
    capability_bindings,
    unproven_catalog_policy,
    validate,
)

ROLE_TOKEN_RE = re.compile(r"pstack:([a-z][a-z0-9-]*)")
PLACEHOLDER_RE = re.compile(r"pstack:<[^>]*>")


def test_role_planner_static_only_even_with_complete_fixture() -> None:
    plan = plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="swarm-workers",
                     capabilities=capability_bindings())
    assert plan.status == "PLANNED"
    assert plan.evidence_level == "static-planning-only"
    assert plan.seats[0].model == "model-a"
    assert plan.source == "host-tier"


def test_plan_role_is_pure_and_performs_no_io(monkeypatch) -> None:
    """#437 acceptance: plan_role is side-effect-free with zero I/O, network, or subprocess calls."""
    import builtins
    import socket

    def denied(*args, **kwargs):
        raise AssertionError("I/O is forbidden during pure resolution")

    monkeypatch.setattr(builtins, "open", denied)
    monkeypatch.setattr(subprocess, "run", denied)
    monkeypatch.setattr(subprocess, "Popen", denied)
    monkeypatch.setattr(socket, "socket", denied)

    policy = catalog_plan_policy()
    plan = plan_role(policy, PACKAGE, host="codex", role="swarm-workers", capabilities=capability_bindings())
    assert plan.status == "PLANNED"
    assert plan.seats[0].model == "model-a"
    assert plan.source == "host-tier"


def test_overrides_are_precedent_but_do_not_silently_replace_unknown_slug() -> None:
    policy = catalog_plan_policy()
    plan = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                     explicit="model-b", project="model-c", user="model-a",
                     capabilities=capability_bindings())
    assert (plan.source, plan.seats[0].model) == ("explicit", "model-b")
    project = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                        project="model-c", user="model-a", capabilities=capability_bindings())
    assert (project.source, project.seats[0].model) == ("project", "model-c")
    user = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                     user="model-b", capabilities=capability_bindings())
    assert (user.source, user.seats[0].model) == ("user", "model-b")
    policy["hosts"]["codex"]["role_overrides"] = {"swarm-workers": {"models": ["model-c"]}}
    host_role = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                          capabilities=capability_bindings())
    assert (host_role.source, host_role.seats[0].model) == ("host-role", "model-c")
    invalid = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                        explicit="does-not-exist", capabilities=capability_bindings())
    assert invalid.status == "BLOCKED"
    assert "no silent substitution" in invalid.reasons[0]


@pytest.mark.parametrize("path", ["explicit", "project", "user"])
@pytest.mark.parametrize("duplicates", [["model-a", "model-a"], ["model-a", "model-a", "model-a"]])
def test_duplicate_choice_lists_are_refused_on_every_caller_path(path: str, duplicates: list[str]) -> None:
    with pytest.raises(ValidationError) as excinfo:
        plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="interrogate-reviewers",
                  capabilities=capability_bindings(), **{path: duplicates})
    assert f"{path}: choices must be unique nonempty list" in str(excinfo.value)


@pytest.mark.parametrize("explicit", ["model-a", ["model-a"]])
def test_single_slug_explicit_choice_still_plans(explicit: str | list[str]) -> None:
    plan = plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="swarm-workers",
                     explicit=explicit, capabilities=capability_bindings())
    assert plan.status == "PLANNED"
    assert (plan.source, plan.seats[0].model) == ("explicit", "model-a")


def test_inherit_parent_omits_model_and_does_not_forge_family() -> None:
    p = plan_role(catalog_plan_policy(), PACKAGE, host="codex", role="swarm-workers",
                  explicit="inherit-parent", capabilities=capability_bindings())
    assert p.status == "PLANNED"
    assert p.seats[0].model is None
    assert p.seats[0].family is None


def test_unconfigured_host_and_role_fail_closed() -> None:
    policy = catalog_plan_policy()
    assert plan_role(policy, PACKAGE, host="claude", role="swarm-workers").status == "BLOCKED"
    assert plan_role(policy, PACKAGE, host="codex", role="imaginary-role").status == "BLOCKED"


def test_skill_role_tokens_resolve_to_descriptor_roles_and_agents() -> None:
    role_ids = {role["id"] for role in PACKAGE["roles"]}
    agent_files = {p.stem for p in (ROOT / "agents").glob("*.md")}
    tokens: set[str] = set()
    for path in sorted((ROOT / "skills").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        text = PLACEHOLDER_RE.sub("", text)
        tokens.update(ROLE_TOKEN_RE.findall(text))
    assert tokens, "no role tokens found; scan is broken"
    missing_roles = tokens - role_ids
    missing_agents = tokens - agent_files
    assert not missing_roles, f"tokens without descriptor role: {sorted(missing_roles)}"
    assert not missing_agents, f"tokens without agent file: {sorted(missing_agents)}"


@pytest.mark.parametrize("status", ["stale", "unverified"])
def test_unproven_catalog_can_never_plan_clean(status: str) -> None:
    assert model_role_policy.UNPROVEN_CATALOG_STATUSES == {"stale", "unverified"}
    plan = plan_role(unproven_catalog_policy(status), PACKAGE, host="codex",
                     role="swarm-workers", capabilities=capability_bindings())
    assert plan.status == "DEGRADED"
    assert len(plan.seats) == 1 and plan.seats[0].model == "model-a"
    assert plan.reasons and "not live evidence" in plan.reasons[0]
    assert status in plan.reasons[0]
    plan_schema = json.loads((ROOT / "schemas/portability/model-plan.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(plan_schema).validate(model_plan_to_wire(plan))


def test_static_only_catalog_still_plans_and_stale_flips_it() -> None:
    policy = catalog_plan_policy()
    static_only = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                            capabilities=capability_bindings())
    assert static_only.status == "PLANNED"
    assert static_only.reasons == ()

    policy["hosts"]["codex"]["verification_status"] = "stale"
    stale = plan_role(policy, PACKAGE, host="codex", role="swarm-workers",
                      capabilities=capability_bindings())
    assert stale.status == "DEGRADED"
    assert (stale.seats, stale.source) == (static_only.seats, static_only.source)


def test_unproven_catalog_gate_cannot_upgrade_a_blocker() -> None:
    plan = plan_role(unproven_catalog_policy("stale"), PACKAGE, host="codex",
                     role="swarm-workers", explicit="not-a-real-model",
                     capabilities=capability_bindings())
    assert plan.status == "BLOCKED"
    assert "no silent substitution" in plan.reasons[0]


def test_unproven_catalog_may_not_carry_observation_or_evidence_refs() -> None:
    live_looking = unproven_catalog_policy("unverified")
    live_looking["hosts"]["codex"]["catalog_observation"] = {
        "host_version": "test-fixture-only", "observed_at": "2026-10-15T00:00:00Z",
        "receipt": ".audit/test-fixture-no-runtime-claim.json",
    }
    with pytest.raises(ValidationError, match="not live evidence"):
        check_model_role_policy(live_looking, PACKAGE)

    referenced = unproven_catalog_policy("stale")
    referenced["hosts"]["codex"]["model_catalog"][0]["evidence_ref"] = ".audit/test-fixture.json"
    with pytest.raises(ValidationError, match="not live evidence"):
        check_model_role_policy(referenced, PACKAGE)

    check_model_role_policy(unproven_catalog_policy("stale"), PACKAGE)


def test_example_policy_covers_every_declared_host_with_empty_catalogs() -> None:
    declared = PACKAGE["host_targets"]
    tiers = {role["default_model_role"] for role in PACKAGE["roles"]}
    assert len(declared) == 6
    assert sorted(EXAMPLE["hosts"]) == sorted(declared)
    for host, config in EXAMPLE["hosts"].items():
        assert config["model_catalog"] == [], f"{host} must not invent unobserved model IDs"
        assert set(config["tier_defaults"]) == tiers, f"{host} does not map every declared tier"
    validate(EXAMPLE)


def test_every_declared_host_plans_without_an_unmapped_host_verdict() -> None:
    for host in PACKAGE["host_targets"]:
        plan = plan_role(EXAMPLE, PACKAGE, host=host, role="independent-verifier")
        assert plan.status != "BLOCKED", f"{host}: {plan.reasons}"
        assert plan.evidence_level == "static-planning-only"
        assert all(seat.model is None for seat in plan.seats), "no model ID may be invented"


def load_project_package_module():
    import scripts.package_projection as module
    return module


def test_project_package_check_surfaces_the_planner_verdict(capsys) -> None:
    project_package = load_project_package_module()
    desc, _ = project_package.load_package_descriptor()
    assert project_package.check_model_role_plan(desc) is True
    out = capsys.readouterr().out
    assert out.count(project_package.PLAN_PROBE_ROLE) == len(PACKAGE["host_targets"])
    for role in project_package.PLAN_PROBE_ROLES:
        assert out.count(role) == len(PACKAGE["host_targets"])
    assert "BLOCKED" not in out
    assert "static-planning-only" in out


@pytest.mark.parametrize(
    "tier_to_drop,expected_blocked_role",
    [
        ("fast-worker", "how-explorer"),
        ("strong-judgment", "how-explainer"),
        ("panel", "architect-runners"),
        ("strongest", "independent-verifier"),
    ],
)
def test_check_model_role_plan_fails_closed_when_tier_dropped(
    monkeypatch, tmp_path, capsys, tier_to_drop, expected_blocked_role
) -> None:
    project_package = load_project_package_module()
    desc, _ = project_package.load_package_descriptor()

    policy_path = ROOT / "examples/portability/model-role-policy.example.json"
    policy_data = json.loads(policy_path.read_text(encoding="utf-8"))

    del policy_data["hosts"]["codex"]["tier_defaults"][tier_to_drop]
    mutant_policy_path = tmp_path / "model-role-policy.json"
    mutant_policy_path.write_text(json.dumps(policy_data), encoding="utf-8")

    monkeypatch.setattr(project_package, "MODEL_ROLE_POLICY", mutant_policy_path)
    assert project_package.check_model_role_plan(desc) is False
    out = capsys.readouterr().out
    assert f"BLOCKED: codex cannot plan {expected_blocked_role}" in out


def test_plan_role_has_exactly_one_production_caller() -> None:
    importers = set()
    for path in (ROOT / "scripts").rglob("*.py"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"\bplan_role\b", line):
                importers.add(path.name)
                break
    assert importers == {"model_role_resolver.py", "package_projection.py"}


def test_reference_fork_ledger_records_completed_source_review() -> None:
    from collections import Counter
    manifest = json.loads(
        (ROOT / "docs/research/pstack-claude-forks-2026-10-15.json").read_text(encoding="utf-8")
    )
    assert manifest["source_sha"] == "94f5ce95abe8a9dec976967d79941f631cf477cd"
    contract = manifest["source_review_contract"]["counterpart_sources"]
    assert contract["reference"]["pin"] == "94f5ce95abe8a9dec976967d79941f631cf477cd"
    assert contract["canonical"]["pin"] == "1dcc2bacde73ddd284803b7af28164d0436198fc"
    assert contract["target"]["pin"] == "3f4cd124f27cab90865df79d18d376e2f4335b2c"
    rows = manifest["entries"]
    assert len(rows) == 48
    assert len({row["path"] for row in rows}) == len(rows)
    assert sum(row["reference_kind"] == "policy" for row in rows) == 40
    assert sum(row["reference_kind"] == "port-feature" for row in rows) == 8
    assert all(row["review_state"] == "source-reviewed" for row in rows)
    assert all(row["why"].strip() for row in rows)
    assert all(row["upstream"] == "not-proposed" for row in rows)
    assert Counter(r["proposed_adoption"] for r in rows) == {"adapt": 36, "preserve": 1, "exclude": 2, "gap": 7, "policy-fork": 2}
    assert Counter(r["proposed_adoption"] for r in rows) == dict(manifest["review_counts"])
    assert not any(row["proposed_adoption"] == "unclassified" for row in rows)
    per_row = [row for row in rows if "license_disposition" in row]
    assert {row["path"] for row in per_row} == {
        "plugins/pstack/skills/thermo-nuclear-code-quality-review/SKILL.md",
        "plugins/pstack/skills/poteto-mode/playbooks/orchestrate.md",
    }
    assert all(row["proposed_adoption"] == "policy-fork" for row in per_row)
    assert all(row["license_disposition"]["scope"] == "per-row" for row in per_row)
    assert all(set(r["source_review"]) >= {"counterpart_blobs", "attribution_profile", "semantic_delta", "check_or_gap"} for r in rows)
    absent = manifest["source_review_contract"]["absent_counterparts"]
    assert [(a["side"], a["path"]) for a in absent] == [("target", "skills/poteto-mode/scripts/check-plan.test.ts")]

    hex_pattern = re.compile(r"^[0-9a-f]{40}$")
    absent_target_paths = {a["path"] for a in absent if a.get("side") == "target"}
    for row in rows:
        blobs = row["source_review"]["counterpart_blobs"]
        assert hex_pattern.match(blobs["reference"]), f"invalid reference blob {blobs['reference']}"
        assert hex_pattern.match(blobs["canonical"]), f"invalid canonical blob {blobs['canonical']}"
        rel_target = row["path"].removeprefix("plugins/pstack/")
        if rel_target in absent_target_paths:
            assert blobs["target"] is None, f"expected absent target blob for {row['path']}"
        else:
            assert hex_pattern.match(blobs["target"]), f"invalid target blob {blobs['target']}"
            is_shallow = subprocess.run(
                ["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT, capture_output=True, text=True
            ).stdout.strip() == "true"
            if not is_shallow:
                res = subprocess.run(["git", "cat-file", "-e", blobs["target"]], cwd=ROOT)
                assert res.returncode == 0, f"target blob {blobs['target']} missing from git object store"

    scope = manifest["review_scope"]
    assert scope["approval"] == "not granted"
    assert scope["implementation"] == "not authorized or claimed"
    assert scope["runtime"] == "not verified"
    assert scope["independent_acceptance"].startswith("completed;")
    assert "resolved on mainline" in scope["watcher_gap"]


def test_cross_harness_promotion_gate_and_evidence_contract() -> None:
    from referencing import Registry, Resource
    schemas_dir = ROOT / "schemas/portability"
    registry = Registry().with_resources(
        [
            (
                (schema := json.loads(path.read_text(encoding="utf-8")))["$id"],
                Resource.from_contents(schema),
            )
            for path in sorted(schemas_dir.glob("*.json"))
        ]
    )

    profile_schema = json.loads((schemas_dir / "profile.schema.json").read_text(encoding="utf-8"))
    profile_validator = Draft202012Validator(profile_schema, registry=registry)

    declared_hosts = ["grok", "codex", "omp", "opencode", "antigravity", "droid"]
    candidate_hosts = ["claude", "copilot"]
    from scripts.portability_schema import Binding, Evidence, HarnessProfile

    for host in candidate_hosts:
        p_path = ROOT / "profiles" / f"{host}.json"
        assert p_path.is_file(), f"missing profile for {host}"
        data = json.loads(p_path.read_text(encoding="utf-8"))
        profile_validator.validate(data)
        assert data["support_state"] == "candidate"

    for host in declared_hosts + candidate_hosts:
        p_path = ROOT / "profiles" / f"{host}.json"
        assert p_path.is_file(), f"missing profile for {host}"
        data = json.loads(p_path.read_text(encoding="utf-8"))
        bindings = [Binding(**b) for b in data.get("bindings", [])]
        evidence = [Evidence(**e) for e in data.get("evidence_ledger", [])]
        profile = HarnessProfile(
            host=data["host"],
            support_state=data["support_state"],
            bindings=bindings,
            skills_dir=data.get("skills_dir"),
            plugins_dir=data.get("plugins_dir"),
            plugin_manifest=data.get("plugin_manifest"),
            evidence_ledger=evidence,
            tool_mappings=data.get("tool_mappings"),
            skill_order=data.get("skill_order"),
            runtime_conventions=data.get("runtime_conventions"),
        )
        profile.validate()

    for host in ("grok", "codex", "opencode", "antigravity"):
        receipt_file = ROOT / f".audit/evidence/{host}-receipt.json"
        data = json.loads(receipt_file.read_text(encoding="utf-8"))
        assert data["planes"]["runtime"] == "UNTESTED", f"{host} must not claim unproven live runtime"
        assert data["overall_verdict"] == "UNTESTED", f"{host} overall verdict must follow untested runtime"

    adr_file = ROOT / "adr/0021-harness-neutral-model-role-policy.md"
    assert adr_file.is_file(), "ADR-0021 missing"
    adr_text = adr_file.read_text(encoding="utf-8")
    assert "Status: **accepted**" in adr_text, "ADR-0021 must be accepted upon gate 445 fulfillment"

    change_adr = ROOT / "openspec/changes/2026-10-15-harness-neutral-role-policy/adr.md"
    assert "Status: accepted" in change_adr.read_text(encoding="utf-8")

    change_design = ROOT / "openspec/changes/2026-10-15-harness-neutral-role-policy/design.md"
    assert "Status: Accepted" in change_design.read_text(encoding="utf-8")
    assert "## Cross-harness contract promotion decision and evidence gate (#445)" in change_design.read_text(encoding="utf-8")

    tasks_file = ROOT / "openspec/changes/2026-10-15-harness-neutral-role-policy/tasks.md"
    tasks_text = tasks_file.read_text(encoding="utf-8")
    for g in range(9):
        assert f"- [x] **G{g}**" in tasks_text, f"Gate G{g} must be marked completed in tasks.md"
    assert "- [ ] **G" not in tasks_text, "no uncompleted G-gates may remain"

    plan_schema = json.loads((ROOT / "schemas/portability/model-plan.schema.json").read_text(encoding="utf-8"))
    wire_validator = Draft202012Validator(plan_schema)
    fake_wire = {
        "status": "VERIFIED",
        "evidence_level": "runtime-verified",
        "source": "explicit",
        "seats": [],
        "reasons": [],
    }
    with pytest.raises(JsonSchemaError):
        wire_validator.validate(fake_wire)


def test_resolve_role_source_precedence_and_setup_parity() -> None:
    from scripts.setup_pstack import effective_role_precedence

    host_config = {
        "tier_defaults": {
            "strongest": ["host-tier-model"],
        },
        "fallback": "fail-closed",
    }
    role_cfg = {
        "models": ["host-role-model"],
    }

    choices, src = resolve_role_source("independent-verifier", tier="strongest", host_config=host_config, role_cfg={})
    assert choices == ["host-tier-model"] and src == "host-tier"
    assert effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg={}) == (choices, src)

    choices, src = resolve_role_source("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg)
    assert choices == ["host-role-model"] and src == "host-role"
    assert effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg) == (choices, src)

    choices, src = resolve_role_source("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"])
    assert choices == ["user-custom-model"] and src == "user"
    assert effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"]) == (choices, src)

    choices, src = resolve_role_source("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"], project=["project-model"])
    assert choices == ["project-model"] and src == "project"
    assert effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"], project=["project-model"]) == (choices, src)

    choices, src = resolve_role_source("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"], project=["project-model"], explicit="cli-model")
    assert choices == ["cli-model"] and src == "explicit"
    assert effective_role_precedence("independent-verifier", tier="strongest", host_config=host_config, role_cfg=role_cfg, user=["user-custom-model"], project=["project-model"], explicit="cli-model") == (choices, src)

    inherit_cfg = {"tier_defaults": {}, "fallback": "inherit-parent"}
    choices, src = resolve_role_source("independent-verifier", tier="strongest", host_config=inherit_cfg, role_cfg={})
    assert choices == ["inherit-parent"] and src == "inherit-parent"
    assert effective_role_precedence("independent-verifier", tier="strongest", host_config=inherit_cfg, role_cfg={}) == (choices, src)

    fail_cfg = {"tier_defaults": {}, "fallback": "fail-closed"}
    choices, src = resolve_role_source("independent-verifier", tier="strongest", host_config=fail_cfg, role_cfg={})
    assert choices == [] and src == "fail-closed"
    assert effective_role_precedence("independent-verifier", tier="strongest", host_config=fail_cfg, role_cfg={}) == (choices, src)

    with pytest.raises(ValidationError, match="choices must be unique"):
        resolve_role_source("independent-verifier", tier="strongest", host_config=host_config, role_cfg={}, explicit=["dup", "dup"])


def test_compile_policy_and_decoupled_planner_validation(monkeypatch) -> None:
    policy = catalog_plan_policy()
    compiled = compile_policy(policy, PACKAGE)
    assert isinstance(compiled, CompiledPolicy)
    assert compiled.policy == policy
    assert compiled.descriptor == PACKAGE

    call_count = 0
    orig_check = check_model_role_policy

    def counting_check(pol, desc):
        nonlocal call_count
        call_count += 1
        return orig_check(pol, desc)

    import scripts.model_role_resolver as resolver_mod
    monkeypatch.setattr(resolver_mod, "check_model_role_policy", counting_check)

    plan1 = plan_role(compiled, host="codex", role="swarm-workers", capabilities=capability_bindings())
    assert plan1.status == "PLANNED"
    assert call_count == 0

    plan2 = plan_role(policy, PACKAGE, host="codex", role="swarm-workers", capabilities=capability_bindings(), validate_policy=False)
    assert plan2.status == "PLANNED"
    assert call_count == 0

    plan3 = plan_role(policy, PACKAGE, host="codex", role="swarm-workers", capabilities=capability_bindings())
    assert plan3.status == "PLANNED"
    assert call_count == 1

    bad_policy = copy.deepcopy(policy)
    bad_policy["version"] = 999
    with pytest.raises(ValidationError, match="model-role policy violates its schema"):
        compile_policy(bad_policy, PACKAGE)
