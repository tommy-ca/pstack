import dataclasses
import json
import re
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.package_projection as project_package


def test_load_package_descriptor() -> None:
    desc, raw = project_package.load_package_descriptor()
    assert desc.id == "pstack"
    # The identity is a host-neutral SemVer prerelease (#699): the numeric triple
    # tracks the upstream packaging base and the suffix names the port, never a
    # single harness.
    assert re.fullmatch(r"\d+\.\d+\.\d+-[a-z]+\.\d+", desc.version), desc.version
    assert "grok" in desc.host_targets
    assert "codex" in desc.host_targets
    assert "omp" in desc.host_targets
    assert "opencode" in desc.host_targets
    assert "antigravity" in desc.host_targets
    assert "droid" in desc.host_targets
    assert "grok" in desc.host_adapters
    # Lockstep, not a literal: every adapter publishes the package identity, so a
    # bump cannot leave one host on the previous label.
    assert {a["version"] for a in desc.host_adapters.values()} == {desc.version}


def test_generate_manifests() -> None:
    desc, _ = project_package.load_package_descriptor()

    grok_m = project_package.generate_grok_manifest(desc)
    assert grok_m["name"] == "pstack"
    assert "skills" in grok_m

    codex_m = project_package.generate_codex_manifest(desc)
    assert codex_m["name"] == "pstack"
    assert "interface" in codex_m

    omp_m = project_package.generate_omp_manifest(desc)
    assert omp_m["name"] == "pstack"
    assert isinstance(omp_m["omp"], dict), "OMP enrolls a package only through package.json#omp"

    opencode_m = project_package.generate_opencode_manifest(desc)
    assert opencode_m["id"] == "pstack"
    assert "skills" in opencode_m

    antigravity_m = project_package.generate_antigravity_manifest(desc)
    assert antigravity_m["name"] == "pstack"
    assert "skills" in antigravity_m
    assert "logo" in antigravity_m
    assert "agents" not in antigravity_m
    assert "commands" not in antigravity_m

    cmds = project_package.generate_antigravity_commands(desc)
    assert len(cmds) >= 21
    assert "poteto-mode.toml" in cmds
    assert "babysit.toml" in cmds
    assert "thermo-nuclear-code-quality-review.toml" in cmds
    assert "thermos.toml" in cmds
    assert "thermo-nuclear-review.toml" in cmds

    antigravity_models = project_package.generate_antigravity_models(desc)
    assert antigravity_models["singleRoleDefault"] == "pro"
    assert antigravity_models["panel"] == ["pro", "flash"]
    assert "gpt-oss" not in json.dumps(antigravity_models)
    assert antigravity_models["drivers"] == {
        "mainReasoning": "gemini-4-hydrogen-high",
        "deepReasoning": "gemini-4-hydrogen-xhigh",
        "fastWorker": "gemini-3.8-flash-high",
        "fastVerifier": "gemini-3.8-flash-medium",
        "paidProOrchestrator": "gemini-pro-orchestrator-g1-pro",
        "paidProReasoning": "gemini-4-argon-high",
        "minimalSpecialist": "claude-opus-5-5-high",
    }
    assert len(antigravity_models["available"]) == 12
    avail = {m["slug"]: m for m in antigravity_models["available"]}
    assert avail["pro"] == {
        "label": "Gemini 4 Hydrogen (Pro Tier)",
        "slug": "pro",
        "family": "gemini-4-hydrogen",
        "driver": "gemini-4-hydrogen-high",
        "paidProDriver": "gemini-4-argon-high",
    }
    assert avail["flash"] == {
        "label": "Gemini 3.8 Flash (Flash Tier)",
        "slug": "flash",
        "family": "gemini-3.8-flash",
        "driver": "gemini-3.8-flash-high",
    }
    assert avail["flash_lite"] == {
        "label": "Gemini 3.8 Flash Lite (Flash Lite Tier)",
        "slug": "flash_lite",
        "family": "gemini-3.8-flash",
        "driver": "gemini-3.8-flash-low",
    }
    assert avail["inherit"] == {
        "label": "Inherited Model",
        "slug": "inherit",
        "family": "inherit",
        "driver": "inherit",
    }
    concrete_invariants = {
        "gemini-4-hydrogen-high": ("gemini-4-hydrogen", "pro"),
        "gemini-4-hydrogen-xhigh": ("gemini-4-hydrogen", "pro"),
        "gemini-3.8-flash-high": ("gemini-3.8-flash", "flash"),
        "gemini-3.8-flash-medium": ("gemini-3.8-flash", "flash"),
        "gemini-3.8-flash-low": ("gemini-3.8-flash", "flash_lite"),
        "gemini-4-argon-high": ("gemini-4-argon", "paid-pro"),
        "gemini-pro-orchestrator-g1-pro": ("gemini-4-argon", "paid-pro"),
        "claude-opus-5-5-high": ("claude-opus-5-5", "minimal-specialist"),
    }
    for slug, (family, tier) in concrete_invariants.items():
        assert avail[slug]["family"] == family, slug
        assert avail[slug]["tier"] == tier, slug
    assert set(avail) == {"pro", "flash", "flash_lite", "inherit"} | set(concrete_invariants)
    assert [m["slug"] for m in antigravity_models["available"] if m["slug"].startswith("claude-")] == [
        "claude-opus-5-5-high"
    ]
    agy_roles = {r["role"]: r["models"] for r in antigravity_models["roles"]}
    assert set(agy_roles) == {r["id"] for r in desc.roles}
    assert {role for role, models in agy_roles.items() if models == ["flash"]} == {
        "comment-sicko",
        "how-explorer",
        "swarm-workers",
        "why-investigators",
    }
    assert {role for role, models in agy_roles.items() if models == ["pro"]} == {
        "bug-fix",
        "feature",
        "hardest-tasks",
        "hillclimb",
        "how-critics",
        "how-explainer",
        "independent-verifier",
        "judgment-and-prose",
        "perf-issue",
        "poteto-agent",
        "refactoring",
        "reflect-judgment",
        "reflect-tooling",
        "why-synthesizer",
    }
    assert {role for role, models in agy_roles.items() if models == "panel"} == {
        "architect-runners",
        "arena-cross-judge-pool",
        "arena-runners",
        "interrogate-reviewers",
    }

    codex_models = project_package.generate_codex_models(desc)
    assert codex_models["singleRoleDefault"] == "gpt-6.1-sol"
    assert "gpt-5.6-terra" not in json.dumps(codex_models)
    assert len(codex_models["panel"]) == 2
    assert "gpt-6.1-sol" in codex_models["panel"]
    assert "gpt-6-luna" in codex_models["panel"]
    assert "gpt-6-astra" not in codex_models["panel"]
    assert "roles" in codex_models

    hardest = [r for r in codex_models["roles"] if r["role"] == "hardest-tasks"][0]
    assert hardest["models"] == ["gpt-6-astra"]

    bug_fix = [r for r in codex_models["roles"] if r["role"] == "bug-fix"][0]
    assert bug_fix["models"] == ["gpt-6-luna"]


