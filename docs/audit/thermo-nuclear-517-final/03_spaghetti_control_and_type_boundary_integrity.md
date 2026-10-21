# Thermo-Nuclear Review: Spaghetti Control & Type Boundary Integrity

- **Subsystem**: Type Safety, Egress Boundaries & Error Defenses  
- **Primary Sources**: [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py), [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py), [`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `a737926189ea73dfcb3d1685764d8a57ba8d2f2b`  
- **Severity**: Critical Design & Safety Standards (Rule 2 & Rule 5)

---

## 1. Problem Diagnosis: Ad-hoc Conditionals & Loosely-Typed Boundaries

Prior to the resilience remediation, the boundary between deterministic routing and semantic provider dispatch suffered from several code-quality smells:
1. **Scattered Egress Checks**: Egress classification checks were mixed into provider JSON formatting and HTTP header generation.
2. **Boolean / Numeric Type Coercion Bugs**: Python's `isinstance(True, int)` evaluates to `True`. Because of this, an answer payload containing `"confidence": true` or `"confidence": 1` could be silently coerced into `1.0`, disguising malformed provider output as high-confidence decisions.
3. **Unvalidated Deserialization**: Receipts loaded from disk could unpack arbitrary attacker-controlled JSON keys directly into dataclass constructors, potentially crashing on unrecognized fields or accepting invalid structures.

---

## 2. Spaghetti Control & Boundary Refactoring

### A. Egress Boundary Isolation via `SafeContext` & `EgressClass` (Rule 5)
In [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L42-L75), context transmission is protected by a strong, non-nullable type boundary:
```python
class EgressClass(str, Enum):
    LOCAL_ONLY = "local_only"
    SAFE_TO_SEND = "safe_to_send"

@dataclass(frozen=True)
class SafeContext:
    text: str
    egress_class: EgressClass
```
- A raw string query cannot be transmitted over the wire without passing through `validate_and_create_safe_context`.
- If `safe_summary` is absent or classifies as `LOCAL_ONLY`, `_is_egress_bypassed` in [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py#L328) immediately terminates execution with zero I/O and zero provider construction.
- No ad-hoc `if` statements are scattered in transport routines; the type contract enforces safety structurally.

### B. Unit-Interval Invariant Enforcement (Rule 2 & Rule 5)
The extracted helper `_parse_unit_interval` strictly enforces finite numeric bounds in `[0.0, 1.0]`:
```python
def _parse_unit_interval(val: Any) -> Optional[float]:
    """Parse and strictly validate a finite float in [0.0, 1.0], rejecting booleans."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return None
    num = float(val)
    if not math.isfinite(num) or num < 0.0 or num > 1.0:
        return None
    return num
```
- Rejecting `bool` explicitly eliminates Python's boolean-integer equivalence trap.
- `math.isfinite(num)` ensures `NaN` and `Infinity` cannot bypass margin or threshold comparisons.
- Applied uniformly across `confidence` and every entry in the `probabilities` mapping.

### C. Safe Deserialization & Extra-Key Filtering (Rule 5)
In [`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L85-L95), `ReceiptBase.from_dict` introduces defensive schema filtering:
```python
@classmethod
def from_dict(cls: Type[T], data: Dict[str, Any]) -> Optional[T]:
    if not isinstance(data, dict):
        return None
    valid_fields = {f.name for f in fields(cls)}
    filtered = {k: v for k, v in data.items() if k in valid_fields}
    try:
        return cls(**filtered)
    except Exception:
        return None
```
Extraneous or maliciously injected fields are stripped prior to instantiation, while missing required fields safely fail to `None` rather than raising uncaught runtime exceptions.

### D. Bounded Fail-Open Error Trap (Rule 4)
In [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py#L555-L558), provider communication is wrapped in a strict fail-open boundary:
```python
    except Exception:
        # Strict fail-open: no provider exception escapes to caller
        pass
    return baseline
```
Any network error, timeout, deserialization failure, or malformed provider response causes the router to return the baseline deterministic route immediately. Callers are never subjected to partial updates, crashed pipelines, or leaked credentials.

---

## 3. Verification & Behavior Pins

- **Boolean Rejection Test**: `tests/test_jev_transport_and_profiles.py::test_rejects_boolean_confidence` (asserts `{"confidence": true}` fails to baseline).
- **Infinite / NaN Rejection Test**: `tests/test_class_calibration_policy.py::test_rejects_non_finite_values` (asserts `inf` and `nan` fail to baseline).
- **Fail-Open Reversibility**: `tests/test_rollback_equivalence.py` (8/8 scenarios pass with <1.0ms latency).
