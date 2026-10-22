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

from scripts.model_role_policy import check_model_role_policy
from scripts.model_role_resolver import plan_role
from scripts.portability_schema import SetupProjection, ValidationError
from scripts.setup_pstack import PACKAGE_JSON, resolve_setup_projection
from tests.model_role_helpers import (
    available_catalog_policy,
    invalid_catalog_policy,
    missing_catalog_policy,
)

ENTRY_SKILL = ROOT / "skills" / "setup-pstack" / "SKILL.md"
GROK_SKILL = ROOT / "skills" / "setup-pstack-grok" / "SKILL.md"

# The six built-in hosts, each with the surface its profile declares. A golden
# per host is what keeps a second registry from appearing: only the profile
# moves when a host's setup surface changes.
GOLDEN = {
    "grok": {
        "source": "host-cli",
        "effort": "live-enum",
        "skill": "setup-pstack-grok",
        "catalog": "~/.grok/pstack-models.toml",
        "overlay": "~/.grok/roles",
    },
    "codex": {
        "source": "host-catalog",
        "effort": "none",
        "skill": None,
        "catalog": ".codex-plugin/models.json",
        "overlay": None,
    },
    "antigravity": {
        "source": "host-catalog",
        "effort": "none",
        "skill": None,
        "catalog": ".antigravity-plugin/models.json",
        "overlay": None,
    },
    "droid": {
        "source": "inherit",
        "effort": "inherit-parent",
        "skill": None,
        "catalog": None,
        "overlay": None,
    },
    "omp": {"source": "none", "effort": "none", "skill": None, "catalog": None, "overlay": None},
    "opencode": {"source": "none", "effort": "none", "skill": None, "catalog": None, "overlay": None},
}


@pytest.mark.parametrize("host", sorted(GOLDEN))
def test_golden_setup_projection_per_builtin_host(host: str) -> None:
    projection = resolve_setup_projection(host)
    assert projection is not None
    assert asdict(projection) == GOLDEN[host]


@pytest.mark.parametrize("host", ["codex", "antigravity", "droid", "omp", "opencode"])
def test_non_grok_projection_carries_no_grok_path(host: str) -> None:
    """Negative control: a non-Grok host must never inherit Grok's write targets."""
    rendered = repr(asdict(resolve_setup_projection(host)))
    assert "~/.grok" not in rendered
    assert "grok" not in rendered
    assert "pstack-models.toml" not in rendered


def test_inherit_parent_projection_declares_no_write_target() -> None:
    projection = resolve_setup_projection("droid")
    assert projection is not None
    assert projection.source == "inherit"
    assert projection.effort == "inherit-parent"
    assert projection.catalog is None and projection.overlay is None and projection.skill is None


def test_candidate_profiles_declare_no_setup_surface() -> None:
    """A candidate host cannot point at a setup surface it has no evidence for."""
    for host in ("claude", "copilot"):
        assert resolve_setup_projection(host) is None


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
        assert (GROK_SKILL.parent / "references" / reference).is_file(), reference
    assert "use one of:" in text


def test_entry_skill_passes_the_host_boundary_scan() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "scan_host_boundary", ROOT / "scripts" / "scan-host-boundary.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["scan_host_boundary"] = module
    spec.loader.exec_module(module)
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


def _write_profile(directory: Path, host: str, support_state: str, setup: dict) -> None:
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


def test_resolver_tolerates_an_absent_home_catalog(tmp_path: Path) -> None:
    """A host-home write target need not exist yet; only repo artifacts must."""
    _write_profile(
        tmp_path / "profiles",
        "acme:gamma",
        "mapped",
        {"source": "host-catalog", "effort": "none", "catalog": str(tmp_path / "models.json")},
    )
    projection = resolve_setup_projection("acme:gamma", tmp_path / "profiles", tmp_path)
    assert projection is not None and projection.catalog == str(tmp_path / "models.json")


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


def test_unknown_host_is_not_a_silent_default() -> None:
    with pytest.raises(ValidationError, match="No harness profile"):
        resolve_setup_projection("no-such-host")


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


def test_every_builtin_profile_setup_block_is_typed() -> None:
    """The profile's declared block must match the typed model, key for key."""
    from scripts.host_identity import BUILTIN_HOSTS

    for host in BUILTIN_HOSTS:
        data = json.loads((ROOT / "profiles" / f"{host}.json").read_text(encoding="utf-8"))
        projection = SetupProjection(**data["setup"])
        projection.validate()
        assert asdict(projection) == GOLDEN[host]
