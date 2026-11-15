#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
run() {
  if ! command -v mise >/dev/null 2>&1; then
    echo "BLOCKED: mise required; install pinned PStack toolchain" >&2
    return 2
  fi
  mise exec -- python scripts/agnix_guard.py "$@"
}
case "${1:-all}" in
  doctor)
    run --check-policy
    :
    ;;
  launch)
    run --check-policy
    ;;
  drive)
    run --formal
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
