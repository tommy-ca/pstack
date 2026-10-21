# Feature Map for verify-decision-contract

## Full sweep

Order of verification sweep across features:
1. `contract-spec.md`
2. `canonical-routing.md`
3. `decision-adapter.md`
4. `offline-eval.md`
5. `rollback-equivalence.md`
6. `bounded-invariants.md`

## Features

- [`contract-spec.md`](contract-spec.md): Strict OpenSpec decision plane specification and delta validation.
- [`canonical-routing.md`](canonical-routing.md): Deterministic 23-playbook registry validation against upstream tree.
- [`decision-adapter.md`](decision-adapter.md): Provider-neutral adapter, egress boundary, and fail-open routing.
- [`offline-eval.md`](offline-eval.md): Offline evaluation corpus, calibration metrics, and blinded behavioral evaluation.
- [`rollback-equivalence.md`](rollback-equivalence.md): Kill-switch, fail-open rollback equivalence, and latency budget verification.
- [`bounded-invariants.md`](bounded-invariants.md): 135-case bounded real-router safety exploration with mutation negative control, explicit scope and source sync.
