# Design: source-pinned semantic building blocks and host-owned execution

Status: architectural proposal / source-review evidence, **not executed Swarm, Arena, Interrogate, native Pi, or TLC proof**. Implements only documentation and skill instructions until separately verified.

## Authority and responsibility boundaries

| Authority | Existing owner | Role |
| --- | --- | --- |
| Canonical workflow intent | cursor/plugins/pstack at c742dd6; target skills/principles/playbooks | Normative order, decision rules, acceptance |
| Reference mechanisms/tests | michael-denyer/pstack-claude at d88063f; tools/forks.json | Candidate observations, *not* normative policy |
| Portable contracts | target openspec/specs/pstack-portability, pstack.package.json, schemas/portability, scripts/portability_types.py | Typed vocabulary, role/capability definitions |
| Host-owned execution | profiles/<host>.json and scripts/drivers/ | Native CLI/tool binding, lifecycle/worktrees |
| Verification and evidence | scripts/verify_portable.py, scripts/evidence_*, create/maintain verification skill pairs | Tiered receipts, negative controls, formal bounds |
| Knowledge projection | .llm-wiki and scripts/llm_wiki.py | Source-linked Markdown analysis; no runtime authority |
| Quant overlay | tommy-ca/qstack | Depends on PStack patterns; PStack must not import QStack code |

Never infer runtime conformance from skill count or wording similarity. Cursor's pstack-path last changed at c742dd6. The target's earlier #840 synced that *intent*, but its manifest/applied pin remains 88d4751 pending separate release policy.

## Atomic semantic decomposition (conceptual, not new Python classes)

| Atom | Input => output | Stable invariant | Existing owner |
| --- | --- | --- | --- |
| SourceRevision | repo, commit, path, content hash => frozen artifact | Exact SHA, source role, rights noted | upstream classifier |
| SemanticDelta | canonical + comparator + target => decision | Policy fork cannot silently become canonical | upstream sync/OpenSpec |
| Intent | task => principle/leaf/playbook | No host tool names in intent | poteto-mode |
| Principle | trigger + constraint => decision | Specific choice traces to leaf principle | principle-* skills |
| Playbook | ordered preconditions/actions/gates => workflow | No hard-coded engine requirement | poteto-mode/playbooks |
| RolePlan | role id + topology + budget => requested seats | Requested != dispatched != verified | existing role resolver |
| CapabilityBinding | semantic capability + host/version => primitive/GAP | Unsupported or unobserved is not PASS | profiles and schemas |
| Admission | operation + actor + current policy => allow/ask/deny | Pre-effect authorization, human.ask != hard human.gate | native host controls |
| ChildLifecycle | spawn/observe/steer/join/cancel => terminal state | Only actual settled child yields terminal receipt | native runtime/driver |
| WorktreeLease | owner, path, git state => retain/remove decision | No unowned, ignored, untracked, symlink or commit loss | worktree_protocol |
| TemporalTrigger | schedule, stop, callback, session => delivery state | No stale wakeup after cancellation or double firing | host-specific schedule implementation |
| VerificationReceipt | exact source/host/run/scenario => graded evidence | Static, offline, observed-live and independent review distinct | existing evidence types |
| ReviewTopology | independently executed roles + identities => reduction | No same-family diversity claim; no fake fanout | swarm/arena/interrogate |
| PromotionGate | receipts + independent verdict + branch head => ship/no-ship | Fresh exact-head blockers dominate | shipping and CI |

