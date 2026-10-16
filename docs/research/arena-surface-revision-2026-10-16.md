# Arena record: validator-module revision and the freshness gate (issue #444)

Trunk: `419fb36`. Scope: how `driver_revision` should treat `scripts/portability_schema.py`, the module that interprets evidence, so that a text-only edit to the interpreter stops costing a live multi-host re-proof.

Status: **base selected, A with C's coverage-registry grafted in.** One claim-affecting gap remains in the base and is named below. The design is not implemented here; this record is input for issue #444.

Candidate designs, their measured ledgers and their rejected alternatives are committed beside this file at `candidate-a.md`, `candidate-b.md` and `candidate-c.md`.

## The defect, reproduced on this trunk

`compute_surface_revisions` (`scripts/portability_schema.py:601-735`) hashes the bytes of seven named scripts including `portability_schema.py` itself (`:698`) plus `scripts/drivers/**/*.py`, and stores the result as `driver_revision`. `PLANE_SURFACE_DEPENDENCIES` (`:462`) puts `driver_revision` in the `adapter` and `runtime` planes, so `check_evidence_durability` (`:945`) turns a mismatch into a hard failure for any `verified` or `supported` claim.

Appending one comment to `scripts/portability_schema.py` changes `driver_revision` and flips `verify-portable.py check-evidence` from exit 0 to exit 1 `driver_revision mismatch` for grok, codex, opencode and antigravity. The staleness hard-fail is scoped to `verified` and `supported` (`:993`), so OMP (packaged) and droid (candidate) stay green; repair is four hosts, not six. The identical comment on `scripts/model_role_resolver.py` or `scripts/model_role_policy.py` changes nothing, because those files are not in the input set.

