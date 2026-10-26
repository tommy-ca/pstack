#!/usr/bin/env python3
"""Portable lever verification engine for pstack across agent harnesses.

Implements the pattern from Build the Lever + Prove It Works + create-verification-skill:
    Launch -> Doctor -> Drive -> Proof Bar -> Evidence -> Cleanup

Usage:
    python3 scripts/verify_portable.py doctor [--host <host>]
    python3 scripts/verify_portable.py drive --feature <feature> [--host <host>]
    python3 scripts/verify_portable.py run [--host <host>] [--evidence-dir <dir>]
    python3 scripts/verify_portable.py refresh-static [--host <host>] [--evidence-dir <dir>]
    python3 scripts/verify_portable.py select-checks --base <ref> [--head <ref>] [--json]
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
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple

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


def resolve_host_version(host: str, root: Path) -> str:
    """Resolve the host runtime version from the live driver or package descriptor."""
    try:
        driver = get_driver(host, root)
        if driver.is_available()[0]:
            live_v = driver.get_version()
            if live_v:
                return live_v
    except Exception:
        pass

    pkg_file = root / "pstack.package.json"
    if not pkg_file.is_file():
        raise RuntimeError(
            f"Package descriptor missing at {pkg_file} and host driver for {host} did not provide a version"
        )
    try:
        pkg_data = json.loads(pkg_file.read_text(encoding="utf-8"))
    except Exception as e:
        raise RuntimeError(f"Corrupt or unreadable package descriptor at {pkg_file}: {e}") from e

    if not isinstance(pkg_data, dict) or not pkg_data.get("version"):
        raise RuntimeError(
            f"Package descriptor at {pkg_file} missing required 'version' field"
        )
    return str(pkg_data["version"])


def normalize_scenarios(
    scenarios: List[ScenarioResult], root: Path, canon_root: Path
) -> List[ScenarioResult]:
    """Normalize worktree file paths in scenario commands and stdout snippets to canonical paths."""
    root_str = str(root)
    canon_str = str(canon_root)
    if root_str == canon_str:
        return list(scenarios)

    normalized: List[ScenarioResult] = []
    for s in scenarios:
        cmd = s.command.replace(root_str, canon_str)
        snip = (
            s.stdout_snippet.replace(root_str, canon_str)
            if s.stdout_snippet
            else s.stdout_snippet
        )
        normalized.append(
            ScenarioResult(
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
            )
        )
    return normalized



class PortableVerifier:
    def __init__(
        self,
        host: str,
        evidence_root: Path,
        change: str | None = None,
        fixture_home: Path | None = None,
        root: Path | None = None,
        get_canonical_root_fn: Optional[Callable[[Path], Path]] = None,
    ):
        self.host = host
        self.evidence_root = evidence_root
        self.change = change
        self.fixture_home = fixture_home
        self.root = root if root is not None else ROOT
        self.get_canonical_root = get_canonical_root_fn or get_canonical_root
        self.run_id = f"{host}-{int(time.time())}-{secrets.token_hex(4)}"
        run_root = evidence_root
        canonical_root = self.get_canonical_root(self.root)
        if canonical_root != self.root and evidence_root.is_relative_to(self.root):
            run_root = canonical_root / evidence_root.relative_to(self.root)
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
                cwd=cwd or self.root,
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

        `package_lifecycle.py verify` and `sync_antigravity_plugin.py --check` read
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
                [sys.executable, str(self.root / "scripts" / "package_lifecycle.py"), "install", "--host", self.host],
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

    def _check_canonical_plane(self, env: Dict[str, str]) -> bool:
        """Execute canonical conformance and OpenSpec change validation scenarios."""
        r1 = self.run_command(
            "doctor-canonical-index",
            "Verify canonical inventory conforms to pin",
            "canonical",
            [sys.executable, str(self.root / "scripts" / "canonical_index.py"), "--check"],
            env=env,
        )

        state, change_name, active_names = resolve_openspec_change(
            self.change, active_resolver=lambda: _active_openspec_changes(cwd=str(self.root))
        )
        r2: Optional[ScenarioResult] = None
        if state in ("explicit", "active"):
            assert change_name is not None
            r2 = self.run_command(
                "doctor-openspec-validation",
                f"Verify {change_name} openspec change passes schema checks",
                "canonical",
                [sys.executable, str(self.root / "scripts" / "openspec_change.py"), change_name],
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

        return all(r.verdict in ("PASS", "UNTESTED") for r in (r1, r2) if r is not None)

    def _check_adapter_plane(self, env: Dict[str, str]) -> bool:
        """Execute static harness and host-neutral adapter boundary scenarios."""
        r3 = self.run_command(
            "doctor-adapter-static",
            "Verify static harness names and discipline",
            "adapter",
            [sys.executable, str(self.root / "scripts" / "verify_harness.py")],
            env=env,
        )

        r3b = self.run_command(
            "doctor-scan-host-boundary",
            "Verify shared skills and playbooks maintain host-neutral adapter boundary",
            "adapter",
            [sys.executable, str(self.root / "scripts" / "scan_host_boundary.py"), "--check"],
            env=env,
        )

        return all(r.verdict in ("PASS", "UNTESTED") for r in (r3, r3b) if r is not None)

    def _check_package_plane(self, env: Dict[str, str]) -> bool:
        """Execute package projection and host package lifecycle scenarios."""
        r4 = self.run_command(
            "doctor-package-projection",
            "Verify package descriptor and projected native harness manifests",
            "package",
            [sys.executable, str(self.root / "scripts" / "project_package.py"), "--check"],
            env=env,
        )

        r4b = self.run_command(
            f"doctor-package-lifecycle-{self.host}",
            f"Verify native package lifecycle contract for {self.host}",
            "package",
            [sys.executable, str(self.root / "scripts" / "package_lifecycle.py"), "verify", "--host", self.host],
            env=env,
        )

        return all(r.verdict in ("PASS", "UNTESTED") for r in (r4, r4b) if r is not None)

    def _check_profile_and_durability(
        self, env: Dict[str, str], check_durability: bool = True, allow_stale: bool = False
    ) -> bool:
        """Execute profile validation, sync check, and standalone evidence durability."""
        passed = True
        profile_file = self.root / "profiles" / f"{self.host}.json"

        if profile_file.is_file():
            r5 = self.run_command(
                f"doctor-profile-{self.host}",
                f"Validate typed harness profile for {self.host}",
                "adapter",
                [sys.executable, str(self.root / "scripts" / "portability_schema.py"), "validate", str(profile_file)],
                env=env,
            )
            passed = passed and (r5.verdict == "PASS")

        if self.host == "antigravity":
            r6 = self.run_command(
                "doctor-antigravity-sync",
                "Verify live Antigravity plugin synchronization",
                "package",
                [sys.executable, str(self.root / "scripts" / "sync_antigravity_plugin.py"), "--check"],
                env=env,
            )
            passed = passed and (r6.verdict == "PASS")

        if check_durability and profile_file.is_file():
            chk_cmd = [
                sys.executable,
                str(self.root / "scripts" / "verify_portable.py"),
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
            passed = passed and (r7.verdict == "PASS")

        return passed

    def _doctor_checks(self, fixture_home: Path, check_durability: bool = True, allow_stale: bool = False) -> bool:
        """Doctor scenarios 1-7; every command runs under fixture_home."""
        print(f"[{self.host}] Running Doctor checks...")
        env = {"HOME": str(fixture_home)}

        canon_pass = self._check_canonical_plane(env)
        adapter_pass = self._check_adapter_plane(env)
        pkg_pass = self._check_package_plane(env)
        doctor_pass = canon_pass and adapter_pass and pkg_pass

        profile_pass = self._check_profile_and_durability(
            env, check_durability=check_durability, allow_stale=allow_stale
        )
        return doctor_pass and profile_pass

    def drive(self, feature: Optional[str] = None) -> bool:
        """Step 3: Drive representative capability scenarios."""
        local_results = execute_local_scenarios(self, self.root)
        self.scenarios.extend(s for s in local_results if isinstance(s, ScenarioResult))

        driver = get_driver(self.host, self.root)
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
        host_version = resolve_host_version(self.host, self.root)
        surface_revisions = compute_surface_revisions(self.root, self.host)
        scenarios = normalize_scenarios(self.scenarios, self.root, self.get_canonical_root(self.root))

        return VerificationReceipt(
            run_id=self.run_id,
            host=self.host,
            host_version=host_version,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            overall_verdict=overall,
            planes=planes,
            surface_revisions=surface_revisions,
            scenarios=scenarios,
            artifacts=[str(self.run_dir / "receipt.json"), f".audit/evidence/{self.host}-receipt.json"],
            claim=f"{self.host} 5-harness portability conformance verification",
            kind="runtime",
        )

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


def run_verifier_action(
    verifier: PortableVerifier, action: str, args: argparse.Namespace
) -> Tuple[VerificationReceipt, bool]:
    """Execute a single verifier action for one host and return (receipt, passed)."""
    verifier.launch()

    if action == "doctor":
        ok = verifier.doctor(check_durability=not args.allow_stale, allow_stale=args.allow_stale)
        receipt = verifier.proof_bar()
        verifier.evidence(receipt, update_durable=False)
        return receipt, ok

    if action == "drive":
        verifier.doctor(check_durability=False)
        verifier.drive(feature=args.feature)
        receipt = verifier.proof_bar()
        verifier.evidence(receipt, update_durable=False)
        return receipt, (receipt.planes.get("runtime") == "PASS")

    if action == "run":
        verifier.doctor(check_durability=False)
        verifier.drive()
        receipt = verifier.proof_bar()
        profile_file = verifier.root / "profiles" / f"{verifier.host}.json"
        claimed_state = ""
        if profile_file.is_file():
            claimed_state = json.loads(profile_file.read_text(encoding="utf-8")).get("support_state", "")
        update_durable = claimed_state != "candidate"
        verifier.evidence(receipt, update_durable=update_durable)
        return receipt, (receipt.overall_verdict == "PASS")

    if action == "refresh-static":
        ok = verifier.doctor(check_durability=False)
        receipt = verifier.proof_bar()
        profile_file = verifier.root / "profiles" / f"{verifier.host}.json"
        claimed_state = ""
        if profile_file.is_file():
            claimed_state = json.loads(profile_file.read_text(encoding="utf-8")).get("support_state", "")
        update_durable = claimed_state != "candidate"
        allow_keep_live = (args.host == "all")
        verifier.evidence(receipt, update_durable=update_durable, allow_keep_live=allow_keep_live)
        return receipt, ok

    raise ValueError(f"Unknown verifier action: {action}")


def render_verification_summary(
    action: str, receipts: List[VerificationReceipt], all_pass: bool
) -> None:
    """Format and print the verification summary matrix table."""
    print(f"\n================ Verification Summary ================")
    for r in receipts:
        if action in ("doctor", "refresh-static"):
            status = reduce_verdicts(
                r.planes.get(p, "UNTESTED") for p in ("canonical", "adapter", "package")
            )
        elif action == "drive":
            status = "PASS" if (r.planes.get("runtime") == "PASS") else "FAIL"
        else:
            status = r.overall_verdict
        print(
            f"Host: {r.host:<12} | "
            f"Canonical: {r.planes.get('canonical', 'N/A'):<4} | "
            f"Adapter: {r.planes.get('adapter', 'N/A'):<4} | "
            f"Package: {r.planes.get('package', 'N/A'):<4} | "
            f"Runtime: {r.planes.get('runtime', 'N/A'):<4} | "
            f"Status: {status}"
        )
    print(f"======================================================")
    print(f"{len(receipts)}-Harness Matrix Verdict: {'PASS' if all_pass else 'FAIL'}\n")


def main(
    root: Path | None = None,
    evidence_dir: Path | None = None,
    get_canonical_root: Optional[Callable[[Path], Path]] = None,
) -> None:
    active_root = root if root is not None else ROOT
    default_ev_dir = evidence_dir if evidence_dir is not None else DEFAULT_EVIDENCE_DIR
    canon_fn = get_canonical_root

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "drive", "run", "refresh-static", "check-evidence", "check-staleness", "select-checks"], help="Action to execute")
    parser.add_argument("--host", choices=[*SUPPORTED_HOSTS, "all"], default="grok", help="Target harness (or 'all' for all declared hosts)")
    parser.add_argument("--feature", help="Feature to drive (for 'drive' action)")
    parser.add_argument("--evidence-dir", type=Path, default=default_ev_dir, help="Evidence directory")
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
        sys.exit(check_evidence_action(hosts, active_root, allow_stale=args.allow_stale))

    if args.action == "check-staleness":
        sys.exit(check_staleness_action(hosts, args.evidence_dir, active_root, json_output=args.json))

    if args.action == "select-checks":
        sys.exit(select_checks_action(args, active_root))

    all_pass = True
    receipts: List[VerificationReceipt] = []

    for h in hosts:
        verifier = PortableVerifier(
            host=h,
            evidence_root=args.evidence_dir,
            change=args.change,
            root=active_root,
            get_canonical_root_fn=canon_fn,
        )
        receipt, ok = run_verifier_action(verifier, args.action, args)
        receipts.append(receipt)
        all_pass = all_pass and ok

    if args.action == "run" or len(hosts) > 1:
        render_verification_summary(args.action, receipts, all_pass)

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
