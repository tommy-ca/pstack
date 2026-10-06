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
    ValidationError,
)

SUPPORTED_HOSTS = ("grok", "codex", "omp", "opencode", "antigravity", "mock")
FIVE_HARNESSES = ("grok", "codex", "omp", "opencode", "antigravity")
DEFAULT_EVIDENCE_DIR = ROOT / ".audit" / "evidence"


@dataclass
class ScenarioResult:
    id: str
    description: str
    plane: str  # canonical | adapter | package | runtime
    command: str
    exit_code: int
    stdout_snippet: str
    verdict: str  # PASS | FAIL | BLOCKED
    duration_s: float


@dataclass
class VerificationReceipt:
    run_id: str
    host: str
    timestamp: str
    overall_verdict: str
    planes: Dict[str, str]
    scenarios: List[ScenarioResult] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)


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

    def doctor(self) -> bool:
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

        doctor_pass = all(r.verdict == "PASS" for r in (r1, r2, r3, r3b, r4))

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

        return doctor_pass

    def drive(self, feature: Optional[str] = None) -> bool:
        """Step 3: Drive representative capability scenarios."""
        print(f"[{self.host}] Driving capability scenarios...")

        # Drive 1: Router and principle discovery
        self.run_command(
            "drive-principles-load",
            "Ensure poteto-mode loads all canonical principles without error",
            "runtime",
            [
                sys.executable,
                "-c",
                "import sys, json; from pathlib import Path; r = Path('.'); inv = json.loads((r/'openspec'/'canonical-inventory.json').read_text()); expected = [a['path'] for a in inv.get('artifacts', []) if a.get('category') == 'principle' and a.get('mode') in ('preserve', 'adapt')]; missing = [p for p in expected if not (r/p).is_file()]; sys.exit(1 if missing else 0)",
            ],
        )

        # Drive 2: Plan checker validation
        self.run_command(
            "drive-check-plan",
            "Verify multi-phase plan checking logic",
            "runtime",
            ["bun", "test", str(ROOT / "skills" / "poteto-mode" / "scripts" / "check-plan.test.mjs")],
        )

        # Drive 3: Worktree audit isolation check
        self.run_command(
            "drive-worktree-audit",
            "Run worktree isolation audit smoke test",
            "runtime",
            ["bash", str(ROOT / "skills" / "poteto-mode" / "scripts" / "worktree-audit.sh"), "."],
        )

        # Drive 4: Cross-harness verification skill scaffolding and check
        smoke_target = self.run_dir / "verify-smoke"
        self.run_command(
            "drive-verification-skill-scaffold",
            f"Prove verification skill scaffolding for {self.host}",
            "runtime",
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
            "runtime",
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

        # Codex-specific runtime compatibility suites
        if self.host == "codex":
            self.run_command(
                "drive-codex-orch",
                "Verify Codex orch and store compatibility suite",
                "runtime",
                ["bun", "test", "./skills/poteto-mode/scripts/orch/orch.test.ts"],
            )
            self.run_command(
                "drive-codex-watch-pr",
                "Verify Codex watch-pr policy and CLI suite",
                "runtime",
                ["bun", "test", "./skills/poteto-mode/scripts/watch-pr/cli.test.ts", "./skills/poteto-mode/scripts/watch-pr/policy.test.ts"],
            )

        # Antigravity-specific runtime verification scenarios
        if self.host == "antigravity":
            self.run_command(
                "drive-antigravity-models",
                "Verify Antigravity model roles and panel definitions",
                "runtime",
                [sys.executable, "-c", "import json; from pathlib import Path; d = json.loads(Path('.antigravity-plugin/models.json').read_text()); assert d['singleRoleDefault'] == 'pro'; assert len(d['roles']) >= 10"],
            )
            self.run_command(
                "drive-antigravity-tools-ref",
                "Verify Antigravity tool-mapping reference integrity",
                "runtime",
                [sys.executable, "-c", "from pathlib import Path; p = Path('skills/poteto-mode/references/antigravity-tools.md'); assert p.is_file(); t = p.read_text(); assert 'invoke_subagent' in t; assert 'ask_question' in t"],
            )

        return all(s.verdict == "PASS" for s in self.scenarios if s.plane == "runtime")

    def proof_bar(self) -> VerificationReceipt:
        """Step 4: Compute the proof bar and verdicts across the four planes."""
        planes = {}
        for plane in ("canonical", "adapter", "package", "runtime"):
            results = [s for s in self.scenarios if s.plane == plane]
            if not results:
                planes[plane] = "UNTESTED"
            elif all(s.verdict == "PASS" for s in results):
                planes[plane] = "PASS"
            else:
                planes[plane] = "FAIL"

        overall = "PASS" if all(v == "PASS" for v in planes.values()) else "FAIL"

        receipt = VerificationReceipt(
            run_id=self.run_id,
            host=self.host,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            overall_verdict=overall,
            planes=planes,
            scenarios=self.scenarios,
            artifacts=[str(self.run_dir)],
        )
        return receipt

    def evidence(self, receipt: VerificationReceipt) -> Path:
        """Step 5: Write structured evidence receipt."""
        receipt_file = self.run_dir / "receipt.json"
        data = asdict(receipt)
        receipt_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"Evidence captured at {receipt_file}")
        return receipt_file

    def cleanup(self) -> None:
        """Step 6: Cleanup transient files while preserving evidence."""
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["doctor", "drive", "run"], help="Action to execute")
    parser.add_argument("--host", choices=[*SUPPORTED_HOSTS, "all"], default="grok", help="Target harness (or 'all' for all 5)")
    parser.add_argument("--feature", help="Feature to drive (for 'drive' action)")
    parser.add_argument("--evidence-dir", type=Path, default=DEFAULT_EVIDENCE_DIR, help="Evidence directory")
    args = parser.parse_args()

    hosts = list(FIVE_HARNESSES) if args.host == "all" else [args.host]
    all_pass = True
    receipts: List[VerificationReceipt] = []

    for h in hosts:
        verifier = PortableVerifier(host=h, evidence_root=args.evidence_dir)
        verifier.launch()

        if args.action == "doctor":
            ok = verifier.doctor()
            receipt = verifier.proof_bar()
            verifier.evidence(receipt)
            receipts.append(receipt)
            all_pass = all_pass and ok

        elif args.action == "drive":
            verifier.doctor()
            ok = verifier.drive(feature=args.feature)
            receipt = verifier.proof_bar()
            verifier.evidence(receipt)
            receipts.append(receipt)
            all_pass = all_pass and ok

        elif args.action == "run":
            verifier.doctor()
            verifier.drive()
            receipt = verifier.proof_bar()
            verifier.evidence(receipt)
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
        print(f"5-Harness Matrix Verdict: {'PASS' if all_pass else 'FAIL'}\n")

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
