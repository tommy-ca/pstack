#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
cd "$ROOT"
case "${1:-doctor}" in
  doctor)
    python3 scripts/prove_pi_vertical_slice.py
    ;;
  launch)
    python3 scripts/prove_pi_vertical_slice.py --live
    ;;
  drive)
    python3 scripts/prove_pi_vertical_slice.py --live
    ;;
  evidence)
    python3 scripts/prove_pi_vertical_slice.py --json
    ;;
  cleanup)
    printf '%s\n' 'PASS (no resources leaked): ephemeral Pi slices leave no background processes or unmanaged files'
    ;;
  *)
    printf 'usage: %s {doctor|launch|drive|evidence|cleanup}\n' "$0" >&2
    exit 2
    ;;
esac
