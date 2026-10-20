# Thermo-Nuclear Code Quality Review: Detail Report 03
## Subsystem: Cross-Port Contract Tests & Domain Modeling

- **Target Module**: [`tests/test_cross_port_contracts.py`](file:///home/tommyk/projects/pstack/tests/test_cross_port_contracts.py)
- **Base Revision**: `329acf2`
- **Head Revision**: `0517eb2`
- **Reviewer**: Thermo-Nuclear Code Quality Reviewer
- **Status**: STRUCTURAL ENHANCEMENT / CONTRACT HARDENING

---

### 1. Concrete Structural Finding: In-Test Ad-Hoc Doubles vs Canonical Domain Models

In `tests/test_cross_port_contracts.py`, Scenarios 1 and 2 define synthetic test classes:
- `ToolCallTracker`: Lines 35–58
- `AgentActivityManager`: Lines 93–113

And Scenario 4 defines a local helper:
- `safe_terminate_process`: Lines 200–208

#### Assessment
- **Positives**: The contract tests successfully decouple the 6-host core from comparator `pstack-claude`'s heavy `SessionStore` and Node child-process machinery, honoring the requirement: *"Do not import child-process or state-store machinery into OMP/Grok/Codex"*.
- **Structural Smell**:
  1. `ToolCallTracker` and `AgentActivityManager` live exclusively inside `tests/test_cross_port_contracts.py`. While they test the invariants, they are not accessible to other harness drivers or test suites that might need to verify parallel tool call settlement or ephemeral activity in driver scenarios.
  2. `safe_terminate_process` tests token mismatch (`actual_token != expected_owner_token`), but omits the dangerous POSIX boundary invariants: `pid <= 1` (PID 0 targets the entire process group; PID -1 targets all processes; PID 1 is init/systemd). In Python `os.kill(0, signal)` terminates the calling process group!
  3. When an orphan/cancel cleanup routine executes in a native harness, passing an unvalidated or parsed PID of `0` or negative numbers is a critical system hazard.

---

### 2. Consumer Reachability Analysis

- `tests/test_cross_port_contracts.py`: Executed via `pytest`.
- `scripts/select_checks.py`: Mapped to `pytest:tests/test_cross_port_contracts.py`.
- `skills/poteto-mode/scripts/orch/store.ts`: Implements real PID probing via `process.kill(pid, 0)` with strict integer and `pid > 0` validation (`holderIsDead`).

---

### 3. "Code Judo" Remedy

1. **Harden `safe_terminate_process` contract in `tests/test_cross_port_contracts.py`**:
   Add explicit assertions and guard logic for non-positive or system PIDs (`pid <= 1`):
   ```python
   def safe_terminate_process(target_pid: int, expected_owner_token: str, actual_token: Optional[str]) -> bool:
       if target_pid <= 1:
           # REFUSE: never signal pid 0 (process group), pid 1 (init), or negative pids
           return False
       if actual_token != expected_owner_token:
           # REFUSE: pid mismatch or token reuse
           return False
       return True
   ```
2. Assert that attempting to terminate `0`, `-1`, or `1` fails closed without sending any signal.
3. Keep `ToolCallTracker` and `AgentActivityManager` clearly typed and annotated with dataclasses, documenting that they define the behavior boundary for native harness driver implementations.

#### Behavior Pin
- Calls with `target_pid <= 1` return `False`.
- Token mismatches return `False`.
- Valid PIDs with matching tokens return `True`.

#### Net Maintained Obligation
Prevents catastrophic process signaling errors in driver cleanup logic.
