#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
cd "$ROOT"
case "${1:-doctor}" in
  doctor)
    python3 scripts/verify_pi_candidate.py check
    python3 scripts/verify_pi_candidate.py model
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
    # The existing preflight never starts or tracks real child processes.
    # A textual assertion cannot prove that host actors or worktrees were cleaned.
    printf '%s\n' 'BLOCKED: no tracked native Pi child/artifact lifecycle; cleanup effects NOT_VERIFIED' >&2
    exit 2
    ;;
  *)
    printf 'usage: %s {doctor|launch|drive|evidence|cleanup}\n' "$0" >&2
    exit 2
    ;;
esac
