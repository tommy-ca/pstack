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
    python3 scripts/verify_pi_candidate.py smoke
    ;;
  drive)
    printf '%s\n' 'BLOCKED: no native Pi subagent/worktree/sandbox driver or observed_live receipt; see #897' >&2
    exit 2
    ;;
  evidence)
    printf '%s\n' 'BLOCKED: offline source checks cannot produce observed Pi runtime evidence' >&2
    exit 2
    ;;
  cleanup)
    printf '%s\n' 'PASS (no resources created): source-only Pi candidate verifier does not spawn processes'
    ;;
  *)
    printf 'usage: %s {doctor|launch|drive|evidence|cleanup}\n' "$0" >&2
    exit 2
    ;;
esac
