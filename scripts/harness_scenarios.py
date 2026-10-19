"""Native harness scenarios runner and local drive scenario execution.

Separated from verify-portable.py for modular decomposition (#604).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List, Optional

from scripts.portability_schema import ScenarioResult


def execute_local_scenarios(verifier: Any, root: Path) -> List[ScenarioResult]:
    results: List[ScenarioResult] = []

    results.append(
        verifier.run_command(
            "drive-principles-load",
            "Ensure poteto-mode loads all canonical principles without error",
            "canonical",
            [
                sys.executable,
                "-c",
                "import sys, json; from pathlib import Path; r = Path('.'); inv = json.loads((r/'openspec'/'canonical-inventory.json').read_text()); expected = [a['path'] for a in inv.get('artifacts', []) if a.get('category') == 'principle' and a.get('mode') in ('preserve', 'adapt')]; missing = [p for p in expected if not (r/p).is_file()]; sys.exit(1 if missing else 0)",
            ],
        )
    )

    results.append(
        verifier.run_command(
            "drive-check-plan",
            "Verify multi-phase plan checking logic",
            "adapter",
            ["bun", "test", str(root / "skills" / "poteto-mode" / "scripts" / "check-plan.test.mjs")],
        )
    )

    results.append(
        verifier.run_command(
            "drive-worktree-audit",
            "Run worktree isolation audit smoke test",
            "adapter",
            ["bash", str(root / "skills" / "poteto-mode" / "scripts" / "worktree-audit.sh"), "."],
        )
    )

    smoke_target = verifier.run_dir / "verify-smoke"
    results.append(
        verifier.run_command(
            "drive-verification-skill-scaffold",
            f"Prove verification skill scaffolding for {verifier.host}",
            "package",
            [
                sys.executable,
                str(root / "scripts" / "scaffold-verification-skill.py"),
                "--host",
                verifier.host,
                "--app",
                "smoke",
                "--write",
                "--target-dir",
                str(smoke_target),
            ],
        )
    )
    results.append(
        verifier.run_command(
            "drive-verification-skill-check",
            f"Validate generated verification skill structure for {verifier.host}",
            "package",
            [
                sys.executable,
                str(root / "scripts" / "scaffold-verification-skill.py"),
                "--host",
                verifier.host,
                "--check",
                "--target-dir",
                str(smoke_target),
            ],
        )
    )

    lifecycle_target = verifier.run_dir / f"lifecycle-{verifier.host}"
    results.append(
        verifier.run_command(
            f"drive-package-lifecycle-proof-{verifier.host}",
            f"Prove isolated native package lifecycle for {verifier.host}",
            "package",
            [
                sys.executable,
                str(root / "scripts" / "package-lifecycle.py"),
                "prove",
                "--host",
                verifier.host,
                "--target-dir",
                str(lifecycle_target),
            ],
        )
    )

    if verifier.host == "codex":
        results.append(
            verifier.run_command(
                "drive-codex-orch",
                "Verify Codex orch and store compatibility suite",
                "adapter",
                ["bun", "test", "./skills/poteto-mode/scripts/orch/orch.test.ts"],
            )
        )
        results.append(
            verifier.run_command(
                "drive-codex-watch-pr",
                "Verify Codex watch-pr policy and CLI suite",
                "adapter",
                ["bun", "test", "./skills/poteto-mode/scripts/watch-pr/cli.test.ts", "./skills/poteto-mode/scripts/watch-pr/policy.test.ts"],
            )
        )

    if verifier.host == "antigravity":
        results.append(
            verifier.run_command(
                "drive-antigravity-models",
                "Verify Antigravity model roles and panel definitions",
                "package",
                [sys.executable, "-c", "import json; from pathlib import Path; d = json.loads(Path('.antigravity-plugin/models.json').read_text()); assert d['singleRoleDefault'] == 'pro'; assert len(d['roles']) >= 10"],
            )
        )
        results.append(
            verifier.run_command(
                "drive-antigravity-tools-ref",
                "Verify Antigravity tool-mapping reference integrity",
                "adapter",
                [sys.executable, "-c", "from pathlib import Path; p = Path('skills/poteto-mode/references/antigravity-tools.md'); assert p.is_file(); t = p.read_text(); assert 'invoke_subagent' in t; assert 'ask_question' in t"],
            )
        )

    return results


def execute_driver_scenarios(
    verifier: Any,
    driver: Any,
    feature: Optional[str] = None,
) -> List[ScenarioResult]:
    results: List[ScenarioResult] = []

    sc_disc = driver.discover(verifier.run_dir)
    results.append(
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

    target_playbook = feature or "feature"
    sc_route = driver.route_playbook(target_playbook, verifier.run_dir)
    results.append(
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

    sc_spawn = driver.child_spawn(verifier.run_dir)
    results.append(
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

    if verifier.host == "omp":
        sc_cancel = driver.child_cancel(verifier.run_dir)
        results.append(
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

    sc_iso = driver.isolation(verifier.run_dir)
    results.append(
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

    sc_ev = driver.evidence_capture(verifier.run_dir)
    results.append(
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

    return results
