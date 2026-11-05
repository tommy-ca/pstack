#!/usr/bin/env python3
"""Offline Pi candidate contracts. NO observed Pi runtime claims or native receipts."""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.portability_types import HarnessProfile, PORTABLE_CAPABILITY_UNIVERSE, ValidationError

HOST = "pstack:pi"
ENGINEERING = ("pi-subagents", "pi-better-sandbox", "pi-ask-user")
RESEARCH = ("pi-web-access",)


class CandidateContractError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise CandidateContractError(f"{path}: expected JSON object")
    return doc


def check_contract(p: dict[str, Any], m: dict[str, Any], s: dict[str, Any]) -> None:
    try:
        HarnessProfile.from_dict(p).validate()
    except (ValidationError, TypeError) as err:
        raise CandidateContractError(f"PStack typed profile: {err}") from err
    if p.get("host") != HOST or p.get("support_state") != "candidate":
        raise CandidateContractError("Standalone Pi must remain a namespaced candidate")
    if p.get("plugin_manifest") != ".pi/settings.json" or p.get("skills_dir") != ".pi/skills":
        raise CandidateContractError("Pi must declare native skill/settings paths")
    rows = p.get("bindings", [])
    by_cap = {r["capability"]: r for r in rows}
    if len(rows) != 17 or set(by_cap) != set(PORTABLE_CAPABILITY_UNIVERSE):
        raise CandidateContractError("All 17 portable capabilities must be mapped once")
    for cap, row in by_cap.items():
        if row.get("host") != HOST or row.get("verification_status") not in ("static-only", "unverified"):
            raise CandidateContractError(f"{cap}: runtime promotion not proven")
        if row.get("evidence_ref"):
            raise CandidateContractError(f"{cap}: no imported evidence allowed")
    for cap in ("agent.spawn", "agent.join", "agent.cancel", "schedule", "monitor"):
        row = by_cap[cap]
        if row["implementation_status"] != "version-gated" or "pi-subagents@" not in row.get("primitive", ""):
            raise CandidateContractError(f"{cap}: Pi delegates to one external subagent engine")
    if by_cap["human.ask"]["implementation_status"] != "version-gated" or "pi-ask-user@" not in by_cap["human.ask"].get("primitive", ""):
        raise CandidateContractError("human.ask requires interactive pi-ask-user")
    if by_cap["human.gate"]["implementation_status"] != "gap" or by_cap["human.gate"]["enforcement"] == "hard":
        raise CandidateContractError("human.gate remains an authorization gap")
    if by_cap["workspace.readonly"]["enforcement"] == "hard":
        raise CandidateContractError("Unverified child sandbox may not be marked hard")
    if m.get("host") != HOST or m.get("verification_status") != "static-only":
        raise CandidateContractError("Extension manifest may not claim runtime verification")
    eng, research = m.get("engineering", []), m.get("research_addon", [])
    if [e.get("name") for e in eng] != list(ENGINEERING) or [e.get("name") for e in research] != list(RESEARCH):
        raise CandidateContractError("Expected exactly 3 engineering and 1 research extension")
    names = [e["name"] for e in eng + research]
    if len(set(names)) != len(names):
        raise CandidateContractError("Duplicate extension owner")
    for package in eng + research:
        if not re.fullmatch(r"\d+\.\d+\.\d+", package.get("version", "")):
            raise CandidateContractError(f"Unpinned extension: {package.get('name')}")
        if not package.get("source", "").startswith("https://"):
            raise CandidateContractError(f"Source URL missing: {package.get('name')}")
    if set(names) & set(m.get("conflicts", [])):
        raise CandidateContractError("Security/delegate engine collision")
    if not {"pi-permission-modes", "@quintinshaw/pi-dynamic-workflows"} <= set(m.get("conflicts", [])):
        raise CandidateContractError("Competing owners not excluded")
    if m.get("active_security_policy") != "pi-better-sandbox":
        raise CandidateContractError("Security owner ambiguous")
    policies = m.get("policies", {})
    for key in ("independent_child_auth_required", "headless_approval_fail_closed",
                "sandbox_main_enabled_required", "sandbox_subagents_enabled_required",
                "sandbox_background_enabled_for_detached_required"):
        if policies.get(key) is not True:
            raise CandidateContractError(f"Not fail closed: {key}")
    if policies.get("stored_credentials") != "deny" or policies.get("outside_project") != "deny":
        raise CandidateContractError("Credential/outside project defaults must be deny")
    if policies.get("dynamic_extension_trust_boundary") != "unverified":
        raise CandidateContractError("Extension process has not been confined")
    if s.get("skills") != ["../skills"] or s.get("enableSkillCommands") is not True:
        raise CandidateContractError("Native Pi must discover canonical shared skills")
    subagents = s.get("subagents", {})
    if subagents.get("projectRootResolution") != "git-root" or subagents.get("agentScanDirs") != ["../agents"]:
        raise CandidateContractError("Pi subagent roles must resolve from canonical repository agents in git-root worktrees")
    if s.get("packages") or s.get("extensions"):
        raise CandidateContractError("No automatic third-party package installation")


