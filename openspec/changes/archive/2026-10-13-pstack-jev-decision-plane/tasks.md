## 1. Contract, boundaries, and seam selection

- [ ] #182 Accept the typed decision envelope, precedence, receipt, and fallback contract.
- [ ] #195 Accept the context-minimization and data-egress contract.
- [ ] #196 Accept the canonical playbook vocabulary and mapping contract.
- [ ] #183 Accept the Arena selection of the no-change runtime and future router-local candidate.
- [ ] #197 Reconcile, Interrogate, validate, and merge PR #194.

## 2. Shadow pilot and evidence

After #197 and #209 close:

- [ ] #184 Add optional Jev provider adapter and default-OFF feature/config gate.
- [ ] #185 Add zero-behavior-change shadow playbook/skill routing.
- [ ] #186 Build offline routing corpus, calibration, latency, and cost lever.
- [ ] #199 Bind decision/eval evidence to implementation, canonical, provider/model, policy, and fixture revisions.
- [ ] #198 Run blinded pstack Eval for baseline versus Jev-assisted behavior.

#184 and the baseline/corpus part of #186 may proceed in parallel after both implementation gates close. The final #186 calibration pass waits for #185. #198 waits for #185, #186, and #199.

## 3. Independent verification and promotion decision

After #198 completes with fresh #199 evidence:

- [ ] #187 Run exact-head Swarm regression matrix.
- [ ] #188 Run exact-head Interrogate on the implementation diff.
- [ ] #200 Prove kill-switch/fail-open rollback equivalence.
- [ ] #189 Promote only if every gate passes; otherwise preserve baseline pstack.

#187 and #188 run at the exact candidate head. #200 proves rollback at that same head. They may run in parallel where possible.

## Program

Parent epic: #193.

Sub-epics:
- #190 contract/boundaries/Arena/spec acceptance;
- #191 shadow pilot/calibration/freshness/blinded Eval;
- #192 Swarm/Interrogate/rollback/promotion decision.

## Dependency graph

```text
#182 ─┐
#195 ─┼─→ #183 Arena ─→ #197 accept/merge PR #194 ─┐
#196 ─┘                                             ├─→ #184 provider ─→ #185 shadow ─→ #199 freshness ─┐
                                      #209 baseline ┘                                                   │
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
