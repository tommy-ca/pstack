#!/usr/bin/env python3
"""Portable lever verification engine for pstack across agent harnesses.

Implements the pattern from Build the Lever + Prove It Works + create-verification-skill:
    Launch -> Doctor -> Drive -> Proof Bar -> Evidence -> Cleanup

Usage:
    python3 scripts/verify-portable.py doctor [--host <host>]
    python3 scripts/verify-portable.py drive --feature <feature> [--host <host>]
    python3 scripts/verify-portable.py run [--host <host>] [--evidence-dir <dir>]
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.portability_schema import (
    Binding,
    Capability,
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
)
from scripts.drivers import get_driver

SUPPORTED_HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "droid", "mock")


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


DECLARED_HOSTS = get_declared_hosts()
FIVE_HARNESSES = tuple(DECLARED_HOSTS)
DEFAULT_EVIDENCE_DIR = ROOT / ".audit" / "evidence"


class PortableVerifier:
    def __init__(self, host: str, evidence_root: Path):
        self.host = host
        self.evidence_root = evidence_root
        self.run_id = f"{host}-{int(time.time())}-{secrets.token_hex(4)}"
        self.run_dir = self.evidence_root / self.run_id
        self.scenarios: List[ScenarioResult] = []

    def launch(self) -> bool:
        """Step 1: Launch prerequisite checks."""
        self.run_dir.mkdir(parents=True, exist_ok=True)
        return True

    def run_command(self, scenario_id: str, desc: str, plane: str, cmd: List[str], cwd: Optional[Path] = None) -> ScenarioResult:
        start = time.time()
        proc = subprocess.run(
            cmd,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        duration = round(time.time() - start, 3)
        stdout_snip = proc.stdout.strip()[:300]
        stderr_snip = proc.stderr.strip()[:300]
        verdict = "PASS" if proc.returncode == 0 else "FAIL"

        result = ScenarioResult(
            id=scenario_id,
            description=desc,
            plane=plane,
            command=" ".join(cmd),
            exit_code=proc.returncode,
            stdout_snippet=stdout_snip or stderr_snip,
            verdict=verdict,
            duration_s=duration,
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

        # 2. OpenSpec change integrity
        r2 = self.run_command(
            "doctor-openspec-validation",
            "Verify active openspec changes pass schema checks",
            "canonical",
            ["openspec", "validate", "pstack-portability-contract", "--type", "change", "--strict"],
        )

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
            )
        )

        # 4. Native workspace isolation contract
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
            )
        )

        # 5. Native evidence capture contract
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
            )
        )

        return all(s.verdict == "PASS" for s in self.scenarios if s.plane == "runtime")

    def proof_bar(self) -> VerificationReceipt:
        """Step 4: Compute the proof bar and verdicts across the four planes."""
        planes = {}
        for plane in ("canonical", "adapter", "package", "runtime"):
            results = [s for s in self.scenarios if s.plane == plane]
            if not results:
                planes[plane] = "UNTESTED"
            elif any(s.verdict == "BLOCKED" for s in results):
                planes[plane] = "BLOCKED"
            elif all(s.verdict == "PASS" for s in results):
                planes[plane] = "PASS"
            else:
                planes[plane] = "FAIL"

        if any(v == "BLOCKED" for v in planes.values()):
            overall = "BLOCKED"
        elif all(v == "PASS" for v in planes.values()):
            overall = "PASS"
        else:
            overall = "FAIL"

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
                host_version = "0.15.15-grokbuild.0"

        surface_revisions = compute_surface_revisions(ROOT, self.host)

        receipt = VerificationReceipt(
            run_id=self.run_id,
            host=self.host,
            host_version=host_version,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            overall_verdict=overall,
            planes=planes,
            surface_revisions=surface_revisions,
            scenarios=self.scenarios,
            artifacts=[str(self.run_dir / "receipt.json"), f".audit/evidence/{self.host}-receipt.json"],
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
            # Stable durable receipt copy
            durable_file = self.evidence_root / f"{self.host}-receipt.json"
            durable_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

            # Update durable index.json
            index_file = self.evidence_root / "index.json"
            index_data: Dict[str, Any] = {"version": 1, "hosts": {}}
            if index_file.is_file():
                try:
                    index_data = json.loads(index_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
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
    parser.add_argument("action", choices=["doctor", "drive", "run", "check-evidence", "check-staleness"], help="Action to execute")
    parser.add_argument("--host", choices=[*SUPPORTED_HOSTS, "all"], default="grok", help="Target harness (or 'all' for all declared hosts)")
    parser.add_argument("--feature", help="Feature to drive (for 'drive' action)")
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR, help="Evidence directory")
    parser.add_argument("--allow-stale", action="store_true", help="Allow stale evidence during durability check")
    parser.add_argument("--json", action="store_true", help="Emit JSON output for machine consumption")
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
                print(f"[{h}] PASS: Evidence durable, derived support state: {res['derived_support_state']} (claimed: {res['claimed_support_state']})")
            except Exception as err:
                print(f"[{h}] FAIL: {err}")
                all_ok = False
        sys.exit(0 if all_ok else 1)

    if args.action == "check-staleness":
        staleness_report: Dict[str, Any] = {}
        all_fresh = True
        for h in hosts:
            current_revs = compute_surface_revisions(ROOT, h)
            receipt_file = args.evidence_dir / f"{h}-receipt.json"
            if not receipt_file.is_file():
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

    all_pass = True
    receipts: List[VerificationReceipt] = []

    for h in hosts:
        verifier = PortableVerifier(host=h, evidence_root=args.evidence_dir)
        verifier.launch()

        if args.action == "doctor":
            ok = verifier.doctor(check_durability=not args.allow_stale, allow_stale=args.allow_stale)
            receipt = verifier.proof_bar()
            verifier.evidence(receipt, update_durable=False)
            receipts.append(receipt)
            all_pass = all_pass and ok

        elif args.action == "drive":
            verifier.doctor(check_durability=False)
            ok = verifier.drive(feature=args.feature)
            receipt = verifier.proof_bar()
            verifier.evidence(receipt, update_durable=False)
            receipts.append(receipt)
            all_pass = all_pass and ok

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

    if args.action == "run" or len(hosts) > 1:
        print(f"\n================ Verification Summary ================")
        for r in receipts:
            if args.action == "doctor":
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
