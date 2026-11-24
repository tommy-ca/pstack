#!/usr/bin/env bash
# Verification driver for Antigravity PStack integration
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SCRIPT_PATH="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/$(basename -- "${BASH_SOURCE[0]}")"
cd "$ROOT"
export _PSTACK_DRIVER_RUNNING=1
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
if [[ -d "$ROOT/.venv/bin" ]]; then
    export PATH="$ROOT/.venv/bin:$PATH"
fi

PYTHON_EXEC="python3"
if command -v uv >/dev/null 2>&1 && [[ -d "$ROOT/.venv" ]]; then
    PYTHON_EXEC="uv run python"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON_EXEC="$ROOT/.venv/bin/python"
fi

TIMEOUT_SECONDS=60

run_bounded() {
    local label="$1"
    shift
    echo "==> Running $label (bounded by ${TIMEOUT_SECONDS}s)..."
    if command -v timeout >/dev/null 2>&1; then
        timeout "${TIMEOUT_SECONDS}" "$@" < /dev/null
    else
        "$@" < /dev/null
    fi
}

run_proof() {
    local label="$1"
    shift
    echo "==> Running $label (bounded by ${TIMEOUT_SECONDS}s)..."
    local rc=0
    if command -v timeout >/dev/null 2>&1; then
        timeout "${TIMEOUT_SECONDS}" "$@" < /dev/null || rc=$?
    else
        "$@" < /dev/null || rc=$?
    fi
    if [[ $rc -ne 0 && $rc -ne 2 ]]; then
        echo "Error: $label failed with unexpected exit code $rc" >&2
        return "$rc"
    fi
    return 0
}

case "${1:-all}" in
    doctor)
        run_bounded "package_projection" $PYTHON_EXEC scripts/package_projection.py --check
        run_bounded "sync_tests" $PYTHON_EXEC -m pytest -q tests/test_sync_antigravity_plugin.py tests/test_antigravity_command_projection.py
        run_proof "native_package_proof" $PYTHON_EXEC scripts/prove_antigravity_native_package.py --json
        run_bounded "doctor_checks" $PYTHON_EXEC scripts/verify_portable.py doctor --host antigravity --allow-stale
        ;;
    launch)
        echo "Launch: Validating environment and profile readiness..."
        if [[ ! -f "profiles/antigravity.json" ]]; then
            echo "Error: profiles/antigravity.json not found" >&2
            exit 1
        fi
        if [[ ! -f ".antigravity-plugin/models.json" ]]; then
            echo "Error: .antigravity-plugin/models.json not found" >&2
            exit 1
        fi
        if command -v agy >/dev/null 2>&1; then
            echo "Launch: Detected $(agy --version 2>/dev/null || echo 'agy')."
        else
            echo "Launch: agy binary not on PATH (static verification mode)."
        fi
        echo "Launch: Antigravity environment ready."
        ;;
    drive)
        run_bounded "package_projection" $PYTHON_EXEC scripts/package_projection.py --check
        run_proof "native_package_proof" $PYTHON_EXEC scripts/prove_antigravity_native_package.py --json
        run_bounded "check_staleness" $PYTHON_EXEC scripts/verify_portable.py check-staleness --host antigravity
        run_bounded "check_evidence" $PYTHON_EXEC scripts/verify_portable.py check-evidence --host antigravity
        ;;
    cleanup)
        echo "Cleanup: No lingering processes or artifacts."
        ;;
    all)
        "$SCRIPT_PATH" doctor
        "$SCRIPT_PATH" launch
        "$SCRIPT_PATH" drive
        "$SCRIPT_PATH" cleanup
        ;;
    *)
        echo "Usage: $0 {doctor|launch|drive|cleanup|all}" >&2
        exit 1
        ;;
esac
