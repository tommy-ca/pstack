# Thermo-Nuclear Review: Model Role Policy Test Decomposition

- **Subsystem**: Model Role Policy & Host Planning Test Harness  
- **Primary Source**: [`tests/test_model_role_policy.py`](file:///home/tommyk/projects/pstack/tests/test_model_role_policy.py)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `804df416c1ec0ce9f6888fbf02a43fe9714c776a`  
- **Severity**: Critical (Breach of Rule 1: 1,000-Line File Threshold Ceiling)

---

## 1. Problem Statement & Code Quality Diagnosis

Under **Rule 1 (1k Line File Limit)** of the Thermo-Nuclear Code Quality Standards:
> "Do not let a PR push a file from under 1k lines to over 1k lines without a very strong reason. Treat this as a strong code-quality smell by default. Prefer extracting helpers, subcomponents, modules, or local abstractions instead of letting a file sprawl past 1000 lines."

A file size audit of the test suite reveals:
```bash
wc -l tests/test_model_role_policy.py
995 tests/test_model_role_policy.py
```

[`tests/test_model_role_policy.py`](file:///home/tommyk/projects/pstack/tests/test_model_role_policy.py) is currently **995 lines long**—precisely 5 lines away from violating the 1,000-line ceiling!

The file has become a catch-all testing monolith containing 47 distinct test functions that conflate three different architectural concerns:
1. **Schema & JSON Schema Draft 2020-12 validation**: Metaschema conformance, example doc validity, disallowed keywords, and token grammar.
2. **Role semantic constraints & panel diversity invariants**: Hard-check capability rules, panel family diversity constraints, cross-judge seat isolation, and override precedence.
3. **Host catalog planning, pure execution, and profile resolution**: Pure planning I/O isolation, host catalog status gates (unproven/stale/clean), host-catalog mapping for the 6 canonical hosts, and setup parity.

If Issue #517 (role-fit evaluation and fast worker role extensions) adds even a single test case to this file, it will break through the 1,000-line threshold. Immediate decomposition is mandatory before landing any Issue #517 implementation.

---

## 2. Consumer Reachability & Behavior Pin

### Consumer Reachability
- Invoked via:
  - `uv run pytest tests/test_model_role_policy.py`
  - `uv run pytest` (full suite)
  - Pre-commit / PR test gates in CI workflows.
- Dependencies:
  - Uses `scripts/model_role_policy.py`, `scripts/portability_schema.py`, `schemas/portability/model-role-policy.schema.json`, `examples/portability/model-role-policy.example.json`, and `pstack.package.json`.

### Behavior Pin
- Every one of the 47 existing test functions must continue to execute and pass.
- Test coverage across `scripts/model_role_policy.py` must remain >= 98%.
- Total execution time must remain < 3.5 seconds.

---

## 3. The "Code Judo" Decomposition Plan

Rather than arbitrarily splitting tests across ad-hoc files, we decompose `test_model_role_policy.py` along cohesive architectural boundaries into three dedicated modules under `tests/model_role/` (or top-level `tests/`):

```
tests/
├── test_model_role_schema.py       (~250 lines)
│   ├── JSON Schema Draft 2020-12 conformance
│   ├── Example document validation against schema
│   ├── Token grammar (inherit tokens, catalog IDs)
│   └── Cross-document syntax and topology validation
│
├── test_model_role_constraints.py  (~380 lines)
│   ├── Role capability requirements (agent.spawn, etc.)
│   ├── Panel family diversity invariants (multi-family seats)
│   ├── Cross-judge seat and family isolation
│   └── Effort and capability matching rules
│
└── test_model_role_profiles.py     (~415 lines)
    ├── Pure planner execution & no-I/O guarantee
    ├── Host catalog status (unproven / stale / clean)
    ├── Six canonical host mappings (Grok, Codex, OMP, OpenCode, Antigravity, Droid)
    └── Fast-worker / role-fit profile resolution (Issue #517 extension seam)
```

### Shared Test Fixtures Helper
Common fixtures, validator setup, and schema caching are extracted into a lightweight test helper `tests/model_role_helpers.py` (~45 lines):
```python
"""Shared fixtures and validator instances for model role policy test modules."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from scripts.model_role_policy import check_model_role_policy

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas/portability/model-role-policy.schema.json").read_text())
EXAMPLE = json.loads((ROOT / "examples/portability/model-role-policy.example.json").read_text())
PACKAGE = json.loads((ROOT / "pstack.package.json").read_text())
VALIDATOR = Draft202012Validator(SCHEMA)

def validate(policy: dict, descriptor: dict = PACKAGE) -> None:
    VALIDATOR.validate(policy)
    check_model_role_policy(policy, descriptor)
```

---

## 4. Net Maintained Obligation & Recheck Commands

### Maintained Obligation Removed
- **Eliminates single monolithic test file danger**: Replaces a 995-line monolith with three cohesive files between 250 and 415 lines each.
- **Isolates Issue #517 fast-worker tests**: Future role-fit and fast-worker tests can be cleanly added to `test_model_role_profiles.py` without risking threshold breaches.
- **Reduces cognitive load**: Developers testing schema changes don't have to navigate through 700 lines of panel diversity tests.

### Recheck Commands
```bash
uv run pytest -q tests/test_model_role_schema.py tests/test_model_role_constraints.py tests/test_model_role_profiles.py
wc -l tests/test_model_role_schema.py tests/test_model_role_constraints.py tests/test_model_role_profiles.py
```
Each file must register strictly under 500 lines and pass 100% of tests.
