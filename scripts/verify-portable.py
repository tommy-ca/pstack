#!/usr/bin/env python3
"""Portable lever verification engine for pstack across agent harnesses.

Implements the pattern from Build the Lever + Prove It Works + create-verification-skill:
    Launch -> Doctor -> Drive -> Proof Bar -> Evidence -> Cleanup

Usage:
    python3 scripts/verify-portable.py doctor [--host <host>]
    python3 scripts/verify-portable.py drive --feature <feature> [--host <host>]
    python3 scripts/verify-portable.py run [--host <host>] [--evidence-dir <dir>]
    python3 scripts/verify-portable.py refresh-static [--host <host>] [--evidence-dir <dir>]
    python3 scripts/verify-portable.py select-checks --base <ref> [--head <ref>] [--json]
        [--record <path>] [--receipt <path>] [--outcome <check-id>=<verdict>]
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    Binding,
    Capability,
    ChildSettlement,
    Evidence,
    HarnessProfile,
    PackageDescriptor,
    REQUIRED_CAPABILITIES,
    ScenarioResult,
    SurfaceRevisions,
    VerificationReceipt,
    ValidationError,
    check_evidence_durability,
    compute_surface_revisions,
    derive_support_state,
    preserve_observed_settlements,
    _is_observed_settlement,
)
from scripts.drivers import get_driver
from scripts.evidence_receipts import (
    can_claim_current_ci,
    check_check_evidence_staleness,
    compute_patch_id,
    create_check_evidence_receipt,
    load_check_evidence_receipt,
    resolve_merge_base,
    resolve_revision,
)

SUPPORTED_HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "droid")


def get_declared_hosts() -> List[str]:
    """Dynamically read declared host targets from package descriptor."""
    pkg_file = ROOT / "pstack.package.json"
    if pkg_file.is_file():
        try:
            data = json.loads(pkg_file.read_text(encoding="utf-8"))
            targets = data.get("host_targets", [])
            if targets and isinstance(targets, list):
                return [str(t) for t in targets]
        except Exception:
            pass
    return ["grok", "codex", "omp", "opencode", "antigravity", "droid"]


def get_canonical_root(root: Path) -> Path:
    git_path = root / ".git"
    if git_path.is_file():
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--git-common-dir"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
            common_dir = Path(res.stdout.strip()).resolve()
            if common_dir.name == ".git":
                return common_dir.parent
        except Exception:
            pass
    return root


DEFAULT_EVIDENCE_DIR = ROOT / ".audit" / "evidence"


def reduce_verdicts(verdicts: Iterable[str]) -> str:
    """Reduce scenario or plane verdicts according to the strict severity lattice:
    FAIL > BLOCKED > UNTESTED > PASS.
    """
    v_set = set(verdicts)
    if not v_set:
        return "UNTESTED"
    if "FAIL" in v_set:
        return "FAIL"
    if "BLOCKED" in v_set:
        return "BLOCKED"
    if "UNTESTED" in v_set:
        return "UNTESTED"
    if v_set == {"PASS"}:
        return "PASS"
    return "FAIL"


def settle_planes(scenarios: Iterable[ScenarioResult]) -> Dict[str, str]:
    """Reduce every conformance plane, gating a runtime PASS on a live settlement.

    A runtime PASS is a live claim: it needs at least one runtime scenario carrying a
    typed child spawn/join settlement. Offline scenario checks (route, config, doctor)
    prove the wiring, not a running child, so a settlement-free runtime plane is
    UNTESTED and never promotes the host. FAIL and BLOCKED are findings in their own
    right and pass through untouched (#444).

    Every path that can add or restore a scenario reduces through here. Preservation
    puts a live settlement back into the scenario list, so a plane reduced before it
    claims a live observation the receipt's own rows contradict (#322, #444).
    """
    scenarios = list(scenarios)
    planes = {
        plane: reduce_verdicts(s.verdict for s in scenarios if s.plane == plane)
        for plane in ("canonical", "adapter", "package", "runtime")
    }
    runtime = [s for s in scenarios if s.plane == "runtime"]
    for s in runtime:
        # A driver hands its settlement back as a plain dict; type it the way
        # ScenarioResult.validate does so the gate reads the same shape.
        if isinstance(s.settlement, dict):
            s.settlement = ChildSettlement(**s.settlement)
    if planes["runtime"] == "PASS" and not any(_is_observed_settlement(s) for s in runtime):
        planes["runtime"] = "UNTESTED"
    return planes


# --- Change-scoped check selection (#312) ------------------------------------
#
# Ownership: the tier inventory stays with its owners — the offline PR gate list
# is read from .github/workflows/portability-offline.yml, never re-typed here,
# and docs/verification-test-tiers.md remains the 3-tier classification. This
# table only maps a changed path to the minimal gate that can fail for it.

OFFLINE_WORKFLOW = Path(".github/workflows/portability-offline.yml")
# Standalone verifiers selected where they gate the changed surface directly and
# run offline: the boundary scanner and the canonical-inventory check.
SCAN_HOST_BOUNDARY = (sys.executable, "scripts/scan-host-boundary.py")
CANONICAL_INDEX_CHECK = (sys.executable, "scripts/canonical-index.py", "--check")


def offline_contract_tests(root: Path = ROOT) -> List[str]:
    """The offline PR gate's pytest file list, read from the workflow itself."""
    workflow = root / OFFLINE_WORKFLOW
    if not workflow.is_file():
        raise RuntimeError(f"Offline gate workflow not found: {workflow}")
    found: List[str] = []
    for match in re.findall(r"tests/[\w./-]+\.py", workflow.read_text(encoding="utf-8")):
        if match not in found:
            found.append(match)
    if not found:
        raise RuntimeError(f"No pytest files found in {workflow}")
    return found


# (path pattern, pytest module tokens, standalone verifier commands). First match
# wins, so specific rows must precede their general fallbacks.
# Tokens: "{changed}" = the changed path itself, "{offline}" = the full offline
# gate set, "!<module>" = needs the documented host-dependent opt-in env var.
CHECK_SELECTION_TABLE: List[tuple] = [
    ("tests/*.py", ("{changed}",), ()),
    ("docs/**", ("tests/test_verify_docs_sync.py",), ()),
    (
        "skills/**",
        ("tests/test_skill_frontmatter.py", "tests/test_scan_host_boundary.py"),
        (SCAN_HOST_BOUNDARY,),
    ),
    (
        "agents/**",
        (
            "tests/test_plugin_agents.py",
            "tests/test_scan_host_boundary.py",
            "tests/test_droid_projection.py",
            "tests/test_verify_harness.py",
        ),
        (SCAN_HOST_BOUNDARY,),
    ),
    (
        "droids/**",
        (
            "tests/test_plugin_agents.py",
            "tests/test_scan_host_boundary.py",
            "tests/test_droid_projection.py",
            "tests/test_verify_harness.py",
        ),
        (SCAN_HOST_BOUNDARY,),
    ),
    # Remaining markdown (root docs, ADRs, openspec prose): the docs-sync gate.
    # fnmatch needs the explicit root pattern, because `**/*.md` matches only paths
    # containing a slash and would send todo.md and README.md to the full-set default.
    ("*.md", ("tests/test_verify_docs_sync.py",), ()),
    ("**/*.md", ("tests/test_verify_docs_sync.py",), ()),
    # OpenSpec change/spec artifacts, including .openspec.yaml: prose, not code.
    ("openspec/**", ("tests/test_verify_docs_sync.py",), ()),
    ("LICENSE", ("tests/test_verify_docs_sync.py",), ()),
    (".github/**", ("{offline}",), ()),  # the gate definition itself
    ("schemas/**", ("tests/test_portability_schemas.py",), ()),
    ("profiles/**", ("tests/test_portability_schemas.py", "tests/test_evidence_durability.py"), ()),
    (
        "scripts/portability_schema.py",
        (
            "tests/test_portability_schemas.py",
            "tests/test_verdict_reduction.py",
            "tests/test_evidence_durability.py",
        ),
        (),
    ),
    (
        "scripts/evidence_receipts.py",
        ("tests/test_evidence_receipts.py", "tests/test_evidence_durability.py", "tests/test_select_checks.py"),
        (),
    ),
    ("scripts/drivers/**", ("!tests/test_harness_drivers.py", "tests/test_route_resolver.py"), ()),
    ("scripts/route_resolver.py", ("tests/test_route_resolver.py", "tests/test_droid_routing.py"), ()),
    (
        "scripts/verify-portable.py",
        ("tests/test_verify_portable.py", "tests/test_verdict_reduction.py"),
        (),
    ),
    ("scripts/verify-harness.py", ("tests/test_verify_harness.py",), ()),
    ("scripts/verify-decision-contract.py", ("tests/test_verify_decision_contract.py",), ()),
    ("scripts/verify_rollback_equivalence.py", ("tests/test_rollback_equivalence.py",), ()),
    ("scripts/scan-host-boundary.py", ("tests/test_scan_host_boundary.py",), ()),
    ("scripts/skill_frontmatter.py", ("tests/test_skill_frontmatter.py",), ()),
    ("scripts/project-package.py", ("tests/test_project_package.py", "tests/test_droid_projection.py"), ()),
    (
        "scripts/package-lifecycle.py",
        ("tests/test_package_lifecycle.py", "tests/test_package_lifecycle_safety.py"),
        (),
    ),
    ("scripts/canonical-index.py", ("tests/test_canonical_index.py",), ()),
    ("scripts/scaffold-verification-skill.py", ("tests/test_scaffold_verification_skill.py",), ()),
    ("scripts/sync-antigravity-plugin.py", ("tests/test_sync_antigravity_plugin.py",), ()),
    (
        "references/**",
        (
            "tests/test_route_resolver.py",
            "tests/test_evidence_receipts.py",
            "tests/test_droid_routing.py",
        ),
        (CANONICAL_INDEX_CHECK,),
    ),
    (
        "pstack.package.json",
        (
            "tests/test_project_package.py",
            "tests/test_verify_harness.py",
            "tests/test_portability_schemas.py",
        ),
        (),
    ),
    ("scripts/**", ("{offline}",), ()),  # any other script: the full offline set
]


def pattern_matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path == pattern[:-3] or path.startswith(pattern[:-2])
    return fnmatch.fnmatch(path, pattern)


def _check_id(command: List[str]) -> str:
    if "pytest" in command:
        return f"pytest:{command[-1]}"
    script = next((token for token in command if token.endswith(".py")), command[-1])
    return f"script:{Path(script).name}"


def _tier(token: str, offline_tests: List[str]) -> str:
    if token.startswith("!"):
        return "host_dependent"  # native smoke behind the documented opt-in
    return "offline" if token in offline_tests else "outside_gate"


def _expand(tokens: Iterable[str], path: str, offline_tests: List[str]) -> List[str]:
    expanded: List[str] = []
    for token in tokens:
        if token == "{changed}":
            expanded.append(path)
        elif token == "{offline}":
            expanded.extend(offline_tests)
        else:
            expanded.append(token)
    return expanded


def _command_for(token: str) -> List[str]:
    run = [sys.executable, "-m", "pytest", "-q", token.lstrip("!")]
    if token.startswith("!"):
        return ["env", "PSTACK_RUN_HOST_DEPENDENT_TESTS=1", *run]
    return run


def select_checks(
    changed: Iterable[str], offline_tests: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Minimal check set for the changed paths, plus the unmapped path list.

    Unmapped paths default to the full offline contract set — never to nothing.
    """
    offline = offline_tests if offline_tests is not None else offline_contract_tests()
    checks: Dict[str, Dict[str, Any]] = {}
    unmapped: List[str] = []

    def add(command: List[str], tier: str, path: str) -> None:
        check = checks.get(_check_id(command))
        if check is None:
            check = {"id": _check_id(command), "tier": tier, "command": command, "paths": []}
            checks[check["id"]] = check
        if path not in check["paths"]:
            check["paths"].append(path)

    for path in changed:
        rule = next((r for r in CHECK_SELECTION_TABLE if pattern_matches(path, r[0])), None)
        if rule is None:
            unmapped.append(path)
            rule = ("(unmapped)", ("{offline}",), ())
        _, module_tokens, verifier_commands = rule
        for token in _expand(module_tokens, path, offline):
            add(_command_for(token), _tier(token, offline), path)
        for command in verifier_commands:
            add(list(command), "offline", path)  # standalone verifier: offline/static evidence

    ordered = sorted(checks.values(), key=lambda c: (c["tier"], c["id"]))
    return {"checks": ordered, "unmapped_paths": unmapped}


def changed_paths(root: Path, base: str, head: str = "HEAD") -> Dict[str, Any]:
    """Real merge base, committed diff, plus staged/unstaged/untracked context at HEAD."""
    merge_base = resolve_merge_base(root, base, head)
    head_sha = resolve_revision(root, head)
    paths = [p for p in _git_lines(root, ["diff", "--name-only", merge_base, head]) if p]
    if head == "HEAD":
        for line in _git_lines(root, ["status", "--porcelain", "-uall"]):
            entry = line[3:].strip().strip('"')
            if " -> " in entry:
                entry = entry.split(" -> ")[-1]
            if entry and entry not in paths:
                paths.append(entry)
    return {"merge_base": merge_base, "head_sha": head_sha, "changed_paths": paths}


def _git_lines(root: Path, args: List[str]) -> List[str]:
    res = subprocess.run(["git", *args], cwd=str(root), capture_output=True, text=True, check=True)
    return res.stdout.splitlines()


def select_checks_plan(
    base: str, head: str = "HEAD", root: Path = ROOT, offline_tests: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Full selection plan: merge base, patch id, changed paths, minimal checks."""
    offline = offline_tests if offline_tests is not None else offline_contract_tests(root)
    diff = changed_paths(root, base, head)
    selection = select_checks(diff["changed_paths"], offline)
    return {
        "base": base,
        "head": head,
        "merge_base": diff["merge_base"],
        "head_sha": diff["head_sha"],
        "patch_id": compute_patch_id(root, diff["merge_base"], head),
        "changed_paths": diff["changed_paths"],
        "unmapped_paths": selection["unmapped_paths"],
        "defaulted_to_offline": bool(selection["unmapped_paths"]),
        "checks": selection["checks"],
    }


def _print_selection_plan(plan: Dict[str, Any]) -> None:
    print(
        f"Change scope: {plan['base']}..{plan['head']} "
        f"(merge-base {plan['merge_base'][:8]}, head {plan['head_sha'][:8]}, patch-id {plan['patch_id'][:8]})"
    )
    print(f"Changed paths: {len(plan['changed_paths'])}")
    for path in plan["changed_paths"]:
        print(f"  {path}")
    if plan["unmapped_paths"]:
        print(f"Unmapped paths defaulted to the full offline set: {', '.join(plan['unmapped_paths'])}")
    else:
        print("Unmapped paths: none")
    print(f"Selected checks: {len(plan['checks'])}")
    for check in plan["checks"]:
        print(f"  [{check['tier']}] {shlex.join(check['command'])}")
        print(f"      for: {', '.join(check['paths'])}")




def _active_openspec_changes() -> list[str] | None:
    """Names from structured `openspec list --json`; None when the lookup itself fails."""
    try:
        listed = subprocess.run(
            ["openspec", "list", "--json"], capture_output=True, text=True, check=False
        )
        if listed.returncode != 0:
            return None
        import json as _json

        payload = _json.loads(listed.stdout or "{}")
        changes = payload.get("changes") if isinstance(payload, dict) else payload
        if not isinstance(changes, list):
            return None
        parsed: list[str] = []
        for entry in changes:
            if not isinstance(entry, dict):
                return None
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                return None
            parsed.append(name)
        return parsed
    except Exception:
        return None


def _validate_named_change(change: str) -> int:
    probed = subprocess.run(
        ["openspec", "validate", change, "--type", "change", "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )
    sys.stdout.write(probed.stdout)
    sys.stderr.write(probed.stderr)
    return probed.returncode


ChangeResolution = Tuple[str, Optional[str], List[str]]


def resolve_openspec_change(change: str | None) -> ChangeResolution:
    """Resolve the change to validate into one typed observation.

    Returns (state, name, names):
      "explicit"      - caller named it; name is that exact string
      "active"        - checkout has exactly one active change; name is it
      "none"          - checkout has no active change (vacuous, nothing to validate)
      "lookup-failed" - `openspec list --json` failed or returned an unusable payload
      "ambiguous"     - two or more active changes; names lists them
    """
    if change is not None:
        return "explicit", change, []
    active = _active_openspec_changes()
    if active is None:
        return "lookup-failed", None, []
    if active == []:
        return "none", None, []
    if len(active) == 1:
        return "active", active[0], []
    return "ambiguous", None, active


def validate_openspec_change(change: str | None) -> int:
    """Exit 0 iff the named change validates, or the live checkout intent validates.

    Argv-safe: change travels as subprocess argv, never interpolated
    into source. A named change always validates exactly that name. None
    means the caller omitted --change and the checkout decides: no active
    change is vacuously satisfied; exactly one active change is validated;
    a failed lookup and a multi-change checkout both FAIL with a diagnostic.
    """
    state, name, names = resolve_openspec_change(change)
    if state in ("explicit", "active"):
        assert name is not None
        return _validate_named_change(name)
    if state == "none":
        return 0
    if state == "lookup-failed":
        print("ERROR: `openspec list --json` lookup failed; cannot determine active changes.", file=sys.stderr)
        print("Resolve the openspec CLI failure, then rerun.", file=sys.stderr)
        return 1
    print(f"ERROR: {len(names)} active openspec changes; pass one explicitly via --change.", file=sys.stderr)
    for entry in names:
        print(f"  - {entry}", file=sys.stderr)
    return 1



class PortableVerifier:
    def __init__(self, host: str, evidence_root: Path, change: str | None = None):
        self.host = host
        self.evidence_root = evidence_root
        self.change = change
        self.run_id = f"{host}-{int(time.time())}-{secrets.token_hex(4)}"
        self.run_dir = self.evidence_root / self.run_id
        self.scenarios: List[ScenarioResult] = []

    def launch(self) -> bool:
        """Step 1: Launch prerequisite checks."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        return True

    def run_command(
        self,
        scenario_id: str,
        desc: str,
        plane: str,
        cmd: List[str],
        cwd: Optional[Path] = None,
        timeout: float = 60.0,
        evidence_level: str = "offline",
    ) -> ScenarioResult:
        start = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd or ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
            duration = round(time.time() - start, 3)
            stdout_snip = proc.stdout.strip()[:300]
            stderr_snip = proc.stderr.strip()[:300]
            verdict = "PASS" if proc.returncode == 0 else "FAIL"
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start, 3)
            stdout_snip = ""
            stderr_snip = f"TIMEOUT: Command exceeded {timeout}s limit"
            verdict = "FAIL"
            exit_code = 124
        except FileNotFoundError as exc:
            duration = round(time.time() - start, 3)
            stdout_snip = ""
            stderr_snip = f"NOT_FOUND: Executable not found: {exc}"
            verdict = "BLOCKED"
            exit_code = 127
        except Exception as exc:
            duration = round(time.time() - start, 3)
            stdout_snip = ""
            stderr_snip = f"ERROR: Subprocess execution failed: {exc}"
            verdict = "FAIL"
            exit_code = 1

        result = ScenarioResult(
            id=scenario_id,
            description=desc,
            plane=plane,
            command=" ".join(cmd),
            exit_code=exit_code,
            stdout_snippet=stdout_snip or stderr_snip,
            verdict=verdict,
            duration_s=duration,
            evidence_level=evidence_level,
        )
        self.scenarios.append(result)
        return result

    def doctor(self, check_durability: bool = True, allow_stale: bool = False) -> bool:
        """Step 2: Doctor static prerequisites, canonical conformance, and schema validity."""
        print(f"[{self.host}] Running Doctor checks...")

        # 1. Canonical conformance
        r1 = self.run_command(
            "doctor-canonical-index",
            "Verify canonical inventory conforms to pin",
            "canonical",
            [sys.executable, str(ROOT / "scripts" / "canonical-index.py"), "--check"],
        )

        # 2. OpenSpec change integrity (argv-safe helper above). Resolve once: the
        # label and the child validation share one observation, so the receipt binds
        # the exact validated target. Only a real change name reaches the child;
        # none/lookup-failed/ambiguous are decided here and recorded as scenarios.
        state, change_name, active_names = resolve_openspec_change(self.change)
        helper = "import importlib.util, sys; spec = importlib.util.spec_from_file_location('vp_helper', 'scripts/verify-portable.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); sys.exit(m.validate_openspec_change(sys.argv[1]))"
        if state in ("explicit", "active"):
            assert change_name is not None
            r2 = self.run_command(
                "doctor-openspec-validation",
                f"Verify {change_name} openspec change passes schema checks",
                "canonical",
                [sys.executable, "-c", helper, change_name],
            )
        elif state == "none":
            r2 = ScenarioResult(
                id="doctor-openspec-validation",
                description="No active OpenSpec change; nothing to validate (vacuous)",
                plane="canonical",
                command="openspec list --json -> no active changes",
                exit_code=0,
                stdout_snippet="no active changes; no change was validated",
                verdict="PASS",
                duration_s=0.0,
            )
            self.scenarios.append(r2)
        elif state == "lookup-failed":
            r2 = ScenarioResult(
                id="doctor-openspec-validation",
                description="openspec list --json lookup failed; active change undetermined",
                plane="canonical",
                command="openspec list --json -> lookup failed",
                exit_code=1,
                stdout_snippet="lookup failed; cannot determine the active change",
                verdict="FAIL",
                duration_s=0.0,
            )
            self.scenarios.append(r2)
        else:
            r2 = ScenarioResult(
                id="doctor-openspec-validation",
                description=f"{len(active_names)} active OpenSpec changes; pass one via --change",
                plane="canonical",
                command="openspec list --json -> multiple active changes",
                exit_code=1,
                stdout_snippet="; ".join(active_names),
                verdict="FAIL",
                duration_s=0.0,
            )
            self.scenarios.append(r2)


        # 3. Static adapter checks
        r3 = self.run_command(
            "doctor-adapter-static",
            "Verify static harness names and discipline",
            "adapter",
            [sys.executable, str(ROOT / "scripts" / "verify-harness.py")],
        )

        # 3b. Host-neutral adapter boundary scanner
        r3b = self.run_command(
            "doctor-scan-host-boundary",
            "Verify shared skills and playbooks maintain host-neutral adapter boundary",
            "adapter",
            [sys.executable, str(ROOT / "scripts" / "scan-host-boundary.py"), "--check"],
        )

        # 4. Package descriptor and native manifest projection integrity
        r4 = self.run_command(
            "doctor-package-projection",
            "Verify package descriptor and projected native harness manifests",
            "package",
            [sys.executable, str(ROOT / "scripts" / "project-package.py"), "--check"],
        )

        # 4b. Native package lifecycle verification
        r4b = self.run_command(
            f"doctor-package-lifecycle-{self.host}",
            f"Verify native package lifecycle contract for {self.host}",
            "package",
            [sys.executable, str(ROOT / "scripts" / "package-lifecycle.py"), "verify", "--host", self.host],
        )

        doctor_pass = all(r.verdict == "PASS" for r in (r1, r2, r3, r3b, r4, r4b))

        # 5. Optional typed harness profile validation
        profile_file = ROOT / "profiles" / f"{self.host}.json"
        if profile_file.is_file():
            r5 = self.run_command(
                f"doctor-profile-{self.host}",
                f"Validate typed harness profile for {self.host}",
                "adapter",
                [sys.executable, "-c", f"import json; from pathlib import Path; from scripts.portability_schema import HarnessProfile, Binding, Evidence; d = json.loads(Path('{profile_file}').read_text()); b = [Binding(**x) for x in d.get('bindings', [])]; e = [Evidence(**x) for x in d.get('evidence_ledger', [])]; HarnessProfile(host=d['host'], support_state=d['support_state'], bindings=b, skills_dir=d.get('skills_dir'), plugins_dir=d.get('plugins_dir'), plugin_manifest=d.get('plugin_manifest'), evidence_ledger=e, tool_mappings=d.get('tool_mappings'), skill_order=d.get('skill_order'), runtime_conventions=d.get('runtime_conventions')).validate()"],
            )
            doctor_pass = doctor_pass and (r5.verdict == "PASS")

        # 6. Antigravity live synchronization check
        if self.host == "antigravity":
            r6 = self.run_command(
                "doctor-antigravity-sync",
                "Verify live Antigravity plugin synchronization",
                "package",
                [sys.executable, str(ROOT / "scripts" / "sync-antigravity-plugin.py"), "--check"],
            )
            doctor_pass = doctor_pass and (r6.verdict == "PASS")

        # 7. Evidence durability and support-state derivation check (when running standalone doctor)
        if check_durability and profile_file.is_file():
            chk_cmd = [
                sys.executable,
                str(ROOT / "scripts" / "verify-portable.py"),
                "check-evidence",
                "--host",
                self.host,
                "--evidence-dir",
                str(self.evidence_root),
            ]
            if allow_stale:
                chk_cmd.append("--allow-stale")

            r7 = self.run_command(
                f"doctor-evidence-durability-{self.host}",
                f"Verify evidence durability and support-state derivation for {self.host}",
                "adapter",
                chk_cmd,
            )
            doctor_pass = doctor_pass and (r7.verdict == "PASS")

        return doctor_pass

    def drive(self, feature: Optional[str] = None) -> bool:
        """Step 3: Drive representative capability scenarios."""
        print(f"[{self.host}] Driving capability scenarios...")

        # Reclassified repository-local static and adapter checks
        # Canonical: principle discovery
        self.run_command(
            "drive-principles-load",
            "Ensure poteto-mode loads all canonical principles without error",
            "canonical",
            [
                sys.executable,
                "-c",
                "import sys, json; from pathlib import Path; r = Path('.'); inv = json.loads((r/'openspec'/'canonical-inventory.json').read_text()); expected = [a['path'] for a in inv.get('artifacts', []) if a.get('category') == 'principle' and a.get('mode') in ('preserve', 'adapt')]; missing = [p for p in expected if not (r/p).is_file()]; sys.exit(1 if missing else 0)",
            ],
        )

        # Adapter: Plan checker validation
        self.run_command(
            "drive-check-plan",
            "Verify multi-phase plan checking logic",
            "adapter",
            ["bun", "test", str(ROOT / "skills" / "poteto-mode" / "scripts" / "check-plan.test.mjs")],
        )

        # Adapter: Worktree audit isolation check
        self.run_command(
            "drive-worktree-audit",
            "Run worktree isolation audit smoke test",
            "adapter",
            ["bash", str(ROOT / "skills" / "poteto-mode" / "scripts" / "worktree-audit.sh"), "."],
        )

        # Package: Cross-harness verification skill scaffolding and check
        smoke_target = self.run_dir / "verify-smoke"
        self.run_command(
            "drive-verification-skill-scaffold",
            f"Prove verification skill scaffolding for {self.host}",
            "package",
            [
                sys.executable,
                str(ROOT / "scripts" / "scaffold-verification-skill.py"),
                "--host",
                self.host,
                "--app",
                "smoke",
                "--write",
                "--target-dir",
                str(smoke_target),
            ],
        )
        self.run_command(
            "drive-verification-skill-check",
            f"Validate generated verification skill structure for {self.host}",
            "package",
            [
                sys.executable,
                str(ROOT / "scripts" / "scaffold-verification-skill.py"),
                "--host",
                self.host,
                "--check",
                "--target-dir",
                str(smoke_target),
            ],
        )

        # Package: Native isolated lifecycle proof (install, verify, update convergence, uninstall residue)
        lifecycle_target = self.run_dir / f"lifecycle-{self.host}"
        self.run_command(
            f"drive-package-lifecycle-proof-{self.host}",
            f"Prove isolated native package lifecycle for {self.host}",
            "package",
            [
                sys.executable,
                str(ROOT / "scripts" / "package-lifecycle.py"),
                "prove",
                "--host",
                self.host,
                "--target-dir",
                str(lifecycle_target),
            ],
        )

        # Codex-specific adapter compatibility suites
        if self.host == "codex":
            self.run_command(
                "drive-codex-orch",
                "Verify Codex orch and store compatibility suite",
                "adapter",
                ["bun", "test", "./skills/poteto-mode/scripts/orch/orch.test.ts"],
            )
            self.run_command(
                "drive-codex-watch-pr",
                "Verify Codex watch-pr policy and CLI suite",
                "adapter",
                ["bun", "test", "./skills/poteto-mode/scripts/watch-pr/cli.test.ts", "./skills/poteto-mode/scripts/watch-pr/policy.test.ts"],
            )

        # Antigravity-specific package/adapter verification scenarios
        if self.host == "antigravity":
            self.run_command(
                "drive-antigravity-models",
                "Verify Antigravity model roles and panel definitions",
                "package",
                [sys.executable, "-c", "import json; from pathlib import Path; d = json.loads(Path('.antigravity-plugin/models.json').read_text()); assert d['singleRoleDefault'] == 'pro'; assert len(d['roles']) >= 10"],
            )
            self.run_command(
                "drive-antigravity-tools-ref",
                "Verify Antigravity tool-mapping reference integrity",
                "adapter",
                [sys.executable, "-c", "from pathlib import Path; p = Path('skills/poteto-mode/references/antigravity-tools.md'); assert p.is_file(); t = p.read_text(); assert 'invoke_subagent' in t; assert 'ask_question' in t"],
            )

        # Native Harness Driver Live Scenarios (Runtime Plane)
        driver = get_driver(self.host, ROOT)
        avail, reason = driver.is_available()
        if not avail:
            self.scenarios.append(
                ScenarioResult(
                    id=f"runtime-driver-{self.host}",
                    description=f"Prove native harness execution for {self.host}",
                    plane="runtime",
                    command=f"check-harness-availability --host {self.host}",
                    exit_code=127,
                    stdout_snippet=f"BLOCKED: Host runtime '{self.host}' is unavailable ({reason})",
                    verdict="BLOCKED",
                    duration_s=0.0,
                )
            )
            return False

        # 1. Native harness discovery
        sc_disc = driver.discover(self.run_dir)
        self.scenarios.append(
            ScenarioResult(
                id=sc_disc.scenario_id,
                description=sc_disc.description,
                plane="runtime",
                command=sc_disc.command,
                exit_code=sc_disc.exit_code,
                stdout_snippet=sc_disc.stdout_snippet,
                verdict=sc_disc.verdict,
                duration_s=sc_disc.duration_s,
                evidence_level=sc_disc.evidence_level,
            )
        )

        # 2. Native playbook routing
        target_playbook = feature or "feature"
        sc_route = driver.route_playbook(target_playbook, self.run_dir)
        self.scenarios.append(
            ScenarioResult(
                id=sc_route.scenario_id,
                description=sc_route.description,
                plane="runtime",
                command=sc_route.command,
                exit_code=sc_route.exit_code,
                stdout_snippet=sc_route.stdout_snippet,
                verdict=sc_route.verdict,
                duration_s=sc_route.duration_s,
                evidence_level=sc_route.evidence_level,
            )
        )

        # 3. Native child spawn / subagent contract
        sc_spawn = driver.child_spawn(self.run_dir)
        self.scenarios.append(
            ScenarioResult(
                id=sc_spawn.scenario_id,
                description=sc_spawn.description,
                plane="runtime",
                command=sc_spawn.command,
                exit_code=sc_spawn.exit_code,
                stdout_snippet=sc_spawn.stdout_snippet,
                verdict=sc_spawn.verdict,
                duration_s=sc_spawn.duration_s,
                evidence_level=sc_spawn.evidence_level,
                settlement=sc_spawn.settlement,
            )
        )

        # 4. Native in-flight child cancellation (omp only: the other drivers declare no
        # cancel surface, so a scenario here would record a host with nothing to drive)
        if self.host == "omp":
            sc_cancel = driver.child_cancel(self.run_dir)
            self.scenarios.append(
                ScenarioResult(
                    id=sc_cancel.scenario_id,
                    description=sc_cancel.description,
                    plane="runtime",
                    command=sc_cancel.command,
                    exit_code=sc_cancel.exit_code,
                    stdout_snippet=sc_cancel.stdout_snippet,
                    verdict=sc_cancel.verdict,
                    duration_s=sc_cancel.duration_s,
                    evidence_level=sc_cancel.evidence_level,
                    settlement=sc_cancel.settlement,
                )
            )

        # 5. Native workspace isolation contract
        sc_iso = driver.isolation(self.run_dir)
        self.scenarios.append(
            ScenarioResult(
                id=sc_iso.scenario_id,
                description=sc_iso.description,
                plane="runtime",
                command=sc_iso.command,
                exit_code=sc_iso.exit_code,
                stdout_snippet=sc_iso.stdout_snippet,
                verdict=sc_iso.verdict,
                duration_s=sc_iso.duration_s,
                evidence_level=sc_iso.evidence_level,
                settlement=sc_iso.settlement,
            )
        )

        # 6. Native evidence capture contract
        sc_ev = driver.evidence_capture(self.run_dir)
        self.scenarios.append(
            ScenarioResult(
                id=sc_ev.scenario_id,
                description=sc_ev.description,
                plane="runtime",
                command=sc_ev.command,
                exit_code=sc_ev.exit_code,
                stdout_snippet=sc_ev.stdout_snippet,
                verdict=sc_ev.verdict,
                duration_s=sc_ev.duration_s,
                evidence_level=sc_ev.evidence_level,
                settlement=sc_ev.settlement,
            )
        )

        return all(s.verdict == "PASS" for s in self.scenarios if s.plane == "runtime")

    def proof_bar(self) -> VerificationReceipt:
        """Step 4: Compute the proof bar and verdicts across the four planes."""
        planes = settle_planes(self.scenarios)
        overall = reduce_verdicts(planes.values())

        # Host version from live driver or package descriptor fallback
        host_version = ""
        try:
            driver = get_driver(self.host, ROOT)
            if driver.is_available()[0]:
                live_v = driver.get_version()
                if live_v:
                    host_version = live_v
        except Exception:
            pass

        if not host_version:
            pkg_file = ROOT / "pstack.package.json"
            if pkg_file.is_file():
                try:
                    host_version = json.loads(pkg_file.read_text(encoding="utf-8")).get("version", "")
                except Exception:
                    pass
            if not host_version:
                host_version = "0.15.21-grokbuild.0"

        surface_revisions = compute_surface_revisions(ROOT, self.host)

        root_str = str(ROOT)
        canon_str = str(get_canonical_root(ROOT))

        scenarios = []
        for s in self.scenarios:
            if root_str != canon_str:
                cmd = s.command.replace(root_str, canon_str)
                snip = s.stdout_snippet.replace(root_str, canon_str) if s.stdout_snippet else s.stdout_snippet
                scenarios.append(ScenarioResult(
                    id=s.id,
                    description=s.description,
                    plane=s.plane,
                    command=cmd,
                    exit_code=s.exit_code,
                    stdout_snippet=snip,
                    verdict=s.verdict,
                    duration_s=s.duration_s,
                    evidence_level=getattr(s, "evidence_level", "offline"),
                    settlement=getattr(s, "settlement", None),
                ))
            else:
                scenarios.append(s)

        run_receipt_path = str(self.run_dir / "receipt.json")
        if root_str != canon_str:
            run_receipt_path = run_receipt_path.replace(root_str, canon_str)

        receipt = VerificationReceipt(
            run_id=self.run_id,
            host=self.host,
            host_version=host_version,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            overall_verdict=overall,
            planes=planes,
            surface_revisions=surface_revisions,
            scenarios=scenarios,
            artifacts=[run_receipt_path, f".audit/evidence/{self.host}-receipt.json"],
            claim=f"{self.host} 5-harness portability conformance verification",
            kind="runtime",
        )
        return receipt

    def evidence(self, receipt: VerificationReceipt, update_durable: bool = True) -> Path:
        """Step 5: Write structured run evidence receipt and optionally durable pointer."""
        self.evidence_root.mkdir(parents=True, exist_ok=True)
        receipt_file = self.run_dir / "receipt.json"
        data = asdict(receipt)
        receipt_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        if update_durable:
            # Parse the index BEFORE writing anything durable: a corrupt index refuses
            # the whole update, so the receipt file and its index row keep one run_id
            # instead of the index row trailing the rewritten receipt (#495).
            index_file = self.evidence_root / "index.json"
            index_data: Dict[str, Any] = {"version": 1, "hosts": {}}
            if index_file.is_file():
                try:
                    index_data = json.loads(index_file.read_text(encoding="utf-8"))
                except Exception as err:
                    # index.json is the only inventory of every host's durable receipt.
                    # Resetting it to a fresh {"hosts": {}} would rewrite the file for
                    # this host alone and silently un-list every other host, so fail
                    # loudly and leave the corrupt bytes in place for recovery (#429, #444).
                    sys.exit(
                        f"REFUSING to rewrite the unreadable evidence index at {index_file}: "
                        f"{type(err).__name__}: {err}. The index lists every host's durable "
                        f"receipt, so resetting it would silently drop the other hosts. Repair "
                        f"or remove the file, then re-run. This run's receipt is at {receipt_file}."
                    )

            # Stable durable receipt copy
            durable_file = self.evidence_root / f"{self.host}-receipt.json"
            durable_data = data
            reusable = True
            if durable_file.is_file():
                try:
                    previous = VerificationReceipt(**json.loads(durable_file.read_text(encoding="utf-8")))
                    preserved = preserve_observed_settlements(previous, receipt)
                except Exception as err:
                    # The durable receipt is the only place a prior observation lives. A
                    # file this run cannot read is exactly when it is worth the most, so
                    # refuse to replace it and let the durability check report the gap.
                    reusable = False
                    print(
                        f"REFUSING to overwrite the durable receipt at {durable_file}: "
                        f"{type(err).__name__}: {err}. This run's receipt is at {receipt_file}."
                    )
                else:
                    if preserved:
                        # A preserved settlement is a live scenario this receipt's planes
                        # never saw, so re-reduce them (and the overall verdict) over the
                        # final scenario set. Without this the durable receipt carries a
                        # live settlement row under a runtime UNTESTED plane and demotes
                        # the host for a reason unrelated to the change (#322, #444).
                        # FAIL and BLOCKED still win the reduction.
                        receipt.planes = settle_planes(receipt.scenarios)
                        receipt.overall_verdict = reduce_verdicts(receipt.planes.values())
                        durable_data = asdict(receipt)
                        print(
                            f"Preserved prior observed_live settlement(s) from {previous.run_id}: "
                            f"{', '.join(preserved)}"
                        )
            if reusable:
                durable_file.write_text(json.dumps(durable_data, indent=2) + "\n", encoding="utf-8")

            # Update durable index.json with the inventory parsed above.
            index_data.setdefault("hosts", {})[self.host] = {
                "receipt": f".audit/evidence/{self.host}-receipt.json",
                "run_id": receipt.run_id,
                "timestamp": receipt.timestamp,
                "overall_verdict": receipt.overall_verdict,
                "planes": receipt.planes,
                "surface_revisions": asdict(receipt.surface_revisions) if isinstance(receipt.surface_revisions, SurfaceRevisions) else receipt.surface_revisions,
            }
            index_file.write_text(json.dumps(index_data, indent=2) + "\n", encoding="utf-8")
            print(f"Evidence captured at {receipt_file} (durable: {durable_file})")
        else:
            print(f"Evidence captured at {receipt_file}")

        return receipt_file

    def cleanup(self) -> None:
        """Step 6: Cleanup transient files while preserving evidence."""
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "drive", "run", "refresh-static", "check-evidence", "check-staleness", "select-checks"], help="Action to execute")
    parser.add_argument("--host", choices=[*SUPPORTED_HOSTS, "all"], default="grok", help="Target harness (or 'all' for all declared hosts)")
    parser.add_argument("--feature", help="Feature to drive (for 'drive' action)")
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR, help="Evidence directory")
    parser.add_argument("--allow-stale", action="store_true", help="Allow stale evidence during durability check")
    parser.add_argument("--change", default=None, help="Target OpenSpec change to validate in doctor (default: checkout's single active change, or no-op when none)")
    parser.add_argument("--json", action="store_true", help="Emit JSON output for machine consumption")
    parser.add_argument("--base", help="Base ref to diff against (select-checks)")
    parser.add_argument("--head", default="HEAD", help="Head ref to scope (select-checks)")
    parser.add_argument("--record", type=Path, help="Write the check evidence receipt for this selection to a path")
    parser.add_argument("--receipt", type=Path, help="Evaluate a recorded check evidence receipt against the current patch")
    parser.add_argument("--outcome", action="append", default=[], metavar="CHECK_ID=VERDICT", help="Recorded outcome per selected check id, repeatable")
    args = parser.parse_args()

    hosts = list(get_declared_hosts()) if args.host == "all" else [args.host]

    if args.action == "check-evidence":
        all_ok = True
        for h in hosts:
            profile_file = ROOT / "profiles" / f"{h}.json"
            if not profile_file.is_file():
                print(f"[{h}] Profile not found at {profile_file}")
                all_ok = False
                continue
            d = json.loads(profile_file.read_text(encoding="utf-8"))
            b = [Binding(**x) for x in d.get("bindings", [])]
            e = [Evidence(**x) for x in d.get("evidence_ledger", [])]
            prof = HarnessProfile(
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
            try:
                res = check_evidence_durability(prof, ROOT, check_freshness=not args.allow_stale)
                if res["derived_support_state"] == "candidate":
                    # #473: a candidate row evaluates no planes, so PASS would
                    # claim coverage it has none of. Exit stays 0; only the
                    # label changes. (ponytail: label-only; exit-code split if
                    # automation ever needs to gate on coverage.)
                    print(f"[{h}] NOT_COVERED: no planes evaluated, derived support state: candidate (claimed: {res['claimed_support_state']})")
                else:
                    print(f"[{h}] PASS: Evidence durable, derived support state: {res['derived_support_state']} (claimed: {res['claimed_support_state']})")
            except Exception as err:
                print(f"[{h}] FAIL: {err}")
                if h == "omp" and "exceeds evidence-derived support state" in str(err):
                    print(
                        "       OMP runtime evidence is only observed by a model-backed run: "
                        "regenerate the durable receipt with PSTACK_RUN_OMP_LIVE=1, then re-check."
                    )
                all_ok = False
        sys.exit(0 if all_ok else 1)

    if args.action == "check-staleness":
        staleness_report: Dict[str, Any] = {}
        all_fresh = True
        for h in hosts:
            current_revs = compute_surface_revisions(ROOT, h)
            receipt_file = args.evidence_dir / f"{h}-receipt.json"
            if not receipt_file.is_file():
                profile_file = ROOT / "profiles" / f"{h}.json"
                claimed_state = ""
                if profile_file.is_file():
                    try:
                        claimed_state = json.loads(profile_file.read_text(encoding="utf-8")).get("support_state", "")
                    except Exception:
                        pass
                if claimed_state == "candidate":
                    staleness_report[h] = {
                        "host": h,
                        "receipt_exists": False,
                        "needs_regeneration": False,
                        "stale_planes": [],
                        "stale_reasons": {},
                        "support_state": "candidate",
                    }
                    continue
                staleness_report[h] = {
                    "host": h,
                    "receipt_exists": False,
                    "needs_regeneration": True,
                    "stale_planes": ["canonical", "adapter", "package", "runtime"],
                    "stale_reasons": {"all": [f"Receipt file {receipt_file} not found"]},
                }
                all_fresh = False
                continue
            try:
                rdata = json.loads(receipt_file.read_text(encoding="utf-8"))
                receipt = VerificationReceipt(**rdata)
                stale_map = receipt.evaluate_plane_staleness(current_revs)
                stale_planes = [p for p, reasons in stale_map.items() if reasons]
                needs_regen = bool(stale_planes)
                if needs_regen:
                    all_fresh = False
                staleness_report[h] = {
                    "host": h,
                    "receipt_exists": True,
                    "run_id": receipt.run_id,
                    "timestamp": receipt.timestamp,
                    "overall_verdict": receipt.overall_verdict,
                    "needs_regeneration": needs_regen,
                    "stale_planes": stale_planes,
                    "stale_reasons": {p: errs for p, errs in stale_map.items() if errs},
                }
            except Exception as err:
                staleness_report[h] = {
                    "host": h,
                    "receipt_exists": True,
                    "needs_regeneration": True,
                    "stale_planes": ["canonical", "adapter", "package", "runtime"],
                    "stale_reasons": {"error": [str(err)]},
                }
                all_fresh = False

        if args.json:
            print(json.dumps(staleness_report, indent=2))
        else:
            print("\n================ Evidence Staleness Report ================")
            for h, info in staleness_report.items():
                status = "REGENERATE" if info["needs_regeneration"] else "FRESH"
                stale_str = ", ".join(info["stale_planes"]) if info["stale_planes"] else "None"
                print(f"Host: {h:<12} | Status: {status:<10} | Stale Planes: {stale_str}")
                for p, reasons in info.get("stale_reasons", {}).items():
                    for r in reasons:
                        print(f"   - [{p}] {r}")
            print("===========================================================")
            print(f"Overall Matrix Evidence: {'ALL FRESH' if all_fresh else 'REGENERATION NEEDED'}\n")
        sys.exit(0 if all_fresh else 1)

    if args.action == "select-checks":
        if not args.base:
            parser.error("select-checks requires --base <ref>")
        plan = select_checks_plan(args.base, args.head, ROOT)

        if args.record:
            outcomes = {}
            for item in args.outcome:
                check_id, _, verdict = item.partition("=")
                outcomes[check_id.strip()] = verdict.strip().upper() or "UNTESTED"
            receipt = create_check_evidence_receipt(
                ROOT, args.base, [c["id"] for c in plan["checks"]], outcomes, args.head
            )
            args.record.parent.mkdir(parents=True, exist_ok=True)
            args.record.write_text(receipt.to_json() + "\n", encoding="utf-8")
            print(
                f"Recorded check evidence: {args.record} "
                f"(head {receipt.head_sha[:8]}, patch-id {receipt.patch_id[:8]}, verdict {receipt.verdict})"
            )

        if args.receipt:
            if not args.receipt.is_file():
                print(f"No recorded evidence at {args.receipt}: run the selected checks, then record them.")
                sys.exit(2)
            receipt = load_check_evidence_receipt(args.receipt)
            stale, reasons = check_check_evidence_staleness(receipt, ROOT, args.base, args.head)
            claimable, claim_reason = can_claim_current_ci(receipt, ROOT, args.base, args.head)
            if args.json:
                print(
                    json.dumps(
                        {
                            **plan,
                            "receipt_path": str(args.receipt),
                            "receipt": receipt.to_dict(),
                            "stale": stale,
                            "stale_reasons": reasons,
                            "claimable": claimable,
                            "claim_reason": claim_reason,
                        },
                        indent=2,
                    )
                )
            else:
                _print_selection_plan(plan)
                print(f"Recorded evidence: {args.receipt}")
                print(
                    f"  head {receipt.head_sha[:8]} patch-id {receipt.patch_id[:8]} "
                    f"verdict {receipt.verdict} recorded {receipt.created_at}"
                )
                if receipt.outcomes:
                    for check_id, verdict in sorted(receipt.outcomes.items()):
                        print(f"  outcome {verdict:<10} {check_id}")
                state = "STALE" if stale else "FRESH"
                print(f"  {state}: {'; '.join(reasons) if reasons else 'bound to the current patch'}")
                print(f"  may be quoted as current CI: {'yes' if claimable else 'no'} — {claim_reason}")
            sys.exit(1 if stale else 0)

        if args.json:
            print(json.dumps(plan, indent=2))
        else:
            _print_selection_plan(plan)
        sys.exit(0)

    all_pass = True
    receipts: List[VerificationReceipt] = []

    for h in hosts:
        verifier = PortableVerifier(host=h, evidence_root=args.evidence_dir, change=args.change)
        verifier.launch()

        if args.action == "doctor":
            ok = verifier.doctor(check_durability=not args.allow_stale, allow_stale=args.allow_stale)
            receipt = verifier.proof_bar()
            verifier.evidence(receipt, update_durable=False)
            receipts.append(receipt)
            all_pass = all_pass and ok

        elif args.action == "drive":
            verifier.doctor(check_durability=False)
            verifier.drive(feature=args.feature)
            receipt = verifier.proof_bar()
            verifier.evidence(receipt, update_durable=False)
            receipts.append(receipt)
            # The matrix verdict reads the same runtime plane the printed status line
            # does: an offline drive proves the wiring, not a child spawn/join, so its
            # runtime plane is UNTESTED and never a PASS (#444).
            all_pass = all_pass and (receipt.planes.get("runtime") == "PASS")

        elif args.action == "run":
            verifier.doctor(check_durability=False)
            verifier.drive()
            receipt = verifier.proof_bar()
            profile_file = ROOT / "profiles" / f"{h}.json"
            claimed_state = ""
            if profile_file.is_file():
                claimed_state = json.loads(profile_file.read_text(encoding="utf-8")).get("support_state", "")
            # Candidate hosts carry no durable runtime receipt: model-backed
            # capabilities are untested, so a durable PASS is never claimed.
            update_durable = claimed_state != "candidate"
            verifier.evidence(receipt, update_durable=update_durable)
            verifier.cleanup()
            receipts.append(receipt)
            all_pass = all_pass and (receipt.overall_verdict == "PASS")

        elif args.action == "refresh-static":
            # Honest static refresh: run the static doctor planes only (no model route,
            # no drive) and record them as the host's durable receipt. The receipt keeps
            # runtime and overall UNTESTED, so the exit status has to come from the
            # doctor result — a failing static plane stays FAIL and is never reported as
            # the nominal UNTESTED the missing runtime plane alone would produce.
            ok = verifier.doctor(check_durability=False)
            receipt = verifier.proof_bar()
            profile_file = ROOT / "profiles" / f"{h}.json"
            claimed_state = ""
            if profile_file.is_file():
                claimed_state = json.loads(profile_file.read_text(encoding="utf-8")).get("support_state", "")
            # Same rule as `run`: a candidate host has no durable receipt to refresh,
            # while every mapped/packaged host records the static planes it does prove.
            update_durable = claimed_state != "candidate"
            verifier.evidence(receipt, update_durable=update_durable)
            verifier.cleanup()
            receipts.append(receipt)
            all_pass = all_pass and ok

    if args.action == "run" or len(hosts) > 1:
        print(f"\n================ Verification Summary ================")
        for r in receipts:
            if args.action in ("doctor", "refresh-static"):
                status = "PASS" if (r.planes.get("canonical") == "PASS" and r.planes.get("adapter") == "PASS" and r.planes.get("package") == "PASS") else "FAIL"
            elif args.action == "drive":
                status = "PASS" if (r.planes.get("runtime") == "PASS") else "FAIL"
            else:
                status = r.overall_verdict
            print(f"Host: {r.host:<12} | Canonical: {r.planes.get('canonical', 'N/A'):<4} | Adapter: {r.planes.get('adapter', 'N/A'):<4} | Package: {r.planes.get('package', 'N/A'):<4} | Runtime: {r.planes.get('runtime', 'N/A'):<4} | Status: {status}")
        print(f"======================================================")
        print(f"{len(hosts)}-Harness Matrix Verdict: {'PASS' if all_pass else 'FAIL'}\n")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
