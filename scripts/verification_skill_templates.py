"""Verification skill templates generator for portable agent harnesses.

Separated from scaffold_verification_skill.py for modular decomposition.
Generates driver.sh, SKILL.md, and feature specification templates.
"""

from __future__ import annotations


def generate_driver_script(app: str, *, formal: bool = False) -> str:
    target_type = "formal verification" if formal else "verification"
    purpose = (
        "formal model checker or bounded test harness"
        if formal
        else "app's real"
    )
    return f"""#!/usr/bin/env bash
# {target_type.capitalize()} driver stub template for {app}
# Wire each branch to the {purpose} command during tailoring; the
# 60s bound below applies to the tailored driver, not this stub.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${{BASH_SOURCE[0]}}")/../../../.." && pwd)"
if [[ -d "$ROOT/.venv/bin" ]]; then
    export PATH="$ROOT/.venv/bin:$PATH"
fi

PYTHON_EXEC="python3"
if command -v uv >/dev/null 2>&1 && [[ -d "$ROOT/.venv" ]]; then
    PYTHON_EXEC="uv run python"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON_EXEC="$ROOT/.venv/bin/python"
fi

BUN_EXEC="bun"
if ! command -v bun >/dev/null 2>&1; then
    BUN_EXEC="node"
fi

TIMEOUT_SECONDS=60

run_bounded() {{
    local label="$1"
    shift
    echo "==> Running $label (bounded by ${{TIMEOUT_SECONDS}}s)..."
    if command -v timeout >/dev/null 2>&1; then
        timeout "${{TIMEOUT_SECONDS}}" "$@" < /dev/null
    else
        "$@" < /dev/null
    fi
}}

case "${{1:-all}}" in
    doctor)
        echo "STUB_NOT_IMPLEMENTED: wire this branch to the {purpose} doctor command" >&2
        exit 2
        ;;
    launch)
        echo "STUB_NOT_IMPLEMENTED: wire this branch to the {purpose} launch command" >&2
        exit 2
        ;;
    drive)
        echo "STUB_NOT_IMPLEMENTED: wire this branch to the {purpose} drive command" >&2
        exit 2
        ;;
    cleanup)
        echo "STUB_NOT_IMPLEMENTED: wire this branch to the {purpose} cleanup command" >&2
        exit 2
        ;;
    all)
        "$0" doctor
        "$0" launch
        "$0" drive
        "$0" cleanup
        ;;
    *)
        echo "Usage: $0 {{doctor|launch|drive|cleanup|all}}" >&2
        exit 1
        ;;
esac
"""


def generate_skill_content(app: str, host: str, *, formal: bool = False) -> str:
    if formal:
        return f"""---
name: verify-{app}
description: "Use when formally verifying invariants, state transitions, or bounded models for {app} on {host}."
disable-model-invocation: true
---

# Formally verify {app} invariants

Draft formal verification skill requiring tailoring with concrete formal model/checker and bounded test harness.
Structural validation does not assess runtime proof.

## Coverage and sync record

- **Covered production commit:** `HEAD` (record checked commit hash during tailoring).
- **Target code:** specify files and functions verified by the model.
- **Invariants:** state safety (forbidden state never reached) and bounded liveness properties.
- **Bound:** finite state traces and input domains modeled.

## Model and checker choice

Specify the formal checker (TLA+ TLC, SMT solver, or bounded Python/Rust test harness) and deliberate broken mutant.
For TLA+ models, read verification outputs and trace invariant violations with `/statechart`.

## Launch

Prepare scratch directory, model files, and environment.

## Doctor

Read-only health check. Verify checker tooling and dependencies are available. Report BLOCKED or UNTESTED if missing, never assume PASS.

## Drive

Drive formal property verification and bounded model tests:
```bash
./scripts/driver.sh drive
```

## Proof bar

Verify all modeled traces pass and deliberate negative mutant fails.
Reduce scenario verdicts with the strict failure-first lattice: FAIL > BLOCKED > UNTESTED > PASS.

## Evidence

Capture counterexample traces, state space size, and git revision. Distinguish offline trace checks from live host observation.
Bound driver command executions to 60 seconds with strict timeout handling once each branch is wired to the real checker.

## Cleanup

Tear down temporary verification directories. Ensure no lingering processes.

## Helpers

Run the verification driver script (stub until each branch is wired to the real checker):
```bash
./scripts/driver.sh doctor
./scripts/driver.sh drive
./scripts/driver.sh cleanup
```
"""

    return f"""---
name: verify-{app}
description: "Use when verifying, reproducing, or proving behavior for {app} on {host}."
disable-model-invocation: true
---

# Verify {app}

Draft requiring tailoring with concrete app commands and a shipped driver.
Structural validation does not assess runtime proof.

## Launch

Start local instance in an isolated environment. Verify process readiness before driving.

## Doctor

Read-only health check. Confirm binary, dependencies, and environment are valid before driving.

## Drive

Drive user paths through programmatic commands or test runner. Prefer stable handles.

## Proof bar

Verify production path plus observable side effects. Exercise happy, error, and boundary states.
Reduce scenario verdicts with the strict failure-first lattice: FAIL > BLOCKED > UNTESTED > PASS.

## Evidence

Capture test outputs, exit codes, transcripts, and artifacts. Verify they survive teardown.
Tag evidence with evidence_level (observed_live for live runs, offline for contract checks).
Bound driver command executions to 60 seconds with strict timeout handling once each branch is wired to the app's real command.

## Cleanup

Tear down any processes or temporary instances spawned during verification.

## Helpers

Run the verification driver script (stub until each branch is wired to the app's real command):
```bash
./scripts/driver.sh doctor
./scripts/driver.sh drive
./scripts/driver.sh cleanup
```
"""


def generate_features_readme(app: str, *, formal: bool = False) -> str:
    feature_file = "formal-model.md" if formal else "core.md"
    description = "Formal model and invariant properties." if formal else "Core application behavior."
    title = f"Formal Feature Map for {app}" if formal else f"Feature Map for {app}"
    return f"""# {title}

## Full sweep

Order of verification sweep across features:
1. `{feature_file}`

## Features

- [`{feature_file}`]({feature_file}): {description}
"""


def generate_feature_content(app: str, *, formal: bool = False) -> str:
    if formal:
        return f"""# Formal Invariant Property: {app}

## Sub-features
- State transition safety
- Bounded invariant exploration

## How to get to it (user POV)
Invoke formal verification driver for `{app}`.

## Driving it with harness
Execute formal checker suite and assert all invariants hold and mutants fail.

## Gotchas
Ensure formal tooling is installed and model sync commit matches target code.
"""

    return f"""# Core Feature: {app}

## Sub-features
- Initial startup
- Primary command execution

## How to get to it (user POV)
Invoke `{app}` with required arguments.

## Driving it with harness
Execute verification recipe and assert exit code 0.

## Gotchas
Ensure working directory and dependencies are initialized.
"""
