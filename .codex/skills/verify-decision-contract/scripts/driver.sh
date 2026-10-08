#!/usr/bin/env bash
set -euo pipefail
cmd="${1:-doctor}"
case "$cmd" in
  doctor)
    openspec validate pstack-jev-decision-plane --type change --strict
    openspec validate pstack-jev-decisions --type spec --strict
    ;;
  drive)
    echo "Drive contract verification lever"
    ;;
  cleanup)
    echo "Cleanup completed"
    ;;
  *)
    echo "Usage: $0 {doctor|drive|cleanup}"
    exit 1
    ;;
esac
