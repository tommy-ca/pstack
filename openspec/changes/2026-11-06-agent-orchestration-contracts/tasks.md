# Recursive execution graph: Agent orchestration (Epic #916)

This is the **draft intent plan**, not an implementation completion report. Source catalog and proposed spec can be authored in parallel, but runtime adapters are blocked by verified contracts.

## AO-01 — Inventory & semantic decomposition ([#917](https://github.com/tommy-ca/pstack/issues/917))
- [x] Pin Mu, Dogsled, Cursor and target PStack SHAs.
- [x] Document atomic semantic source anchors and adoption dispositions.
- [ ] Confirm any upstream functionality claimed by a runtime adapter through executable tests.
- [ ] Audit license obligations if copying source, not just extracting concepts.

## AO-02 — Formal contracts ([#918](https://github.com/tommy-ca/pstack/issues/918))
- [x] Draft ownership/authority architecture, code and data flows.
- [x] Draft typed TaskUnit, ExecutionRequest/Receipt, Evidence and VerificationResult models.
- [x] Draft identity, cancellation, custody, settlement and cleanup invariants with GWT negative scenarios.
- [ ] Validate OpenSpec with the repository's available CLI/checker and reconcile schema with canonical host portability models.
- [ ] Confirm accepted design with independent review.

## AO-03 — Verification skills and negative controls ([#919](https://github.com/tommy-ca/pstack/issues/919))
- [x] Identify existing create-verification and create-formal-verification skill generators and retention rules.
- [x] Define runtime + formal falsification matrix; do not claim it was executed.
- [ ] Generate a project-local adapter verification skill **only after an adapter is implemented**.
- [ ] Demonstrate every relevant mutant fails against target code and baseline checker works.
- [ ] Record checker version, source-sync SHA, bounds and exact observed receipts.

## AO-04 — Optional adapter proof ([#920](https://github.com/tommy-ca/pstack/issues/920))
- [ ] First demonstrate a capability gap in active native PStack host profiles.
- [ ] Decide one adapter (or close not planned) via a recorded design choice.
- [ ] Implement if warranted, with explicit opt-in, no second task store and no implicit executable fallback.
- [ ] Run crash/retry/identity/permission/cancel/cleanup checks on the actual binary.

## AO-05 — Workflow review and acceptance ([#921](https://github.com/tommy-ca/pstack/issues/921))
- [ ] Run actual Swarm independently across review slices; record coverage gaps/dropouts.
- [ ] Run actual Arena with frozen rubric and real candidate isolation (or mark BLOCKED).
- [ ] Run Interrogate, independently reproduce findings.
- [ ] Run both Thermo-Nuclear review lenses on the changed diff.
- [ ] Verify acceptance on real host/app/CLI and add revision-bound receipts; no invented green statuses.

## AO-06 — Downstream semantic integration ([#922](https://github.com/tommy-ca/pstack/issues/922))
- [ ] Compare with existing PStack / QStack LLMWiki semantic building blocks, dedupe.
- [ ] Produce typed, source-backed, separately promoted wiki candidates.
- [ ] Verify QStack only consumes PStack and generic orchestration is not copied into qorch.
- [ ] Run QStack-specific verifier for any changed quant overlay, independently.

## DAG

```text
AO-01 (#917) --> AO-02 (#918) --> AO-03 (#919) --> AO-04 (#920)
                      |                |                |
                      +----------------+--> AO-05 (#921)|
                                        \      ^         /
                                         ------+---------
AO-01 + AO-02 + AO-05 ------------------------> AO-06 (#922)
```

Interpret AO-04 as a *conditional* execution lane. When native host integration already suffices, close #920 with a documented `not_planned` rationale; #921 may still review the contract-only change. This avoids dependency-by-ceremony.

## Acceptance semantics

Unexecuted `[ ]` does not become `[x]` because documentation exists. No commit/PR is self-approval. Separate static completeness from host-native smoke and live/falsifier proof. PStack orch owns development tasks; QStack qorch owns quant research tasks. The OpenSpec intent graph is not a runtime task store.
