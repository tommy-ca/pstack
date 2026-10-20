# Thermo-Nuclear Review: Route Resolver Pipeline & Bypass Chain

- **Subsystem**: Route Resolution & Decision Plane Seam  
- **Primary Source**: [`scripts/route_resolver.py`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py#L314-L494)  
- **Base Revision**: `dea54d5cd723e06aa6a3afb78f9c3a79e82abb32`  
- **Head Revision**: `804df416c1ec0ce9f6888fbf02a43fe9714c776a`  
- **Severity**: Major (Structural Spaghetti & Modularity Defect)

---

## 1. Problem Statement & Code Quality Diagnosis

In the recent JEV resilience wave (PRs #665, #666, #667), [`resolve_skill_order_with_shadow`](file:///home/tommyk/projects/pstack/scripts/route_resolver.py#L314-L494) absorbed numerous essential security, privacy, and freshness invariant checks:
1. Early slash command bypass
2. Baseline agent/droid target bypass
3. Context privacy guard (prohibiting unreviewed raw query egress)
4. Canonical mapping pin and router blob drift detection
5. Baseline direct/system_two route bypass
6. ChoiceRequest construction and provider dispatch
7. Provider decision status check
8. Semantic candidate set membership check
9. Class-specific confidence threshold calibration check
10. Probability margin check (margin >= 0.10)
11. Persisted calibrated evidence receipt validation
12. Staleness hook check and observation recording
13. Promoted RouteResolution construction

While each check is functionally correct and covered by tests, having all 13 checks written sequentially as procedural inline `if` statements inside a single 180-line function violates **Rule 0 (Ambition / Code Judo)** and **Rule 2 (Spaghetti Growth)**.

Specifically:
- The function mixes three fundamentally distinct concerns: (a) deterministic egress gatekeeping, (b) provider invocation, and (c) advisory promotion vetting.
- Every check exits via `return baseline`, producing 14 separate return statements.
- Any future extension—such as the role/model recommendations explored in Issue #517—would be forced to add yet another ad-hoc `if` statement to this already busy path, further tangling core routing.

---

## 2. Consumer Reachability & Behavior Pin

### Consumer Reachability
- **Direct in-repo callers**:
  - [`scripts/eval_decision_routing.py`](file:///home/tommyk/projects/pstack/scripts/eval_decision_routing.py#L109)
  - [`scripts/eval_blinded_pstack.py`](file:///home/tommyk/projects/pstack/scripts/eval_blinded_pstack.py#L72)
  - [`scripts/verify_rollback_equivalence.py`](file:///home/tommyk/projects/pstack/scripts/verify_rollback_equivalence.py#L86)
- **Host Drivers** (indirect via `resolve_skill_order` or direct optional shadow):
  - Grok, Codex, OMP, OpenCode, Antigravity, and Droid drivers in `scripts/drivers/`.
- **Test Suites**:
  - `tests/test_route_resolver.py`
  - `tests/test_shadow_routing.py`
  - `tests/test_advisory_promotion.py`
  - `tests/test_class_calibration_policy.py`
  - `tests/test_jev_privacy_and_bypass.py`
  - `tests/test_jev_mapping_and_calibrated_evidence.py`

### Behavior Pin
Observable behavior must remain 100% byte-for-byte and verdict-for-verdict identical across:
- All 113 JEV offline contract tests.
- All 8 scenarios in `scripts/verify_rollback_equivalence.py` (gate_off, provider_unavailable, provider_timeout, malformed_result, abstention, below_threshold, stale_evidence, receipt_failure).
- All 12 evaluation fixtures in `scripts/eval_decision_routing.py`.
- Full candidate scoring matrix in `tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json`.

---

## 3. The "Code Judo" Restructuring

Instead of an 180-line procedural conditional ladder, we reframe the resolver into three cohesive, single-responsibility helper stages:

```
[Incoming Query + Baseline]
           │
           ▼
Stage 1: _is_egress_bypassed(baseline, query_str, safe_summary)
   ├── Slash commands (`/`)
   ├── Agent / droid targets
   ├── Missing / prohibited safe_summary
   └── Direct / system_two playbooks
           │
      (Not bypassed)
           │
           ▼
Stage 2: _load_semantic_candidates(root)
   ├── Canonical UPSTREAM pin validation
   ├── Canonical router blob validation
   └── Candidate extraction from references/decision-routing.json
           │
      (Valid candidates)
           │
           ▼
Stage 3: _evaluate_advisory_promotion(obs, candidates, root, cal_path)
   ├── Status & candidate membership check
   ├── Class-calibrated confidence threshold check
   ├── Margin check (>= 0.10)
   ├── Persisted calibrated evidence receipt check
   └── Observation audit recording
           │
           ▼
[Promoted RouteResolution or Baseline]
```

### Proposed Worked Implementation

```python
def _is_egress_bypassed(
    baseline: RouteResolution,
    query_str: str,
    safe_summary: Optional[Union[SafeContext, str]],
    bypass_playbooks: Set[str],
) -> bool:
    """Determine if query or baseline must bypass provider egress entirely."""
    if query_str.strip().startswith("/"):
        return True
    if baseline.status == "matched":
        raw_target = str(baseline.target or "").strip()
        if raw_target.startswith("/") or baseline.kind in ("agent", "droid-definition"):
            return True
        norm_target = raw_target.lstrip("/").replace("playbooks/", "").removesuffix(".md").strip()
        if norm_target in bypass_playbooks:
            return True
    if not safe_summary:
        return True
    if isinstance(safe_summary, SafeContext) and safe_summary.egress_class in (
        EgressClass.LOCAL_ONLY,
        EgressClass.PROHIBITED,
    ):
        return True
    return False
```

```python
def resolve_skill_order_with_shadow(
    profile: Dict[str, Any],
    query_str: str,
    root: Path,
    provider: Optional[Any] = None,
    mode: Optional[str] = None,
    safe_summary: Optional[Union[SafeContext, str]] = None,
    calibrated_evidence_path: Optional[Union[Path, str]] = None,
) -> RouteResolution:
    baseline = resolve_skill_order(profile, query_str, root)
    effective_mode = (mode or os.environ.get("PSTACK_JEV_MODE", "shadow")).strip().lower()

    if provider is None or effective_mode in ("none", "off", "0", "disabled"):
        return baseline

    try:
        candidates, bypass_playbooks = _load_and_validate_candidates(root)
        if not candidates or _is_egress_bypassed(baseline, query_str, safe_summary, bypass_playbooks):
            return baseline

        safe_ctx = (
            safe_summary
            if isinstance(safe_summary, SafeContext)
            else validate_and_create_safe_context(str(safe_summary), EgressClass.SAFE_TO_SEND)
        )
        req = ChoiceRequest(question_id="route_selection", context=safe_ctx, choices=tuple(candidates[:32]))
        obs = provider.decide(req)
        baseline.shadow_observation = obs

        if effective_mode != "advisory":
            return baseline

        promoted = _evaluate_advisory_promotion(
            baseline=baseline,
            obs=obs,
            semantic_candidates={c.id: c for c in candidates},
            root=root,
            calibrated_evidence_path=calibrated_evidence_path,
        )
        return promoted or baseline
    except Exception:
        return baseline
```

### Net Maintained Obligation
- **Lines of code**: Reduces `resolve_skill_order_with_shadow` body from 180 lines to 35 lines.
- **Cognitive complexity**: Each helper has a single, testable responsibility.
- **Extensibility**: Future research policies (such as #517 model-role evaluation) can hook into the pipeline without touching the deterministic baseline resolution or corrupting existing bypass invariants.
