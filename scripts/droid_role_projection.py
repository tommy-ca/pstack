#!/usr/bin/env python3
"""Droid role and marketplace projection for Factory Droid.

Transforms canonical agent definitions in agents/*.md into Droid-native
custom droid roles in droids/pstack-*.md and generates marketplace manifest.
Decomposed from package_projection.py per Single Responsibility Principle.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import PackageDescriptor, ValidationError

AGENTS_DIR = ROOT / "agents"
DROIDS_DIR = ROOT / "droids"
FACTORY_PLUGIN_DIR = ROOT / ".factory-plugin"

AGENT_ROLE_CONTRACT = (
    "Shipped effort is frontmatter `effort`. Setup may overlay per-role values"
    " using the overlay path the active host declares in `profiles/<host>.json`."
)

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

FORBIDDEN_DROID_TOOLS = ("tools: all", "ExitSpecMode", "GenerateDroid")
DROID_EXECUTE_TOOLS = "Read, Grep, Glob, LS, Execute"
DROID_FILE_EDIT_TOOL_IDS = ("Edit", "Create")


def generate_droid_marketplace(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "name": desc.name,
        "description": f"{desc.name} plugin marketplace (self-hosted source ./)",
        "owner": {"name": "tommy-ca"},
        "plugins": [
            {
                "name": desc.name,
                "description": desc.description or f"{desc.name} plugin",
                "source": "./",
            }
        ],
    }


def _split_frontmatter(text: str) -> tuple[Dict[str, str], str]:
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValidationError(f"role source has no frontmatter block: {text[:40]!r}")
    fm: Dict[str, str] = {}
    for line in parts[1].splitlines():
        m = re.match(r"([A-Za-z][A-Za-z0-9]*):\s*(.*)", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, parts[2].lstrip("\n")


def adapt_droid_description(description: str, source_name: str, droid_name: str) -> str:
    adapted = description.replace(
        AGENT_ROLE_CONTRACT,
        f"Spawned on Droid with `Task` (`subagent_type: {droid_name}`);"
        " the model inherits the parent session and there is no per-spawn effort field.",
    )
    adapted = adapted.replace("`general-purpose`", "`worker`")
    adapted = adapted.replace(f"`{source_name}`", f"`{droid_name}`")
    return adapted


def generate_droid_role(agent_path: Path) -> tuple[str, str]:
    fm, body = _split_frontmatter(agent_path.read_text(encoding="utf-8"))
    source_name = fm.get("name") or agent_path.stem
    droid_name = f"pstack-{source_name}"
    if not re.fullmatch(r"pstack-[a-z0-9-_]+", droid_name):
        raise ValidationError(f"droid name is not Droid-native: {droid_name!r}")
    description = adapt_droid_description(fm.get("description", ""), source_name, droid_name)
    lines = ["---", f"name: {droid_name}", f"description: {json.dumps(description)}", "model: inherit"]
    if fm.get("capabilityMode") == "execute":
        lines.append(f"tools: {DROID_EXECUTE_TOOLS}")
    content = "\n".join(lines) + "\n---\n\n" + body
    if not content.endswith("\n"):
        content += "\n"
    validate_droid_role(droid_name, content)
    return droid_name, content


def validate_droid_role(droid_name: str, content: str) -> None:
    lowered = content.lower()
    if "grok" in lowered or "~/.grok" in lowered:
        raise ValidationError(f"generated droid {droid_name} pins Grok vocabulary or slugs")
    if AGENT_ROLE_CONTRACT in content:
        raise ValidationError(f"generated droid {droid_name} retains the unadapted agent overlay sentence")
    if "reasoningEffort" in content or "reasoning_effort" in content:
        raise ValidationError(f"generated droid {droid_name} carries an effort override")
    desc_match = re.search(r"(?m)^description: (.+)$", content)
    if not desc_match or not re.fullmatch(r'"(?:[^"\\]|\\.)*"', desc_match.group(1)):
        raise ValidationError(f"generated droid {droid_name} description is not a quoted YAML scalar")
    try:
        json.loads(desc_match.group(1))
    except json.JSONDecodeError as error:
        raise ValidationError(f"generated droid {droid_name} description is not valid quoted YAML: {error}") from error
    for forbidden in FORBIDDEN_DROID_TOOLS:
        if forbidden in content:
            raise ValidationError(f"generated droid {droid_name} uses forbidden tools value {forbidden!r}")
    for tools_line in re.findall(r"(?m)^tools: (.+)$", content):
        if "[" in tools_line or "]" in tools_line:
            raise ValidationError(f"generated droid {droid_name} uses a bracket literal in tools restriction {tools_line!r}")
        for tool_id in (tid.strip() for tid in tools_line.split(",")):
            if tool_id in DROID_FILE_EDIT_TOOL_IDS:
                raise ValidationError(f"generated droid {droid_name} grants file-edit tool {tool_id!r}")
    for token in HOST_PRIMITIVES + LEFTOVER_CALL_SITES:
        if token in content:
            raise ValidationError(f"generated droid {droid_name} carries host call site {token!r}")


def generate_droid_roles() -> Dict[str, str]:
    roles: Dict[str, str] = {}
    for agent_path in sorted(AGENTS_DIR.glob("*.md")):
        droid_name, content = generate_droid_role(agent_path)
        roles[f"{droid_name}.md"] = content
    if not roles:
        raise ValidationError(f"no role sources found under {AGENTS_DIR}")
    return roles
