#!/usr/bin/env bash
# Hermetic JEV decision-contract verifier: no credentials, network or hidden cleanup.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

if ! command -v timeout >/dev/null 2>&1; then
  echo "BLOCKED: GNU timeout is required to enforce the 60-second command bound." >&2
  exit 2
fi

run_bounded() {
  local label="$1"; shift
  echo "==> $label"
  timeout --kill-after=5s 60s "$@" < /dev/null
}

case "${1:-doctor}" in
  launch)
    run_bounded "python prerequisite" python3 --version
    run_bounded "pytest prerequisite" python3 -m pytest --version
    echo "No process launched; use doctor before drive."
    ;;
  doctor)
    run_bounded "bounded real-router invariants and mutation probe" python3 -m pytest -q tests/test_decision_bounded_invariants.py
    run_bounded "atomic paid budget reservation and model-checked interleavings" python3 -m pytest -q tests/test_paid_budget_concurrency.py
    run_bounded "decision contract, privacy, evidence and wire regressions" python3 -m pytest -q \
      tests/test_verify_decision_contract.py \
      tests/test_jev_privacy_and_bypass.py \
      tests/test_jev_mapping_and_calibrated_evidence.py \
      tests/test_jev_transport_and_profiles.py \
      tests/test_class_calibration_policy.py \
      tests/test_rollback_equivalence.py
    if command -v openspec >/dev/null 2>&1; then
      run_bounded "living decision OpenSpec" openspec validate pstack-jev-decisions --type spec --strict
    else
      echo "UNTESTED: OpenSpec CLI unavailable; living spec validation must be run separately." >&2
    fi
    ;;
  drive)
    # Doctor first so a malformed or stale local verifier never receives a PASS.
    run_bounded "bounded real-router invariants and mutation probe" python3 -m pytest -q tests/test_decision_bounded_invariants.py
    run_bounded "rollback equivalence" python3 scripts/verify_rollback_equivalence.py --format json
    run_bounded "decision routing evaluation" python3 scripts/eval_decision_routing.py --format json

    if [[ -z "${PSTACK_UPSTREAM_COMMIT_JSON:-}" || -z "${PSTACK_UPSTREAM_TREE_JSON:-}" ]]; then
      echo "BLOCKED: set PSTACK_UPSTREAM_COMMIT_JSON and PSTACK_UPSTREAM_TREE_JSON to independently captured pinned official GitHub objects." >&2
      exit 2
    fi
    if [[ ! -f "$PSTACK_UPSTREAM_COMMIT_JSON" || ! -f "$PSTACK_UPSTREAM_TREE_JSON" ]]; then
      echo "BLOCKED: canonical GitHub commit/tree capture file missing." >&2
      exit 2
    fi
    if [[ -n "${PSTACK_DECISION_EVIDENCE_DIR:-}" ]]; then
      run_bounded "official-pinned canonical decision parity" python3 scripts/verify-decision-contract.py \
        --root "$ROOT" \
        --upstream-commit "$PSTACK_UPSTREAM_COMMIT_JSON" \
        --upstream-tree "$PSTACK_UPSTREAM_TREE_JSON" \
        --evidence-dir "$PSTACK_DECISION_EVIDENCE_DIR"
    else
      run_bounded "official-pinned canonical decision parity" python3 scripts/verify-decision-contract.py \
        --root "$ROOT" \
        --upstream-commit "$PSTACK_UPSTREAM_COMMIT_JSON" \
        --upstream-tree "$PSTACK_UPSTREAM_TREE_JSON"
      echo "UNTESTED durable evidence: PSTACK_DECISION_EVIDENCE_DIR not specified." >&2
    fi
    ;;
  cleanup)
    echo "No processes or temporary roots owned. Durable proof and externally captured snapshots preserved."
    ;;
  *)
    echo "Usage: $0 {launch|doctor|drive|cleanup}" >&2
    exit 2
    ;;
esac
