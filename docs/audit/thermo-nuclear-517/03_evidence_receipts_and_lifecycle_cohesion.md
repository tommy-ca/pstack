# Thermo-Nuclear Review: Evidence Receipts & Lifecycle Cohesion

- **Subsystem**: Evidence Receipts & Staleness Verification Lifecycle  
- **Primary Source**: [`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `804df416c1ec0ce9f6888fbf02a43fe9714c776a`  
- **Severity**: Moderate (Lifecycle Fragmentation & Serialization Redundancy)

---

## 1. Problem Statement & Code Quality Diagnosis

In the evolution of pstack's drift detection and JEV resilience architecture (Tasks #199, #312, and PR #667), three distinct cryptographic evidence receipts were introduced in [`scripts/evidence_receipts.py`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py):
1. [`DecisionReceipt`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L74-L99): Binds a single decision judgment to exact git commit, canonical tree, router blob SHA, and provider/model identities.
2. [`CalibratedEvidenceReceipt`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L102-L124): Persisted holdout benchmark proof required to authorize advisory promotion (#659).
3. [`CheckEvidenceReceipt`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L424-L449): Binds change-scoped test/check selections to merge base, patch-id, and clean worktree digest (#312).

While each receipt serves an indispensable integrity role, an audit under **Rule 3 (Clean the design)** and **Rule 4 (Direct, boring code)** reveals significant lifecycle fragmentation and structural duplication:

### A. Redundant Serialization Boilerplate
All three dataclasses repeat verbatim implementations of `to_dict` and `to_json`:
```python
def to_dict(self) -> Dict[str, Any]:
    return asdict(self)

def to_json(self, indent: int = 2) -> str:
    return json.dumps(self.to_dict(), indent=indent, sort_keys=True)
```
This is copy-pasted across lines 94-98, 119-123, and 444-448.

### B. Asymmetric and Brittle Deserialization
Each receipt type handles deserialization completely differently:
- [`CalibratedEvidenceReceipt`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L126-L150) uses a bespoke 25-line procedural function `load_calibrated_evidence_receipt` that manually unpacks 13 keys with `str(raw.get(...))` and `dict(raw.get(...))`.
- [`CheckEvidenceReceipt`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L486-L487) uses raw kwargs unpacking: `CheckEvidenceReceipt(**json.loads(path.read_text(...)))`, which raises unhandled `TypeError` if extra or missing keys exist.
- [`DecisionReceipt`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L74) has **zero** load helper or `from_dict` constructor, forcing ad-hoc consumer reconstruction.

### C. Divergent Staleness and Validation Interfaces
The three receipts expose inconsistent validation signatures:
- `DecisionReceipt`: `check_receipt_staleness(receipt, root, expected_provider, expected_model) -> Tuple[bool, List[str]]`
- `CalibratedEvidenceReceipt`: `validate_calibrated_evidence(receipt, root, provider, model, class, conf) -> Tuple[bool, List[str]]`
- `CheckEvidenceReceipt`: `check_check_evidence_staleness(receipt, root, base, head) -> Tuple[bool, List[str]]`

While the domain criteria differ (e.g. check outcomes vs class thresholds), all three evaluate the identical invariant: **has the underlying environment, revision, or canonical mapping drifted since the evidence was signed?**

---

## 2. Consumer Reachability & Behavior Pin

### Consumer Reachability
- **Core Resolvers & Gates**:
  - [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py#L477): Loads and validates `CalibratedEvidenceReceipt` for advisory promotion.
  - [`scripts/verify_rollback_equivalence.py`](file:///home/tommyk/projects/pstack/scripts/verify_rollback_equivalence.py#L86): Validates receipt rejection under drift scenarios.
  - [`scripts/verify-portable.py`](file:///home/tommyk/projects/pstack/scripts/verify-portable.py): Calls `create_check_evidence_receipt` and `can_claim_current_ci`.
- **Test Suites**:
  - `tests/test_evidence_receipts.py`: 18 tests asserting staleness detection and SHA calculation.
  - `tests/test_jev_mapping_and_calibrated_evidence.py`: 12 tests asserting receipt loading, expiration, and threshold enforcement.

### Behavior Pin
- Existing serialized receipt JSON files (including [`references/calibrated-evidence.json`](file:///home/tommyk/projects/pstack/references/calibrated-evidence.json)) must remain 100% valid and parseable without modification.
- All drift conditions (tampered SHA, moved HEAD, expired UTC timestamp, altered patch-id) must continue returning `is_stale=True` with exact match diagnostic strings.
- Pass all 30 offline tests in `test_evidence_receipts.py` and `test_jev_mapping_and_calibrated_evidence.py`.

---

## 3. The "Code Judo" Restructuring

We unify receipt serialization and deserialization under a single lightweight, reusable base mixin: `ReceiptBase`.

```python
class ReceiptBase:
    """Standardized serialization and safe deserialization for revision-bound receipts."""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> Optional[T]:
        """Safely instantiate dataclass from dict, ignoring extraneous keys and handling defaults."""
        if not isinstance(data, dict):
            return None
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        try:
            return cls(**filtered)
        except Exception:
            return None

    @classmethod
    def load(cls: Type[T], path: Optional[Path]) -> Optional[T]:
        """Load and parse receipt from JSON file path."""
        if path is None or not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return cls.from_dict(raw)
        except Exception:
            return None
```

### Impact on Dataclasses
Each receipt class simply inherits `ReceiptBase`:
```python
@dataclass(frozen=True)
class DecisionReceipt(ReceiptBase):
    ...

@dataclass(frozen=True)
class CalibratedEvidenceReceipt(ReceiptBase):
    ...

@dataclass(frozen=True)
class CheckEvidenceReceipt(ReceiptBase):
    ...
```

### Preserving Backward Compatibility
To avoid breaking existing callers:
```python
def load_calibrated_evidence_receipt(path: Optional[Path]) -> Optional[CalibratedEvidenceReceipt]:
    return CalibratedEvidenceReceipt.load(path)

def load_check_evidence_receipt(path: Path) -> CheckEvidenceReceipt:
    receipt = CheckEvidenceReceipt.load(path)
    if receipt is None:
        raise ValueError(f"Failed to load CheckEvidenceReceipt from {path}")
    return receipt
```

---

## 4. Net Maintained Obligation & Recheck Commands

### Maintained Obligation Removed
- **Eliminates 3x duplicated serialization boilerplate** (`to_dict` and `to_json` across classes).
- **Eliminates bespoke 25-line manual dictionary mapping** in `load_calibrated_evidence_receipt`.
- **Fixes silent fragility in `load_check_evidence_receipt`**, which previously crashed on unexpected keys.
- **Provides `DecisionReceipt` with first-class deserialization** without adding new procedural code.

### Recheck Commands
```bash
uv run pytest -q tests/test_evidence_receipts.py tests/test_jev_mapping_and_calibrated_evidence.py
uv run python scripts/verify_rollback_equivalence.py
```
Both commands must pass with zero errors or schema mismatches.
