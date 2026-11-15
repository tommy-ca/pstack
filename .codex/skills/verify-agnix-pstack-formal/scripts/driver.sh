#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

TIMEOUT_SECONDS=60

get_python() {
  if ! command -v mise >/dev/null 2>&1; then
    echo "BLOCKED: mise required; install pinned PStack toolchain" >&2
    return 2
  fi
  local python_bin
  python_bin="$(mise where python@3.12)/bin/python3"
  if [[ ! -x "$python_bin" ]]; then
    echo "BLOCKED: pinned Python 3.12 missing" >&2
    return 2
  fi
  echo "$python_bin"
}

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
    py="$(get_python)"
    run_bounded "doctor" "$py" scripts/agnix_guard.py --check-policy
    ;;
  launch)
    py="$(get_python)"
    run_bounded "launch" "$py" scripts/agnix_guard.py --check-policy
    ;;
  drive)
    py="$(get_python)"
    run_bounded "formal" "$py" scripts/agnix_guard.py --formal
    ;;
  cleanup)
    echo "CLEAN: read-only verification, no temporary resources"
    ;;
  all)
    "$0" doctor
    "$0" launch
    "$0" drive
    "$0" cleanup
    ;;
  *)
    echo "usage: $0 {doctor|launch|drive|cleanup|all}" >&2
    exit 1
    ;;
esac