Reference-backed cases to mine:
- Comparator docs/pi-equivalence.md T01–T21 and H/* rows: foreground/background child IDs, resume/steer, kill-after-exit, session hooks, capability substitution and explicit differences.
- Comparator plugins/pstack/pi/index.ts, agents.ts, schedule.ts, worktree.ts: host-specific process ownership; **do not copy**.
- Comparator tla/PiScheduler.tla and mutation set: liveness under fairness/idle, prompt delivery, timer cancellation; models include host assumptions and must be corroborated on target behavior.
- Comparator tools/forks.json and tools/sync.mjs: typed policy-fork/exclusion manifest, reproducible three-way upstream derivation.
- Cursor canonical pstack/skills/poteto-mode/SKILL.md and playbooks/orchestrate.md: intent, agentic coordination, independent reviewer/ship gates.
- Target scripts/verify_pi_candidate.py already preserves 17 candidate bindings and forbids observed_live promotion by static source; #894 is a closed source-audit baseline.

## Code and data flows

~~~text
Cursor source c742dd6 -----------\
Comparator source d88063f ---------+--> normalize artifact identity, hash and rights
Target implementation 5d58283 ----/     |
                                       v
                             semantic delta classifier
                   canonical | host-only | fork | reusable | GAP
                                       |
                                  OpenSpec decision
                    +------------------+-------------------+
                    |                                      |
             workflow semantic                       host-local native
             principle/skill                         adapter/profile
                    |                                      |
              intent + plan -> role/capability plan -> admission -> native child
                                                          |
                                   worktree lease <- observe/settle/timeout
                                         |                |
                                         +------> evidence receipt
                                                     |
                                 deterministic gates, actual independent review
                                                     |
                                               PR promotion/rollback

SourceRevision -> curated wiki analysis -> wiki index/search/graph.
No wiki page, compiler candidate, or referee model can authorize native tool effects.
~~~

## Data schemas/models (semantic contracts; map to existing typed schema)

A delta row is a review artifact, not a new runtime registry:

~~~json
{
  "source_revision": {"repo":"michael-denyer/pstack-claude","commit":"d88063f3355a5ecff0e6dbb890a11bab4b08bc2e","path":"tla/PiScheduler.tla"},
  "canonical_revision":"c742dd61706fbacc1b95f1a20b7b988cf096ce6c",
  "target_base":"5d58283f40f7fc8f56a536946abe79418538fe6e",
  "semantic_atom":"TemporalTrigger",
  "classification":"reusable-postcondition",
  "owner":"host-adapter",
  "postcondition":"cancelled wakeup never sends its prompt later",
  "target_host":"pstack:pi",
  "evidence_level":"source-only",
  "verification_status":"UNTESTED",
  "negative_scenario":"cancel-then-late-callback"
}
~~~

Required concepts: SourceRevision (repository, commit, path, hash when recorded), SemanticDecision (classification, rationale, owner), CapabilityBinding (existing 17-capability schema), Scenario (precondition, action, stable postcondition, forbidden effect), EvidenceReceipt (host, executable version, exact target tree, timestamps, stdout/stderr, terminal state, proof level), FormalProperty (linked code span, atomicity mapping, assumptions/fairness, bounds, checker, mutant). Reuse existing typed definitions; the JSON above is descriptive only. Never promote an unvalidated example into schema or claim sources were ingested.

## Critical invariants and failure models
- Safety S1: after denial, no descendant process/tool effect launches (unless an independently authorized operation occurred).
- Safety S2: cancellation/timeout/stopped cannot count as settled PASS, even if a previous transcript said completed.
- Safety S3: child permission ceiling cannot exceed actual parent/host ceiling; extension-owned tools may bypass local FS sandbox and must be separately admitted.
- Safety S4: worktree removal allowed only for an owned, proved disposable lease, and retain history/ignored/untracked content; no symlink path escape.
- Safety S5: evidence or model roster from a different exact SHA/host/model family cannot meet current gate.
- Liveness L1 (conditional): under explicitly stated idle/timer fairness, eligible wakeup eventually fires; document counterexample when fairness is absent. Never claim unconditional liveness.
- Safety S6: an ask-user UI prompt is not a hard effect-authorizing human gate; headless ask behavior must fail closed.

## Review alternatives and execution honesty
Arena alternatives: A document-only delta (minimum), B add targeted host-local negative fixtures (default when unmet), C build generic scheduler/process manager (reject without measured duplicate failure in >=2 hosts). Swarm lanes: normative semantics, host safety, formal reachability, provenance/rights. Interrogate adversarial probes: cancel/late delivery, permission escalation, hidden Git files, stale receipts, same-family fanout, policy-fork laundering. Both upstream Thermo Nuclear reviews apply to the actual changed diff. These are **planned checks**, not completed model-backed review sessions.

## Risks, limitations and rollback
Github compare output for the 86-commit comparator range was capped at 300 files; first pass is a prioritized path-level audit, NOT an exhaustive modified-file manifest. Do not mistake source-only documentation as native proof, and do not advance the official pin. Missing checker/binary credentials remain BLOCKED/UNTESTED. Revert documentation/skill guidance independently of any later host-specific code additions.
