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
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

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
    resolve_openspec_change,
    validate_openspec_change,
)

from scripts.evidence_index import (
    _file_or_denied,
    check_evidence_action,
    check_staleness_action,
    evidence_index_row,
    get_declared_hosts,
    index_row_mismatch,
    receipt_payload,
    rows_from_receipts,
    write_verification_evidence,
)
from scripts.harness_scenarios import (
    execute_driver_scenarios,
    execute_local_scenarios,
)

# Re-exported from scripts.evidence_index (#613)
_receipt_payload = receipt_payload


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
    def __init__(
        self,
        host: str,
        evidence_root: Path,
        change: str | None = None,
        fixture_home: Path | None = None,
    ):
        self.host = host
        self.evidence_root = evidence_root
        self.change = change
        # Caller-owned fixture HOME for the doctor phase (#709). When None the doctor
        # allocates and removes its own; supplying one pins the exact home whose
        # mirrors the verdict is allowed to see.
        self.fixture_home = fixture_home
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
        record: bool = True,
        env: Optional[Dict[str, str]] = None,
    ) -> ScenarioResult:
        start = time.time()
        # `env` layers on the inherited environment: HOME is the lever (#709), not a
        # wholesale replacement that would strip PATH/PYTHONPATH from the child.
        child_env = None if env is None else {**os.environ, **env}
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd or ROOT,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
                env=child_env,
            )
            duration = round(time.time() - start, 3)
            stdout_snip = proc.stdout.strip()[:300]
            stderr_snip = proc.stderr.strip()[:300]
            # Exit 2 is the untested convention: the check ran and settled nothing
            # (canonical-index.py reports stale upstream freshness this way).
            verdict = {0: "PASS", 2: "UNTESTED"}.get(proc.returncode, "FAIL")
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
            command=self._recorded_command(cmd, env),
            exit_code=exit_code,
            stdout_snippet=stdout_snip or stderr_snip,
            verdict=verdict,
            duration_s=duration,
            evidence_level=evidence_level,
        )
        if record:
            self.scenarios.append(result)
        return result

    @staticmethod
    def _recorded_command(cmd: List[str], env: Optional[Dict[str, str]]) -> str:
        """Record the HOME a command ran under, so a receipt says which home decided it.

        Without it a hermetic run and a run against the developer's live mirrors store
        byte-identical command strings (#709).
        """
        command = " ".join(cmd)
        home = (env or {}).get("HOME")
        return command if home is None else f"{command} [HOME={home}]"

    def doctor(self, check_durability: bool = True, allow_stale: bool = False) -> bool:
        """Step 2: Doctor checks bound to a fixture HOME (#709).

        `package-lifecycle.py verify` and `sync-antigravity-plugin.py --check` read
        `$HOME` plugin mirrors, so whatever a developer has installed live could
        decide the verdict. Every doctor command therefore runs under one fixture
        HOME: the host package is installed into it first, so the checks still
        observe a real native projection while the ambient mirrors stay out of the
        result. `fixture_home` is caller-owned; otherwise the fixture is a
        disposable temp dir removed afterwards.
        """
        with self._fixture_home() as fixture_home:
            seed = self.run_command(
                f"doctor-fixture-install-{self.host}",
                f"Install {self.host} package into fixture HOME for hermetic doctor checks",
                "package",
                [sys.executable, str(ROOT / "scripts" / "package-lifecycle.py"), "install", "--host", self.host],
                env={"HOME": str(fixture_home)},
                record=False,
            )
            if seed.verdict != "PASS":
                # Fail closed: with an empty fixture the downstream mirrors read as
                # missing drift, not real state, so a green doctor would be vacuous.
                self.scenarios.append(seed)
                return False
            return self._doctor_checks(fixture_home, check_durability=check_durability, allow_stale=allow_stale)

    @contextmanager
    def _fixture_home(self) -> Iterator[Path]:
        if self.fixture_home is not None:
            fixture_home = self.fixture_home.resolve()
            fixture_home.mkdir(parents=True, exist_ok=True)
            yield fixture_home
            return
        with tempfile.TemporaryDirectory(
            prefix=f"pstack-doctor-{self.host}-", ignore_cleanup_errors=True
        ) as tmp:
            # Resolve before installing: package-lifecycle refuses a target under a
            # symlinked ancestor (macOS /var -> /private/var), which would fail the
            # doctor closed on a host whose TMPDIR is a link.
            yield Path(tmp).resolve()

    def _doctor_checks(self, fixture_home: Path, check_durability: bool = True, allow_stale: bool = False) -> bool:
        """Doctor scenarios 1-7; every command runs under fixture_home."""
        print(f"[{self.host}] Running Doctor checks...")
        env = {"HOME": str(fixture_home)}

        # 1. Canonical conformance
        r1 = self.run_command(
            "doctor-canonical-index",
            "Verify canonical inventory conforms to pin",
            "canonical",
            [sys.executable, str(ROOT / "scripts" / "canonical-index.py"), "--check"],
            env=env,
        )

        # 2. OpenSpec change integrity (argv-safe helper above). Resolve once: the
        # label and the child validation share one observation, so the receipt binds
        # the exact validated target. Only a real change name reaches the child;
        # lookup-failed/ambiguous are decided here and recorded as scenarios. A
        # checkout with no active change appends no row, because a row that executed
        # nothing is not evidence and the canonical plane still reduces from the
        # canonical-index row.
        state, change_name, active_names = resolve_openspec_change(
            self.change, active_resolver=lambda: _active_openspec_changes(cwd=str(ROOT))
        )
        helper = "import sys; from scripts.openspec_change import validate_openspec_change; sys.exit(validate_openspec_change(sys.argv[1]))"
        r2: Optional[ScenarioResult] = None
        if state in ("explicit", "active"):
            assert change_name is not None
            r2 = self.run_command(
                "doctor-openspec-validation",
                f"Verify {change_name} openspec change passes schema checks",
                "canonical",
                [sys.executable, "-c", helper, change_name],
                env=env,
            )
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
        elif state == "ambiguous":
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
            env=env,
        )

        # 3b. Host-neutral adapter boundary scanner
        r3b = self.run_command(
            "doctor-scan-host-boundary",
            "Verify shared skills and playbooks maintain host-neutral adapter boundary",
            "adapter",
            [sys.executable, str(ROOT / "scripts" / "scan-host-boundary.py"), "--check"],
            env=env,
        )

        # 4. Package descriptor and native manifest projection integrity
        r4 = self.run_command(
            "doctor-package-projection",
            "Verify package descriptor and projected native harness manifests",
            "package",
            [sys.executable, str(ROOT / "scripts" / "project-package.py"), "--check"],
            env=env,
        )

        # 4b. Native package lifecycle verification
        r4b = self.run_command(
            f"doctor-package-lifecycle-{self.host}",
            f"Verify native package lifecycle contract for {self.host}",
            "package",
            [sys.executable, str(ROOT / "scripts" / "package-lifecycle.py"), "verify", "--host", self.host],
            env=env,
        )

        doctor_pass = all(
            r.verdict in ("PASS", "UNTESTED")
            for r in (r1, r2, r3, r3b, r4, r4b)
            if r is not None
        )

        # 5. Optional typed harness profile validation
        profile_file = ROOT / "profiles" / f"{self.host}.json"
        if profile_file.is_file():
            r5 = self.run_command(
                f"doctor-profile-{self.host}",
                f"Validate typed harness profile for {self.host}",
                "adapter",
                [sys.executable, "-c", f"import json; from pathlib import Path; from scripts.portability_schema import HarnessProfile, Binding, Evidence; d = json.loads(Path('{profile_file}').read_text()); b = [Binding(**x) for x in d.get('bindings', [])]; e = [Evidence(**x) for x in d.get('evidence_ledger', [])]; HarnessProfile(host=d['host'], support_state=d['support_state'], bindings=b, skills_dir=d.get('skills_dir'), plugins_dir=d.get('plugins_dir'), plugin_manifest=d.get('plugin_manifest'), evidence_ledger=e, tool_mappings=d.get('tool_mappings'), skill_order=d.get('skill_order'), runtime_conventions=d.get('runtime_conventions'), setup=d.get('setup')).validate()"],
                env=env,
            )
            doctor_pass = doctor_pass and (r5.verdict == "PASS")

        # 6. Antigravity live synchronization check
        if self.host == "antigravity":
            r6 = self.run_command(
                "doctor-antigravity-sync",
                "Verify live Antigravity plugin synchronization",
                "package",
                [sys.executable, str(ROOT / "scripts" / "sync-antigravity-plugin.py"), "--check"],
                env=env,
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
                env=env,
            )
            doctor_pass = doctor_pass and (r7.verdict == "PASS")

        return doctor_pass

    def drive(self, feature: Optional[str] = None) -> bool:
        """Step 3: Drive representative capability scenarios."""
        local_results = execute_local_scenarios(self, ROOT)
        self.scenarios.extend(s for s in local_results if isinstance(s, ScenarioResult))

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

        self.scenarios.extend(execute_driver_scenarios(self, driver, feature))
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
            if not pkg_file.is_file():
                raise RuntimeError(
                    f"Package descriptor missing at {pkg_file} and host driver for {self.host} did not provide a version"
                )
            try:
                pkg_data = json.loads(pkg_file.read_text(encoding="utf-8"))
            except Exception as e:
                raise RuntimeError(f"Corrupt or unreadable package descriptor at {pkg_file}: {e}") from e

            if not isinstance(pkg_data, dict) or not pkg_data.get("version"):
                raise RuntimeError(
                    f"Package descriptor at {pkg_file} missing required 'version' field"
                )
            host_version = str(pkg_data["version"])

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
                    live_attempted=getattr(s, "live_attempted", False),
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

    def evidence(
        self,
        receipt: VerificationReceipt,
        update_durable: bool = True,
        allow_keep_live: bool = False,
    ) -> Path:
        """Step 5: Write structured run evidence receipt and optionally durable pointer."""
        return write_verification_evidence(
            receipt,
            evidence_root=self.evidence_root,
            run_dir=self.run_dir,
            host=self.host,
            update_durable=update_durable,
            allow_keep_live=allow_keep_live,
        )


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
        sys.exit(check_staleness_action(hosts, args.evidence_dir, ROOT, json_output=args.json))

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
            allow_keep_live = (args.host == "all")
            verifier.evidence(receipt, update_durable=update_durable, allow_keep_live=allow_keep_live)
            receipts.append(receipt)
            all_pass = all_pass and ok

    if args.action == "run" or len(hosts) > 1:
        print(f"\n================ Verification Summary ================")
        for r in receipts:
            if args.action in ("doctor", "refresh-static"):
                status = reduce_verdicts(
                    r.planes.get(p, "UNTESTED") for p in ("canonical", "adapter", "package")
                )
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
