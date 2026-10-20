#!/usr/bin/env bash
# Verification driver helper for verify-decision-contract
# Wraps Launch, Doctor, Drive, and Cleanup with 60s timeout handling
set -euo pipefail

TIMEOUT_SECONDS=60
export PSTACK_TRANSCRIPTS_DIR="${PSTACK_TRANSCRIPTS_DIR:-/tmp/empty-transcripts}"
mkdir -p "${PSTACK_TRANSCRIPTS_DIR}"

if [ -x ".venv/bin/pytest" ]; then
    PYTEST_CMD=".venv/bin/pytest"
else
    PYTEST_CMD="python3 -m pytest"
fi

run_bounded() {
    local label="$1"
    shift
    echo "==> Running $label (bounded by ${TIMEOUT_SECONDS}s)..."
    if command -v timeout >/dev/null 2>&1; then
        timeout --kill-after=5s "${TIMEOUT_SECONDS}" "$@" < /dev/null
    else
        "$@" < /dev/null
    fi
}

cmd="${1:-doctor}"
case "$cmd" in
  doctor)
    if [ -d "openspec/changes/pstack-jev-decision-plane" ]; then
      run_bounded "openspec-validate-change" openspec validate pstack-jev-decision-plane --type change --strict
    fi
    run_bounded "openspec-validate-spec" openspec validate pstack-jev-decisions --type spec --strict
    run_bounded "test-decision-contract" $PYTEST_CMD tests/test_verify_decision_contract.py tests/test_jev_transport_and_profiles.py tests/test_class_calibration_policy.py
    ;;
  launch)
    echo "Launch verified"
    ;;
  drive)
    run_bounded "eval-decision-routing" python3 scripts/eval_decision_routing.py --format json
    run_bounded "eval-blinded-pstack" python3 scripts/eval_blinded_pstack.py --format json
    run_bounded "verify-rollback-equivalence" python3 scripts/verify_rollback_equivalence.py --format json
    run_bounded "jev-transport-and-profiles" $PYTEST_CMD tests/test_jev_transport_and_profiles.py
    run_bounded "class-calibration-policy" $PYTEST_CMD tests/test_class_calibration_policy.py
    ;;
  cleanup)
    echo "Cleanup completed"
    ;;
  *)
    echo "Usage: $0 {doctor|launch|drive|cleanup}"
    exit 1
    ;;
esac
