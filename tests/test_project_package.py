import importlib.util
import json
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project-package.py"

loader = importlib.util.spec_from_file_location("project_package", SCRIPT)
assert loader is not None and loader.loader is not None
project_package = importlib.util.module_from_spec(loader)
sys.modules["project_package"] = project_package
loader.loader.exec_module(project_package)


def test_load_package_descriptor() -> None:
    desc, raw = project_package.load_package_descriptor()
    assert desc.id == "pstack"
    assert desc.version == "0.15.5-grokbuild.0"
    assert "grok" in desc.host_targets
    assert "codex" in desc.host_targets
    assert "omp" in desc.host_targets
    assert "opencode" in desc.host_targets
    assert "antigravity" in desc.host_targets
    assert "grok" in desc.host_adapters
    assert desc.host_adapters["grok"]["version"] == "0.15.5-grokbuild.0"


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
    assert "skills_root" in omp_m

    opencode_m = project_package.generate_opencode_manifest(desc)
    assert opencode_m["id"] == "pstack"
    assert "skills" in opencode_m

    antigravity_m = project_package.generate_antigravity_manifest(desc)
    assert antigravity_m["name"] == "pstack"
    assert "skills" in antigravity_m
    assert "agents" in antigravity_m
    assert "commands" in antigravity_m

    cmds = project_package.generate_antigravity_commands(desc)
    assert len(cmds) >= 13
    assert "poteto-mode.toml" in cmds
    assert "babysit.toml" in cmds
    assert "thermo-nuclear-code-quality-review.toml" in cmds

    antigravity_models = project_package.generate_antigravity_models(desc)
    assert antigravity_models["singleRoleDefault"] == "pro"
    assert "roles" in antigravity_models

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

