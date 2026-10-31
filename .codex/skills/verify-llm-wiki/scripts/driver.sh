#!/usr/bin/env bash
# Codex project-local wiki verifier: bounded, offline, no shared service.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

if ! command -v timeout >/dev/null 2>&1; then
  echo "BLOCKED: GNU timeout required for 60s execution bounds" >&2
  exit 2
fi

run_bounded() {
  local label="$1"; shift
  echo "==> $label"
  timeout --kill-after=5s 60s "$@" < /dev/null
}

drive() {
  doctor
  run_bounded "original PStack wiki contracts" python3 -m pytest -q tests/test_llm_wiki.py
  run_bounded "source and path negatives" python3 -m pytest -q tests/test_llm_wiki_safety.py
  run_bounded "bounded production-code model" python3 -m pytest -q tests/test_llm_wiki_bounded_model.py
  run_bounded "proposed schema conformance and negative controls" python3 -m pytest -q tests/test_llm_wiki_spec_contracts.py
  run_bounded "real-code and mutation trace" python3 scripts/verify_llm_wiki_model.py
}

doctor() {
  run_bounded "python" python3 --version
  run_bounded "pytest" python3 -m pytest --version
  run_bounded "structural wiki CLI" python3 scripts/llm_wiki.py check --wiki-dir .llm-wiki
}

if [[ -n "${LLM_WIKI_EVIDENCE_DIR:-}" ]]; then
  mkdir -p "$LLM_WIKI_EVIDENCE_DIR"
  receipt="$(mktemp "$LLM_WIKI_EVIDENCE_DIR/verify-llm-wiki.XXXXXXXX.log")"
  echo "Evidence transcript: $receipt"
  exec > >(tee -a "$receipt") 2>&1
  git rev-parse HEAD || true
fi

case "${1:-doctor}" in
  launch) run_bounded "python" python3 --version; run_bounded "pytest" python3 -m pytest --version ;;
  doctor) doctor ;;
  drive) drive ;;
  cleanup) echo "No owned persistent processes; scratch roots belong to test fixtures; receipts retained." ;;
  *) echo "Usage: $0 {launch|doctor|drive|cleanup}" >&2; exit 2 ;;
esac
