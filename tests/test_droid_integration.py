#!/usr/bin/env python3
"""Droid sixth-host integration tests (S6).

Census declaration, profile honesty, thin driver registration, and the
repository-owned lifecycle round trip for the droid host.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    DEFAULT_PLUGIN_MANIFESTS,
    DEFAULT_SKILLS_DIRS,
    HOSTS,
    HarnessProfile,
    Binding,
    Evidence,
    derive_support_state,
)


def _load_module(name: str, rel: str):
    loader = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert loader is not None and loader.loader is not None
    module = importlib.util.module_from_spec(loader)
    sys.modules[name] = module
    loader.loader.exec_module(module)
    return module


lifecycle = _load_module("package_lifecycle", "scripts/package-lifecycle.py")
verify_portable = _load_module("verify_portable", "scripts/verify-portable.py")
verify_harness = _load_module("verify_harness", "scripts/verify-harness.py")
scan_boundary = _load_module("scan_host_boundary", "scripts/scan-host-boundary.py")
scaffold = _load_module("scaffold_verification_skill", "scripts/scaffold-verification-skill.py")

from scripts.drivers import DroidDriver, get_driver


# --- VAL-DROID-001: descriptor, schema enums, and host census ---


def test_descriptor_declares_droid_like_existing_hosts() -> None:
    raw = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))
    assert "droid" in raw["host_targets"]
    adapter_keys = {tuple(sorted(v.keys())) for v in raw["host_adapters"].values()}
    assert "droid" in raw["host_adapters"]
    assert len(adapter_keys) == 1, "droid adapter shape must match the five existing hosts"


def test_schema_host_enums_accept_droid() -> None:
    for schema_name, enum_path in (
        ("package-descriptor", ("host_targets", "items")),
        ("profile", ("host",)),
        ("binding", ("host",)),
        ("receipt", ("host",)),
    ):
        schema = json.loads(
            (ROOT / "schemas" / "portability" / f"{schema_name}.schema.json").read_text(encoding="utf-8")
        )
        node = schema["properties"]
        for key in enum_path:
            node = node[key]
        assert "droid" in node["enum"], schema_name
        declared = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))["host_targets"]
        assert set(declared) <= set(node["enum"]), schema_name


def test_portability_schema_census_includes_droid() -> None:
    assert "droid" in HOSTS
    assert DEFAULT_SKILLS_DIRS["droid"] == ".factory/skills"
    assert DEFAULT_PLUGIN_MANIFESTS["droid"] == ".factory-plugin/plugin.json"


def test_package_lifecycle_census_includes_droid() -> None:
    assert "droid" in lifecycle.SUPPORTED_HOSTS
    assert "droid" in lifecycle.HOST_PLUGIN_REL_PATHS


def test_verify_portable_all_uses_declared_six_host_census() -> None:
    declared = json.loads((ROOT / "pstack.package.json").read_text(encoding="utf-8"))["host_targets"]
    assert "droid" in declared
    assert set(declared) <= set(verify_portable.SUPPORTED_HOSTS)
    assert verify_portable.get_declared_hosts() == declared


def test_boundary_scanner_census_includes_droid() -> None:
    assert "droid" in scan_boundary.HARNESS_NAMES


def test_scaffold_host_detection_includes_droid() -> None:
    assert "droid" in scaffold.HOST_DETECT_ORDER


def test_verify_harness_skip_files_include_droid_reference() -> None:
    assert "droid-tools.md" in verify_harness.SKIP_FILES


# --- VAL-DROID-006: profile honesty ---


def _droid_profile_data() -> dict:
    return json.loads((ROOT / "profiles" / "droid.json").read_text(encoding="utf-8"))


def _droid_profile() -> HarnessProfile:
    d = _droid_profile_data()
    b = [Binding(**x) for x in d.get("bindings", [])]
    e = [Evidence(**x) for x in d.get("evidence_ledger", [])]
    return HarnessProfile(
        host=d["host"],
        support_state=d["support_state"],
        bindings=b,
        skills_dir=d.get("skills_dir"),
        plugins_dir=d.get("plugins_dir"),
        plugin_manifest=d.get("plugin_manifest"),
        evidence_ledger=e,
        tool_mappings=d.get("tool_mappings"),
        skill_order=d.get("skill_order"),
        runtime_conventions=d.get("runtime_conventions"),
    )


def test_droid_profile_validates_and_support_state_is_candidate() -> None:
    profile = _droid_profile()
    profile.validate()
    assert profile.support_state == "candidate"
    assert derive_support_state(profile, ROOT) == "candidate"


def test_droid_profile_runtime_conventions() -> None:
    rc = _droid_profile_data()["runtime_conventions"]
    assert rc["max_subagent_depth"] == 1
    required = {"subagent_type", "description", "prompt"}
    assert required <= set(rc["allowed_spawn_fields"])
    # Live session schema evidence: the await family is a real optional field.
    assert "await" in rc["allowed_spawn_fields"]
    for field in ("readonly", "isolation", "cwd", "model", "reasoning_effort", "environment"):
        assert field in rc["forbidden_spawn_fields"], field
        assert field not in rc["allowed_spawn_fields"], field
    assert any("worktree" in mode for mode in rc["supported_isolation_modes"])


def test_droid_profile_records_gaps() -> None:
    raw = (ROOT / "profiles" / "droid.json").read_text(encoding="utf-8")
    assert "untested" in raw
    assert "candidate" in raw
    assert "inherit" in raw
    ref = ROOT / "skills" / "poteto-mode" / "references" / "droid-tools.md"
    assert ref.is_file()
    text = ref.read_text(encoding="utf-8")
    for token in ("untested", "model: inherit", "parent-owned", "no per-spawn"):
        assert token in text, token


# --- VAL-DROID-001: thin driver registration ---


def test_droid_driver_registered() -> None:
    driver = get_driver("droid", ROOT)
    assert isinstance(driver, DroidDriver)


@pytest.mark.parametrize(
    "method", ["discover", "route_playbook", "child_spawn", "isolation", "evidence_capture"]
)
def test_droid_driver_scenarios_run_offline(tmp_path: Path, method: str) -> None:
    driver = get_driver("droid", ROOT)
    avail, reason = driver.is_available()
    if not avail:
        pytest.skip(f"droid CLI unavailable: {reason}")
    result = getattr(driver, method)(tmp_path) if method != "route_playbook" else driver.route_playbook("feature", tmp_path)
    assert result.verdict == "PASS", (result.scenario_id, result.stdout_snippet)


# --- Repository-owned lifecycle round trip ---


def test_droid_lifecycle_install_verify_uninstall(tmp_path: Path) -> None:
    target = tmp_path / "target-droid"
    plugin_dir = lifecycle.install_plugin("droid", target)
    assert (plugin_dir / ".factory-plugin" / "plugin.json").is_file()
    assert (plugin_dir / ".factory-plugin" / "marketplace.json").is_file()
    assert (plugin_dir / "skills" / "poteto-mode" / "SKILL.md").is_file()
    assert len(list((plugin_dir / "droids").glob("*.md"))) > 0

    ok, errors = lifecycle.verify_plugin("droid", target)
    assert ok is True, errors

    ok, errors = lifecycle.update_plugin("droid", target)
    assert ok is True, errors

    ok, errors = lifecycle.uninstall_plugin("droid", target)
    assert ok is True, errors
    assert not plugin_dir.exists()


def test_droid_lifecycle_prove(tmp_path: Path) -> None:
    ok, scenarios = lifecycle.prove_lifecycle("droid", tmp_path / "target-prove")
    assert ok is True, scenarios
    assert [s["step"] for s in scenarios] == ["install", "update", "uninstall"]
    assert all(s["verdict"] == "PASS" for s in scenarios)
