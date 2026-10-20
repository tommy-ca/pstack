# Thermo-Nuclear Code Quality Review: Detail Report 01
## Subsystem: OpenSpec Active Change Resolution & Lifecycle State

- **Target Module**: [`scripts/openspec_change.py`](file:///home/tommyk/projects/pstack/scripts/openspec_change.py)
- **Base Revision**: `329acf2` (merge base for Program #636)
- **Head Revision**: `0517eb2` (Program #636 closeout on `main`)
- **Reviewer**: Thermo-Nuclear Code Quality Reviewer
- **Status**: BLOCKER / BUG IDENTIFIED

---

### 1. Concrete Structural Finding: Fallback Flaw in `_active_openspec_changes`

In PR #640, `_active_openspec_changes()` was modified to filter `status != "complete"`:

```python
parsed: list[str] = []
in_progress: list[str] = []
for entry in changes:
    if not isinstance(entry, dict):
        return None
    name = entry.get("name")
    if not isinstance(name, str) or not name:
        return None
    parsed.append(name)
    if entry.get("status") != "complete":
        in_progress.append(name)
return in_progress if in_progress else parsed
```

#### The Defect
When all OpenSpec changes in the workspace reach `status: "complete"`:
1. `in_progress` is empty (`[]`).
2. The expression `in_progress if in_progress else parsed` evaluates the falsiness of `[]` and falls back to returning `parsed`.
3. `parsed` contains **all completed changes**.
4. If there are 2 or more completed changes (which is the case right now on `main`: `2026-10-20-cross-port-semantic-delta` and `2026-10-15-harness-neutral-role-policy`), `_active_openspec_changes()` returns `['2026-10-20-cross-port-semantic-delta', '2026-10-15-harness-neutral-role-policy']`.
5. `resolve_openspec_change(None)` sees `len(active) == 2` and returns:
   `ChangeResolution(state='ambiguous', name=None, names=[...])`.
6. `validate_openspec_change(None)` prints:
   `ERROR: 2 active openspec changes; pass one explicitly via --change.` and **fails with exit code 1**!

#### Live Evidence
Running right now on `main` @ `0517eb2`:
```bash
$ .venv/bin/python -c "from scripts.openspec_change import validate_openspec_change; print('Exit:', validate_openspec_change(None))"
ERROR: 2 active openspec changes; pass one explicitly via --change.
  - 2026-10-20-cross-port-semantic-delta
  - 2026-10-15-harness-neutral-role-policy
Exit: 1
```

The intended behavior documented in `scripts/verify-portable.py`:
`--change CHANGE: Target OpenSpec change to validate in doctor (default: checkout's single active change, or no-op when none)`

When there are no active changes in progress, the checkout has **zero** active changes. It must resolve to `state="none"` and perform a clean no-op, rather than crashing with an ambiguous error.

---

### 2. Consumer Reachability Analysis

- **`scripts/verify-portable.py`**:
  - `PortableVerifier.doctor`: invokes `validate_openspec_change(self.change)` where `self.change` defaults to `None`. When invoked without `--change` after all tasks are completed, doctor fails.
  - CLI parser `--change` option.
- **`scripts/harness_scenarios.py`**:
  - Scenario `doctor-openspec-validation` passes `sys.argv[1]` explicitly, which bypassed the default `None` path and masked this bug during Wave 1 & 2 doctor runs.
- **`tests/test_verify_portable.py`**:
  - Tests monkeypatched `_active_openspec_changes` with static lambdas, so the dynamic fallback logic when all items have `status: "complete"` was never exercised against real output.

---

### 3. "Code Judo" Remedy

Eliminate the conditional fallback `in_progress if in_progress else parsed`.
The concept of "active changes" is purely: **changes whose status is not complete**.
If no changes exist whose status is not complete, then the list of active changes is simply empty (`[]`), which maps cleanly to `state="none"` and exits with 0.

#### Worked Replacement

```python
def _active_openspec_changes() -> list[str] | None:
    try:
        listed = subprocess.run(
            ["openspec", "list", "--json"], capture_output=True, text=True, check=False
        )
        if listed.returncode != 0:
            return None
        import json as _json

        payload = _json.loads(listed.stdout or "{}")
        changes = payload.get("changes") if isinstance(payload, dict) else payload
        if not isinstance(changes, list):
            return None
        in_progress: list[str] = []
        for entry in changes:
            if not isinstance(entry, dict):
                return None
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                return None
            if entry.get("status") != "complete":
                in_progress.append(name)
        return in_progress
    except Exception:
        return None
```

#### Behavior Pin
- When `in_progress` has 1 change: returns `state="active"`, name=`"..."`.
- When `in_progress` has 2+ changes: returns `state="ambiguous"`, names=`[...]`.
- When `in_progress` is empty (all changes complete or zero changes): returns `state="none"`, name=`None`, and `validate_openspec_change(None)` exits 0 as a no-op.
- When `openspec list --json` fails: returns `state="lookup-failed"`.

#### Net Maintained Obligation
Removes the ambiguous fallback path. Fixes the default doctor execution on clean, completed trees.
Adds regression tests in `tests/test_verify_portable.py` asserting that a list of completed changes resolves to `[]` (`state="none"`).
