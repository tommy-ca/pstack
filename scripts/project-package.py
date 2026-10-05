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
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import PackageDescriptor, ValidationError

PACKAGE_JSON = ROOT / "pstack.package.json"


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
        "description": f"{desc.name} for Grok Build: shared skills, HARNESS.md mapping.",
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
    }


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


TARGET_MAP = {
    "grok": (ROOT / ".grok-plugin" / "plugin.json", generate_grok_manifest),
    "codex": (ROOT / ".codex-plugin" / "plugin.json", generate_codex_manifest),
    "omp": (ROOT / ".omp-plugin" / "plugin.json", generate_omp_manifest),
    "opencode": (ROOT / ".opencode-plugin" / "package.json", generate_opencode_manifest),
    "antigravity": (ROOT / ".antigravity-plugin" / "plugin.json", generate_antigravity_manifest),
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
