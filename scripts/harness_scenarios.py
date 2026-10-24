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
            record=False,
        )
    )

    results.append(
        verifier.run_command(
            "drive-check-plan",
            "Verify multi-phase plan checking logic",
            "adapter",
            ["bun", "test", str(root / "skills" / "poteto-mode" / "scripts" / "check-plan.test.mjs")],
            record=False,
        )
    )

    results.append(
        verifier.run_command(
            "drive-worktree-audit",
            "Run worktree isolation audit smoke test",
            "adapter",
            ["bash", str(root / "skills" / "poteto-mode" / "scripts" / "worktree-audit.sh"), "."],
            record=False,
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
            record=False,
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
            record=False,
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
            record=False,
        )
    )

    if verifier.host == "codex":
        results.append(
            verifier.run_command(
                "drive-codex-orch",
                "Verify Codex orch and store compatibility suite",
                "adapter",
                ["bun", "test", "./skills/poteto-mode/scripts/orch/orch.test.ts"],
                record=False,
            )
        )
        results.append(
            verifier.run_command(
                "drive-codex-watch-pr",
                "Verify Codex watch-pr policy and CLI suite",
                "adapter",
                ["bun", "test", "./skills/poteto-mode/scripts/watch-pr/cli.test.ts", "./skills/poteto-mode/scripts/watch-pr/policy.test.ts"],
                record=False,
            )
        )

    if verifier.host == "antigravity":
        results.append(
            verifier.run_command(
                "drive-antigravity-models",
                "Verify Antigravity model roles and panel definitions",
                "package",
                [sys.executable, "-c", "import json; from pathlib import Path; d = json.loads(Path('.antigravity-plugin/models.json').read_text()); assert d['singleRoleDefault'] == 'pro'; assert len(d['roles']) >= 10"],
                record=False,
            )
        )
        results.append(
            verifier.run_command(
                "drive-antigravity-tools-ref",
                "Verify Antigravity tool-mapping reference integrity",
                "adapter",
                [sys.executable, "-c", "from pathlib import Path; p = Path('skills/poteto-mode/references/antigravity-tools.md'); assert p.is_file(); t = p.read_text(); assert 'invoke_subagent' in t; assert 'ask_question' in t"],
                record=False,
            )
        )

    return results


def execute_driver_scenarios(
    verifier: Any,
    driver: Any,
    feature: Optional[str] = None,
) -> List[ScenarioResult]:
    results: List[ScenarioResult] = []

    results.append(ScenarioResult.from_driver_result(driver.discover(verifier.run_dir)))

    target_playbook = feature or "feature"
    results.append(
        ScenarioResult.from_driver_result(
            driver.route_playbook(target_playbook, verifier.run_dir)
        )
    )

    results.append(ScenarioResult.from_driver_result(driver.child_spawn(verifier.run_dir)))

    if verifier.host == "omp":
        results.append(
            ScenarioResult.from_driver_result(driver.child_cancel(verifier.run_dir))
        )

    results.append(ScenarioResult.from_driver_result(driver.isolation(verifier.run_dir)))

    results.append(ScenarioResult.from_driver_result(driver.evidence_capture(verifier.run_dir)))

    return results
