#!/usr/bin/env python3
"""Project canonical pstack.package.json into harness-native plugin descriptors.

Implements the projection lever per Build the Lever + Model the Domain + Zero Drift:
    pstack.package.json (canonical source of truth)
        ├── .grok-plugin/plugin.json
        ├── .codex-plugin/plugin.json
        ├── .omp-plugin/package.json
        └── .opencode-plugin/package.json

Usage:
    python3 scripts/project-package.py --check
    python3 scripts/project-package.py --project [--host <host>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Sole production caller of the pure planner: a read-only planning check, never
# a model dispatch path.
from scripts.host_identity import require_builtin_host_keys
from scripts.model_role_resolver import plan_role
from scripts.portability_schema import PackageDescriptor, ValidationError

PACKAGE_JSON = ROOT / "pstack.package.json"
MODEL_ROLE_POLICY = ROOT / "examples/portability/model-role-policy.example.json"
# One probe role with no required capability bindings, so `--check` reports the
# host/tier/model-mapping verdict instead of re-testing capability opinions.
PLAN_PROBE_ROLE = "independent-verifier"
AGENTS_DIR = ROOT / "agents"
DROIDS_DIR = ROOT / "droids"
FACTORY_PLUGIN_DIR = ROOT / ".factory-plugin"
CLAUDE_PLUGIN_DIR = ROOT / ".claude-plugin"
# What a Claude Code install reads out of .claude-plugin/plugin.json, and the
# type each key must carry: a wrong-typed descriptor is drift, not presence.
CLAUDE_MANIFEST_SHAPE = {"name": str, "version": str, "skills": str, "agents": str}
# Host-local lifecycle hooks (#438) have no implementation on this revision; the
# probe names the gap and the tracker instead of reporting a silent pass. Hook
# data would land in a host plugin dir (`.antigravity-plugin/hooks.json`, the
# `hooks/` surfaces referenced by sync-antigravity-plugin.py) or under the
# descriptor's own `hooks` key, so both are probed.
HOOKS_TRACKER = "#438"
HOOKS_SURFACE_GLOB = ".*-plugin/hooks*"

# Grok-native role frontmatter sentence, replaced with the Droid-native spawn
# contract. The overlay path is Grok-only; Droid has no per-role toml overlay.
GROK_OVERLAY_SENTENCE = re.compile(
    r"Shipped effort is frontmatter `effort`\. Setup may overlay via ~/\.grok/roles/pstack:[a-z0-9-]+\.toml\."
)

# Generation-time guards. Mirrors scan-host-boundary.py's host primitives and
# verify-harness.py's leftover call sites: a generated Droid role must never
# carry another host's call vocabulary (kept inline because neither script is
# importable by module name).
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
# Runtime-verified frontmatter llmIds (traced via the Droid runtime, not CLI
# inventory names). Grok's execute capabilityMode grants read + shell, but
# Droid's `execute` category is shell-only, so execute-mode roles spell the
# union out explicitly as a comma-separated scalar. The native parser splits
# commas without stripping bracket characters, and file-edit IDs must stay
# absent from a read+shell posture.
DROID_EXECUTE_TOOLS = "Read, Grep, Glob, LS, Execute"
DROID_FILE_EDIT_TOOL_IDS = ("Edit", "Create")


def load_package_descriptor() -> tuple[PackageDescriptor, Dict[str, Any]]:
    if not PACKAGE_JSON.is_file():
        raise FileNotFoundError(f"Missing {PACKAGE_JSON}")
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    clean_dict = {k: v for k, v in data.items() if not k.startswith("$")}
    desc = PackageDescriptor(**clean_dict, raw_dict=data)
    desc.validate()
    return desc, data


def generate_grok_manifest(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "name": desc.name,
        "version": desc.version,
        "description": f"{desc.name} for Grok Build: shared skills, grok-tools.md mapping.",
        "homepage": "https://github.com/tommy-ca/pstack",
        "repository": "https://github.com/tommy-ca/pstack",
        "license": "MIT",
        "skills": ["./skills/", "./automations/benny-grok/skills/"],
        "agents": "./agents/",
    }


def generate_codex_manifest(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "name": desc.name,
        "version": desc.version,
        "description": f"{desc.name} for Codex: shared skills; tool names resolve via skills/poteto-mode/references/codex-tools.md.",
        "author": {
            "name": "Lauren Tan (original); tommy-ca (three-host port)",
        },
        "homepage": "https://github.com/tommy-ca/pstack",
        "repository": "https://github.com/tommy-ca/pstack",
        "license": "MIT",
        "keywords": [
            "pstack",
            "poteto-mode",
            "codex",
        ],
        "skills": "./skills/",
        "interface": {
            "displayName": desc.name,
            "shortDescription": "Rigorous agent workflows: go deep first.",
            "longDescription": "Shared pstack blocks (principles, primitives, composition, playbooks) recomposed on Codex via codex-tools.md.",
            "developerName": "Lauren Tan (original), tommy-ca",
            "category": "Developer Tools",
            "capabilities": ["Interactive", "Read", "Write"],
            "websiteURL": "https://github.com/tommy-ca/pstack",
        },
    }


def generate_omp_manifest(desc: PackageDescriptor) -> Dict[str, Any]:
    """Native OMP package descriptor.

    OMP enrolls a package when `package.json` carries an `omp` (or legacy `pi`)
    key, and only a package whose manifest survives that read is listed by
    `omp plugin list`; the conventional `skills/<name>/SKILL.md` and
    `agents/*.md` siblings are what the runtime then discovers
    (discovery/omp-plugins.ts and task/discovery.ts at the pinned OMP head).
    """
    description = f"{desc.name} for Oh-My-Pi (OMP): portable principles, playbooks, skills, and role agents."
    return {
        "name": desc.name,
        "version": desc.version,
        "description": description,
        "omp": {
            "name": desc.name,
            "version": desc.version,
            "description": description,
        },
    }


def generate_opencode_manifest(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "id": desc.id,
        "version": desc.version,
        "description": f"{desc.name} extension for OpenCode harness.",
        "skills": f"./{desc.skills_root}",
        "namespace": desc.id,
        "router": desc.entrypoints.get("router", "skills/poteto-mode/SKILL.md"),
    }


def generate_antigravity_manifest(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "name": desc.name,
        "version": desc.version,
        "displayName": desc.name,
        "description": f"{desc.description} (Google Antigravity port)",
        "author": {
            "name": "Lauren Tan (original); tommy-ca (multi-harness port)",
        },
        "homepage": "https://github.com/tommy-ca/pstack",
        "repository": "https://github.com/tommy-ca/pstack",
        "license": "MIT",
        "skills": ["./skills/"],
        "agents": "./agents/",
        "commands": "./commands/",
    }


def generate_antigravity_commands(desc: PackageDescriptor) -> Dict[str, str]:
    cmds = {}
    for cmd in desc.commands:
        name = cmd["name"]
        d = cmd["description"]
        p = cmd["prompt"]
        cmds[f"{name}.toml"] = f'description = "{d}"\nprompt = "{p}"\n'
    return cmds


# Host-native role catalogs (.codex-plugin/models.json#/roles,
# .antigravity-plugin/models.json#/roles) key on the canonical role IDs in
# pstack.package.json#/roles, which is also what the model-role-policy schema
# binds (#440). Row order and the ID set come from the descriptor; the routing
# skill and the per-host model choice are host-local maps validated against it,
# so a renamed, merged, dropped, duplicated or non-canonical row cannot project.
ROLE_SKILLS = {
    "architect-runners": "architect",
    "arena-cross-judge-pool": "arena",
    "arena-runners": "arena",
    "bug-fix": "poteto-mode",
    "comment-sicko": "poteto-mode",
    "feature": "poteto-mode",
    "hardest-tasks": "poteto-mode",
    "hillclimb": "poteto-mode",
    "how-critics": "how",
    "how-explainer": "how",
    "how-explorer": "how",
    "independent-verifier": "poteto-mode",
    "interrogate-reviewers": "interrogate",
    "judgment-and-prose": "poteto-mode",
    "perf-issue": "poteto-mode",
    "poteto-agent": "poteto-mode",
    "refactoring": "poteto-mode",
    "reflect-judgment": "reflect",
    "reflect-tooling": "reflect",
    "swarm-workers": "swarm",
    "why-investigators": "why",
    "why-synthesizer": "why",
}

# Per-host model choice, by canonical role ID. "panel" is the host's panel
# selector, not a model slug.
CODEX_ROLE_MODELS: Dict[str, Any] = {
    "architect-runners": ["gpt-6.1-sol"],
    "arena-cross-judge-pool": ["gpt-6.1-sol"],
    "arena-runners": "panel",
    "bug-fix": ["gpt-6-luna"],
    "comment-sicko": ["gpt-6-luna"],
    "feature": ["gpt-6-luna"],
    "hardest-tasks": ["gpt-6-astra"],
    "hillclimb": ["gpt-6-luna"],
    "how-critics": ["gpt-6-luna"],
    "how-explainer": ["gpt-6-luna"],
    "how-explorer": ["gpt-6-luna"],
    "independent-verifier": ["gpt-6.1-sol"],
    "interrogate-reviewers": ["gpt-6.1-sol"],
    "judgment-and-prose": ["gpt-6.1-sol", "gpt-6-luna"],
    "perf-issue": ["gpt-6-luna"],
    "poteto-agent": ["gpt-6.1-sol"],
    "refactoring": ["gpt-6-luna"],
    "reflect-judgment": ["gpt-6.1-sol"],
    "reflect-tooling": ["gpt-6-luna"],
    "swarm-workers": ["gpt-6-luna"],
    "why-investigators": ["gpt-6-luna"],
    "why-synthesizer": ["gpt-6.1-sol"],
}

ANTIGRAVITY_ROLE_MODELS: Dict[str, Any] = {
    "architect-runners": "panel",
    "arena-cross-judge-pool": "panel",
    "arena-runners": "panel",
    "bug-fix": ["pro"],
    "comment-sicko": ["flash"],
    "feature": ["pro"],
    "hardest-tasks": ["pro"],
    "hillclimb": ["pro"],
    "how-critics": ["pro"],
    "how-explainer": ["pro"],
    "how-explorer": ["pro"],
    "independent-verifier": ["pro"],
    "interrogate-reviewers": "panel",
    "judgment-and-prose": ["pro"],
    "perf-issue": ["pro"],
    "poteto-agent": ["pro"],
    "refactoring": ["pro"],
    "reflect-judgment": ["pro"],
    "reflect-tooling": ["pro"],
    "swarm-workers": ["flash"],
    "why-investigators": ["pro"],
    "why-synthesizer": ["pro"],
}


def generate_role_catalog(desc: PackageDescriptor, host: str, models: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Project pstack.package.json#/roles into one host's role catalog rows.

    Fails closed: a role added to the descriptor without a host model, a
    non-canonical row, or a duplicated canonical ID raises instead of projecting
    a catalog that has silently drifted from the canonical vocabulary (#440).
    """
    canonical = [role["id"] for role in desc.roles]
    duplicates = sorted({role_id for role_id in canonical if canonical.count(role_id) > 1})
    missing = [role_id for role_id in canonical if role_id not in models or role_id not in ROLE_SKILLS]
    extra = [role_id for role_id in models if role_id not in canonical]
    if duplicates or missing or extra:
        raise ValidationError(
            f"{host} role catalog must be exactly pstack.package.json#/roles: "
            f"duplicate={duplicates} missing={missing} non-canonical={extra}"
        )
    return [{"role": role_id, "models": models[role_id], "skill": ROLE_SKILLS[role_id]} for role_id in canonical]


