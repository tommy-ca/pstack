# Arena record: driver-revision recipe for the verifier self-hash (issue #444, lane-B row F2)

Trunk: `f3fb816`. Worktree: `.worktrees/arena/f2-seam`. Harness: `arena/f2/f2_arena.py`
(plus `results.json`, `pins.json`, `suite-*.json`, `migrate-B.json`, `unparse.json` and
`c_registry.json` written beside this file).

Scope: how `compute_surface_revisions` (`scripts/portability_schema.py:601-735`) should fingerprint
the verifier and its sibling drivers, so a byte edit that cannot move a verdict stops costing a
multi-host re-proof. No fix is implemented on trunk; this record is input for #444.

Prior art: `docs/research/arena-surface-revision-2026-10-16.md` (trunk `419fb36`) ran the same
question on `portability_schema.py` alone and recommended a behavioural projection over a split
module. That record's candidates were not the three compared here, and it measured no runnable
CLI-level flip. This pass re-frames the seam as the wave-11 note asked for ("a behavior-bearing
core, not the whole wrapper") and measures it end to end.

## The defect, reproduced end to end

`compute_surface_revisions` step 8 (`:698-710`) hashes the bytes of eight named scripts, including
`verify-portable.py` itself, plus every `scripts/drivers/**/*.py`; step 9 does the same for three
packaging scripts and step 10 for `scan-host-boundary.py`. `PLANE_SURFACE_DEPENDENCIES` (`:462`)
puts `driver_revision` in the `adapter` and `runtime` planes, and `package_driver_revision` in
`package`.

Reproduced on this trunk in a disposable copy: appending

```
    # F2 comment probe: a comment that cannot move a verdict.
```

inside `if __name__ == "__main__":` of `scripts/verify-portable.py` and running
`verify-portable.py check-staleness --host all` flips **5 of 6 hosts** to
`REGENERATE` with `adapter, runtime` stale on each, exit 1:

```
Host: grok         | Status: REGENERATE | Stale Planes: adapter, runtime
   - [adapter] driver_revision mismatch (receipt=fc217de3..., current=2c7e2691...)
   - [runtime] driver_revision mismatch (receipt=fc217de3..., current=2c7e2691...)
   ... codex, omp, opencode, antigravity identical ...
Host: droid        | Status: FRESH      | Stale Planes: None
```

`droid` is exempt because it is a `candidate` host with no durable `droid-receipt.json`; the five
`packaged` hosts carry durable receipts whose `verified`/`supported` claims hard-fail on the
mismatch. Five hosts' worth of live re-proof is the price of one comment.

Against the filed report (#444 comment 6225805375, trunk `d61a2fd`): "verifier hashes its own
source (one comment stales all six hosts, 2 tracked tests fail)". Reproduced here as **five**
durable-receipt hosts (droid contributes no durable receipt, so it cannot go stale) and **two test
functions** — `test_driver_source_change_invalidates_adapter_and_runtime`, whose nine parameters
each fail, and `test_candidate_table_matches_the_live_run` — ten cases in all. The same comment
asks to "decide hash scoping (function-level scope or explicit dependency list)"; the selection in
this record is that decision, and it rejects the explicit dependency list on measured evidence.

## Candidates and their measured ledgers

All four recipes are implemented in `f2_arena.py` over the trunk's exact input sets and measured on
disposable copies of this tree. `B+` is the grafted result, carried through the whole battery so the
graft is measured rather than asserted.

* **A — whole-file byte hash.** Trunk, unchanged: `sha256(name + read_bytes())` per file.
* **B — behavior-bearing core.** Per file, `sha256(name + ast.unparse(strip_docstrings(ast.parse(src))))`:
  comments, docstrings, formatting and blank lines drop out; everything the AST can carry
  (operators, literals, names, defaults, branches, decorators) stays. A file that will not parse
  raises `RecipeError` instead of silently falling back to bytes.
* **C — explicit dependency list.** A declared registry of each file's public top-level surfaces
  (`c_registry.json`, built once from this tree) is hashed symbol by symbol, each symbol's source
  normalized as in B. A declared symbol that disappears, or a public symbol that appears without
  being declared, raises.
* **B+ — B plus the declared byte complement.** The two modules that consume their own module
  docstring at runtime (`canonical-index.py`, `verify-portable.py`, both
  `argparse.ArgumentParser(description=__doc__)`) contribute that docstring raw.

### Mutation battery — `python3 arena/f2/f2_arena.py compare`

15 mutants applied to the real files (six neutral, two observable, seven behavior-bearing; each
anchor asserted to occur exactly once), `MOVED` = the
revision moved, `SAME` = identical, `REFUSED` = recipe raised.

| mutant | class | A | B | B+ | C |
| --- | --- | --- | --- | --- | --- |
| `b1-reason-string` (`mismatch` → `differs`) | behavior | MOVED | MOVED | MOVED | MOVED |
| `b2-plane-name` (`runtime` → `runtime_x`) | behavior | MOVED | MOVED | MOVED | MOVED |
| `b3-operator` (`!=` → `==` in `evaluate_plane_staleness`) | behavior | MOVED | MOVED | MOVED | MOVED |
| `b4-public-rename` (`compute_surface_revisions` → `_v2`) | behavior | MOVED | MOVED | MOVED | **REFUSED** |
| `b5-new-public-fn` (new public top-level function) | behavior | MOVED | MOVED | MOVED | **REFUSED** |
| `b6-private-body-edit` (`_is_observed_settlement` plane test) | behavior | MOVED | MOVED | MOVED | **SAME** |
| `b7-const-value` (`"driver_revision"` → `"driver_revision_v2"`) | behavior | MOVED | MOVED | MOVED | MOVED |
| `n1-comment-eof` | neutral | MOVED | SAME | SAME | SAME |
| `n2-comment-body` | neutral | MOVED | SAME | SAME | SAME |
| `n4-comment-two` | neutral | MOVED | SAME | SAME | SAME |
| `n5-whitespace` | neutral | MOVED | SAME | SAME | SAME |
| `n6-local-rename` (new local + alias) | neutral | MOVED | MOVED | MOVED | MOVED |
| `n7-docstring-func` | neutral | MOVED | SAME | SAME | SAME |
| `n3-docstring-module` (argparse-consumed) | observable | MOVED | **SAME** | MOVED | **SAME** |
| `o1-docstring-module-consumed` (argparse-consumed) | observable | MOVED | **SAME** | MOVED | **SAME** |

| recipe | neutral edits that staled (cost) | observable edits survived | behavior edits missed (risk) | behavior edits refused loudly |
| --- | --- | --- | --- | --- |
| A | **6 / 6** | 0 | 0 | 0 |
| B | 1 / 6 | **2** | 0 | 0 |
| B+ | 1 / 6 | 0 | 0 | 0 |
| C | 1 / 6 | **2** | **1** (`b6-private-body-edit`) | 2 |

### Steady state at the CLI — `python3 arena/f2/f2_arena.py steady <recipe>`

The battery measures revisions; this measures what a host actually sees. Each recipe: restamp the
five durable receipts and `index.json` once, then edit, then re-run `check-staleness --host all`.

| recipe | hosts that REGENERATE after a comment edit | hosts that REGENERATE after a behavior edit |
| --- | --- | --- |
| A | **5 / 6** (`adapter, runtime`) | 5 / 6 (`b3-operator`) |
| B | **0 / 6** | 5 / 6 (`b3-operator`) |
| C | **0 / 6** | **0 / 6** (`b6-private-body-edit`) |

C's second cell is the selection-deciding number: the private predicate that decides whether a
`runtime` settlement counts is not in C's declared surface set, so a behavior edit to it leaves
every host FRESH. The gate fails open, silently.

### Pins — `python3 arena/f2/f2_arena.py pins`

The harness patches a disposable copy's `compute_surface_revisions` and `_probe_scope_hash` onto
each recipe and runs the three pinned suites. Recipe A is the control and must stay green, which
checks the patch itself.

| recipe | exit | failures |
| --- | --- | --- |
| A | 0 | 0 |
| B | 1 | 9 × `test_driver_source_change_invalidates_adapter_and_runtime[...]` + `test_eval_blinded_pstack_dsh_candidate.py::...::test_candidate_table_matches_the_live_run` |
| B+ | 1 | the same 10 |
| C | 1 | the same 10 |

`test_driver_source_change_invalidates_adapter_and_runtime` (`tests/test_evidence_durability.py:421`)
appends `b"\n# Changed verification behavior.\n"` — a comment — and asserts `driver_revision` moves.
That test pins the defect, not the invariant, and must be rewritten to append a behavior-bearing
edit instead. `test_unrelated_docs_change_does_not_change_driver_revision` passes under all three
recipes. The DSH failure is the second instance below.

### Interpreters — unparse stability

`ast.unparse` output is byte-identical across `python3.12.15`, `python3.13.16` and `python3.14.8`
for the 20 files in the driver/package scope (probe: `python3 arena/f2/f2_arena.py unparse`,
`arena/f2/unparse.json`; all hashes equal on all three). B and C are
therefore hermetic across the interpreter versions this repo's `__pycache__` already shows in use
(`cpython-312` and `cpython-314`), which was the sharpest risk against an AST-based recipe.

## Scoring

Rubric frozen before the battery ran: five criteria, equal weight, 1 to 5, maximum 25.

Footprint as implemented in the harness: B is a 21-line normalizer (`_strip_docstrings` 12,
`core_bytes` 9) plus three call sites inside `compute_surface_revisions`; B+ adds an 11-line
complement helper and a two-entry list. C needs the same normalizer plus a persisted registry
(`c_registry.json` covers 12 files) and its refusal paths.

1. Integrity: any edit that can change validation outcomes still invalidates the affected claims.
2. Regeneration cost: comment-only, whitespace and docstring edits require zero live re-proof.
3. Minimal diff, no new concept: no second hash system, no registry to maintain, no new receipt field.
4. Offline-testable in both directions.
5. Honesty: state any weakening exactly.

| Criterion | A | B | B+ | C |
| --- | --- | --- | --- | --- |
| 1. Integrity | 5 | 4 | 5 | 3 |
| 2. Regeneration cost | 1 | 5 | 5 | 5 |
| 3. Minimal diff, no new concept | 5 | 4 | 4 | 2 |
| 4. Offline-testable, both directions | 5 | 5 | 5 | 4 |
| 5. Honesty | 5 | 5 | 5 | 5 |
| **Total** | **21** | **23** | **24** | **19** |

B loses one integrity point only for the two observable survivals, both `__doc__`-consumed module
docstrings. No test, receipt or claim in this tree reads `verify-portable.py`'s published
description (`grep -rn -- "--help" tests/` returns two hits: an unrelated `omp task ... --help`
command string at `tests/test_evidence_durability.py:850` and a scaffolded skill template at
`tests/test_scaffold_verification_skill.py:34`), so the survival is observable but not
claim-affecting; it is recorded rather than waved away. C loses two integrity points to a
measured fail-open and two more to `REFUSED` on a public rename, which turns a free refactor into a
hard error and pushes ordinary maintenance back into the "registry edit" path.

## Selection and graft

**Base: B. Graft: C's fail-closed declaration discipline, reshaped into B's grammar → B+.**

A is rejected: it is the defect, measured at 5/6 hosts per comment.

C is rejected as a base on the CLI number: a behavior edit to `_is_observed_settlement`'s body
stales 0 of 6 hosts. An explicit surface list only protects what the maintainer remembered to list,
and the thing it forgets is exactly the private helper that decides a verdict. Its coverage
assertion is good discipline wired to the wrong granularity.

The graft keeps C's idea — silence must be a failure — without its registry:

* the complement list is explicit, two entries, and hashed raw: the module docstrings that
  `argparse` publishes at runtime;
* every file in scope must parse; a parse failure raises instead of quietly degrading to a byte
  hash, so a recipe that stops seeing a file is loud;
* the driver file set stays the trunk's own (eight named scripts plus the `drivers/` glob), so a
  new driver file still joins the fingerprint automatically and nothing needs declaring to be
  covered.

That closes both observable survivals (measured: `B+` observable-survived 0) with two names and one
assertion, and keeps B's zero-cost comments and its 5/6 behavior-edit sensitivity at the CLI. If the
owner rules `--help` text out of the gate's scope, the graft can be dropped and B alone (23) is the
answer; the measurement is the same either way.

Rejected sub-variants, not measured, recorded so they are not re-proposed blind: hashing
`ast.dump()` instead of `ast.unparse` (fatter, ordering-sensitive, no measured benefit), and
byte-falling-back on parse failure (silent, and the fail-open shape C was rejected for).

## Full offline suite

`python3 arena/f2/f2_arena.py suite <recipe>` runs `pytest -q tests/` in a patched disposable copy.
Recipe A is an unpatched copy and is the control for pre-existing failures.

| run | result |
| --- | --- |
| A (control) | 5 failed, 968 passed, 11 skipped in 295.52s (0:04:55) |
| B | 37 failed, 936 passed, 11 skipped in 210.69s (0:03:30) |
| B+ (selected) | 37 failed, 936 passed, 11 skipped in 219.22s (0:03:39) |

Control failures (5) are pre-existing and unrelated to the recipe: the two DSH baseline-corpus drift
assertions, `test_sync_remote_cache_is_primary_checkout` (worktree/primary-checkout layout), and the
`antigravity`/`droid` live-host probes. Recipe B adds **32**: 31 in
`tests/test_evidence_durability.py` and the DSH `test_candidate_table_matches_the_live_run`.

Most of the 31 are the one-time migration, not a recipe defect: every durability artifact in
`.audit/evidence/` was recorded under the whole-file recipe, so the first run after any recipe
change reads `driver_revision mismatch` everywhere. `python3 arena/f2/f2_arena.py migrate B`
separates the two populations. In an isolated run of that file the count is 15 (the full-suite 31
carries order-dependent state from earlier files sharing the copy's evidence dir), and after one
restamp of the 5 durable receipts **and `.audit/evidence/index.json`** it drops to **9** — exactly
the nine parameters of `test_driver_source_change_invalidates_adapter_and_runtime`. That test
appends a *comment* and asserts `driver_revision` moves, so it pins the defect rather than the
invariant; rewriting it to append a behavior-bearing edit is part of the fix, not of the migration.

The migration surface is therefore: 5 durable receipts + `index.json` + the DSH candidate fixture.
Nothing else changes. B+ fails the same set as B (the complement changes two module docstrings' raw
bytes, which no test in the suite edits), so the graft adds no suite cost beyond the migration.

## Known gaps in the selected design

* **Neutral refactors are not free under any recipe.** `n6-local-rename` moves A, B, B+ and C: a new
  local and an alias inside a hashed body is an AST change. "Free" covers comments, whitespace and
  docstrings, not statement-level refactoring. Stated rather than implied.
* **`__doc__` is a declared complement, not a discovered one.** A module that starts consuming its
  docstring later is not caught by the two-entry list. The parse assertion does not cover it.
* **Migration is a one-time re-proof.** The five durable receipts and `.audit/evidence/index.json`
  were recorded under the whole-file recipe; the first run after any recipe change shows
  `driver_revision`/`package_driver_revision`/`boundary_driver_revision` mismatch everywhere until
  both are restamped (measured by `steady`: all FRESH before the comment edit from a restamped
  state; measured by `migrate B`: 15 → 9 failures in `tests/test_evidence_durability.py`). Per-edit
  cost is what drops to zero, not the one-time migration.

## Follow-ups (out of scope here)

1. **`_probe_scope_hash` (`scripts/eval_blinded_pstack.py:256`) is a second instance of the same
   property.** It hashes whole-file bytes of `verify-portable.py`, `route_resolver.py`,
   `decision_adapter.py`, `eval_blinded_pstack.py` plus the skills tree and pins the value in
   `tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json`. A comment in any of those four
   files invalidates a frozen eval table; measured here as the one DSH suite failure beyond the
   durability file (`test_candidate_table_matches_the_live_run`). Same recipe applies; the fixture
   needs one re-record, which is the remaining migration item after 5 receipts + `index.json`.
2. **`skills_tree_hash` hashes all of `skills/` byte-wise** and sits in the `runtime` plane, so a
   comment under `skills/` stales runtime for every host with no schema involvement. Same property,
   wider surface, separate decision (also named in the `419fb36` record).
3. **Rewrite the pin.** `test_driver_source_change_invalidates_adapter_and_runtime` must assert that
   a behavior-bearing edit stales and that the comment edit does not — the nine-parameter form
   currently asserts the defect.
4. **#495 partial-write residue** is unaffected by any recipe here; it stays open on its own terms.

## Artifacts

| file | what |
| --- | --- |
| `arena/f2/f2_arena.py` | recipes A/B/B+/C, the 15-mutant battery, per-host plane flip, pins, steady-state CLI, full-suite mode, `demo` self-check |
| `arena/f2/results.json` | battery + summary + comment-edit plane map at `f3fb816` |
| `arena/f2/pins.json` | per-recipe pinned-suite failures |
| `arena/f2/suite-A.json`, `suite-B.json`, `suite-B+.json` | control, B and B+ full-offline-suite failures |
| `arena/f2/migrate-B.json` | recipe-change breakage split into restamp vs pin rewrite |
| `arena/f2/unparse.json` | `ast.unparse` hashes for 20 files across python 3.12/3.13/3.14 |
| `arena/f2/c_registry.json` | C's declared public surface list, built from this tree |

Reproduce: `python3 arena/f2/f2_arena.py demo | compare | pins | unparse | steady A|B|C | migrate B | suite A|B|B+`.
`demo` re-derives every headline number in this record and fails if one moved.
