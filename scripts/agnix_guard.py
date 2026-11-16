#!/usr/bin/env python3
"""Read-only version-pinned Agnix static guard for active PStack agent configs.

Structural configuration linting is NOT native host execution or unbounded proof.
The binary is resolved from a mise pin or an explicitly supplied test candidate.
The binary is never resolved opportunistically from PATH or node_modules.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.61.0"
MIN_FILES = 325
BASELINE_WARNINGS = 31
MAX_SECONDS = 120
EXPECTED_EXCLUDES = frozenset({
    ".git/**", ".worktrees/**", ".audit/**", ".llm-wiki/**", "docs/**",
    "openspec/changes/archive/**", "tests/**", "examples/**",
})
EXPECTED_GENERIC = ["droids/*.md"]
MISE_TOOL = "github:agent-sh/agnix"


def policy_errors(root: Path) -> list[str]:
    """Detect policy erosion before trusting a potentially vacuous linter PASS."""
    errors: list[str] = []
    try:
        config = tomllib.loads((root / ".agnix.toml").read_text(encoding="utf-8"))
        mise = tomllib.loads((root / "mise.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"missing or invalid agnix or mise configuration: {exc}"]

    if config.get("severity") != "Warning":
        errors.append("severity must remain Warning (not weakened to Info)")
    if config.get("target") or config.get("tools") or config.get("extend"):
        errors.append("multi-host guard must not narrow its target or inherit hidden rules")
    exclusions = config.get("exclude")
    if not isinstance(exclusions, list) or set(map(str, exclusions)) != EXPECTED_EXCLUDES or len(exclusions) != len(EXPECTED_EXCLUDES):
        errors.append("exclusions differ from the reviewed non-active surface list")
    rules = config.get("rules")
    if not isinstance(rules, dict) or rules.get("disabled_rules") != [] or any(v is False for k, v in rules.items() if k != "disabled_rules"):
        errors.append("rule categories must stay enabled and disabled_rules must be empty")
    if config.get("overrides"):
        errors.append("per-file rule overrides are not authorized by the guard")
    files = config.get("files")
    if not isinstance(files, dict) or files.get("include_as_generic") != EXPECTED_GENERIC or files.get("exclude") or files.get("include_as_memory"):
        errors.append("files scope differs from the reviewed Droid-only generic mapping")
    if mise.get("tools", {}).get(MISE_TOOL) != VERSION:
        errors.append(f"mise must pin {MISE_TOOL} at {VERSION}")
    return errors


def resolve_binary(explicit: Path | None) -> Path | None:
    path = explicit or (Path(os.environ["AGNIX_BIN"]) if os.environ.get("AGNIX_BIN") else None)
    if path is None:
        home = os.environ.get("HOME")
        if not home:
            return None
        path = Path(home) / ".local/share/mise/installs/github-agent-sh-agnix" / VERSION / "agnix"
    if "node_modules" in path.resolve().parts:
        return None
    return path.resolve() if path.is_file() else None


def receipt_errors(payload: Any, code: int, warning_budget: int | None = None) -> list[str]:
    """Pure verdict boundary rejecting malformed, wrong-version, or contradictory receipts."""
    if not isinstance(payload, dict):
        return ["agnix did not return an object"]
    errors: list[str] = []
    if payload.get("version") != VERSION:
        errors.append("agnix version differs from the pinned version")
    files = payload.get("files_checked")
    if type(files) is not int or files < MIN_FILES:
        errors.append(f"agnix checked fewer than {MIN_FILES} files")
    summary = payload.get("summary")
    diagnostics = payload.get("diagnostics")
    if not isinstance(summary, dict) or not isinstance(diagnostics, list):
        return errors + ["agnix receipt lacks diagnostics or summary"]

    counts: dict[str, int] = {}
    for level in ("errors", "warnings", "info"):
        value = summary.get(level)
        if type(value) is not int or value < 0:
            errors.append(f"agnix summary {level} must be a nonnegative integer")
        else:
            counts[level] = value

    if any(not isinstance(d, dict) for d in diagnostics):
        errors.append("agnix diagnostics contain a non-object entry")

    detail_counts = {"errors": 0, "warnings": 0, "info": 0}
    for d in diagnostics:
        if isinstance(d, dict):
            lvl = d.get("level")
            if lvl == "error":
                detail_counts["errors"] += 1
            elif lvl == "warning":
                detail_counts["warnings"] += 1
            elif lvl == "info":
                detail_counts["info"] += 1

    for key, count_val in counts.items():
        if count_val != detail_counts[key]:
            errors.append(
                f"agnix summary {key} ({count_val}) does not match diagnostics count ({detail_counts[key]})"
            )

    if counts.get("errors", 0) > 0 or detail_counts["errors"] > 0:
        errors.append("agnix reported error-level diagnostics")
    effective_warnings = max(counts.get("warnings", 0), detail_counts["warnings"])
    if warning_budget is not None and effective_warnings > warning_budget:
        errors.append(f"warnings ({effective_warnings}) exceed budget ({warning_budget})")
    if code != 0:
        errors.append(f"agnix process exited with status {code}")
    return errors


def bounded_model() -> tuple[int, list[str]]:
    """Enumerate a finite lattice of receipt states and assert invariant satisfaction."""
    failures: list[str] = []
    count = 0
    mutant_witness = False
    versions = [VERSION, "0.59.0"]
    file_counts = [MIN_FILES, MIN_FILES - 1]
    error_counts = [0, 1]
    warning_counts = [0, 20, BASELINE_WARNINGS + 1]
    exit_codes = [0, 1]
    budgets = [None, BASELINE_WARNINGS, 10]
    inconsistent_states = [False, True]

    for version, files, err_count, warn_count, exit_code, budget, inconsistent in itertools.product(
        versions, file_counts, error_counts, warning_counts, exit_codes, budgets, inconsistent_states
    ):
        if inconsistent:
            diag_err = err_count
            diag_warn = warn_count + 1
        else:
            diag_err = err_count
            diag_warn = warn_count

        diagnostics: list[dict[str, Any]] = []
        for _ in range(diag_err):
            diagnostics.append({"level": "error", "rule": "AS-001"})
        for _ in range(diag_warn):
            diagnostics.append({"level": "warning", "rule": "AS-002"})

        payload = {
            "version": version,
            "files_checked": files,
            "summary": {"errors": err_count, "warnings": warn_count, "info": 0},
            "diagnostics": diagnostics,
        }
        actual = not receipt_errors(payload, exit_code, budget)
        expected = (
            version == VERSION and
            files >= MIN_FILES and
            err_count == 0 and
            exit_code == 0 and
            not inconsistent and
            (budget is None or warn_count <= budget)
        )
        count += 1
        if actual != expected:
            failures.append(
                f"counterexample: {version=}, {files=}, {err_count=}, {warn_count=}, {exit_code=}, {budget=}, {inconsistent=}"
            )

        # Negative mutant drops detail reconciliation and accepts inconsistent counts.
        mutated_pass = (
            version == VERSION and
            files >= MIN_FILES and
            err_count == 0 and
            exit_code == 0 and
            (budget is None or warn_count <= budget)
        )
        if mutated_pass and inconsistent and not actual:
            mutant_witness = True

    if not mutant_witness:
        failures.append("negative mutant did not expose a failing witness")
    return count, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Agnix guard for PStack")
    parser.add_argument("--binary", type=Path, default=None)
    parser.add_argument("--check-policy", action="store_true")
    parser.add_argument("--doctor", action="store_true", help="check pinned executable and version")
    parser.add_argument(
        "--formal",
        action="store_true",
        help="run bounded real-code receipt invariants and a negative mutant",
    )
    parser.add_argument("--warning-budget", type=int, default=BASELINE_WARNINGS)
    args = parser.parse_args(argv)
    if args.formal:
        count, failures = bounded_model()
        print(
            f"AGNIX_FORMAL bounded_states={count} mutant=detected"
            if not failures
            else f"AGNIX_FORMAL FAIL states={count}"
        )
        for error in failures[:8]:
            print(error, file=sys.stderr)
        return 1 if failures else 0

    errors = policy_errors(ROOT)
    if errors:
        for error in errors:
            print(f"AGNIX_POLICY FAIL: {error}", file=sys.stderr)
        return 1
    if args.check_policy:
        print("AGNIX_POLICY PASS (configuration only; execution UNTESTED)")
        return 0
    if args.warning_budget < 0 or args.warning_budget > BASELINE_WARNINGS:
        print("AGNIX_POLICY FAIL: warning budget must not exceed reviewed baseline", file=sys.stderr)
        return 1

    binary = resolve_binary(args.binary)
    if binary is None:
        print("AGNIX_BLOCKED: run mise install for pinned github:agent-sh/agnix", file=sys.stderr)
        return 2
    if args.doctor:
        try:
            version = subprocess.run(
                [str(binary), "--version"],
                capture_output=True,
                text=True,
                timeout=MAX_SECONDS,
                env={"LC_ALL": "C.UTF-8", "NO_COLOR": "1"},
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            print(f"AGNIX_BLOCKED: {exc}", file=sys.stderr)
            return 2
        if version.returncode != 0 or VERSION not in version.stdout:
            print("AGNIX_BLOCKED: pinned executable version mismatch", file=sys.stderr)
            return 2
        print(f"AGNIX_DOCTOR PASS version={VERSION} (static only)")
        return 0
    try:
        proc = subprocess.run(
            [str(binary), "--format", "json", "--config", str(ROOT / ".agnix.toml"), str(ROOT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=MAX_SECONDS,
            env={"LC_ALL": "C.UTF-8", "NO_COLOR": "1"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"AGNIX_BLOCKED: {exc}", file=sys.stderr)
        return 2
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        print(f"AGNIX_BLOCKED: non-JSON output; exit={proc.returncode}; {proc.stderr[:400]}", file=sys.stderr)
        return 2
    errors = receipt_errors(payload, proc.returncode, args.warning_budget)
    summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
    print(
        f"AGNIX_STATIC files={payload.get('files_checked')} version={payload.get('version')} "
        f"errors={summary.get('errors')} warnings={summary.get('warnings')} "
        f"info={summary.get('info')} verdict={'FAIL' if errors else 'PASS'}"
    )
    if isinstance(payload.get("diagnostics"), list):
        actionable = [
            d for d in payload["diagnostics"]
            if isinstance(d, dict) and d.get("level") in ("error", "warning")
        ]
        for d in actionable[:100]:
            print(f"  {d.get('level')} {d.get('rule')} {d.get('file')}:{d.get('line')}")
        if len(actionable) > 100:
            print(f"  {len(actionable) - 100} additional actionable diagnostics omitted")
    for error in errors:
        print(f"AGNIX_FAIL: {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
