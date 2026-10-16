# Arena record: harness-neutral role/model-policy seam (gate #436)

Date: 2026-10-16. Reviewed head: `ae06ef1` (stack branch `stack/pr428-static-planner`), base `main` `1fa1671`.
Method: four candidates against a frozen rubric, then one cross-judge scoring criterion by criterion and independently re-verifying one load-bearing claim per candidate.

## Frozen rubric

Weights: C1 upstream fidelity 30%, C2 maintenance burden 20%, C3 host-native correctness 25%, C4 verifiability 15%, C5 boundary safety 10%.

## Candidates and scores

| Candidate | C1 | C2 | C3 | C4 | C5 | Weighted |
| --- | --- | --- | --- | --- | --- | --- |
| D0 no-change control (prose mapping) | 4 | 4 | 3 | 2 | 5 | 3.55 |
| D1 typed seam (shipped: policy schema + pure `plan_role`) | 4 | 4 | 4 | 5 | 5 | 4.25 |
| D2 provider-independent runtime gateway | 1 | 1 | 1 | 2 | 1 | 1.15 |
| D3 host-per-adapter deep fork | 2 | 2 | 5 | 3 | 1 | 2.80 |

Candidate briefs: the D0 case rests on the typed seam having no runtime consumer outside its own tests (1,191 new lines; `verify-portable.py` and `verify-harness.py` reference it zero times). D2 and D3 were rejected on the change's own non-goals (second control plane; imported policy forks and durable store).

## Base: D1, with grafts

D1 is the only candidate scoring 4+ on four of five criteria. It keeps one pinned workflow source and one role registry, makes static-versus-runtime confusion structurally impossible, and is the only candidate with a deterministic negative-fixture harness. Its C1 deduction is the honest #437 precedence overlap: the policy document's `model_catalog`/`tier_defaults` restate host facts ADR-0016 assigns to `profiles/<host>.json` plus projected manifests, with no parity gate yet.

Grafts adopted or filed:

- From D0: the projector stays the sole writer with its `--check` drift gate; a plan never authorizes dispatch; the planner must gain a real runtime consumer in #440-#444 or face YAGNI removal.
- From D3: emit canonical role IDs in `generate_*_models` (measured divergence recorded in #440), plus per-host negative fixtures including droid's forbidden model/effort fields.

## Independent verification performed in this run

- `wc -l` on the five new modules confirmed the 1,191-line figure; every reference to the resolver lives in schemas/scripts/tests/example and the OpenSpec change, none in the levers.
- D1's const constraints (`role_source`, `evidence_level`, `allow_unverified_models`) and roughly twenty negative tests confirmed; `grep model_catalog profiles/` returns no hits, so the duplicate-catalog charge is about the projector tables, not the profiles.
- Primitive divergence confirmed across profiles (`spawn_agent`, `task`, `spawn_subagent`, `invoke_subagent/define_subagent`), with `codex agent.cancel` and `omp agent.message` declared gaps.
- Projector label divergence measured directly, correcting an earlier bad probe: `generate_codex_models` has 19 labels, 5 exact canonical matches (`bug-fix`, `hardest-tasks`, `hillclimb`, `independent-verifier`, `perf-issue`), 14 non-canonical, 17 of 22 canonical roles absent. `generate_antigravity_models` has 17 labels, 3 exact matches, 14 non-canonical, 19 of 22 absent. Recorded in #440.

## Gap this record does not close

Every arm here ran on the harness default model family. The rubric of gate #436 asks for candidates plus a no-change control and independent reviewers; the candidates and control are satisfied, and the cross-judge re-verified claims independently, but model-family independence is not. That remains a stated gap, not a pass.
