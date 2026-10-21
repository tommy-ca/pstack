# 03: Spaghetti Control and Type Boundary Integrity

- **Base Revision**: `66648081fbd7b4642f38ba0b273417a8891026ba`
- **Head Revision**: `676275f1dfa83857500b171f1a50a1dfd9a690bf`
- **Focus**: Preventing ad-hoc conditional branching, untyped metadata fallbacks, and boundary leaks across environment variable readers.

---

## 1. Analysis of Spaghetti & Boundary Drift

Rule 2 warns against "random spaghetti growth in existing code... new ad-hoc conditionals, scattered special cases, or one-off branches inserted into unrelated flows."
Rule 5 demands: "Push hard on type and boundary cleanliness when they affect maintainability."

The audit identified two key areas where boundary cleanliness can be improved:

---

## 2. Findings & Recommended Actions

### Finding SC-1: Inconsistent Environment Flag Parsing Across Modules

- **Severity**: Boundary Drift & Maintenance Friction
- **Locations**:
  - [`scripts/route_resolver.py:434-437`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py#L434-L437):
    ```python
    allow_fixture = (
        os.environ.get("PSTACK_JEV_ALLOW_FIXTURE_EVIDENCE") == "1"
        or os.environ.get("PSTACK_JEV_ALLOW_FIXTURE_PROMOTION") == "1"
    )
    ```
  - [`scripts/evidence_receipts.py:184-185`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L184-L185):
    ```python
    if os.environ.get("PSTACK_JEV_ALLOW_FIXTURE_EVIDENCE") == "1":
        allow_fixture = True
    ```
- **Problem**:
  1. `route_resolver.py` permits either `PSTACK_JEV_ALLOW_FIXTURE_EVIDENCE=1` or `PSTACK_JEV_ALLOW_FIXTURE_PROMOTION=1`.
  2. `evidence_receipts.py` only checks `PSTACK_JEV_ALLOW_FIXTURE_EVIDENCE=1` and ignores `PSTACK_JEV_ALLOW_FIXTURE_PROMOTION=1`.
  3. `validate_calibrated_evidence` accepts an explicit parameter `allow_fixture: bool = False`, but if passed `allow_fixture=False`, it still checks `os.environ` and overrides it to `True`.
- **Consumer Reachability**:
  - `validate_calibrated_evidence`: called in `scripts/route_resolver.py`, `scripts/eval_fast_role_task_fit.py`, and across tests.
- **Recommended Remediation**:
  Centralize the environment check into a single canonical helper in `scripts/evidence_receipts.py`:
  ```python
  def is_fixture_evidence_allowed() -> bool:
      return os.environ.get("PSTACK_JEV_ALLOW_FIXTURE_EVIDENCE") == "1" or \
             os.environ.get("PSTACK_JEV_ALLOW_FIXTURE_PROMOTION") == "1"
  ```
  In `validate_calibrated_evidence`:
  ```python
  def validate_calibrated_evidence(
      ...,
      allow_fixture: Optional[bool] = None,
  ) -> Tuple[bool, List[str]]:
      if allow_fixture is None:
          allow_fixture = is_fixture_evidence_allowed()
  ```
  And in `route_resolver.py`, pass `allow_fixture` directly from `is_fixture_evidence_allowed()` without duplicate ad-hoc `os.environ.get` expressions.

---

### Finding SC-2: Untyped Metadata Fallback for Provenance

- **Severity**: Type Contract Weakness
- **Location**: [`scripts/evidence_receipts.py:212`](file:///home/tommyk/projects/pstack/scripts/evidence_receipts.py#L212)
- **Problem**:
  ```python
  prov = receipt.provenance or receipt.metadata.get("provenance")
  ```
  And:
  ```python
  is_fixture = (
      receipt.status == "specimen_fixture"
      or receipt.review_decision == "specimen_fixture"
      or (isinstance(receipt.provenance, dict) and receipt.provenance.get("kind") == "fixture")
      or receipt.metadata.get("is_specimen_fixture") is True
  )
  ```
  `CalibratedEvidenceReceipt` now defines `provenance: Optional[Dict[str, Any]] = None` as a first-class dataclass field. Allowing unstructured fallbacks into `receipt.metadata["provenance"]` and `receipt.metadata["is_specimen_fixture"]` weakens the type contract and creates duplicate representation of state.
- **Consumer Reachability**:
  Internal to `scripts/evidence_receipts.py:validate_calibrated_evidence`.
- **Recommended Remediation**:
  Normalize `receipt.provenance` during receipt deserialization in `ReceiptBase` or `load_calibrated_evidence_receipt`:
  ```python
  if receipt.provenance is None and "provenance" in receipt.metadata:
      receipt.provenance = receipt.metadata.pop("provenance")
  ```
  This guarantees that downstream validation only ever inspects the typed `receipt.provenance` field.
