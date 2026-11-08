#!/usr/bin/env bash
# Verification driver for Pi candidate PStack integration
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
        run_bounded "pi_check" $PYTHON_EXEC scripts/verify_pi_candidate.py check
        run_bounded "pi_model" $PYTHON_EXEC scripts/verify_pi_candidate.py model
        ;;
    launch)
        echo "Launch: Validating Pi candidate environment readiness..."
        if [[ ! -f "profiles/pstack-pi.json" ]]; then
            echo "Error: profiles/pstack-pi.json not found" >&2
            exit 1
        fi
        if [[ ! -f ".pi/settings.json" ]]; then
            echo "Error: .pi/settings.json not found" >&2
            exit 1
        fi
        echo "Launch: Pi candidate environment ready."
        ;;
    drive)
        run_bounded "pi_check" $PYTHON_EXEC scripts/verify_pi_candidate.py check
        run_bounded "pi_model" $PYTHON_EXEC scripts/verify_pi_candidate.py model
        run_bounded "pi_profile_tests" $PYTHON_EXEC -m pytest -q tests/test_pi_candidate_profile.py
        ;;
    evidence)
        run_bounded "pi_evidence" $PYTHON_EXEC scripts/prove_pi_vertical_slice.py --json || true
        ;;
    cleanup)
        printf '%s\n' 'BLOCKED: no tracked native Pi child/artifact lifecycle; cleanup effects NOT_VERIFIED' >&2
        exit 2
        ;;
    all)
        "$0" doctor
        "$0" launch
        "$0" drive
        "$0" cleanup || true
        ;;
    *)
        printf 'usage: %s {doctor|launch|drive|evidence|cleanup|all}\n' "$0" >&2
        exit 2
        ;;
esac
