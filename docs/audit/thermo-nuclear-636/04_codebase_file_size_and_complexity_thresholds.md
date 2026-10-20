# Thermo-Nuclear Code Quality Review: Detail Report 04
## Subsystem: Codebase File Size & Complexity Thresholds

- **Target Files**:
  - [`skills/poteto-mode/scripts/orch/store.ts`](file:///home/tommyk/projects/pstack/skills/poteto-mode/scripts/orch/store.ts) (1,677 lines)
  - [`tests/test_verify_harness.py`](file:///home/tommyk/projects/pstack/tests/test_verify_harness.py) (1,437 lines)
  - [`tests/test_evidence_durability.py`](file:///home/tommyk/projects/pstack/tests/test_evidence_durability.py) (1,016 lines)
  - [`tests/test_evidence_settlement.py`](file:///home/tommyk/projects/pstack/tests/test_evidence_settlement.py) (1,003 lines)
- **Base Revision**: `329acf2`
- **Head Revision**: `0517eb2`
- **Reviewer**: Thermo-Nuclear Code Quality Reviewer
- **Status**: STRUCTURAL DECOMPOSITION REQUIRED (1,000-LINE LIMIT BREACHES)

---

### 1. Concrete Structural Finding: Severe Breaches of the 1,000-Line Threshold

Rule 1 of the Thermo-Nuclear Code Quality standard is non-negotiable:
*"Do not let a PR push a file from under 1k lines to over 1k lines without a very strong reason. Treat this as a strong code-quality smell by default. Prefer extracting helpers, subcomponents, modules, or local abstractions instead of letting a file sprawl past 1000 lines."*

The current tree contains four files that exceed the 1,000-line ceiling:

| File | Current Lines | Primary Responsibility | Tangled Secondary Responsibilities |
| --- | --- | --- | --- |
| `skills/poteto-mode/scripts/orch/store.ts` | **1,677** | Plain-file store CRUD engine | Domain types/errors (lines 1–250), PID lock management (lines 369–420), Forge CLI execution & loop detection (lines 971–1268), TSV table serialization |
| `tests/test_verify_harness.py` | **1,437** | Core verify-harness test suite | Intent archive chain integrity (lines 121–210), Playbook text & parity checks (lines 240–348), Slash command collision checks (lines 925–980), Frontmatter checks |
| `tests/test_evidence_durability.py` | **1,016** | Evidence durability & staleness | Re-declared mock receipt factories, synthetic scenario generators, filesystem simulation |
| `tests/test_evidence_settlement.py` | **1,003** | Evidence settlement retention | Duplicate fixture generation, scenario list mock builders |

---

### 2. "Code Judo" Decomposition Plans

#### A. Decompose `skills/poteto-mode/scripts/orch/store.ts` (1,677 lines -> 4 files < 500 lines)

Extract three cohesive child modules:
1. `skills/poteto-mode/scripts/orch/types.ts` (~260 lines):
   - Export all domain interfaces (`Verdict`, `Unit`, `LedgerEntry`, `InboxPointer`, `Gate`, `Frontier`, `StatusReport`, etc.).
   - Export error classes (`UserError`, `UsageError`, `NotFoundError`).
   - Export validator parsers (`parseVerdict`, `parseForge`, etc.).
2. `skills/poteto-mode/scripts/orch/lock.ts` (~120 lines):
   - Export `acquireLock`, `holderIsDead`, `LOCK_FILE`, and lock timeout constants.
   - Enforce PID integer safety and signal 0 probes.
3. `skills/poteto-mode/scripts/orch/frontier.ts` (~320 lines):
   - Export `resolveFrontier`, `queryGhBaseChain`, `queryOriginBaseChain`, and linear chain validation (loop detection, single-parent tree traversal).
4. `skills/poteto-mode/scripts/orch/store.ts` (~950 lines):
   - Focus strictly on table CRUD operations (`openStore`, `units`, `ledger`, `inbox`, `gates`, `frontier`, `standing`).
   - Re-export `types.ts`, `lock.ts`, and `frontier.ts` for backwards compatibility with `orch.ts` and `orch.test.ts`.

#### B. Decompose `tests/test_verify_harness.py` (1,437 lines -> 3 files < 600 lines)

1. `tests/test_verify_harness_archive.py` (~350 lines):
   - Extract `test_archivable_intent_chain_guard_distinguishes_changes`, `test_archived_intent_chains_are_complete`, `test_archived_change_missing_adr_artifact_is_flagged`, `test_durable_specs_have_non_placeholder_purposes`.
2. `tests/test_verify_harness_playbooks.py` (~450 lines):
   - Extract `test_playbooks_are_not_plugin_rhai_workflows`, `test_autopilot_is_parent_fanout_and_skips_goal`, `test_poteto_mode_*`, `test_babysit_and_shipping_*`.
3. `tests/test_verify_harness.py` (~630 lines):
   - Retain core script existence, harness discipline, boundary assertions, and execution tests.

#### C. Extract Shared Evidence Test Helpers (Decomposing `test_evidence_durability.py` & `test_evidence_settlement.py`)

1. Create `tests/evidence_test_helpers.py` (~250 lines):
   - Consolidate duplicated mock receipt creators, synthetic scenario builders, and fake filesystem fixture factories.
2. In `tests/test_evidence_durability.py`: Import from `evidence_test_helpers.py`. File drops from 1,016 lines to **~760 lines**.
3. In `tests/test_evidence_settlement.py`: Import from `evidence_test_helpers.py`. File drops from 1,003 lines to **~750 lines**.

---

### 3. Verification & Mapping Invariants

- Update `scripts/select_checks.py` to map the new decomposed test files:
  - `tests/test_verify_harness_archive.py` and `tests/test_verify_harness_playbooks.py` mapped to `scripts/verify-harness.py` and `openspec/`.
- Ensure all tests continue to pass without regression.
- Validate that zero files in the repository exceed 1,000 lines.
