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
import stat
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

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
    reduce_verdicts,
    settle_planes,
    _is_observed_settlement,
)
from scripts.drivers import get_driver
from scripts.host_identity import BUILTIN_HOSTS
from scripts.evidence_receipts import (
    can_claim_current_ci,
    check_check_evidence_staleness,
    compute_patch_id,
    create_check_evidence_receipt,
    load_check_evidence_receipt,
    resolve_merge_base,
    resolve_revision,
)

SUPPORTED_HOSTS = BUILTIN_HOSTS


def _receipt_payload(receipt: VerificationReceipt) -> Dict[str, Any]:
    """Serialized receipt, minus optional keys the schema types as strings.

    `adapter_version` is optional in the receipt schema, so an unset value is an
    absent key rather than a null a reader would have to special-case (#446).
    """
    data = asdict(receipt)
    if data.get("adapter_version") is None:
        data.pop("adapter_version", None)
    return data


from scripts.select_checks import (
    CANONICAL_INDEX_CHECK,
    CHECK_SELECTION_TABLE,
    OFFLINE_WORKFLOW,
    SCAN_HOST_BOUNDARY,
    _check_id,
    _command_for,
    _expand,
    _git_lines,
    _print_selection_plan,
    _tier,
    changed_paths,
    offline_contract_tests,
    pattern_matches,
    select_checks,
    select_checks_action,
    select_checks_plan,
)
from scripts.openspec_change import (
    ChangeResolution,
    _active_openspec_changes,
    _validate_named_change,
    resolve_openspec_change as _resolve_openspec_change,
    validate_openspec_change as _validate_openspec_change,
)


def resolve_openspec_change(
    change: str | None,
    *,
    active_resolver: Optional[Callable[[], list[str] | None]] = None,
) -> ChangeResolution:
    resolver = active_resolver if active_resolver is not None else _active_openspec_changes
    return _resolve_openspec_change(change, active_resolver=resolver)


def validate_openspec_change(
    change: str | None,
    *,
    active_resolver: Optional[Callable[[], list[str] | None]] = None,
) -> int:
    resolver = active_resolver if active_resolver is not None else _active_openspec_changes
    return _validate_openspec_change(change, active_resolver=resolver)

from scripts.evidence_index import (
    _file_or_denied,
    check_evidence_action,
    evidence_index_row,
    get_declared_hosts,
    index_row_mismatch,
    rows_from_receipts,
)


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



class PortableVerifier:
    def __init__(self, host: str, evidence_root: Path, change: str | None = None):
        self.host = host
        self.evidence_root = evidence_root
        self.change = change
        self.run_id = f"{host}-{int(time.time())}-{secrets.token_hex(4)}"
        # The raw run dir has to outlive the checkout that made it: a lane runs in a
        # linked worktree that is pruned after merge, while the durable receipt it
        # commits lives on. An evidence root inside the worktree is therefore mapped to
        # the same relative path in the canonical checkout, so the `artifacts[0]`
        # pointer the receipt commits names a path a reader of that receipt can still
        # reach (#446). An explicit --evidence-dir outside the worktree is untouched.
        run_root = evidence_root
        canonical_root = get_canonical_root(ROOT)
        if canonical_root != ROOT and evidence_root.is_relative_to(ROOT):
            run_root = canonical_root / evidence_root.relative_to(ROOT)
        self.run_dir = run_root / self.run_id
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
        state, change_name, active_names = resolve_openspec_change(
            self.change, active_resolver=_active_openspec_changes
        )
        helper = "import sys; from scripts.openspec_change import validate_openspec_change; sys.exit(validate_openspec_change(sys.argv[1]))"
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
        data = _receipt_payload(receipt)
        receipt_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        if update_durable:
            # Parse the index BEFORE writing anything durable: an unreadable or
            # wrong-shaped index refuses the whole update, so the receipt file and its
            # index row keep one run_id instead of the index row trailing the rewritten
            # receipt (#495).
            index_file = self.evidence_root / "index.json"
            index_data: Dict[str, Any] = {"version": 1, "hosts": {}}
            if _file_or_denied(index_file):
                try:
                    index_data = json.loads(index_file.read_text(encoding="utf-8"))
                    if not isinstance(index_data, dict) or not isinstance(index_data.get("hosts", {}), dict):
                        # Parses, wrong shape: `[]` and {"version": 1, "hosts": []} both
                        # reached the row assignment below and died with AttributeError /
                        # TypeError *after* the durable receipt was rewritten (#495), so
                        # the index kept naming a run whose bytes were gone. Same refusal
                        # as the unreadable case: nothing durable is written at all.
                        raise ValueError(
                            "expected an object with a 'hosts' object, got "
                            f"{type(index_data).__name__}"
                        )
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

            # The rows follow the receipts on disk: put back the rows a deleted index or a
            # crash between the two writes left out, so one host's run cannot leave the
            # inventory listing that host alone. Missing rows only — an existing row is
            # left for the cross-check to report, and bytes a row cannot stand on are left
            # for the reader's orphan check instead of being guessed at (#495).
            index_data.setdefault("hosts", {}).update(
                {
                    host: row
                    for host, row in rows_from_receipts(self.evidence_root).items()
                    if host not in index_data["hosts"]
                }
            )

            # Stable durable receipt copy
            durable_file = self.evidence_root / f"{self.host}-receipt.json"
            durable_data = data
            reusable = True
            if _file_or_denied(durable_file):
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
                        durable_data = _receipt_payload(receipt)
                        print(
                            f"Preserved prior observed_live settlement(s) from {previous.run_id}: "
                            f"{', '.join(preserved)}"
                        )
            if reusable:
                durable_file.write_text(json.dumps(durable_data, indent=2) + "\n", encoding="utf-8")

                # The row follows the durable bytes it names: a refused overwrite must not
                # advance the index onto a run whose receipt was never written (#495).
                index_data.setdefault("hosts", {})[self.host] = evidence_index_row(self.host, receipt)
                try:
                    index_file.write_text(json.dumps(index_data, indent=2) + "\n", encoding="utf-8")
                except OSError as err:
                    # A refused index write leaves the inventory trailing the receipt this
                    # run just wrote (ENOSPC, a read-only index, a denied directory). Name
                    # it instead of a traceback: the reader cross-check reports the split,
                    # and no in-process retry can undo a denial (#495).
                    sys.exit(
                        f"FAILED to write the evidence index at {index_file}: "
                        f"{type(err).__name__}: {err}. The durable receipt at {durable_file} is "
                        f"already written, so the inventory trails it until the file is writable "
                        f"and this check is re-run."
                    )
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
        sys.exit(check_evidence_action(hosts, ROOT, allow_stale=args.allow_stale))

    if args.action == "check-staleness":
        staleness_report: Dict[str, Any] = {}
        all_fresh = True
        for h in hosts:
            current_revs = compute_surface_revisions(ROOT, h)
            receipt_file = args.evidence_dir / f"{h}-receipt.json"
            if not _file_or_denied(receipt_file):
                profile_file = ROOT / "profiles" / f"{h}.json"
                claimed_state = ""
                if _file_or_denied(profile_file):
                    # A denied profile stat is not an absent claim: the read
                    # below refuses by name instead of defaulting to non-candidate.
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
        sys.exit(select_checks_action(args, ROOT))

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
