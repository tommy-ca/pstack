#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
run() {
  if ! command -v mise >/dev/null 2>&1; then
    echo "BLOCKED: mise required; install pinned PStack toolchain" >&2
    return 2
  fi
  local python_bin
  python_bin="$(mise where python@3.12)/bin/python3"
  if [[ ! -x "$python_bin" ]]; then echo "BLOCKED: pinned Python 3.12 missing" >&2; return 2; fi
  "$python_bin" scripts/agnix_guard.py "$@"
}
case "${1:-all}" in
  doctor)
    run --doctor
    ;;
  launch)
    run --check-policy
    ;;
  drive)
    run 
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
