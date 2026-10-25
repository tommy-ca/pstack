"""Check selection and git diff mapping for portable verification (#594).

Separated from verify-portable.py for modular decomposition.
"""

from __future__ import annotations

import fnmatch
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Tuple, TypedDict

from scripts.evidence_receipts import (
    can_claim_current_ci,
    check_check_evidence_staleness,
    compute_patch_id,
    create_check_evidence_receipt,
    load_check_evidence_receipt,
    resolve_merge_base,
    resolve_revision,
)

ROOT = Path(__file__).resolve().parents[1]

OFFLINE_WORKFLOW = Path(".github/workflows/portability-offline.yml")
SCAN_HOST_BOUNDARY = (sys.executable, "scripts/scan-host-boundary.py")
CANONICAL_INDEX_CHECK = (sys.executable, "scripts/canonical-index.py", "--check")


class CheckRule(NamedTuple):
    pattern: str
    module_tokens: Tuple[str, ...]
    verifier_commands: Tuple[Tuple[str, ...], ...] = ()

    @property
    def tests(self) -> Tuple[str, ...]:
        return self.module_tokens

    @property
    def commands(self) -> Tuple[Tuple[str, ...], ...]:
        return self.verifier_commands


class SelectedCheck(TypedDict):
    id: str
    tier: str
    command: List[str]
    paths: List[str]


CheckEntry = SelectedCheck


class CheckSelectionResult(TypedDict):
    checks: List[SelectedCheck]
    unmapped_paths: List[str]


CheckSelection = CheckSelectionResult


class ChangedPathsResult(TypedDict):
    merge_base: str
    head_sha: str
    changed_paths: List[str]


class SelectionPlan(TypedDict):
    base: str
    head: str
    merge_base: str
    head_sha: str
    patch_id: str
    changed_paths: List[str]
    unmapped_paths: List[str]
    defaulted_to_offline: bool
    checks: List[SelectedCheck]


def offline_contract_tests(root: Path = ROOT) -> List[str]:
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