def test_check_all_in_sync() -> None:
    desc, _ = project_package.load_package_descriptor()
    assert project_package.check_all(desc) is True


def test_projected_role_catalogs_speak_canonical_role_ids() -> None:
    """#440: the host role catalogs key on pstack.package.json#/roles IDs.

    The model-role-policy schema binds these IDs, so a re-spaced label ('how
    explorer'), a merged pair ('feature, refactoring') or a dropped row would
    desync the projected manifest from the policy vocabulary.
    """
    desc, _ = project_package.load_package_descriptor()
    canonical = [role["id"] for role in desc.roles]
    assert len(canonical) == 22
    assert {"feature", "refactoring", "judgment-and-prose"} <= set(canonical)
    assert {"comment-sicko", "how-critics", "poteto-agent"} <= set(canonical)

    for host, catalog in (
        ("codex", project_package.generate_codex_models(desc)),
        ("antigravity", project_package.generate_antigravity_models(desc)),
    ):
        ids = [row["role"] for row in catalog["roles"]]
        assert ids == canonical, f"{host} role catalog must be exactly the canonical ID set"
        for role_id in ids:
            assert role_id == role_id.strip(), (host, role_id)
            assert " " not in role_id and "," not in role_id, (host, role_id)


def test_role_catalog_rejects_renamed_merged_or_missing_roles() -> None:
    """Tooth: a renamed label, a merged pair and a dropped row all fail closed."""
    desc, _ = project_package.load_package_descriptor()

    renamed = dict(project_package.CODEX_ROLE_MODELS)
    renamed["judgment and prose"] = renamed.pop("judgment-and-prose")
    with pytest.raises(project_package.ValidationError):
        project_package.generate_role_catalog(desc, "codex", renamed)

    merged = dict(project_package.CODEX_ROLE_MODELS)
    merged["feature, refactoring"] = merged.pop("refactoring")
    with pytest.raises(project_package.ValidationError):
        project_package.generate_role_catalog(desc, "codex", merged)

    dropped = dict(project_package.CODEX_ROLE_MODELS)
    dropped.pop("comment-sicko")
    with pytest.raises(project_package.ValidationError):
        project_package.generate_role_catalog(desc, "codex", dropped)