The interpreter is not the only surface with this property, and it is not the most-edited one. Comments anywhere under `skills/` also stale the runtime plane, because `skills_tree_hash` hashes that whole tree byte-wise (`:623-637`) and sits in the runtime plane (`:478`); a one-line comment under `skills/` was measured to produce the same forced re-proof with no schema involvement. Commit counts put `scripts/portability_schema.py` third among the hashed drivers at 20 commits, behind `scripts/verify-harness.py` at 31 and `scripts/verify-portable.py` at 29. Its last edit was `56c102a` (#387), 62 commits before this trunk. So this arena fixes one instance of a property the tree holds in at least two places, and the larger instance is left for a separate decision.

## Candidates and what each measured

Three designs were produced and read end to end. A and C each carried a runnable measurement harness; B was derived by inspection.

**A, split module with decision projection.** Move the hashing machinery to a new `scripts/surface_revisions.py` and stop hashing the interpreter's bytes. `driver_revision` becomes a digest of driver bytes plus three behavioural inputs: the values of the declarative rule constants, the 32 branches of the settlement-admission predicate, and nine declared gate probes. Measured: 15 of 17 claim-affecting mutations move the fingerprint and stale adapter and runtime, the two non-movers being outcome-neutral on every declared configuration; five neutral edits (comment, type hint, refactor, message reword, helper extraction) leave it identical. Migration to the new recipe is proven offline against all five stored receipts.

**B, separate `validator_revision`.** Keep byte hashing, remove `portability_schema.py` from `driver_revision`, and add a new field that gates only scenario-pinned static claims, never a plane. Derived by inspection, not measured: `validator_revision` appears in no `PLANE_SURFACE_DEPENDENCIES` tuple, so no plane can be staled by an interpreter edit. Fully neutral for four hosts in that reading; OMP needs one offline restamp of a static pin.

**C, semantic-surface digest.** Replace only the interpreter's byte contribution with a digest over twenty declared vocabularies plus the outcomes of the admission, staleness and gate rules across a 294,410-row decision corpus. Measured: six of six neutral edits stay identical, eleven of eleven semantic mutations are caught, and a coverage assertion hard-errors when a covered public symbol is renamed, added or removed.

## Scoring

The frozen rubric is five criteria, equal weight, scored 1 to 5, maximum 25. It was frozen before any candidate ran.

1. Integrity preserved: any edit that can change validation outcomes still invalidates the affected live claims.
2. Regeneration cost: comment-only, refactor, or type-hint edits require zero live re-proof.
3. Minimal diff, no new concept: no second hash system, no new abstraction layer, no new receipt kind.
4. Offline-testable: an offline test proves both directions.
5. Honesty: state any weakening exactly rather than papering over it.

| Criterion | A | B | C |
| --- | --- | --- | --- |
| 1. Integrity | 4 | 1 | 5 |
| 2. Regeneration cost | 5 | 4 | 5 |
| 3. Minimal diff, no new concept | 4 | 3 | 2 |
| 4. Offline-testable, both directions | 5 | 2 | 5 |
| 5. Honesty | 5 | 5 | 5 |
| **Total (max 25)** | **23** | **15** | **22** |

B fails criterion 1 by construction, and its own record states this plainly: a byte edit to the interpreter invalidates no live claim, and a widening edit leaves CI green with no required regeneration. C scores highest on integrity because its corpus is the most complete of the three, but it pays twice on criterion 3, adding both a second hash system and a new abstraction layer.

## The selection, and the correction it rests on

A is the base, with C's coverage assertion grafted in.

The first draft of this record declined to select a winner, on the ground that A failed criterion 1 on two of its seventeen mutations. That reading was wrong. Criterion 1 is scoped to edits that *can change validation outcomes*, and `candidate-a.md` §6.1 measures those two mutations as outcome-neutral on every declared configuration: the derived-state ceiling refuses the same shapes first, so no decision moves either way. An edit that cannot move a decision is outside the criterion's scope by its own wording, not a failure of it.

A's genuine criterion-1 gap is the other residual its §10 names, and it is narrower than the first draft claimed. Validator behaviour on a configuration that is neither a rule value nor a declared probe is invisible to the fingerprint. A new harness, a new plane verdict, or a new scenario shape would exercise such a configuration, and an edit confined to it would change outcomes without invalidating anything. That is a real hole, it is bounded to configurations nobody has declared yet, and `EVIDENCE_GATE_PROBES` is the declared extension point that closes it one entry at a time.

The two-question framing survives, as the boundary of the recommendation rather than a refusal to make one. If the freshness gate exists to answer "is this claim still true", a behavioural projection answers it for every configuration the repo declares. If the gate exists to answer "has anything in the interpretation path changed since this receipt was minted", only byte hashing answers it, and the multi-host re-proof cost is the price of the question. This record recommends A on the first reading and names the second as the owner's call, because that part is a product decision rather than an experimental one.

## What the graft buys and what it does not

C's coverage assertion fails closed when a covered public symbol is renamed, added or removed. That is worth importing: today such a symbol can drift out of any projection silently.

Its reach is narrower than the first draft of this record claimed. `candidate-c.md` §4 class 1 states the limit in its own words: the assertion fires on new symbols only. It does not catch prose changes, value-neutral edits, or a rewrite of the extractor itself, and C's threat model is explicitly accidental staleness-blindness rather than an adversary who rewrites the extractor together with the receipts. Grafting it in also imports C's class-5 price: once the registry is present, renaming or relocating a public symbol is no longer a neutral refactor, because it trips the assertion. Criterion 2's "free refactors" therefore hold for private helpers and stop holding for public renames.

## Known gaps in the selected design

A's §10 names two residuals and both are carried forward. Behaviour exercised by no rule value and no declared probe is invisible, as above. Diagnostics are invisible by design, because criterion 2 requires that a reworded refusal stay neutral; the assertion the projection protects is "the same claims are accepted and refused", not "the same error text appears".

B's coverage reduction is real and is not part of this selection: removing `scripts/portability_schema.py` from the `tests/test_evidence_durability.py` parametrize list narrows what that test asserts, and A replaces that entry with its two-direction tests rather than deleting the coverage.

One candidate ledger does not add up. `candidate-c.md` §5 states a headline corpus of 294,410 rows, which the prototype reproduces, but its breakdown enumerates components summing to 271,028. The total is measured; the decomposition is not, and it stands uncorrected in the candidate file.

## Artifacts and evidence

Candidate designs sit beside this record. Cross-judge scoring is the table above; the rubric's weights are equal and stated, so the totals are reconstructable from the per-criterion scores. The measurement harnesses (`battery.py`, `migrate-demo.py`, the digest prototypes) ran in a scratch directory and are not committed; the candidate files carry their measured ledgers.

## Not established

No implementation was written or tested, so every diff size, test name and symbol in the candidate files is a design claim rather than a verified one. The candidates, the cross-judge and the adversarial review all ran in a single model family, so this is not a multi-family independence result; gates #436 and #445 remain open on that basis. The claim that criterion 1 is unsatisfiable alongside criterion 2 for any behavioural projection is an inference from two designs rather than a proof, and is marked as such here rather than asserted.
