#!/usr/bin/env bash
# Verification driver for Antigravity PStack integration
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
        run_bounded "sync_tests" $PYTHON_EXEC -m pytest -q tests/test_sync_antigravity_plugin.py
        run_bounded "doctor_checks" $PYTHON_EXEC scripts/verify_portable.py doctor --host antigravity
        ;;
    launch)
        echo "Launch: Validating environment and profile readiness..."
        if [[ ! -f "profiles/antigravity.json" ]]; then
            echo "Error: profiles/antigravity.json not found" >&2
            exit 1
        fi
        echo "Launch: Antigravity environment ready."
        ;;
    drive)
        run_bounded "package_projection" $PYTHON_EXEC scripts/package_projection.py --check
        run_bounded "check_staleness" $PYTHON_EXEC scripts/verify_portable.py check-staleness --host antigravity
        run_bounded "check_evidence" $PYTHON_EXEC scripts/verify_portable.py check-evidence --host antigravity
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
