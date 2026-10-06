"""Droid native package and role projection tests (S5)."""

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "project-package.py"

loader = importlib.util.spec_from_file_location("project_package", SCRIPT)
assert loader is not None and loader.loader is not None
project_package = importlib.util.module_from_spec(loader)
sys.modules["project_package"] = project_package
loader.loader.exec_module(project_package)

DROID_NAME_PATTERN = re.compile(r"^pstack-[a-z0-9-_]+$")

# Grok-native primitives and call-site leftovers that must never reach a
# generated Droid role body (mirrors scan-host-boundary and verify-harness).
HOST_PRIMITIVES = (
    "spawn_subagent",
    "get_command_or_subagent_output",
    "kill_command_or_subagent",
    "scheduler_create",
    "kill_task",
    "spawn_agent",
    "wait_agent",
    "resume_agent",
    "pi_spawn",
    "pi_wait",
    "pi_resume",
    "pi_send",
    "pi_prompt",
    "task.spawn",
    "task.wait",
    "task.resume",
    "task.cancel",
    "task.message",
    "invoke_subagent",
    "define_subagent",
    "manage_subagents",
    "ask_user_question",
    "MAX_SUBAGENT_DEPTH",
)

LEFTOVER_CALL_SITES = (
    "the Task tool",
    "using the Task ",
    "via Task ",
    "TodoWrite",
    "AskQuestion",
    "generalPurpose",
)


def _agents_population() -> dict[str, dict[str, str]]:
    population = {}
    for agent_path in sorted((ROOT / "agents").glob("*.md")):
        fm, _ = project_package._split_frontmatter(
            agent_path.read_text(encoding="utf-8")
        )
        population[agent_path.name] = fm
    return population


def _generated_roles() -> dict[str, str]:
    return project_package.generate_droid_roles()


def test_droid_roles_match_enumerated_agent_population() -> None:
    population = _agents_population()
    roles = _generated_roles()
    assert set(roles) == {f"pstack-{Path(name).stem}.md" for name in population}


def test_generated_droid_frontmatter_contract() -> None:
    for fname, content in _generated_roles().items():
        assert DROID_NAME_PATTERN.match(fname[: -len(".md")]), fname
        assert DROID_NAME_PATTERN.match(
            re.search(r"(?m)^name: (.+)$", content).group(1)
        ), fname
        assert re.search(r"(?m)^model: inherit$", content), fname
        assert "reasoningEffort" not in content, fname
        assert "reasoning_effort" not in content, fname
        for forbidden in ("tools: all", "ExitSpecMode", "GenerateDroid"):
            assert forbidden not in content, (fname, forbidden)


def test_capability_mode_maps_to_native_tools_restriction() -> None:
    roles = _generated_roles()
    for fname, fm in _agents_population().items():
        droid_name = f"pstack-{Path(fname).stem}"
        content = roles[f"{droid_name}.md"]
        if fm.get("capabilityMode") == "execute":
            assert re.search(r"(?m)^tools: execute$", content), droid_name
        else:
            assert not re.search(r"(?m)^tools:", content), droid_name


def test_generated_droids_free_of_host_vocabulary() -> None:
    for fname, content in _generated_roles().items():
        assert "grok" not in content.lower(), fname
        for token in HOST_PRIMITIVES:
            assert token not in content, (fname, token)


def test_generated_droids_avoid_leftover_call_sites() -> None:
    for fname, content in _generated_roles().items():
        for pattern in LEFTOVER_CALL_SITES:
            assert pattern not in content, (fname, pattern)


def test_spawn_dispatch_uses_native_subagent_type() -> None:
    for fname, content in _generated_roles().items():
        droid_name = fname[: -len(".md")]
        if "Same posture" in content:
            assert f"subagent_type: {droid_name}" in content, droid_name


def test_droid_projection_deterministic() -> None:
    assert _generated_roles() == _generated_roles()


def test_droid_manifest_and_marketplace_shape() -> None:
    desc, _ = project_package.load_package_descriptor()
    manifest = project_package.generate_droid_manifest(desc)
    assert manifest["name"] == "pstack"
    assert manifest["skills"] == "./skills/"
    assert manifest["droids"] == "./droids/"

    marketplace = project_package.generate_droid_marketplace(desc)
    assert marketplace["plugins"][0]["name"] == "pstack"
    assert marketplace["plugins"][0]["source"] == "./"


def test_check_all_covers_droid() -> None:
    desc, _ = project_package.load_package_descriptor()
    assert "droid" in project_package.TARGET_MAP
    assert project_package.check_all(desc) is True
