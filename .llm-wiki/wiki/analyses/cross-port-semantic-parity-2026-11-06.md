# Cross-port semantic parity — November 2026

**Source-review analysis only; no native runtime, formal checker, or independent multi-model proof is asserted.** This page tracks three pinned PStack sources and reusable contracts, without taking normative policy from a reference port.

## Exact source references

- [Cursor canonical PStack](https://github.com/cursor/plugins/tree/c742dd61706fbacc1b95f1a20b7b988cf096ce6c/pstack): latest observed path-scoped change commit c742dd61706fbacc1b95f1a20b7b988cf096ce6c (2026-10-27, 0.15.36); source of workflow intent.
- [Michael Denyer's comparator](https://github.com/michael-denyer/pstack-claude/tree/d88063f3355a5ecff0e6dbb890a11bab4b08bc2e): d88063f3355a5ecff0e6dbb890a11bab4b08bc2e (2026-11-05); source of additional host mechanisms, policy-fork declarations and negative scenarios.
- [Target PStack baseline](https://github.com/tommy-ca/pstack/tree/5d58283f40f7fc8f56a536946abe79418538fe6e): 5d58283f40f7fc8f56a536946abe79418538fe6e; native host profiles, verification skills, schema and wiki authority.
- The target's applied UPSTREAM pin is still 88d47514b82e7c44f00f2b2a72ff6dd12158038c; semantic sync #840 and host-specific release pin promotion are distinct.
- Reference port's tools/upstream.json already pins canonical c742dd6. The old target cross-port OpenSpec design compared comparator 0.9.95 (88f6d39f); GitHub compare to d88063f reports 86 commits and only the first 300 modified files. Coverage is prioritized, not exhaustive.

## Atomic concepts and separation

| Semantic block | Canonical question | Comparator lesson | Target owner/decision |
| --- | --- | --- | --- |
| SourceRevision | What exact file/revision? | tools/upstream.json + tools/forks.json show derivation vs deliberate divergence | Reuse pinned classifier, never implicit latest |
| Intent + Principle | Why and how to act? | Port-local syntax should not redefine canonical meaning | Canonical poteto-mode/principle-* skills |
| PlaybookStep | What ordered observable gate? | Runtime-specific mappings differ, step outcome remains meaningful | Existing playbooks; no port-specific code in semantics |
| RolePlan | Which independent roles/seats? | Model aliases are config, not availability | pstack.package.json and model_role resolver |
| CapabilityBinding | Is capability present and proven here? | docs/pi-equivalence.md maps explicit statuses and real-vs-offline tests | Existing 17 bindings, profiles and native drivers |
| Admission | Was tool effect authorized? | Pi extensions can define different ask/permission surfaces | Native guard + deny before effect; human.ask not human.gate |
| ChildLifecycle | Is child actually alive/settled? | tests/pi and Pi process tools expose stop, steer, join, transcript and exact ID edge cases | Host native driver, no universal RPC daemon |
| TemporalTrigger | Can a cancelled timer fire late? | tla/PiScheduler.tla + mutations document fairness-dependent delivery and races | Host-owned schedule invariants and code-bound formal proof |
| WorktreeLease | May this path be safely removed? | Child artifacts, ignored/untracked, reflog commits and linked-worktree checks matter | Existing worktree_protocol and negative fixtures |
| EvidenceReceipt | What was really measured on which head? | Equivalence table separates static/offline/live proof | Current evidence receipts and failure-first lattice |
| ReviewTopology | Were seats truly independent? | Model/provider identity must be observed for actual fanout | Swarm, Arena, Interrogate; no simulated agreement |
| PromotionGate | Is exact-head patch accepted? | Source sync and release policies differ | Independent review and existing shipping gates |

## Gaps worth a small follow-up

1. **Partial comparator manifest:** the 86-commit GitHub comparison's 300-file result cap means every changed path is not yet classified; #907 owns a full bounded manifest.
2. **Host-level negative fixture coverage:** reuse comparator tests/pi/* to locate uncovered child lifecycle, late callback, worktree and denial postconditions. Existing target tests are substantial; do not presume absence without executable comparison. #908.
3. **Formal assumption mapping:** the comparator PiScheduler TLA+ model is code-linked to the comparator's own Node/Pi callbacks and fairness; it cannot prove target's driver or another host without a new concrete abstraction map. #909.
4. **Provenance:** these GitHub source links are externally pinned but were NOT captured into .llm-wiki/raw/sources via write-once ingest. The page is a compiled analytical interpretation only; no local SHA-256 ingestion attestation is claimed. #910.
5. **Independent gate:** this source review did not execute independent Swarm/Arena/Interrogate model seats or the two Thermo Nuclear reviews; #911 must preserve exact-head traceability.

## Formal contract and related compiled concepts

- [Existing semantic crosswalk](../concepts/semantic-blocks-and-crosswalk.md)
- [Standalone Pi source-only candidate](pi-1-5-pstack-candidate.md)
- [Statechart qualification](statechart-qualification.md)
- [LLMWiki reference evaluation](llm-wiki-reference-evaluation.md)
- [Formal OpenSpec proposal](https://github.com/tommy-ca/pstack/tree/audit/cross-port-semantic-parity-2026-11-06/openspec/changes/2026-11-06-cross-port-parity)
- [Tracking epic #906](https://github.com/tommy-ca/pstack/issues/906)

The domain separation remains one-way: QStack may consume PStack compiled skill/workflow contracts; PStack cannot rely on QStack's runtime, quant wiki compiler or knowledge publisher.
