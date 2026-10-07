#!/usr/bin/env python3
"""Project canonical pstack.package.json into harness-native plugin descriptors.

Implements the projection lever per Build the Lever + Model the Domain + Zero Drift:
    pstack.package.json (canonical source of truth)
        ├── .grok-plugin/plugin.json
        ├── .codex-plugin/plugin.json
        ├── .omp-plugin/plugin.json
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

from scripts.portability_schema import PackageDescriptor, ValidationError

PACKAGE_JSON = ROOT / "pstack.package.json"
AGENTS_DIR = ROOT / "agents"
DROIDS_DIR = ROOT / "droids"
FACTORY_PLUGIN_DIR = ROOT / ".factory-plugin"

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
    return {
        "name": desc.name,
        "version": desc.version,
        "description": f"{desc.name} for Oh-My-Pi (OMP): portable principles and playbooks.",
        "skills_root": f"./{desc.skills_root}/",
        "entrypoint": desc.entrypoints.get("router", "skills/poteto-mode/SKILL.md"),
        "lifecycle": {
            "install": desc.lifecycle.get("install", ""),
            "verify": desc.lifecycle.get("verify", ""),
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


def generate_antigravity_models(desc: PackageDescriptor) -> Dict[str, Any]:
    return {
        "singleRoleDefault": "pro",
        "panel": ["pro", "flash"],
        "available": [
            {"label": "Gemini Pro", "slug": "pro"},
            {"label": "Gemini Flash", "slug": "flash"},
            {"label": "Gemini Flash Lite", "slug": "flash_lite"},
            {"label": "Inherited Model", "slug": "inherit"},
        ],
        "roles": [
            {"role": "feature, refactoring", "models": ["pro"], "skill": "poteto-mode"},
            {"role": "bug-fix", "models": ["pro"], "skill": "poteto-mode"},
            {"role": "perf-issue", "models": ["pro"], "skill": "poteto-mode"},
            {"role": "hillclimb", "models": ["pro"], "skill": "poteto-mode"},
            {"role": "judgment and prose", "models": ["pro"], "skill": "poteto-mode"},
            {"role": "strongest judgment", "models": ["pro"], "skill": "poteto-mode"},
            {"role": "how explorer", "models": ["pro"], "skill": "how"},
            {"role": "how explainer", "models": ["pro"], "skill": "how"},
            {"role": "why investigators", "models": ["pro"], "skill": "why"},
            {"role": "why synthesizer", "models": ["pro"], "skill": "why"},
            {"role": "reflect tooling", "models": ["pro"], "skill": "reflect"},
            {"role": "reflect judgment, divergent, synthesizer", "models": ["pro"], "skill": "reflect"},
            {"role": "arena runners", "models": "panel", "skill": "arena"},
            {"role": "arena cross-judge pool", "models": "panel", "skill": "arena"},
            {"role": "swarm workers", "models": ["flash"], "skill": "swarm"},
            {"role": "architect runners", "models": "panel", "skill": "architect"},
            {"role": "interrogate reviewers", "models": "panel", "skill": "interrogate"},
        ],
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
    "omp": (ROOT / ".omp-plugin" / "plugin.json", generate_omp_manifest),
    "opencode": (ROOT / ".opencode-plugin" / "package.json", generate_opencode_manifest),
    "antigravity": (ROOT / ".antigravity-plugin" / "plugin.json", generate_antigravity_manifest),
    "droid": (FACTORY_PLUGIN_DIR / "plugin.json", generate_droid_manifest),
}


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



def check_all(desc: PackageDescriptor, hosts: List[str] | None = None) -> bool:
    targets = hosts or list(TARGET_MAP.keys())
    all_ok = True
    for host in targets:
        if host not in TARGET_MAP:
            continue
        dest_file, generator = TARGET_MAP[host]
        if not dest_file.is_file():
            print(f"MISSING: {host} manifest not found at {dest_file.relative_to(ROOT)}")
            all_ok = False
            continue
        expected = generator(desc)
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
            if not models_file.is_file():
                print(f"MISSING: antigravity models not found at {models_file.relative_to(ROOT)}")
                all_ok = False
            else:
                expected_models = generate_antigravity_models(desc)
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
    return all_ok


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
