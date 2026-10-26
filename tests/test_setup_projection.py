"""Setup projection per host (#703): the entry skill is host-neutral and each host owns its surface."""

from __future__ import annotations


import json
from dataclasses import asdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from scripts.host_identity import BUILTIN_HOSTS
from scripts.model_role_policy import check_model_role_policy
from scripts.model_role_resolver import plan_role
from scripts.portability_types import SetupProjection, ValidationError
from scripts.setup_pstack import PACKAGE_JSON, resolve_setup_projection
from tests.model_role_helpers import (
    available_catalog_policy,
    invalid_catalog_policy,
    missing_catalog_policy,
)

ENTRY_SKILL = ROOT / "skills" / "setup-pstack" / "SKILL.md"
GROK_SKILL = ROOT / "skills" / "setup-pstack-grok" / "SKILL.md"


def _profile(host: str) -> dict:
    return json.loads((ROOT / "profiles" / f"{host}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("host", BUILTIN_HOSTS)
def test_every_builtin_profile_resolves_against_the_tree_it_ships_with(host: str) -> None:
    """A shipped profile whose skill or repo catalog is missing fails here, not silently.

    Deleting a guide, moving a projected catalog or dropping a setup skill is a
    repository defect the resolver names; the test exists so the defect is caught
    by a suite rather than by whoever next runs `/setup-pstack`.
    """
    projection = resolve_setup_projection(host)
    assert projection is not None, host
    projection.validate()


def test_host_catalog_hosts_name_a_host_specific_file_that_exists() -> None:
    """Two hosts pointing at one catalog is the second registry this design forbids."""
    declared: dict[Path, str] = {}
    for host in BUILTIN_HOSTS:
        projection = resolve_setup_projection(host)
        assert projection is not None
        if projection.source != "host-catalog":
            continue
        catalog = ROOT / str(projection.catalog)
        assert catalog.is_file(), f"{host} declares a catalog that is not projected: {catalog}"
        assert catalog not in declared, f"{host} and {declared[catalog]} share one catalog"
        declared[catalog] = host
    assert declared, "no host-catalog host: the invariant would pass vacuously"


def test_inherit_hosts_inherit_the_parent_model_instead_of_overriding_it() -> None:
    """`inherit` is a claim about the spawn call, so the profile must agree with it."""
    checked = 0
    for host in BUILTIN_HOSTS:
        projection = resolve_setup_projection(host)
        assert projection is not None
        if projection.source != "inherit":
            continue
        conventions = _profile(host).get("runtime_conventions", {})
        assert conventions.get("default_model") == "inherit", host
        assert "model" in conventions.get("forbidden_spawn_fields", []), host
        checked += 1
    assert checked, "no inherit host: the invariant would pass vacuously"


def test_host_cli_hosts_name_a_setup_skill_that_exists() -> None:
    checked = 0
    for host in BUILTIN_HOSTS:
        projection = resolve_setup_projection(host)
        assert projection is not None
        if projection.source != "host-cli":
            continue
        assert (ROOT / "skills" / str(projection.skill) / "SKILL.md").is_file(), host
        checked += 1
    assert checked, "no host-cli host: the invariant would pass vacuously"


def test_grok_is_the_one_cli_probing_surface() -> None:
    """The one host whose setup writes host-home config, pinned explicitly."""
    assert resolve_setup_projection("grok") == SetupProjection(
        source="host-cli",
        effort="live-enum",
        skill="setup-pstack-grok",
        catalog="~/.grok/pstack-models.toml",
        overlay="~/.grok/roles",
    )


@pytest.mark.parametrize("host", ["codex", "antigravity", "droid", "omp", "opencode"])
def test_non_grok_projection_carries_no_grok_path(host: str) -> None:
    """Negative control: a non-Grok host must never inherit Grok's write targets."""
    projection = resolve_setup_projection(host)
    assert projection is not None
    rendered = repr(asdict(projection))
    assert "~/.grok" not in rendered
    assert "grok" not in rendered
    assert "pstack-models.toml" not in rendered


def test_inherit_parent_projection_declares_no_write_target() -> None:
    projection = resolve_setup_projection("droid")
    assert projection is not None
    assert projection.source == "inherit"
    assert projection.effort == "inherit-parent"
    assert projection.catalog is None and projection.overlay is None and projection.skill is None


def test_candidate_hosts_declare_a_passive_surface_or_none() -> None:
    """A candidate may declare `inherit`/`none`, never a surface it has no evidence for."""
    droid = resolve_setup_projection("droid")
    assert droid is not None and droid.source == "inherit"
    # A declared alias and a namespaced id with no setup block are both GAPs.
    assert resolve_setup_projection("claude") is None
    assert resolve_setup_projection("github:copilot") is None


def test_entry_skill_names_no_host_path_or_slug() -> None:
    """The shared entry must stay host-neutral; the Grok body lives in its own skill."""
    text = ENTRY_SKILL.read_text(encoding="utf-8")
    for token in ("~/.grok", "grok-4.6", "pstack-models.toml", "Grok Build", ".grok/"):
        assert token not in text, token
    assert "profiles/<host>.json#setup" in text
    assert "skills/<setup.skill>/SKILL.md" in text
    assert "Never substitute one host's setup for another." in text
    assert "pstack.package.json#roles" in text
    assert "scripts/model_role_resolver.py" in text


def test_grok_skill_owns_the_adapter_body() -> None:
    text = GROK_SKILL.read_text(encoding="utf-8")
    assert text.startswith("---\nname: setup-pstack-grok\n")
    assert "../setup-pstack/SKILL.md" in text
    for reference in ("defaults.toml", "effort-ladder.md", "resolve-effort.md", "resolve-model.md"):
        path = GROK_SKILL.parent / "references" / reference
        assert path.is_file(), f"deleted guide: {path.relative_to(ROOT)}"
    assert "use one of:" in text


def test_entry_skill_passes_the_host_boundary_scan() -> None:
    import scripts.scan_host_boundary as module

    vocab = module.extract_forbidden_vocabulary(ROOT / "profiles")
    assert module.scan_file(ENTRY_SKILL, ROOT, vocab) == []


@pytest.mark.parametrize(
    "block",
    [
        {"source": "inherit", "effort": "inherit-parent", "overlay": "~/.some/roles"},
        {"source": "host-cli", "effort": "live-enum", "catalog": "x.json"},
        {"source": "host-cli", "effort": "none", "skill": "s", "catalog": "x.json"},
        {"source": "host-catalog", "effort": "none"},
        {"source": "none", "effort": "inherit-parent"},
        {"source": "bogus", "effort": "none"},
        {"source": "none", "effort": "bogus"},
        {"source": "inherit", "effort": "inherit-parent", "skill": "setup-pstack-grok"},
    ],
)
def test_setup_projection_rejects_incoherent_shapes(block: dict) -> None:
    with pytest.raises(ValidationError):
        SetupProjection(**block).validate()


def _write_profile(directory: Path, host: str, support_state: str, setup: object) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{host}.json").write_text(
        json.dumps(
            {
                "host": host,
                "support_state": support_state,
                "plugin_manifest": ".x-plugin/plugin.json",
                "skills_dir": ".x/skills",
                "bindings": [],
                "setup": setup,
            }
        ),
        encoding="utf-8",
    )


def test_resolver_requires_a_declared_skill_dir(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "profiles",
        "acme:alpha",
        "mapped",
        {"source": "host-cli", "effort": "live-enum", "skill": "no-such-skill", "catalog": "~/.acme/models.toml"},
    )
    with pytest.raises(ValidationError, match="no skills/no-such-skill/SKILL.md"):
        resolve_setup_projection("acme:alpha", tmp_path / "profiles", tmp_path)


def test_resolver_requires_a_projected_repo_catalog(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "profiles",
        "acme:beta",
        "mapped",
        {"source": "host-catalog", "effort": "none", "catalog": ".acme-plugin/models.json"},
    )
    with pytest.raises(ValidationError, match="not projected"):
        resolve_setup_projection("acme:beta", tmp_path / "profiles", tmp_path)


def test_resolver_tolerates_a_host_home_catalog(tmp_path: Path) -> None:
    """Only a `~` write target is late-bound; a repo artifact must already exist."""
    _write_profile(
        tmp_path / "profiles",
        "acme:gamma",
        "mapped",
        {"source": "host-cli", "effort": "live-enum", "skill": "gamma", "catalog": "~/.acme/models.toml"},
    )
    (tmp_path / "skills" / "gamma").mkdir(parents=True)
    (tmp_path / "skills" / "gamma" / "SKILL.md").write_text("---\nname: gamma\n---\n", encoding="utf-8")
    projection = resolve_setup_projection("acme:gamma", tmp_path / "profiles", tmp_path)
    assert projection is not None and projection.catalog == "~/.acme/models.toml"


def test_candidate_host_cannot_declare_a_cli_probe(tmp_path: Path) -> None:
    _write_profile(
        tmp_path / "profiles",
        "acme:delta",
        "candidate",
        {"source": "host-cli", "effort": "live-enum", "skill": "s", "catalog": "~/.acme/models.toml"},
    )
    with pytest.raises(ValidationError, match="Candidate host"):
        resolve_setup_projection("acme:delta", tmp_path / "profiles", tmp_path)

    _write_profile(
        tmp_path / "profiles",
        "acme:delta",
        "candidate",
        {"source": "inherit", "effort": "inherit-parent"},
    )
    projection = resolve_setup_projection("acme:delta", tmp_path / "profiles", tmp_path)
    assert projection is not None and projection.effort == "inherit-parent"


def test_the_host_argument_is_the_declared_id_not_a_filename_stem() -> None:
    """`profiles/copilot.json` declares `github:copilot`, so the stem is not an id."""
    with pytest.raises(ValidationError, match="Invalid host id"):
        resolve_setup_projection("copilot")
    assert resolve_setup_projection("github:copilot") is None


@pytest.mark.parametrize("host", ["../profiles/grok", "profiles/grok", "grok/../codex", "", "grok\n"])
def test_host_argument_cannot_address_a_path(host: str) -> None:
    """A path, a stem or a trailing newline must never select another host's targets."""
    with pytest.raises(ValidationError, match="Invalid host id"):
        resolve_setup_projection(host)


def test_unknown_host_is_not_a_silent_default() -> None:
    with pytest.raises(ValidationError, match="Invalid host id"):
        resolve_setup_projection("no-such-host")
    with pytest.raises(ValidationError, match="No harness profile"):
        resolve_setup_projection("acme:absent")


def test_boundary_failures_are_validation_errors(tmp_path: Path) -> None:
    """One exception type at the profile boundary, whatever the malformed shape."""
    _write_profile(
        tmp_path / "profiles",
        "acme:typo",
        "mapped",
        {"source": "none", "effort": "none", "overlay_dir": "~/.acme/roles"},
    )
    with pytest.raises(ValidationError, match="does not match SetupProjection"):
        resolve_setup_projection("acme:typo", tmp_path / "profiles", tmp_path)

    _write_profile(tmp_path / "profiles", "acme:shape", "mapped", "host-cli")
    with pytest.raises(ValidationError, match="must be an object"):
        resolve_setup_projection("acme:shape", tmp_path / "profiles", tmp_path)

    (tmp_path / "profiles" / "broken.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValidationError, match="Unreadable harness profile"):
        resolve_setup_projection("acme:anything", tmp_path / "profiles", tmp_path)


def test_catalog_states_gate_the_planner() -> None:
    """Available plans; missing and drifted catalogs block with no substitution."""
    descriptor = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))

    available = available_catalog_policy()
    check_model_role_policy(available, descriptor)
    planned = plan_role(available, descriptor, host="codex", role="independent-verifier")
    assert planned.status == "PLANNED"
    assert [seat.model for seat in planned.seats] == ["model-a"]
    assert planned.evidence_level == "static-planning-only"

    # Empty catalog: a caller-named slug has nothing to resolve against.
    missing = missing_catalog_policy()
    check_model_role_policy(missing, descriptor)
    blocked = plan_role(
        missing, descriptor, host="codex", role="independent-verifier", user=["fixture-model"]
    )
    assert blocked.status == "BLOCKED"
    assert "absent from codex catalog" in " ".join(blocked.reasons)

    # Drifted catalog: the policy checker refuses the disagreement before planning.
    drifted = invalid_catalog_policy()
    with pytest.raises(ValidationError, match="absent from host catalog"):
        check_model_role_policy(drifted, descriptor)


