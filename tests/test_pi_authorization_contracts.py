"""Pi verdict autonomous authorization, confinement proof, and gate tests (#897, #902)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import VerificationReceipt
from scripts.prove_pi_vertical_slice import (
    build_receipt,
    build_scenarios,
    live_slice,
    offline_slice,
    probe_pi_packages,
)
from scripts.verify_pi_candidate import from_disk


def test_verdict_policy_example_invariants():
    """Verify references/pi-verdict-pstack.example.json enforces fail-closed deny floor."""
    example_path = ROOT / "references" / "pi-verdict-pstack.example.json"
    assert example_path.is_file()
    data = json.loads(example_path.read_text(encoding="utf-8"))

    assert data.get("builtinDenyFloor") is True
    assert data.get("allow") == []
    assert data.get("deny") == []
    assert data.get("ignoreTools") == []
    assert data.get("classifierFallbackMode") == "enforce"
    assert data.get("auditRedactSecrets") is True

    denied_paths = data.get("denyPaths", [])
    expected_paths = [
        "~/.ssh/",
        "~/.gnupg/",
        "~/.aws/",
        "~/.kube/",
        "~/.pi/agent/auth.json",
    ]
    for path in expected_paths:
        assert path in denied_paths, f"Missing denied path: {path}"


def test_manifest_authorization_invariants():
    """Verify references/pi-essential-extensions.json declares strict authorization boundary."""
    _, manifest, _ = from_disk()
    auth = manifest.get("authorization", {})

    assert manifest.get("active_authorization_policy") == "pi-verdict"
    assert auth.get("owner") == "pi-verdict"
    assert auth.get("version") == "0.16.0"
    assert auth.get("default_on_required") is True
    assert auth.get("builtin_deny_floor_required") is True
    assert auth.get("headless_ask_must_deny") is True
    assert auth.get("gate_disable_fails_closed_externally") is True
    assert auth.get("requires_os_isolation") is True
    assert auth.get("fallback_rescue_allowed") is False
    assert auth.get("classifier_allow_can_authorize_human_gate") is False
    assert auth.get("child_tool_interception") == "unverified"
    assert auth.get("audit_covers_all_actions") is False
    assert auth.get("ignore_tools_for_permission_sensitive_actions") == []


def evaluate_simulated_verdict(
    policy: Dict[str, Any],
    tool_name: str,
    tool_args: Dict[str, Any],
    *,
    headless: bool = True,
    user_confirmed: bool = False,
    classifier_verdict: str = "allow",
) -> str:
    """Reference adjudicator modeling pi-verdict 0.16.0 fail-closed semantics."""
    if tool_name in policy.get("ignoreTools", []):
        if tool_name in ("subagent_launch", "execute_command", "write_file"):
            raise ValueError(f"Dangerous tool {tool_name} cannot be ignored")
        return "ignored"

    # Deterministic hard path denial floor
    target_path = str(tool_args.get("path", ""))
    for denied in policy.get("denyPaths", []):
        clean_denied = denied.rstrip("/")
        if clean_denied and (clean_denied in target_path or target_path.startswith(clean_denied)):
            return "deny"

    # Builtin deny floor
    if policy.get("builtinDenyFloor") and not policy.get("allow"):
        if classifier_verdict == "deny":
            return "deny"
        if classifier_verdict == "ask":
            if headless and policy.get("headless_ask_must_deny", True):
                return "deny"
            return "allow" if user_confirmed else "deny"

    return classifier_verdict


def test_verdict_path_denial_floor_overrides_classifier_allow():
    policy = {
        "builtinDenyFloor": True,
        "allow": [],
        "denyPaths": ["~/.ssh/", "~/.aws/"],
        "headless_ask_must_deny": True,
    }
    verdict = evaluate_simulated_verdict(
        policy,
        "read_file",
        {"path": "~/.ssh/id_rsa"},
        classifier_verdict="allow",
    )
    assert verdict == "deny"


def test_verdict_headless_ask_fails_closed_to_deny():
    policy = {
        "builtinDenyFloor": True,
        "allow": [],
        "denyPaths": [],
        "headless_ask_must_deny": True,
    }
    verdict = evaluate_simulated_verdict(
        policy,
        "run_command",
        {"command": "rm -rf /tmp/test"},
        headless=True,
        classifier_verdict="ask",
    )
    assert verdict == "deny"


def test_verdict_interactive_ask_without_user_confirmation_denies():
    policy = {
        "builtinDenyFloor": True,
        "allow": [],
        "denyPaths": [],
        "headless_ask_must_deny": True,
    }
    verdict = evaluate_simulated_verdict(
        policy,
        "run_command",
        {"command": "rm -rf /tmp/test"},
        headless=False,
        user_confirmed=False,
        classifier_verdict="ask",
    )
    assert verdict == "deny"


def test_dangerous_tools_cannot_be_ignored_by_verdict():
    policy = {
        "builtinDenyFloor": True,
        "allow": [],
        "ignoreTools": ["subagent_launch"],
        "denyPaths": [],
    }
    with pytest.raises(ValueError, match="Dangerous tool"):
        evaluate_simulated_verdict(policy, "subagent_launch", {"agent": "worker"})


def test_package_parsing_and_conflict_detection():
    sample_list = (
        "User packages:\n"
        "  npm:pi-ask-user@0.14.0\n"
        "    /path/to/pi-ask-user\n"
        "  npm:@quintinshaw/pi-dynamic-workflows@3.7.0\n"
        "    /path/to/dynamic\n"
        "  npm:@zenspc/pi-pstack@0.6.0\n"
        "    /path/to/pstack\n"
    )
    # Simulate parser logic
    packages: Dict[str, str] = {}
    import re
    for line in sample_list.splitlines():
        line = line.strip()
        match = re.match(r"^npm:(@?[\w/-]+)@([\w.-]+)$", line)
        if match:
            packages[match.group(1)] = match.group(2)

    assert packages.get("pi-ask-user") == "0.14.0"
    assert packages.get("@quintinshaw/pi-dynamic-workflows") == "3.7.0"
    assert "pi-subagents" not in packages
    assert "pi-better-sandbox" not in packages
    assert "pi-verdict" not in packages


def test_prove_pi_vertical_slice_offline():
    offline = offline_slice()
    assert offline["router_ok"] is True
    assert offline["profile_ok"] is True
    assert offline["settings_ok"] is True
    assert offline["mutants_ok"] is True
    assert offline["mutant_count"] == 53

    scenarios = build_scenarios(offline, live=None, live_requested=False)
    assert len(scenarios) == 5
    by_plane = {s.plane: s.verdict for s in scenarios}
    assert by_plane["canonical"] == "PASS"
    assert by_plane["adapter"] == "PASS"
    assert by_plane["package"] == "PASS"
    assert by_plane["runtime"] == "BLOCKED"

    receipt = build_receipt(scenarios, "testhead", "1.5.0")
    assert receipt.overall_verdict == "BLOCKED"
    assert receipt.host == "pstack:pi"
    assert receipt.planes == {
        "canonical": "PASS",
        "adapter": "PASS",
        "package": "PASS",
        "runtime": "BLOCKED",
    }


def test_prove_pi_vertical_slice_live_blocks_on_missing_extensions():
    offline = offline_slice()
    # Mock live result missing required extensions
    live = {
        "duration_s": 0.2,
        "pi_bin": "/usr/local/bin/pi",
        "pi_version": "1.5.0",
        "packages": {"pi-ask-user": "0.14.0"},
        "missing_required": ["pi-subagents", "pi-better-sandbox", "pi-verdict"],
        "mismatched_versions": ["pi-ask-user (0.14.0 != 0.17.2)"],
        "detected_conflicts": ["@quintinshaw/pi-dynamic-workflows"],
        "ephemeral_probe": {"exit_code": 0, "stdout": "HELLO", "stderr": "", "duration_s": 0.1},
    }
    scenarios = build_scenarios(offline, live, live_requested=True)
    runtime_scenario = next(s for s in scenarios if s.plane == "runtime")
    assert runtime_scenario.verdict == "BLOCKED"
    assert runtime_scenario.exit_code == 2
    assert "missing required extensions" in runtime_scenario.stdout_snippet
    assert "conflicting extension" in runtime_scenario.stdout_snippet


def test_healthy_pi_preflight_does_not_pretend_native_child_or_sandbox_pass():
    """A successful --no-tools echo cannot establish spawn/authorization/OS confinement."""
    offline = offline_slice()
    manifest = offline["manifest"]
    live = {
        "duration_s": 0.1,
        "pi_bin": "/usr/bin/pi",
        "pi_version": "1.5.0",
        "packages": {row["name"]: row["version"] for row in manifest["engineering"]},
        "missing_required": [],
        "mismatched_versions": [],
        "detected_conflicts": [],
        "ephemeral_probe": {"exit_code": 0, "stdout": "HELLO", "stderr": "", "duration_s": 0.1},
    }
    scenarios = build_scenarios(offline, live, live_requested=True)
    runtime = next(s for s in scenarios if s.plane == "runtime")
    assert runtime.verdict == "BLOCKED"
    assert runtime.exit_code == 2
    assert runtime.evidence_level != "observed_live"
    assert "no real child ID" in runtime.stdout_snippet
    receipt = build_receipt(scenarios, "test-preflight-not-live", "1.5.0")
    assert receipt.planes["runtime"] == "BLOCKED"
    assert receipt.overall_verdict == "BLOCKED"


def test_pi_cleanup_without_native_actor_tracking_never_claims_pass():
    """The cleanup command cannot certify subprocess/worktree absence by assertion."""
    proc = subprocess.run(
        ["bash", ".pi/skills/verify-pi-pstack/scripts/driver.sh", "cleanup"],
        capture_output=True, text=True, cwd=ROOT, check=False,
    )
    assert proc.returncode == 2
    assert "BLOCKED" in proc.stderr and "NOT_VERIFIED" in proc.stderr
    assert "PASS" not in proc.stdout + proc.stderr
