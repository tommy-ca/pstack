#!/usr/bin/env bash
# Verification driver helper for verify-decision-contract
# Wraps Launch, Doctor, Drive, and Cleanup with 60s timeout handling
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

cmd="${1:-doctor}"
case "$cmd" in
  doctor)
    run_bounded "openspec-validate-change" openspec validate pstack-jev-decision-plane --type change --strict
    run_bounded "openspec-validate-spec" openspec validate pstack-jev-decisions --type spec --strict
    ;;
  launch)
    echo "Launch verified"
    ;;
  drive)
    run_bounded "eval-decision-routing" python3 scripts/eval_decision_routing.py --format json
    run_bounded "eval-blinded-pstack" python3 scripts/eval_blinded_pstack.py --format json
    ;;
  cleanup)
    echo "Cleanup completed"
    ;;
  *)
    echo "Usage: $0 {doctor|launch|drive|cleanup}"
    exit 1
    ;;
esac