def test_effort_requires_a_live_catalog() -> None:
    """A per-role level off an offline inventory is a plan-grade guess, never a plan."""
    descriptor = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    policy = available_catalog_policy()
    policy["hosts"]["codex"]["discovery"] = "catalog"
    policy["hosts"]["codex"]["verification_status"] = "static-only"
    policy["hosts"]["codex"]["role_overrides"] = {
        "independent-verifier": {"models": ["model-a"], "effort": "high"}
    }

    # The policy checker refuses the claim outright over an offline inventory...
    with pytest.raises(ValidationError, match="effort needs live host proof"):
        check_model_role_policy(policy, descriptor)

    # ...and the planner holds the same line for a policy it was told not to re-check.
    blocked = plan_role(
        policy, descriptor, host="codex", role="independent-verifier", validate_policy=False
    )
    assert blocked.status == "BLOCKED"
    assert "requires a live-observed catalog" in " ".join(blocked.reasons)

    live = available_catalog_policy()
    live["hosts"]["codex"]["role_overrides"] = {
        "independent-verifier": {"models": ["model-a"], "effort": "high"}
    }
    check_model_role_policy(live, descriptor)
    planned = plan_role(live, descriptor, host="codex", role="independent-verifier")
    assert planned.status == "PLANNED"
    assert planned.effort == "high"


def test_malformed_catalog_entry_is_rejected_by_the_schema() -> None:
    descriptor = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    policy = available_catalog_policy()
    policy["hosts"]["codex"]["model_catalog"] = [{"id": "model-a", "provider": "fixture"}]
    with pytest.raises(ValidationError, match="violates its schema"):
        check_model_role_policy(policy, descriptor)
