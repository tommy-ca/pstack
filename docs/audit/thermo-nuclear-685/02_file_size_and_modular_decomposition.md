# Detail Report 02: File Size & Modular Decomposition

- **Subsystem**: Source Code Metrics & Line Count Ceilings across Repository
- **Base Revision**: `5f649c6`
- **Head Revision**: `20164ba`
- **Reviewed Epic**: Issue [#685](https://github.com/tommy-ca/pstack/issues/685) (PR [#686](https://github.com/tommy-ca/pstack/pull/686), commit `7d0dbd2`)

---

## 1. Context & Standard

Standard 1 of the Thermo-Nuclear Code Quality Review mandates:
> Do not let a PR push a file from under 1k lines to over 1k lines without a very strong reason. Treat this as a strong code-quality smell by default. Prefer extracting helpers, subcomponents, modules, or local abstractions instead of letting a file sprawl past 1000 lines.

---

## 2. Line Count Inventory of Touched Files

The following table reflects the exact line counts of all files modified by PR [#686](https://github.com/tommy-ca/pstack/pull/686) and PR [#688](https://github.com/tommy-ca/pstack/pull/688):

| File Path | Base Lines (`5f649c6`) | Head Lines (`20164ba`) | Net Delta | Ceiling Compliance (< 1,000) |
| :--- | :--- | :--- | :--- | :--- |
| `scripts/decision_adapter.py` | 657 | 747 | +90 | **PASS** (253 lines below ceiling) |
| `tests/test_jev_transport_and_profiles.py` | 420 | 507 | +87 | **PASS** (493 lines below ceiling) |
| `tests/test_paid_budget_concurrency.py` | 271 | 335 | +64 | **PASS** (665 lines below ceiling) |
| `scripts/prove-omp-native-package.py` | 589 | 596 | +7 | **PASS** (404 lines below ceiling) |
| `.codex/skills/verify-decision-contract/SKILL.md` | 105 | 105 | 0 | **PASS** |
| `.codex/skills/verify-decision-contract/features/bounded-invariants.md` | 72 | 73 | +1 | **PASS** |

---

## 3. Modular Decomposition Analysis

### 3.1 `scripts/decision_adapter.py` (747 lines)
- **Role**: Coordinates the entire semantic decision provider interface, including the abstract base class `SemanticDecisionProvider`, immutable request/response types (`ChoiceRequest`, `DecisionOutcome`, `ProviderObservation`), constructor validation gates (`validate_provider_api_root`, `validate_credential_env_name`), provider profiles (`JevProviderProfile`), thread-safe budget ledger (`SpendLedger`), real provider adapter (`JevDecisionAdapter`), and deterministic test mock (`FakeDecisionProvider`).
- **Growth Analysis**: The addition of 90 lines was solely dedicated to security allowlists, origin parsing via `urllib.parse` and `ipaddress`, and `SpendLedger` over-reservation truth tracking.
- **Decomposition Assessment**: At 747 lines, the module remains well below the 1,000-line threshold. However, if additional request types (e.g. `ScoreRequest`, `BooleanRequest`) are wired to provider transports in future phases, the module should be evaluated for decomposition into `decision_types.py`, `provider_profiles.py`, and `decision_adapter.py`. Currently, keeping them co-located in `decision_adapter.py` avoids cross-module import cycles and maintains clean cohesion.

### 3.2 `tests/test_jev_transport_and_profiles.py` (507 lines)
- **Role**: Unit tests for provider profile validation, wire contracts, and transport exception handling.
- **Growth Analysis**: Added 87 lines covering positive and negative test cases for HTTPS scheme enforcement, loopback rejection, cloud metadata blocking, private network range isolation, and sensitive environment variable filtering.
- **Decomposition Assessment**: At 507 lines, the test suite is compact, readable, and well-isolated.

### 3.3 `tests/test_paid_budget_concurrency.py` (335 lines)
- **Role**: Multithreaded race-condition stress tests and exhaustive BFS state-space exploration for `SpendLedger`.
- **Growth Analysis**: Added 64 lines extending the state-machine exploration model to verify over-reservation charges and negative control mutations.
- **Decomposition Assessment**: At 335 lines, the file isolates complex concurrency testing from standard functional unit tests, keeping both suites maintainable.

---

## 4. Verdict
Zero files crossed or approached the 1,000-line ceiling. Modular cohesion is strictly preserved.
