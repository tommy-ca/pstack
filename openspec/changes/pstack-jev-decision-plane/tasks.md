## 1. Contract, boundaries, and seam selection

- [ ] #182 Define typed Jev decision envelope, precedence, and fallback semantics.
- [ ] #195 Define context-minimization and data-egress boundary.
- [ ] #196 Derive canonical playbook decision vocabulary and deterministic mapping.
- [ ] #183 Run Arena against the no-change control and select the minimal seam.
- [ ] #197 Reconcile, Interrogate, validate, and merge PR #194.

## 2. Shadow pilot and evidence

After #197 closes:

- [ ] #184 Add optional Jev provider adapter and default-OFF feature/config gate.
- [ ] #185 Add zero-behavior-change shadow playbook/skill routing.
- [ ] #186 Build offline routing corpus, calibration, latency, and cost lever.
- [ ] #199 Bind decision/eval evidence to implementation, canonical, provider/model, policy, and fixture revisions.
- [ ] #198 Run blinded pstack Eval for baseline vs Jev-assisted behavior.

#184 and the baseline/corpus part of #186 may proceed in parallel. The final #186 calibration pass waits for #185. #198 waits for #185, #186, and #199.

## 3. Independent verification and promotion decision

After #198 completes with fresh #199 evidence:

- [ ] #187 Run exact-head Swarm regression matrix.
- [ ] #188 Run exact-head Interrogate on the implementation diff.
- [ ] #200 Prove kill-switch/fail-open rollback equivalence.
- [ ] #189 Promote only if every gate passes; otherwise preserve baseline pstack.

#187, #188, and #200 run in parallel where possible.

## Program

Parent epic: #193.

Sub-epics:
- #190 contract/boundaries/Arena/spec acceptance;
- #191 shadow pilot/calibration/freshness/blinded Eval;
- #192 Swarm/Interrogate/rollback/promotion decision.

## Dependency graph

```text
#182 ─┐
#195 ─┼─→ #183 Arena ─→ #197 accept/merge PR #194
#196 ─┘                          │
                                ├─→ #184 provider ─→ #185 shadow ─→ #199 freshness ─┐
                                └─→ #186 corpus/baseline ────────────────────────────┤
                                                                                     ↓
                                                                                  #198 Eval
                                                                                     ↓
                                                                          ┌──────────┼──────────┐
                                                                          ↓          ↓          ↓
                                                                        #187       #188       #200
                                                                        Swarm   Interrogate  rollback
                                                                          └──────────┼──────────┘
                                                                                     ↓
                                                                                   #189
```

A no-promotion result is a valid successful outcome when Jev does not earn its place over baseline pstack.