def generate_antigravity_models(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "singleRoleDefault": "pro",
        "panel": ["pro", "flash"],
        "available": [
            {"label": "Gemini Pro 3.1", "slug": "pro", "family": "gemini-pro-3.1"},
            {"label": "Gemini Flash 3.8", "slug": "flash", "family": "gemini-flash-3.8"},
            {"label": "Gemini Flash 3.8 Lite", "slug": "flash_lite", "family": "gemini-flash-3.8-lite"},
            {"label": "Inherited Model", "slug": "inherit", "family": "inherit"},
        ],
        "roles": generate_role_catalog(desc, "antigravity", ANTIGRAVITY_ROLE_MODELS),
    }


def generate_codex_models(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "singleRoleDefault": "gpt-6.1-sol",
        "panel": ["gpt-6.1-sol", "gpt-6-luna"],
        "available": [
            {"label": "GPT-6.1 Sol", "slug": "gpt-6.1-sol"},
            {"label": "GPT-6 Astra", "slug": "gpt-6-astra"},
            {"label": "GPT-6 Luna", "slug": "gpt-6-luna"},
        ],
        "roles": generate_role_catalog(desc, "codex", CODEX_ROLE_MODELS),
    }



def generate_droid_manifest(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "name": desc.name,
        "version": desc.version,
        "description": f"{desc.name} for Factory Droid: shared skills, native droids, droid-tools.md mapping.",
        "homepage": "https://github.com/tommy-ca/pstack",
        "repository": "https://github.com/tommy-ca/pstack",
        "license": "MIT",
        "skills": f"./{desc.skills_root}/",
        "droids": "./droids/",
    }


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
    adapted = GROK_OVERLAY_SENTENCE.sub(
        f"Spawned on Droid with `Task` (`subagent_type: {droid_name}`);"
        " the model inherits the parent session and there is no per-spawn effort field.",
        description,
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
    # The description carries injected `key: value`-shaped text (the spawn
    # contract sentence), which is invalid as an unquoted YAML plain scalar.
    # Emit a double-quoted scalar so the frontmatter stays parseable YAML.
    lines = ["---", f"name: {droid_name}", f"description: {json.dumps(description)}", "model: inherit"]
    # Native tool definitions: grok's capabilityMode becomes a per-definition
    # Droid tools restriction; roles without it get all tools (field omitted).
    # Grok's execute mode grants read + shell, so the read+shell union is
    # spelled out explicitly (comma-separated scalar of runtime llmIds).
    # Note: the frontmatter `tools:` value namespace is load-time-untested
    # (see droid-tools.md); the union IDs are verified llmIds.
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
    """Enumerate agents/*.md at run time and project one droid per source."""
    roles: Dict[str, str] = {}
    for agent_path in sorted(AGENTS_DIR.glob("*.md")):
        droid_name, content = generate_droid_role(agent_path)
        roles[f"{droid_name}.md"] = content
    if not roles:
        raise ValidationError(f"no role sources found under {AGENTS_DIR}")
    return roles


TARGET_MAP = {
    "grok": (ROOT / ".grok-plugin" / "plugin.json", generate_grok_manifest),
    "codex": (ROOT / ".codex-plugin" / "plugin.json", generate_codex_manifest),
    "omp": (ROOT / ".omp-plugin" / "package.json", generate_omp_manifest),
    "opencode": (ROOT / ".opencode-plugin" / "package.json", generate_opencode_manifest),
    "antigravity": (ROOT / ".antigravity-plugin" / "plugin.json", generate_antigravity_manifest),
    "droid": (FACTORY_PLUGIN_DIR / "plugin.json", generate_droid_manifest),
}
# The projection census is the identity census: a built-in host without a row here
# would silently project nothing, so the key set is checked against the one source
# of host identity rather than restated (#446).
require_builtin_host_keys(TARGET_MAP, "TARGET_MAP")


def project_all(desc: PackageDescriptor, hosts: List[str] | None = None) -> None:
    targets = hosts or list(TARGET_MAP.keys())
    for host in targets:
        if host not in TARGET_MAP:
            continue
        dest_file, generator = TARGET_MAP[host]
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        content = generator(desc)
        dest_file.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
        print(f"Projected {host} -> {dest_file.relative_to(ROOT)}")
        if host == "antigravity":
            models_file = ROOT / ".antigravity-plugin" / "models.json"
            models_file.write_text(json.dumps(generate_antigravity_models(desc), indent=2) + "\n", encoding="utf-8")
            print(f"Projected antigravity models -> {models_file.relative_to(ROOT)}")

            cmds_dir = ROOT / ".antigravity-plugin" / "commands"
            cmds_dir.mkdir(parents=True, exist_ok=True)
            for fname, toml_str in generate_antigravity_commands(desc).items():
                (cmds_dir / fname).write_text(toml_str, encoding="utf-8")
            print(f"Projected {len(desc.commands)} antigravity commands -> {cmds_dir.relative_to(ROOT)}")

        if host == "codex":
            models_file = ROOT / ".codex-plugin" / "models.json"
            models_file.write_text(json.dumps(generate_codex_models(desc), indent=2) + "\n", encoding="utf-8")
            print(f"Projected codex models -> {models_file.relative_to(ROOT)}")

        if host == "droid":
            marketplace_file = FACTORY_PLUGIN_DIR / "marketplace.json"
            marketplace_file.write_text(
                json.dumps(generate_droid_marketplace(desc), indent=2) + "\n", encoding="utf-8"
            )
            print(f"Projected droid marketplace -> {marketplace_file.relative_to(ROOT)}")

            roles = generate_droid_roles()
            DROIDS_DIR.mkdir(parents=True, exist_ok=True)
            for fname, content in roles.items():
                (DROIDS_DIR / fname).write_text(content, encoding="utf-8")
            stale = [p for p in DROIDS_DIR.glob("*.md") if p.name not in roles]
            for p in stale:
                p.unlink()
                print(f"Removed stale droid role -> {p.relative_to(ROOT)}")
            print(f"Projected {len(roles)} droid roles -> {DROIDS_DIR.relative_to(ROOT)}")



def check_model_role_plan(desc: PackageDescriptor) -> bool:
    """Read-only planner verdict per declared host; a static plan, never a receipt.

    A BLOCKED probe plan means the checked-in policy cannot map a host the
    descriptor declares, so that host has no planning path at all.
    """
    policy = json.loads(MODEL_ROLE_POLICY.read_text(encoding="utf-8"))
    all_ok = True
    for host in desc.host_targets:
        plan = plan_role(policy, desc.raw_dict, host=host, role=PLAN_PROBE_ROLE)
        reasons = f": {'; '.join(plan.reasons)}" if plan.reasons else ""
        if plan.status == "BLOCKED":
            print(f"BLOCKED: {host} cannot plan {PLAN_PROBE_ROLE}{reasons}")
            all_ok = False
        else:
            print(f"{plan.status}: {host} {PLAN_PROBE_ROLE} <- {plan.source} ({plan.evidence_level}){reasons}")
    return all_ok
def check_claude_plugin(desc: PackageDescriptor) -> bool:
    """.claude-plugin presence, shape and version lockstep.

    Claude Code is a supported host whose descriptors are hand-maintained, not
    TARGET_MAP projections, so --check validates the files that exist instead of
    manifest equality: a missing, unparseable, wrong-typed, wrongly named or
    stale descriptor fails the check rather than passing as "present".
    """
    ok = True
    plugin_file = CLAUDE_PLUGIN_DIR / "plugin.json"
    market_file = CLAUDE_PLUGIN_DIR / "marketplace.json"
    for path in (plugin_file, market_file):
        if not path.is_file():
            label = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
            print(f"MISSING: {label} (Claude Code host descriptor)")
            ok = False
    if not ok:
        return False
    try:
        plugin = json.loads(plugin_file.read_text(encoding="utf-8"))
        market = json.loads(market_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: .claude-plugin descriptor failed to parse: {e}")
        return False
    if not isinstance(plugin, dict) or not isinstance(market, dict):
        print("DRIFT: .claude-plugin descriptors must be JSON objects")
        return False
    for key, expected_type in CLAUDE_MANIFEST_SHAPE.items():
        value = plugin.get(key)
        if not isinstance(value, expected_type) or (isinstance(value, str) and not value):
            print(
                f"DRIFT: .claude-plugin/plugin.json {key!r} must be a non-empty "
                f"{expected_type.__name__}, got {type(value).__name__}"
            )
            ok = False
    for key in ("name", "version"):
        if plugin.get(key) != getattr(desc, key):
            print(
                f"DRIFT: .claude-plugin/plugin.json {key} {plugin.get(key)!r} "
                f"!= pstack.package.json {getattr(desc, key)!r}"
            )
            ok = False
    entries = market.get("plugins")
    if not isinstance(entries, list):
        print(f"DRIFT: .claude-plugin/marketplace.json plugins must be a list, got {type(entries).__name__}")
        return False
    entry = next((p for p in entries if isinstance(p, dict) and p.get("name") == desc.name), None)
    if entry is None:
        print(f"MISSING: .claude-plugin/marketplace.json has no {desc.name!r} plugin entry")
        ok = False
    elif entry.get("version") != desc.version:
        print(
            f"DRIFT: .claude-plugin/marketplace.json {desc.name} version {entry.get('version')!r} "
            f"!= pstack.package.json {desc.version!r}"
        )
        ok = False
    if ok:
        print("PASS: .claude-plugin manifests present, shaped and in version lockstep")
    return ok


def hook_surface_paths(root: Path = ROOT) -> List[Path]:
    """Hook-bearing paths a host plugin dir would carry, if the lifecycle existed."""
    return sorted(root.glob(HOOKS_SURFACE_GLOB))


def check_hooks(raw: Dict[str, Any], root: Path = ROOT) -> bool:
    """Fail-closed probe for the host-local hook lifecycle (spec G3, open).

    Hooks are not implemented, so the surface is reported ABSENT with its
    tracker rather than omitted; a green --check must never imply a hook
    lifecycle that does not exist. Hook data appearing before that lifecycle is
    verifiable fails the check instead of being silently projected.
    """
    if raw.get("hooks") is None and not hook_surface_paths(root):
        print(f"ABSENT: host-local hooks not implemented; nothing claimed ({HOOKS_TRACKER})")
        return True
    print(f"FAIL: hook surface present but unverifiable; land the lifecycle before projecting it ({HOOKS_TRACKER})")
    return False


def check_all(desc: PackageDescriptor, hosts: List[str] | None = None) -> bool:
    targets = hosts or list(TARGET_MAP.keys())
    all_ok = True
    for host in targets:
        if host not in TARGET_MAP:
            continue
        dest_file, generator = TARGET_MAP[host]
        try:
            expected = generator(desc)
        except ValidationError as e:
            print(f"ERROR: {host} manifest cannot be projected: {e}")
            all_ok = False
            continue
        if not dest_file.is_file():
            print(f"MISSING: {host} manifest not found at {dest_file.relative_to(ROOT)}")
            all_ok = False
            continue
        try:
            actual = json.loads(dest_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"ERROR: {dest_file.relative_to(ROOT)} failed to parse: {e}")
            all_ok = False
            continue
        if actual != expected:
            print(f"DRIFT: {host} manifest at {dest_file.relative_to(ROOT)} does not match pstack.package.json")
            all_ok = False
        else:
            print(f"PASS: {host} manifest at {dest_file.relative_to(ROOT)} in sync")

        if host == "antigravity":
            models_file = ROOT / ".antigravity-plugin" / "models.json"
            try:
                expected_models = generate_antigravity_models(desc)
            except ValidationError as e:
                print(f"ERROR: antigravity models cannot be projected: {e}")
                expected_models = None
            if expected_models is None:
                all_ok = False
            elif not models_file.is_file():
                print(f"MISSING: antigravity models not found at {models_file.relative_to(ROOT)}")
                all_ok = False
            else:
                try:
                    actual_models = json.loads(models_file.read_text(encoding="utf-8"))
                    if actual_models != expected_models:
                        print(f"DRIFT: antigravity models at {models_file.relative_to(ROOT)} does not match expected")
                        all_ok = False
                    else:
                        print(f"PASS: antigravity models at {models_file.relative_to(ROOT)} in sync")
                except Exception as e:
                    print(f"ERROR: {models_file.relative_to(ROOT)} failed to parse: {e}")
                    all_ok = False

            cmds_dir = ROOT / ".antigravity-plugin" / "commands"
            expected_cmds = generate_antigravity_commands(desc)
            if not cmds_dir.is_dir() and expected_cmds:
                print(f"MISSING: antigravity commands directory not found at {cmds_dir.relative_to(ROOT)}")
                all_ok = False
            elif expected_cmds:
                cmds_ok = True
                for fname, expected_content in expected_cmds.items():
                    target_file = cmds_dir / fname
                    if not target_file.is_file():
                        print(f"MISSING: antigravity command not found at {target_file.relative_to(ROOT)}")
                        cmds_ok = False
                        all_ok = False
                    elif target_file.read_text(encoding="utf-8") != expected_content:
                        print(f"DRIFT: antigravity command at {target_file.relative_to(ROOT)} does not match expected")
                        cmds_ok = False
                        all_ok = False
                if cmds_ok:
                    print(f"PASS: {len(expected_cmds)} antigravity commands at {cmds_dir.relative_to(ROOT)} in sync")

        if host == "codex":
            models_file = ROOT / ".codex-plugin" / "models.json"
            try:
                expected_models = generate_codex_models(desc)
            except ValidationError as e:
                print(f"ERROR: codex models cannot be projected: {e}")
                expected_models = None
            if expected_models is None:
                all_ok = False
            elif not models_file.is_file():
                print(f"MISSING: codex models not found at {models_file.relative_to(ROOT)}")
                all_ok = False
            else:
                try:
                    actual_models = json.loads(models_file.read_text(encoding="utf-8"))
                    if actual_models != expected_models:
                        print(f"DRIFT: codex models at {models_file.relative_to(ROOT)} does not match expected")
                        all_ok = False
                    else:
                        print(f"PASS: codex models at {models_file.relative_to(ROOT)} in sync")
                except Exception as e:
                    print(f"ERROR: {models_file.relative_to(ROOT)} failed to parse: {e}")
                    all_ok = False

        if host == "droid":
            marketplace_file = FACTORY_PLUGIN_DIR / "marketplace.json"
            expected_marketplace = generate_droid_marketplace(desc)
            if not marketplace_file.is_file():
                print(f"MISSING: droid marketplace not found at {marketplace_file.relative_to(ROOT)}")
                all_ok = False
            else:
                actual_marketplace = json.loads(marketplace_file.read_text(encoding="utf-8"))
                if actual_marketplace != expected_marketplace:
                    print(f"DRIFT: droid marketplace at {marketplace_file.relative_to(ROOT)} does not match expected")
                    all_ok = False
                else:
                    print(f"PASS: droid marketplace at {marketplace_file.relative_to(ROOT)} in sync")

            expected_roles = generate_droid_roles()
            roles_ok = True
            for fname, expected_content in expected_roles.items():
                target_file = DROIDS_DIR / fname
                if not target_file.is_file():
                    print(f"MISSING: droid role not found at {target_file.relative_to(ROOT)}")
                    roles_ok = False
                    all_ok = False
                elif target_file.read_text(encoding="utf-8") != expected_content:
                    print(f"DRIFT: droid role at {target_file.relative_to(ROOT)} does not match agents/ source")
                    roles_ok = False
                    all_ok = False
            unexpected = sorted(p.name for p in DROIDS_DIR.glob("*.md") if p.name not in expected_roles) if DROIDS_DIR.is_dir() else []
            if unexpected:
                print(f"DRIFT: unexpected files in {DROIDS_DIR.relative_to(ROOT)}: {unexpected}")
                all_ok = False
            elif roles_ok:
                print(f"PASS: {len(expected_roles)} droid roles at {DROIDS_DIR.relative_to(ROOT)} in sync")
    # Policy coverage and the Claude/hook probes are package-wide: they are
    # reported regardless of which host's manifests this run projected.
    claude_ok = check_claude_plugin(desc)
    hooks_ok = check_hooks(desc.raw_dict)
    return all_ok and check_model_role_plan(desc) and claude_ok and hooks_ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check manifests for drift")
    parser.add_argument("--project", action="store_true", help="Project manifests to disk")
    parser.add_argument("--host", choices=list(TARGET_MAP.keys()), help="Target specific host")
    args = parser.parse_args()

    desc, _ = load_package_descriptor()
    hosts = [args.host] if args.host else None

    if args.project:
        project_all(desc, hosts)
        sys.exit(0)
    elif args.check:
        ok = check_all(desc, hosts)
        sys.exit(0 if ok else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