CHECK_SELECTION_TABLE: List[CheckRule] = [
    CheckRule(*entry)
    for entry in [
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
    ("*.md", ("tests/test_verify_docs_sync.py",), ()),
    ("**/*.md", ("tests/test_verify_docs_sync.py",), ()),
    ("openspec/**", ("tests/test_verify_docs_sync.py",), ()),
    ("LICENSE", ("tests/test_verify_docs_sync.py",), ()),
    (".github/**", ("{offline}",), ()),
    ("schemas/**", ("tests/test_portability_schemas.py",), ()),
    ("profiles/**", ("tests/test_portability_schemas.py", "tests/test_evidence_durability.py"), ()),
    (
        "scripts/portability_types.py",
        (
            "tests/test_portability_schemas.py",
            "tests/test_verdict_reduction.py",
            "tests/test_evidence_durability.py",
        ),
        (),
    ),
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
        "scripts/harness_scenarios.py",
        ("tests/test_verify_portable.py",),
        (),
    ),
    (
        "scripts/verify-portable.py",
        ("tests/test_verify_portable.py", "tests/test_verdict_reduction.py", "tests/test_evidence_refresh_static.py"),
        (),
    ),
    (
        "scripts/portable_verifier.py",
        ("tests/test_verify_portable.py", "tests/test_verdict_reduction.py", "tests/test_evidence_refresh_static.py"),
        (),
    ),
    (
        "scripts/verify-harness.py",
        (
            "tests/test_verify_harness.py",
            "tests/test_verify_harness_archive.py",
            "tests/test_verify_harness_guides.py",
            "tests/test_verify_harness_playbooks.py",
        ),
        (),
    ),
    (
        "scripts/verify_harness.py",
        (
            "tests/test_verify_harness.py",
            "tests/test_verify_harness_archive.py",
            "tests/test_verify_harness_guides.py",
            "tests/test_verify_harness_playbooks.py",
        ),
        (),
    ),
    (
        "scripts/adapt-harness.py",
        ("tests/test_verify_harness.py",),
        (),
    ),
    (
        "scripts/adapt_harness.py",
        ("tests/test_verify_harness.py",),
        (),
    ),
    ("scripts/verify-decision-contract.py", ("tests/test_verify_decision_contract.py",), ()),
    ("scripts/verify_decision_contract.py", ("tests/test_verify_decision_contract.py",), ()),
    ("scripts/verify_rollback_equivalence.py", ("tests/test_rollback_equivalence.py",), ()),
    ("scripts/scan-host-boundary.py", ("tests/test_scan_host_boundary.py",), ()),
    ("scripts/scan_host_boundary.py", ("tests/test_scan_host_boundary.py",), ()),
    ("scripts/skill_frontmatter.py", ("tests/test_skill_frontmatter.py",), ()),
    ("scripts/project-package.py", ("tests/test_project_package.py", "tests/test_droid_projection.py"), ()),
    ("scripts/package_projection.py", ("tests/test_project_package.py", "tests/test_droid_projection.py"), ()),
    (
        "scripts/package-lifecycle.py",
        ("tests/test_package_lifecycle.py", "tests/test_package_lifecycle_safety.py"),
        (),
    ),
    (
        "scripts/package_lifecycle.py",
        ("tests/test_package_lifecycle.py", "tests/test_package_lifecycle_safety.py"),
        (),
    ),
    ("scripts/canonical-index.py", ("tests/test_canonical_index.py",), ()),
    ("scripts/canonical_index.py", ("tests/test_canonical_index.py",), ()),
    ("scripts/scaffold-verification-skill.py", ("tests/test_scaffold_verification_skill.py",), ()),
    ("scripts/scaffold_verification_skill.py", ("tests/test_scaffold_verification_skill.py",), ()),
    ("scripts/sync-antigravity-plugin.py", ("tests/test_sync_antigravity_plugin.py",), ()),
    ("scripts/sync_antigravity_plugin.py", ("tests/test_sync_antigravity_plugin.py",), ()),
    (
        "scripts/sync-from-upstream.py",
        ("tests/test_verify_harness_guides.py", "tests/test_refresh_hygiene.py"),
        (),
    ),
    (
        "scripts/sync_from_upstream.py",
        ("tests/test_verify_harness_guides.py", "tests/test_refresh_hygiene.py"),
        (),
    ),
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
    (
        "scripts/surface_revisions.py",
        ("tests/test_portability_schemas.py", "tests/test_surface_cache.py"),
        (),
    ),
    (
        "scripts/evidence_durability.py",
        (
            "tests/test_evidence_durability.py",
            "tests/test_evidence_index_resilience.py",
            "tests/test_evidence_settlement.py",
            "tests/test_evidence_cancellation.py",
            "tests/test_portability_schemas.py",
        ),
        (),
    ),
    (
        "scripts/select_checks.py",
        ("tests/test_select_checks.py", "tests/test_verify_portable.py"),
        (),
    ),
    (
        "scripts/openspec_change.py",
        ("tests/test_openspec_change.py", "tests/test_verify_portable.py"),
        (),
    ),
    (
        "scripts/evidence_index.py",
        (
            "tests/test_evidence_durability.py",
            "tests/test_evidence_index_resilience.py",
            "tests/test_verify_portable.py",
        ),
        (),
    ),
    (
        "scripts/model_role_resolver.py",
        (
            "tests/test_model_role_schema.py",
            "tests/test_model_role_constraints.py",
            "tests/test_model_role_profiles.py",
            "tests/test_setup_pstack.py",
        ),
        (),
    ),
    (
        "scripts/model_role_policy.py",
        (
            "tests/test_model_role_schema.py",
            "tests/test_model_role_constraints.py",
            "tests/test_model_role_profiles.py",
            "tests/test_setup_pstack.py",
        ),
        (),
    ),
    (
        "scripts/setup_pstack.py",
        (
            "tests/test_setup_pstack.py",
            "tests/test_model_role_schema.py",
            "tests/test_model_role_constraints.py",
            "tests/test_model_role_profiles.py",
        ),
        (),
    ),
    (
        "scripts/host_identity.py",
        ("tests/test_host_identity.py", "tests/test_portability_schemas.py"),
        (),
    ),
    (
        "scripts/effort_ladder.py",
        ("tests/test_verify_harness.py",),
        (),
    ),
    (
        "scripts/check-plugin-agents.py",
        ("tests/test_plugin_agents.py",),
        (),
    ),
    (
        "scripts/check_plugin_agents.py",
        ("tests/test_plugin_agents.py",),
        (),
    ),
    (
        "scripts/eval_blinded_pstack.py",
        ("tests/test_eval_blinded_pstack_dsh_candidate.py",),
        (),
    ),
    (
        "scripts/eval_decision_routing.py",
        ("tests/test_verify_decision_contract.py",),
        (),
    ),
    (
        "scripts/decision_adapter.py",
        ("tests/test_verify_decision_contract.py",),
        (),
    ),
    (
        "scripts/prove-omp-native-package.py",
        ("tests/test_omp_native_package.py",),
        (),
    ),
    (
        "scripts/prove_omp_native_package.py",
        ("tests/test_omp_native_package.py",),
        (),
    ),
    (
        "scripts/prove-omp-vertical-slice.py",
        ("tests/test_omp_native_package.py", "tests/test_verdict_reduction.py"),
        (),
    ),
    (
        "scripts/prove_omp_vertical_slice.py",
        ("tests/test_omp_native_package.py", "tests/test_verdict_reduction.py"),
        (),
    ),
    ("scripts/**", ("{offline}",), ()),
    ]
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
        return "host_dependent"
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
) -> CheckSelectionResult:
    offline = offline_tests if offline_tests is not None else offline_contract_tests()
    checks: Dict[str, SelectedCheck] = {}
    unmapped: List[str] = []

    def add(command: List[str], tier: str, path: str) -> None:
        check = checks.get(_check_id(command))
        if check is None:
            check = {"id": _check_id(command), "tier": tier, "command": command, "paths": []}
            checks[check["id"]] = check
        if path not in check["paths"]:
            check["paths"].append(path)

    for path in changed:
        rule = next((r for r in CHECK_SELECTION_TABLE if pattern_matches(path, r.pattern)), None)
        if rule is None:
            unmapped.append(path)
            rule = CheckRule("(unmapped)", ("{offline}",), ())
        for token in _expand(rule.module_tokens, path, offline):
            add(_command_for(token), _tier(token, offline), path)
        for command in rule.verifier_commands:
            add(list(command), "offline", path)

    ordered = sorted(checks.values(), key=lambda c: (c["tier"], c["id"]))
    return {"checks": ordered, "unmapped_paths": unmapped}


