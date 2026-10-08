#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-doctor}"
case "$cmd" in
  doctor)
    openspec validate pstack-jev-decision-plane --type change --strict
    openspec validate pstack-jev-decisions --type spec --strict
    ;;
  drive)
    python3 scripts/eval_decision_routing.py --format json
    python3 scripts/eval_blinded_pstack.py --format json
    ;;
  cleanup)
    echo "Cleanup completed"
    ;;
  *)
    echo "Usage: $0 {doctor|drive|cleanup}"
    exit 1
    ;;
esac
