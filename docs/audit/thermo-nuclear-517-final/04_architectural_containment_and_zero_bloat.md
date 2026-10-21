# Thermo-Nuclear Review: Architectural Containment & Zero External Bloat

- **Subsystem**: Cross-Repository Architectural Boundary & Host Catalog Confinement  
- **Primary Sources**: [`scripts/eval_fast_role_task_fit.py`](https://github.com/tommy-ca/pstack/blob/66648081fbd7b4642f38ba0b273417a8891026ba/scripts/eval_fast_role_task_fit.py), [`tests/test_fast_role_task_fit.py`](https://github.com/tommy-ca/pstack/blob/66648081fbd7b4642f38ba0b273417a8891026ba/tests/test_fast_role_task_fit.py), [`tests/test_context_overlays.py`](https://github.com/tommy-ca/pstack/blob/66648081fbd7b4642f38ba0b273417a8891026ba/tests/test_context_overlays.py)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `a737926189ea73dfcb3d1685764d8a57ba8d2f2b`  
- **Severity**: Architectural Discipline & Invariant Enforcement (Rule 6)

---

## 1. Problem Statement: Boundary Drift & Risk of Duplicate Systems

Issue [#517](https://github.com/tommy-ca/pstack/issues/517) explores extending semantic decision assistance to best-fit fast worker roles and leaf skill suggestions for QStack workflows. 

Under **Rule 6 (Keep logic in the canonical layer; prevent architectural drift)** and the user mandate:
> *"keep the jev integration lean and clean, do not bloat to qstack, keep it at pstack"*,

there was an acute risk that:
1. Duplicate router logic, model catalogs, or taxonomy registries would be introduced into `qstack`, causing split-brain routing and double maintenance overhead.
2. Synthetic, hard-coded, or invented model slugs would be introduced into role resolvers without host catalog backing (violating Contract #429).
3. Fast-worker down-selection would inadvertently demote high-risk cognitive roles (`architect-runners`, `independent-verifier`, `arena-cross-judge-pool`), undermining verification rigor.

---

## 2. Inviolable Architectural Invariants

### Invariant 1: Complete PStack Containment & Zero External Bloat
All decision transports, provider adapters, role resolvers, cryptographic receipts, and benchmark replay harnesses reside **100% inside `pstack`**. 

This boundary is mechanically enforced by [`tests/test_context_overlays.py`](https://github.com/tommy-ca/pstack/blob/66648081fbd7b4642f38ba0b273417a8891026ba/tests/test_context_overlays.py#L360-L365):
```python
coupled = sorted(
    path.relative_to(ROOT).as_posix()
    for path in (*ROOT.glob("scripts/**/*.py"), *ROOT.glob("profiles/*.json"))
    if "qstack" in path.read_text(encoding="utf-8", errors="ignore")
)
assert not coupled, f"pstack must not own a qstack router or model namespace: {coupled}"
```
- Every file in `scripts/` and `profiles/` is scanned.
- If any script or profile mentions the external domain namespace, the offline test suite immediately fails.
- During PR #673 development, any prospective string coupling was refactored to domain-neutral representations (`quant-domain`, `bench #1791`).
- The test suite passes with `0` coupled files.

### Invariant 2: Host Catalog Confinement (Contract #429)
Candidate models evaluated for role fit must be sourced exclusively from actual host catalogs via `/setup-pstack` (such as [`.antigravity-plugin/models.json`](https://github.com/tommy-ca/pstack/blob/66648081fbd7b4642f38ba0b273417a8891026ba/.antigravity-plugin/models.json) or host profile catalogs).
- Invented model identifiers (e.g. `gpt-fictional-fast`) are rejected with `BLOCKED` status and flagged as `unmapped_model_violation`.
- Enforced by `load_host_model_catalog(host, root)` and verified in `tests/test_fast_role_task_fit.py::test_catalog_confinement_contract_429`.

### Invariant 3: Cognitive Frontier Tier Protection
Frontier reasoning and verification roles cannot be demoted by semantic recommendations or task-fit rules:
- `architect-runners`: pinned to `panel`
- `arena-cross-judge-pool`: pinned to `panel`
- `arena-runners`: pinned to `panel`
- `independent-verifier`: pinned to `strongest`
- `judgment-and-prose`: pinned to `strongest`
- `feature`: pinned to `strongest`
- `hardest-tasks`: pinned to `strongest`
- `poteto-agent`: pinned to `strongest`
- `why-synthesizer`: pinned to `strongest`

Any attempt to down-select these roles to `fast-worker` or `fast-verifier` triggers a `demotion_violation`, rejects the advice, and fails open to baseline. Enforced in `tests/test_fast_role_task_fit.py::test_cognitive_frontier_roles_cannot_be_demoted`.

### Invariant 4: Bounded Fast-Worker Candidate Roster
Fast-worker tier routing is restricted exclusively to low-risk execution roles:
- `comment-sicko`: hunting/deleting dead comments and debug logs.
- `how-explorer`: codebase file navigation and symbol lookups.
- `why-investigators`: commit history and PR archaeology.
- `swarm-workers`: parallel test execution.
- `refactoring`: **only** when `diff_loc < 100`, existing test coverage is present, and consequence of error is `low`. Any diff $\ge 100$ LOC remains on `strongest`.

---

## 3. Verification Evidence

- `uv run pytest -q tests/test_context_overlays.py` (55/55 passed, zero namespace coupling).
- `uv run pytest -q tests/test_fast_role_task_fit.py` (6/6 passed, 0 demotion violations, 0 unmapped slugs).
- `uv run python scripts/eval_fast_role_task_fit.py` (0 demotions, 0 unmapped slugs, PASS).