def changed_paths(root: Path, base: str, head: str = "HEAD") -> ChangedPathsResult:
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
) -> SelectionPlan:
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


def _print_selection_plan(plan: SelectionPlan) -> None:
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


def select_checks_action(args, root: Path = ROOT) -> int:
    if not args.base:
        print("ERROR: --base is required for select-checks", file=sys.stderr)
        return 2

    plan = select_checks_plan(args.base, args.head, root)

    if args.record:
        outcomes = {}
        for item in args.outcome:
            check_id, _, verdict = item.partition("=")
            outcomes[check_id.strip()] = verdict.strip().upper() or "UNTESTED"
        receipt = create_check_evidence_receipt(
            root, args.base, [c["id"] for c in plan["checks"]], outcomes, args.head
        )
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(receipt.to_json() + "\n", encoding="utf-8")
        print(
            f"Recorded check evidence: {args.record} "
            f"(head {receipt.head_sha[:8]}, patch-id {receipt.patch_id[:8]}, verdict {receipt.verdict})"
        )

    if args.receipt:
        from scripts.evidence_index import _file_or_denied

        if not _file_or_denied(args.receipt):
            print(f"No recorded evidence at {args.receipt}: run the selected checks, then record them.")
            return 2
        try:
            receipt = load_check_evidence_receipt(args.receipt)
        except OSError as err:
            print(
                f"REFUSING to evaluate unreadable recorded evidence {args.receipt}: "
                f"{type(err).__name__}: {err}"
            )
            return 2
        stale, reasons = check_check_evidence_staleness(receipt, root, args.base, args.head)
        claimable, claim_reason = can_claim_current_ci(receipt, root, args.base, args.head)
        if args.json:
            import json

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
        return 1 if stale else 0

    if args.json:
        import json

        print(json.dumps(plan, indent=2))
    else:
        _print_selection_plan(plan)
    return 0
