# Thermo-Nuclear Review: Decision Adapter Validation & Transport Decoupling

- **Subsystem**: Decision Transport & Wire Client  
- **Primary Source**: [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py#L432-L557)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `804df416c1ec0ce9f6888fbf02a43fe9714c776a`  
- **Severity**: Moderate (Repetitive Boilerplate & Inefficient Validation)

---

## 1. Problem Statement & Code Quality Diagnosis

In PR #666 (addressing #664 and #660), [`scripts/decision_adapter.py`](file:///home/tommyk/projects/pstack/scripts/decision_adapter.py) added strict finite validation for `confidence` and `probabilities` to prevent non-finite numbers (`NaN`, `Inf`), boolean masquerading as integers, and out-of-interval numbers from ever causing corrupted downstream decisions.

However, an inspection of `_parse_provider_response` reveals substantial copy-pasted validation:
1. **Duplicated unit-interval logic**:
   - Lines 499-512 validate `confidence`:
     ```python
     if isinstance(confidence_val, bool) or not isinstance(confidence_val, (int, float)):
         return ProviderObservation(...)
     c_float = float(confidence_val)
     if not math.isfinite(c_float) or c_float < 0.0 or c_float > 1.0:
         return ProviderObservation(...)
     ```
   - Lines 532-545 repeat the exact same 4-check sequence for every probability entry:
     ```python
     if isinstance(p_val, bool) or not isinstance(p_val, (int, float)):
         return ProviderObservation(...)
     p_float = float(p_val)
     if not math.isfinite(p_float) or p_float < 0.0 or p_float > 1.0:
         return ProviderObservation(...)
     ```
2. **Repetitive observation construction**:
   - `ProviderObservation(outcome=DecisionOutcome(status="invalid"), provider_identity=resp_provider_str, model_identity=resp_model_str)` is written verbatim **8 times** in `_parse_provider_response`.

This violates **Rule 4 (Direct, boring code; avoid copy-paste logic)** and **Rule 6 (Reuse existing helpers)**.

---

## 2. Consumer Reachability & Behavior Pin

### Consumer Reachability
- Direct callers of `SemanticDecisionProvider.decide`:
  - `scripts/route_resolver.py`
  - `scripts/eval_decision_routing.py`
  - `scripts/eval_blinded_pstack.py`
  - `tests/test_decision_adapter.py`
  - `tests/test_jev_transport_and_profiles.py`

### Behavior Pin
All 14 parameterized fuzzing tests in `tests/test_jev_transport_and_profiles.py` (covering `NaN`, `+Inf`, `-Inf`, `True`, `False`, strings, arrays, `-0.01`, `1.01`, and out-of-domain choice keys) must continue to produce `status="invalid"` and `is_decided() == False`.

---

## 3. The "Code Judo" Restructuring

We extract a single pure helper `_parse_unit_interval(val: Any) -> Optional[float]` and an observation factory:

```python
def _parse_unit_interval(val: Any) -> Optional[float]:
    """Strictly parse a finite float in [0.0, 1.0], rejecting booleans and non-numeric types."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        return None
    num = float(val)
    if not math.isfinite(num) or num < 0.0 or num > 1.0:
        return None
    return num
```

And in `SemanticDecisionProvider`:
```python
def _invalid_obs(self, provider: str = "unknown", model: str = "unknown") -> ProviderObservation:
    return ProviderObservation(
        outcome=DecisionOutcome(status="invalid"),
        provider_identity=provider,
        model_identity=model,
    )
```

### In `_parse_provider_response`:
```python
# Validate confidence
confidence = None
if confidence_val is not None:
    confidence = _parse_unit_interval(confidence_val)
    if confidence is None:
        return self._invalid_obs(resp_provider_str, resp_model_str)

# Validate probabilities
probabilities = None
if probabilities_val is not None:
    if not isinstance(probabilities_val, dict):
        return self._invalid_obs(resp_provider_str, resp_model_str)
    probabilities = {}
    for opt_id, p_val in probabilities_val.items():
        if opt_id not in valid_choice_ids:
            return self._invalid_obs(resp_provider_str, resp_model_str)
        p_float = _parse_unit_interval(p_val)
        if p_float is None:
            return self._invalid_obs(resp_provider_str, resp_model_str)
        probabilities[opt_id] = p_float
```

### Net Maintained Obligation
- **Complexity reduction**: Eliminates 35 lines of duplicate type-checking and validation code.
- **Single point of truth**: Any future extension to numeric probability validation (e.g. sum-to-one tolerances) touches exactly one helper rather than multiple locations.