def test_role_catalog_rejects_duplicate_ids(monkeypatch) -> None:
    """Tooth: a duplicated canonical ID fails closed instead of projecting twice."""
    desc, _ = project_package.load_package_descriptor()
    duplicated = dataclasses.replace(
        desc, roles=desc.roles + [{"id": "comment-sicko", "description": "dup", "default_model_role": "fast-worker"}]
    )
    with pytest.raises(project_package.ValidationError) as excinfo:
        project_package.generate_role_catalog(duplicated, "codex", project_package.CODEX_ROLE_MODELS)
    assert "duplicate=['comment-sicko']" in str(excinfo.value)


def test_projector_reports_a_refused_catalog_instead_of_crashing(capsys) -> None:
    """Tooth: an unprojectable descriptor is a reported FAIL, not a traceback.

    `check_all` is also the `package_lifecycle.py verify` gate, which expects a
    bool, so a refused catalog must print and return False.
    """
    desc, _ = project_package.load_package_descriptor()
    bogus = dataclasses.replace(desc, roles=[{"id": "ghost-role", "description": "x", "default_model_role": "panel"}])
    assert project_package.check_all(bogus) is False
    out = capsys.readouterr().out
    assert "ERROR: codex models cannot be projected" in out
    assert "ERROR: antigravity models cannot be projected" in out
    assert "ghost-role" in out
    assert "ABSENT: host-local hooks not implemented" in out


def test_check_claude_plugin_presence_shape_and_lockstep() -> None:
    desc, _ = project_package.load_package_descriptor()
    assert project_package.check_claude_plugin(desc) is True


@pytest.mark.parametrize(
    "plugin_payload",
    [
        ["not", "an", "object"],
        {"name": "pstack", "version": "0.0.1-stale", "skills": "./skills/", "agents": "./agents/"},
        {"name": "renamed-fork", "version": "0.0.0-fixture.0", "skills": "./skills/", "agents": "./agents/"},
        {"name": "pstack", "version": "0.0.0-fixture.0", "skills": 42, "agents": "./agents/"},
        {"name": "pstack", "version": "0.0.0-fixture.0", "skills": "./skills/", "agents": []},
        {"name": "pstack", "version": "0.0.0-fixture.0", "skills": "./skills/"},
    ],
)
def test_claude_plugin_check_refuses_wrong_shaped_descriptors(tmp_path, monkeypatch, plugin_payload) -> None:
    """Tooth: a wrong-typed, misnamed, unshaped or stale descriptor fails."""
    desc, _ = project_package.load_package_descriptor()
    plugin_dir = tmp_path / ".claude-plugin"
    plugin_dir.mkdir()
    real_marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    (plugin_dir / "marketplace.json").write_text(json.dumps(real_marketplace), encoding="utf-8")
    (plugin_dir / "plugin.json").write_text(json.dumps(plugin_payload), encoding="utf-8")
    monkeypatch.setattr(project_package, "CLAUDE_PLUGIN_DIR", plugin_dir)
    assert project_package.check_claude_plugin(desc) is False


