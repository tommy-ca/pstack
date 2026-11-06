#!/usr/bin/env bash
# Verification driver script for Pi candidate formal verification
set -euo pipefail

TIMEOUT_SECONDS=60

run_bounded() {
    local label="$1"
    shift
    echo "==> Running $label (bounded by ${TIMEOUT_SECONDS}s)..."
    if command -v timeout >/dev/null 2>&1; then
        timeout "${TIMEOUT_SECONDS}" "$@"
    else
        "$@"
    fi
}

case "${1:-all}" in
    doctor)
        run_bounded "doctor" python3 scripts/verify_pi_candidate.py check
        ;;
    launch)
        echo "Launch: Python and pytest environment ready"
        ;;
    drive)
        run_bounded "model" python3 scripts/verify_pi_candidate.py model
        run_bounded "pytest" python3 -m pytest -q tests/test_pi_candidate_profile.py
        ;;
    cleanup)
        echo "Cleanup: No persistent state created"
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
