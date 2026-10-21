---
name: verify-decision-contract
description: "Verify pstack JEV decision routing, bounded real-code safety invariants, canonical source parity and rollback when those covered surfaces change."
disable-model-invocation: true
---

# Verify the decision contract

This is a **project-local offline verification skill**, not a proof of provider availability or unbounded concurrency. The bounded finite-state checker invokes the **actual** `scripts/route_resolver.py` entrypoint for 135 specified input combinations and demonstrates a negative mutation control. The external canonical verifier is a separate, fail-closed gate and requires **independently captured** upstream Git objects. See [bounded safety feature](features/bounded-invariants.md) and the [feature map](features/README.md).

## Coverage and sync record

- **Covered implementation at last reconciled source revision:** `66648081fbd7b4642f38ba0b273417a8891026ba` (2026-10-21). Verification changes on a different commit do not update this source sync record automatically.
- **Code paths:** `scripts/route_resolver.py::{resolve_skill_order,resolve_skill_order_with_shadow,_is_egress_bypassed,_load_semantic_candidates,_evaluate_advisory_promotion}`; `scripts/decision_adapter.py::{SafeContext,SpendLedger,JevDecisionAdapter}`; `scripts/evidence_receipts.py::{validate_calibrated_evidence,CalibratedEvidenceReceipt}`; `scripts/verify-decision-contract.py`; `references/decision-routing.json`; `references/calibrated-evidence.json`; `profiles/grok.json`; JEV OpenSpec contract.
- **Properties:** forbidden egress (including slash/direct/System-Two/agent routes), baseline equivalence for off/shadow and rejected outcomes, no forbidden promotion, request context equals the authorized fixture, stale/missing mapping/receipt baseline fallback, provenance-backed calibration receipt gate rejecting self-authorizing specimen fixtures (#676), atomic thread-safe spend reservation and mandatory settlement (#677), model-checked budget safety interleaving with negative mutation controls (#680), custom provider profile origin validation rejecting plaintext HTTP, loopback, private IP ranges, and cloud metadata SSRF targets, strict credential environment allowlist (#683), and truthful accounting of over-reservation provider charges (#682); canonical 23-playbook source parity is checked separately with external captures.
- **Bound:** 5 query classes × 3 summary classes × 3 modes × 3 provider outcomes = **135 routing code-path cases**, plus atomic concurrency and state-machine interleaving checks with negative mutation controls, not every string, provider billing anomaly or live host.
- **Assumptions:** approved summary is externally positively authorized (NOT inferred by regex); Grok profile and pinned 0.15.29 mapping are checked out; fake provider is hermetic; no external networking or billing.
- **Sync rule:** review `git diff 66648081fbd7b4642f38ba0b273417a8891026ba..HEAD -- <covered paths>` before relying on these assumptions. If routing semantics change, adapt the finite-state matrix and replay the mutation before moving the source revision. A green stale test does not renew evidence.

## Launch

Use Python 3.12, `pytest`, `jsonschema`, `git`, and (for externally captured canonical proof) an upstream pinned commit/tree JSON pair. Run from repo root. The helper resolves root from its own path; nothing needs to be started or stopped.

```sh
bash .codex/skills/verify-decision-contract/scripts/driver.sh launch
```

## Doctor

```sh
bash .codex/skills/verify-decision-contract/scripts/driver.sh doctor
```

This runs the hermetic bounded verifier, its negative mutation control, canonical verifier unit tests, privacy/bypass, evidence and transport suites; no API credential is needed. `openspec validate pstack-jev-decisions --type spec --strict` may be run separately when the CLI is installed; label it **UNTESTED** rather than claiming it passed if absent.

## Drive

To establish independently captured canonical source parity, provide both snapshots exported from the **actual official pinned upstream commit** (not generated from the local mapping):

```sh
export PSTACK_UPSTREAM_COMMIT_JSON=/path/to/official-commit.json
export PSTACK_UPSTREAM_TREE_JSON=/path/to/official-recursive-tree.json
export PSTACK_DECISION_EVIDENCE_DIR=/path/to/durable/evidence
bash .codex/skills/verify-decision-contract/scripts/driver.sh drive
```

The driver returns **BLOCKED (exit 2)** when either snapshot path is missing. It intentionally does **not** pass `--require-clean` for in-progress PR verification. For release-grade proof from a clean checkout, invoke `scripts/verify-decision-contract.py` separately with the same independent snapshots and `--require-clean`, then record the exact HEAD. Use `features/README.md` sweep order for broad coverage.

## Proof bar

- Offline checker executes all 135 cases through real routing code and **catches the intentionally disabled early-bypass guard** without modifying product source.
- No provider call for slash/direct/System-Two/agent, unset/rejected context, or disabled mode; no promotion for shadow/abstention/outside-scope.
- Official source parity can be PASS only from independently captured commit+tree against `UPSTREAM` and current mapping, not a copied local registry or missing files.
- No unverified `observed_live` receipts; `PLANNED` model seats are never native execution evidence.
- Reduce verdicts FAIL > BLOCKED > UNTESTED > PASS. These checks are **bounded code-level conformance**, not TLA+/Lean proof or authenticated billing/provider success.

## Evidence

Run the helper with optional `PSTACK_DECISION_EVIDENCE_DIR`; the independent canonical verifier writes revision-bound JSON evidence there. CI and pytest output is offline evidence only. Record exact PR head, command, exit code, assumptions, mutation result and any uncovered cases. Keep evidence **after cleanup**. No raw prompt or credentials in evidence.

## Cleanup

No daemon is launched, and no global process is killed. `cleanup` does **not** destroy evidence or mutate source; the operator owns temporary upstream JSON and may remove scratch copies after preserving the proof.

## Helpers

```sh
bash .codex/skills/verify-decision-contract/scripts/driver.sh {launch|doctor|drive|cleanup}
```

Each invoked check is bounded to 60 seconds with GNU `timeout`; on platforms lacking it the helper returns BLOCKED rather than running unbounded. When covered code changes, run `/maintain-formal-verification-skill` and independently inspect the source diff before updating this sync record.
