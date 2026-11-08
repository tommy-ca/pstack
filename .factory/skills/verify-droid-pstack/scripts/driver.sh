#!/usr/bin/env bash
# Verification driver for Droid PStack integration
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
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

BUN_EXEC="bun"
if ! command -v bun >/dev/null 2>&1; then
    BUN_EXEC="node"
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

case "${1:-all}" in
    doctor)
        run_bounded "package_projection" $PYTHON_EXEC scripts/package_projection.py --check
        run_bounded "droid_tests" $PYTHON_EXEC -m pytest -q tests/test_droid_projection.py tests/test_droid_integration.py
        run_bounded "doctor_checks" $PYTHON_EXEC scripts/verify_portable.py doctor --host droid
        ;;
    launch)
        echo "Launch: Validating environment and profile readiness..."
        if [[ ! -f "profiles/droid.json" ]]; then
            echo "Error: profiles/droid.json not found" >&2
            exit 1
        fi
        if [[ ! -f ".factory-plugin/plugin.json" ]]; then
            echo "Error: .factory-plugin/plugin.json not found" >&2
            exit 1
        fi
        echo "Launch: Droid environment ready."
        ;;
    drive)
        run_bounded "package_projection" $PYTHON_EXEC scripts/package_projection.py --check
        run_bounded "check_staleness" $PYTHON_EXEC scripts/verify_portable.py check-staleness --host droid
        run_bounded "check_evidence" $PYTHON_EXEC scripts/verify_portable.py check-evidence --host droid
        ;;
    cleanup)
        echo "Cleanup: No lingering processes or artifacts."
        ;;
    all)
        "$0" doctor
        "$0" launch
        "$0" drive
        "$0" cleanup
        ;;
    *)
        echo "Usage: $0 {doctor|launch|drive|cleanup|all}" >&2
        exit 1
        ;;
esac