@pytest.mark.parametrize("marketplace_plugins", [None, 42, {"name": "pstack"}, [{"name": "other"}]])
def test_claude_plugin_check_refuses_wrong_marketplace_shapes(tmp_path, monkeypatch, marketplace_plugins) -> None:
    """Tooth: a non-list `plugins` and a missing `pstack` entry both fail."""
    desc, _ = project_package.load_package_descriptor()
    plugin_dir = tmp_path / ".claude-plugin"
    plugin_dir.mkdir()
    real_plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    (plugin_dir / "plugin.json").write_text(json.dumps(real_plugin), encoding="utf-8")
    (plugin_dir / "marketplace.json").write_text(json.dumps({"plugins": marketplace_plugins}), encoding="utf-8")
    monkeypatch.setattr(project_package, "CLAUDE_PLUGIN_DIR", plugin_dir)
    assert project_package.check_claude_plugin(desc) is False


def test_claude_plugin_check_refuses_a_missing_descriptor(tmp_path, monkeypatch) -> None:
    desc, _ = project_package.load_package_descriptor()
    monkeypatch.setattr(project_package, "CLAUDE_PLUGIN_DIR", tmp_path / "empty")
    assert project_package.check_claude_plugin(desc) is False


def test_hooks_probe_reports_absent_with_tracker(capsys) -> None:
    """Spec G3 is open: --check names the gap instead of silently omitting it."""
    _, raw = project_package.load_package_descriptor()
    assert project_package.check_hooks(raw) is True
    out = capsys.readouterr().out
    assert "ABSENT" in out
    assert "hooks" in out
    assert project_package.HOOKS_TRACKER in out


def test_hooks_probe_fails_closed_once_hook_data_appears(capsys, tmp_path) -> None:
    """Tooth: hook data without a verifiable lifecycle fails the check."""
    assert project_package.check_hooks({"hooks": {"startup": []}}) is False
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert project_package.HOOKS_TRACKER in out

    # A per-host plugin hook surface counts too, not only the descriptor key.
    host_dir = tmp_path / ".antigravity-plugin"
    host_dir.mkdir()
    (host_dir / "hooks.json").write_text("{}", encoding="utf-8")
    assert project_package.hook_surface_paths(tmp_path) == [host_dir / "hooks.json"]
    assert project_package.check_hooks({}, tmp_path) is False


def test_check_droid_auxiliary_handles_malformed_json(capsys, tmp_path, monkeypatch) -> None:
    desc, _ = project_package.load_package_descriptor()
    factory_dir = tmp_path / ".factory-plugin"
    factory_dir.mkdir()
    (factory_dir / "marketplace.json").write_text("{not valid json", encoding="utf-8")
    monkeypatch.setattr(project_package, "FACTORY_PLUGIN_DIR", factory_dir)

    assert project_package._check_droid_auxiliary(desc) is False
    out = capsys.readouterr().out
    assert "ERROR:" in out
    assert "failed to parse" in out


def test_check_pi_package_reports_missing_error_drift_and_pass(capsys, tmp_path) -> None:
    desc, _ = project_package.load_package_descriptor()
    pi_dir = tmp_path / ".pi"

    assert project_package.check_pi_package(desc, pi_dir) is False
    assert "MISSING:" in capsys.readouterr().out

    pi_dir.mkdir()
    pkg_file = pi_dir / "package.json"
    pkg_file.write_text("{bad json", encoding="utf-8")
    assert project_package.check_pi_package(desc, pi_dir) is False
    assert "ERROR:" in capsys.readouterr().out

    pkg_file.write_text(json.dumps({"name": "drifted"}), encoding="utf-8")
    assert project_package.check_pi_package(desc, pi_dir) is False
    assert "DRIFT:" in capsys.readouterr().out

    project_package._write_json(pkg_file, project_package.generate_pi_manifest(desc), "pi package")
    capsys.readouterr()
    assert project_package.check_pi_package(desc, pi_dir) is True
    assert "PASS: pi package" in capsys.readouterr().out


def test_write_and_check_json_roundtrip(capsys, tmp_path) -> None:
    target = tmp_path / "nested" / "manifest.json"
    payload = {"name": "pstack", "version": "1.0.0"}

    project_package._write_json(target, payload, "sample")
    assert "Projected sample ->" in capsys.readouterr().out
    assert target.read_text(encoding="utf-8") == json.dumps(payload, indent=2) + "\n"

    assert project_package._check_json(target, payload, "sample") is True
    assert "PASS: sample" in capsys.readouterr().out

