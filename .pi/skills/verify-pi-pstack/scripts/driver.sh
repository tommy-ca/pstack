#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
cd "$ROOT"

PYTHON_EXEC="python3"
if command -v uv >/dev/null 2>&1 && [[ -d "$ROOT/.venv" ]]; then
  PYTHON_EXEC="uv run python"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON_EXEC="$ROOT/.venv/bin/python"
fi

case "${1:-doctor}" in
  doctor)
    $PYTHON_EXEC scripts/verify_pi_candidate.py check
    $PYTHON_EXEC scripts/verify_pi_candidate.py model
    ;;
  launch)
    $PYTHON_EXEC scripts/prove_pi_vertical_slice.py --live
    ;;
  drive)
    $PYTHON_EXEC scripts/prove_pi_vertical_slice.py --live
    ;;
  evidence)
    $PYTHON_EXEC scripts/prove_pi_vertical_slice.py --json
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
