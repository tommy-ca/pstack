# Arena record: validator-module revision and the freshness gate (issue #444)

Trunk: `419fb36`. Scope: how `driver_revision` should treat `scripts/portability_schema.py`, the module that interprets evidence, so that a text-only edit to the interpreter stops costing a live six-host re-proof.

Status: **no winner selected.** Two candidates failed the frozen rubric's hard criterion, and the criterion is unsatisfiable alongside the cost criterion it is scored against. The three designs, their measured behaviour, and the decision only the owner can make are recorded below. Nothing here is implemented.

## The defect, reproduced on this trunk

`compute_surface_revisions` (`scripts/portability_schema.py:601-734`) hashes the bytes of seven named scripts including `portability_schema.py` itself (`:698`) plus `scripts/drivers/**/*.py`, and stores the result as `driver_revision`. `PLANE_SURFACE_DEPENDENCIES` (`:462`) puts `driver_revision` in the `adapter` and `runtime` planes, so `check_evidence_durability` (`:945`) turns a mismatch into a hard failure for any `verified` or `supported` claim.

The consequence is measured. Appending one comment to `scripts/portability_schema.py` changes `driver_revision` and flips `verify-portable.py check-evidence --host grok` from exit 0 to exit 1 `driver_revision mismatch`. Repair requires live runs on four hosts plus OMP under `PSTACK_RUN_OMP_LIVE=1`. The identical comment on `scripts/model_role_resolver.py` or `scripts/model_role_policy.py` changes nothing, because those files are not in the input set. So the interpreter of evidence is pinned by bytes exactly like the producers of evidence, and this program has edited that interpreter repeatedly (#456, #465, #468).

## The frozen rubric

1. Integrity preserved: any edit that can change validation outcomes still invalidates the affected live claims.
2. Regeneration cost: comment-only, refactor, or type-hint edits require zero live re-proof.
3. Minimal diff, no new concept: no second hash system, no new abstraction layer, no new receipt kind.
4. Offline-testable: an offline test proves both directions.
5. Honesty: state any weakening exactly rather than papering over it.

## Candidates and what each measured

Three designs were produced and read end to end.

**A, split module with decision projection.** Move the hashing machinery to a new `scripts/surface_revisions.py` and stop hashing the interpreter's bytes. `driver_revision` becomes a digest of driver bytes plus three behavioural inputs: the values of the declarative rule constants, the 32 branches of the settlement-admission predicate, and nine declared gate probes. Measured: 15 of 17 claim-affecting mutations move the fingerprint and stale adapter and runtime; four hygiene mutations (comment, annotation, refactor, reword) leave it identical. Migration to the new recipe is proven offline against all five stored receipts.

**B, separate `validator_revision`.** Keep byte hashing, remove `portability_schema.py` from `driver_revision`, and add a new field that gates only scenario-pinned static claims, never a plane. Measured: fully neutral for four hosts, one offline restamp for OMP. This is the smallest diff and the most legible trade.

**C, semantic-surface digest.** Replace only the interpreter's byte contribution with a digest over twenty declared vocabularies plus the outcomes of the admission, staleness and gate rules across an exhaustive 294,410-row decision corpus. Measured: six of six hygiene mutations neutral, eleven of eleven semantic mutations caught, plus a fail-closed coverage assertion that hard-errors when a covered public symbol is renamed or added.

## Why no winner was selected

Criterion 1's literal bar is unmet by every candidate except the status quo, and the status quo is the defect.

B fails criterion 1 by construction: a byte edit to the interpreter invalidates no live claim, and a widening edit leaves CI green with no required regeneration. Its own record states this plainly.

A fails criterion 1 on two of its seventeen mutations. `gate:drop-refs-guard` and `gate:drop-stale-details` are outcome-neutral across every declared configuration because the derived-state ceiling refuses the same shapes first, so no decision moves and the fingerprint stays identical. Validator behaviour that neither a rule value nor a declared probe exercises is likewise invisible.

C fails criterion 1 outside its finite corpus. Its own record names five bounded escape classes, including value axes inside existing validators that the corpus does not enumerate, and it states its threat model as guarding accidental staleness-blindness rather than an adversary who rewrites the extractor and the receipts together.

The scores still separate the candidates, 23 for A and 22 for C against 15 for B, but a total cannot waive a hard criterion. The deeper finding is that criteria 1 and 2 are in tension by construction. Hashing bytes satisfies criterion 1 and fails criterion 2. Projecting behaviour satisfies criterion 2 and cannot satisfy criterion 1 completely, because a behavioural projection is only as complete as the corpus it enumerates. Any design that claims both is overclaiming, which is why the arena stopped rather than picking the higher total.

## What the arena does settle

Three things are now measured rather than assumed, and they hold whichever direction the owner takes.

The cost is real and localised to this one file. The interpreter is the only claim-relevant surface whose text edits currently force live re-proofs, and it is the most-edited file in this program.

A behavioural projection can convert a silent integrity hole into a loud error. C's coverage registry, which fails closed when a covered public symbol is renamed, added or removed, is the one mechanism among the three candidates that turns "this edit is invisible" into a build failure. Grafting that onto A's smaller surface is the closest any candidate comes to criterion 1 without byte hashing.

Outcome-neutral edits exist and can be named. A's residual enumerates two of them rather than hiding them, which means the trade can be stated as a finite, auditable list instead of an unknown.

## The decision this needs

Two options are defensible, and they differ in what the owner is willing to trade.

Keep byte hashing, which preserves criterion 1 exactly and keeps the live re-proof cost. This is the status quo, and the only work it needs is a note in the freshness documentation that the interpreter's text is claim-pinned on purpose.

Adopt A with C's coverage registry grafted in, which buys free text and refactor edits plus one offline migration, and pays with a named, finite list of outcome-neutral edits that no longer invalidate anything. The registry keeps new blind spots from appearing silently, but it cannot close the two already known.

The recorded recommendation boundary is this. If the freshness gate exists to answer "is this claim still true", a behavioural projection is adequate and the two named holes are acceptable, because an edit that changes no accept or reject decision changes no claim's truth. If the gate exists to answer "has anything in the interpretation path changed since this receipt was minted", only byte hashing answers it, and the live re-proof cost is the price of the question. That is a product decision about which question the gate serves, and no experiment in this arena settles it.

## Artifacts

Candidate designs, each with its measured ledger and rejected alternatives, are recorded at `candidate-a.md`, `candidate-b.md` and `candidate-c.md` alongside this file's source run. Cross-judge scoring, criterion by criterion with citations, is part of the same run.

This record is design input for issue #444. No requirement, schema, receipt or gate changed here, and no candidate is implemented.

## Not established

No implementation was written or tested, so every diff size, test name and symbol in the candidate files is a design claim rather than a verified one. The cross-judge and candidate runners ran in a single model family, so this is not a multi-family independence result. Gate #436 and gate #445 remain open on that basis.
