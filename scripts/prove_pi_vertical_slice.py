#!/usr/bin/env python3
"""Prove one smallest end-to-end Pi candidate vertical slice (#897, #902).

Offline (default):
  Verifies the canonical poteto-mode router, typed candidate profile (profiles/pstack-pi.json),
  essential extensions manifest (references/pi-essential-extensions.json), settings discovery (.pi/settings.json),
  and 53 bounded negative mutants. Emits a four-plane receipt with runtime plane BLOCKED.

Live (--live or PSTACK_RUN_PI_LIVE=1):
  Probes local Pi 1.5.0 binary presence, package list via `pi list`, checks for essential engineering
  extensions (pi-subagents, pi-better-sandbox, pi-verdict, pi-ask-user), checks for conflicting
  extensions, and probes non-interactive invocation. Missing required extensions or conflicting
  extensions fail closed with BLOCKED status; never promotes unobserved behavior to PASS.

Usage:
    python3 scripts/prove_pi_vertical_slice.py [--live] [--json] [--out PATH]

Exit codes: 0 PASS, 1 FAIL, 2 BLOCKED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    ScenarioResult,
    VerificationReceipt,
    compute_surface_revisions,
    reduce_verdicts,
    settle_planes,
)
from scripts.verify_pi_candidate import (
    CandidateContractError,
    bounded_negative_controls,
    check_contract,
    check_verdict_template,
    from_disk,
)

HOST = "pstack:pi"
ADAPTER_VERSION = "0.15.36"
ROUTER_SKILL = "poteto-mode"
LIVE_ENV = "PSTACK_RUN_PI_LIVE"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_revision(root: Path = ROOT, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=str(root), capture_output=True, text=True, check=False
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def probe_pi_binary() -> Optional[str]:
    return shutil.which("pi")


def probe_pi_version(pi_bin: Optional[str]) -> str:
    if not pi_bin:
        return ""
    try:
        proc = subprocess.run(
            [pi_bin, "--version"], capture_output=True, text=True, check=False, timeout=10
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def probe_pi_packages(pi_bin: Optional[str]) -> Dict[str, str]:
    """Parse installed packages from `pi list`."""
    if not pi_bin:
        return {}
    try:
        proc = subprocess.run(
            [pi_bin, "list"], capture_output=True, text=True, check=False, timeout=15
        )
        if proc.returncode != 0:
            return {}
        packages: Dict[str, str] = {}
        for line in proc.stdout.splitlines():
            line = line.strip()
            match = re.match(r"^npm:(@?[\w/-]+)@([\w.-]+)$", line)
            if match:
                packages[match.group(1)] = match.group(2)
        return packages
    except (OSError, subprocess.SubprocessError):
        return {}


def run_ephemeral_probe(pi_bin: str) -> Dict[str, Any]:
    """Execute a minimal non-interactive ephemeral probe: pi -p --no-session --no-tools 'echo HELLO'."""
    try:
        started = time.time()
        proc = subprocess.run(
            [pi_bin, "-p", "--no-session", "--no-tools", "echo HELLO"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        duration = round(time.time() - started, 3)
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "duration_s": duration,
        }
    except (OSError, subprocess.SubprocessError) as err:
        return {
            "exit_code": 1,
            "stdout": "",
            "stderr": str(err),
            "duration_s": 0.0,
        }


def offline_slice() -> Dict[str, Any]:
    started = time.time()
    canonical_router = ROOT / "skills" / ROUTER_SKILL / "SKILL.md"
    router_ok = canonical_router.is_file()
    router_sha = sha256_file(canonical_router) if router_ok else ""

    profile, manifest, settings = from_disk()
    profile_errors: List[str] = []
    try:
        check_contract(profile, manifest, settings)
        check_verdict_template()
    except CandidateContractError as err:
        profile_errors.append(str(err))

    settings_file = ROOT / ".pi" / "settings.json"
    settings_ok = (
        settings_file.is_file()
        and settings.get("skills") == ["../skills"]
        and settings.get("subagents", {}).get("projectRootResolution") == "git-root"
        and settings.get("subagents", {}).get("agentScanDirs") == ["../agents"]
        and not settings.get("packages")
    )

    mutant_count = bounded_negative_controls()
    mutants_ok = mutant_count == 53

    return {
        "duration_s": round(time.time() - started, 3),
        "router_ok": router_ok,
        "router_sha256": router_sha,
        "profile_ok": len(profile_errors) == 0,
        "profile_errors": profile_errors,
        "settings_ok": settings_ok,
        "mutants_ok": mutants_ok,
        "mutant_count": mutant_count,
        "profile": profile,
        "manifest": manifest,
        "settings": settings,
    }


def live_slice(manifest: Dict[str, Any]) -> Dict[str, Any]:
    started = time.time()
    pi_bin = probe_pi_binary()
    pi_ver = probe_pi_version(pi_bin)
    packages = probe_pi_packages(pi_bin)

    required_eng = [e["name"] for e in manifest.get("engineering", [])]
    pinned_versions = {e["name"]: e["version"] for e in manifest.get("engineering", [])}
    conflicts = list(manifest.get("conflicts", []))

    missing_required = [pkg for pkg in required_eng if pkg not in packages]
    mismatched_versions = [
        f"{pkg} ({packages[pkg]} != {pinned_versions[pkg]})"
        for pkg in required_eng
        if pkg in packages and packages[pkg] != pinned_versions[pkg]
    ]
    detected_conflicts = [pkg for pkg in conflicts if pkg in packages]

    ephemeral_probe: Optional[Dict[str, Any]] = None
    if pi_bin:
        ephemeral_probe = run_ephemeral_probe(pi_bin)

    return {
        "duration_s": round(time.time() - started, 3),
        "pi_bin": pi_bin,
        "pi_version": pi_ver,
        "packages": packages,
        "missing_required": missing_required,
        "mismatched_versions": mismatched_versions,
        "detected_conflicts": detected_conflicts,
        "ephemeral_probe": ephemeral_probe,
    }


def build_scenarios(
    offline: Dict[str, Any],
    live: Optional[Dict[str, Any]],
    live_requested: bool,
) -> List[ScenarioResult]:
    scenarios: List[ScenarioResult] = []

    # 1. Canonical Plane
    scenarios.append(
        ScenarioResult(
            id="slice-router-canonical",
            description="The canonical poteto-mode router is present and verified",
            plane="canonical",
            command=f"sha256(skills/{ROUTER_SKILL}/SKILL.md)",
            exit_code=0 if offline["router_ok"] else 1,
            stdout_snippet=f"canonical router sha256={offline['router_sha256'][:16]}",
            verdict="PASS" if offline["router_ok"] else "FAIL",
            duration_s=offline["duration_s"],
            evidence_level="offline",
        )
    )

    # 2. Adapter Plane
    adapter_ok = offline["profile_ok"]
    adapter_snippet = (
        "PASS: candidate profile and extensions policy conform to typed schema"
        if adapter_ok
        else f"FAIL: {'; '.join(offline['profile_errors'])}"
    )
    scenarios.append(
        ScenarioResult(
            id="slice-pi-profile-and-manifest",
            description="Candidate profiles/pstack-pi.json and references/pi-essential-extensions.json contract",
            plane="adapter",
            command="scripts/verify_pi_candidate.py check",
            exit_code=0 if adapter_ok else 1,
            stdout_snippet=adapter_snippet,
            verdict="PASS" if adapter_ok else "FAIL",
            duration_s=offline["duration_s"],
            evidence_level="offline",
        )
    )

    scenarios.append(
        ScenarioResult(
            id="slice-pi-bounded-mutations",
            description="53 bounded negative mutations rejected by fail-closed candidate validator",
            plane="adapter",
            command="scripts/verify_pi_candidate.py model",
            exit_code=0 if offline["mutants_ok"] else 1,
            stdout_snippet=f"PASS: {offline['mutant_count']} bounded mutants rejected",
            verdict="PASS" if offline["mutants_ok"] else "FAIL",
            duration_s=offline["duration_s"],
            evidence_level="offline",
        )
    )

    # 3. Package Plane
    package_ok = offline["settings_ok"]
    package_snippet = (
        "PASS: .pi/settings.json discovers git-root skills/agents with no automatic package installs"
        if package_ok
        else "FAIL: .pi/settings.json invalid discovery or auto-packages detected"
    )
    scenarios.append(
        ScenarioResult(
            id="slice-pi-package-discovery",
            description="Native Pi .pi/settings.json discovery configuration and package confinement",
            plane="package",
            command="cat .pi/settings.json",
            exit_code=0 if package_ok else 1,
            stdout_snippet=package_snippet,
            verdict="PASS" if package_ok else "FAIL",
            duration_s=offline["duration_s"],
            evidence_level="offline",
        )
    )

    # 4. Runtime Plane
    if not live_requested or live is None:
        runtime_snippet = "BLOCKED: live runtime execution not requested (pass --live or PSTACK_RUN_PI_LIVE=1)"
        runtime_verdict = "BLOCKED"
        runtime_exit = 2
        runtime_duration = 0.0
    else:
        runtime_duration = live["duration_s"]
        unmet: List[str] = []
        if not live["pi_bin"]:
            unmet.append("pi binary not found in PATH")
        if live["missing_required"]:
            unmet.append(f"missing required extensions: {', '.join(live['missing_required'])}")
        if live["mismatched_versions"]:
            unmet.append(f"version mismatch: {', '.join(live['mismatched_versions'])}")
        if live["detected_conflicts"]:
            unmet.append(f"conflicting extension present: {', '.join(live['detected_conflicts'])}")

        probe = live.get("ephemeral_probe")
        if probe and probe.get("exit_code") != 0:
            unmet.append(f"ephemeral probe exited {probe.get('exit_code')}")

        if unmet:
            runtime_verdict = "BLOCKED"
            runtime_exit = 2
            runtime_snippet = f"BLOCKED: {'; '.join(unmet)}; zero unverified runtime claims promoted"
        else:
            # A no-tools Pi echo probe establishes *only* process/package preflight.
            # It cannot exercise child launch, tool_call denials, or OS confinement.
            # Until a real actor driver supplies per-child proof, fail closed.
            runtime_verdict = "BLOCKED"
            runtime_exit = 2
            runtime_snippet = (
                f"BLOCKED: Pi {live['pi_version']} and pinned packages pass preflight, "
                "but no real child ID, denied subagent_launch, terminal join/cancel, "
                "or parent/child/background sandbox-effect receipt was observed"
            )

    scenarios.append(
        ScenarioResult(
            id="slice-runtime-child-spawn",
            description="Pi process/package preflight only; live child authorization and sandbox remain unverified",
            plane="runtime",
            command="pi -p --no-session --no-tools (ephemeral probe + package audit)",
            exit_code=runtime_exit,
            stdout_snippet=runtime_snippet,
            verdict=runtime_verdict,
            duration_s=runtime_duration,
            evidence_level="observed_live" if runtime_verdict == "PASS" else "offline",
        )
    )

    return scenarios


def build_receipt(
    scenarios: List[ScenarioResult],
    head: str,
    host_version: str,
) -> VerificationReceipt:
    planes = settle_planes(scenarios)
    overall_verdict = reduce_verdicts(planes.values())
    revisions = compute_surface_revisions(ROOT, HOST, profile_path=ROOT / "profiles/pstack-pi.json")
    run_id = f"pi-slice-{secrets.token_hex(4)}"
    receipt = VerificationReceipt(
        run_id=run_id,
        host=HOST,
        host_version=host_version or "unobserved",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        overall_verdict=overall_verdict,
        planes=planes,
        surface_revisions=revisions,
        scenarios=scenarios,
        artifacts=[],
        claim=f"Pi candidate contract/preflight slice at exact head {head}; runtime capability NOT PROVEN",
        kind="runtime",
        adapter_version=ADAPTER_VERSION,
    )
    receipt.validate()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--live", action="store_true", help="Attempt live Pi subprocess and package probe")
    parser.add_argument("--json", action="store_true", help="Print JSON receipt to stdout")
    parser.add_argument("--out", type=Path, help="Write receipt JSON to path")
    args = parser.parse_args()

    live_requested = args.live or bool(os.environ.get(LIVE_ENV))
    head = git_revision(ROOT, "rev-parse", "HEAD")

    offline = offline_slice()
    live = live_slice(offline["manifest"]) if live_requested else None
    scenarios = build_scenarios(offline, live, live_requested)

    host_ver = (live.get("pi_version") if live else "") or "unobserved"
    receipt = build_receipt(scenarios, head, host_ver)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(asdict(receipt), indent=2), encoding="utf-8")

    reason = (
        f"canonical={receipt.planes['canonical']}, "
        f"adapter={receipt.planes['adapter']}, "
        f"package={receipt.planes['package']}, "
        f"runtime={receipt.planes['runtime']}"
    )

    if args.json:
        payload = {
            "lever": "prove-pi-vertical-slice",
            "issue": 897,
            "verdict": receipt.overall_verdict,
            "reason": reason,
            "live_requested": live_requested,
            "exact_head": head,
            "host_version": host_ver,
            "planes": receipt.planes,
            "offline": {
                "duration_s": offline["duration_s"],
                "router_ok": offline["router_ok"],
                "profile_ok": offline["profile_ok"],
                "settings_ok": offline["settings_ok"],
                "mutants_ok": offline["mutants_ok"],
            },
            "live": live,
            "receipt": asdict(receipt),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Pi vertical slice: {receipt.overall_verdict}")
        print(f"  exact_head: {head}")
        print(f"  planes: {receipt.planes}")
        print(f"  reason: {reason}")
        if live:
            missing = live.get("missing_required")
            conflicts = live.get("detected_conflicts")
            if missing:
                print(f"  missing required extensions: {missing}")
            if conflicts:
                print(f"  detected conflicts: {conflicts}")

    if receipt.overall_verdict == "PASS":
        return 0
    elif receipt.overall_verdict == "BLOCKED":
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