def from_disk(root: Path = ROOT) -> tuple[dict, dict, dict]:
    return (load_json(root / "profiles/pstack-pi.json"),
            load_json(root / "references/pi-essential-extensions.json"),
            load_json(root / ".pi/settings.json"))


def bounded_negative_controls(root: Path = ROOT) -> int:
    """Explore fixed finite input mutations of existing PStack validator code."""
    p, m, s = from_disk(root)
    check_contract(p, m, s)
    count = 0

    def reject(profile: dict, manifest: dict, settings: dict, label: str) -> None:
        nonlocal count
        try:
            check_contract(profile, manifest, settings)
        except CandidateContractError:
            count += 1
            return
        raise AssertionError(f"Mutant accepted: {label}")

    for state in ("mapped", "packaged", "verified", "supported"):
        mutant = copy.deepcopy(p)
        mutant["support_state"] = state
        reject(mutant, m, s, state)
    for cap in PORTABLE_CAPABILITY_UNIVERSE:
        mutant = copy.deepcopy(p)
        next(r for r in mutant["bindings"] if r["capability"] == cap)["verification_status"] = "verified"
        reject(mutant, m, s, f"{cap}: false proof")
        mutant = copy.deepcopy(p)
        mutant["bindings"].append(copy.deepcopy(next(r for r in mutant["bindings"] if r["capability"] == cap)))
        reject(mutant, m, s, f"{cap}: duplicated")
    for label in ("extra-engine", "credential-write", "unapproved-headless", "package-execution"):
        pm, mm, sm = copy.deepcopy(p), copy.deepcopy(m), copy.deepcopy(s)
        if label == "extra-engine":
            mm["engineering"].append({"name":"pi-dynamic-workflows", "version":"1.0.0"})
        if label == "credential-write":
            mm["policies"]["stored_credentials"] = "write"
        if label == "unapproved-headless":
            mm["policies"]["headless_approval_fail_closed"] = False
        if label == "package-execution":
            sm["packages"] = ["npm:unreviewed"]
        reject(pm, mm, sm, label)
    mutant = copy.deepcopy(p)
    next(r for r in mutant["bindings"] if r["capability"] == "human.gate")["implementation_status"] = "native"
    reject(mutant, m, s, "unproven human gate")
    return count


def smoke() -> int:
    if not shutil.which("pi"):
        print("BLOCKED: Pi not installed; no native child/sandbox proof")
        return 2
    try:
        proc = subprocess.run(["pi","--version"], capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as err:
        print(f"BLOCKED: unable to check Pi: {err}")
        return 2
    if proc.returncode:
        print(f"BLOCKED: Pi version command exited {proc.returncode}")
        return 2
    print(f"UNTESTED: {proc.stdout.strip()} is present; no child, worktree or sandbox was driven")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check","model","smoke"))
    args = parser.parse_args()
    try:
        if args.action == "check":
            check_contract(*from_disk())
            print("PASS: static Pi candidate profile and minimal extension policy; NOT native runtime")
            return 0
        if args.action == "model":
            n = bounded_negative_controls()
            print(f"PASS: {n} bounded invalid variants rejected; NOT Pi runtime proof")
            return 0
        return smoke()
    except (CandidateContractError, ValueError, OSError, AssertionError) as err:
        print(f"FAIL: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
