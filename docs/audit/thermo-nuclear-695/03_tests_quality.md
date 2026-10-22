# Tests changed by the merged train — detail report

Lane: tests quality. Reviewer: TestsQuality.
Revisions (all findings rest on these): BASE `ef34052`, main HEAD `1002590`, PR heads `e18ba48`
(#717), `4bfddd9` (#718), `9c4b680` (#719). Diff reviewed: `git diff ef34052 1002590 -- tests/`
(9 files, +267/−69). Interpreter: `.venv/bin/python` (3.14). Nothing in the repo was edited,
staged, or committed; probes live under `/tmp/thermo-695/probe/`.

Scope note: the probe-scope fixture `tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json`
was checked and is clean. Its `probe_scope_hash` (`8c31c0ca…`) equals `_probe_scope_hash(HEAD)`
computed live, its `pstack_revision` `9c27c63` has a byte-identical `skills/` tree to HEAD
(`git diff --stat 9c27c63 HEAD -- skills` is empty), and its timing fields are explicitly popped
by `tests/test_eval_blinded_pstack_dsh_candidate.py:90-97` before comparison. No finding.

## BLOCKER — the refusal guard rejects a live-observed FAIL, so a real regression can no longer be recorded

The train adds a guard in `scripts/evidence_index.py:145-158`: when the durable receipt carries a
preservable settlement for a scenario id and the current receipt's row for that id is not
preservable, it `sys.exit`s instead of writing. `_is_preservable_settlement`
(`scripts/evidence_durability.py:29-32`) is built on `_is_observed_settlement`
(`scripts/portability_types.py:560-571`), which requires `verdict == "PASS"`. So "the current row
is not a passing live settlement" is treated as "the current run has no evidence", and the guard
cannot tell a *static restamp* (must be refused) from a *live run that observed a failure* (must be
recorded).

Both new tests construct only the static case. `tests/test_evidence_settlement.py:333-343`
(`_proof_bar_refresh(..., verdict="FAIL")`) and `tests/test_evidence_index_resilience.py:360-373`
(same helper, same verdict) append `_omp_spawn_scenario("static", verdict=verdict)`
(`tests/evidence_test_helpers.py:207-222`), i.e. `evidence_level="static"`. The train's other
refusal test, `tests/test_evidence_durability.py:589-631`, monkeypatches `doctor` with static stub
rows, so it is the same shape. No changed test builds an `observed_live`/`offline` failing row.

That row is what production emits. `scripts/drivers/omp.py:419-431` returns
`id="runtime-child-spawn-omp"`, `verdict="FAIL"` (or `"BLOCKED"`), `evidence_level="offline"` for a
live gate run whose child did not settle, and `scripts/verify-portable.py:535-536` writes that
receipt with `update_durable=True` for a `verified` claim. I ran that exact shape against the
helpers (`/tmp/thermo-695/probe/live_fail_probe.py`):

    REFUSED live FAIL: REFUSING to overwrite the durable receipt at …/omp-receipt.json
    unchanged: True

The operator is told "Re-run live proof with `PSTACK_RUN_OMP_LIVE=1 …`" — which is the command that
just failed, and re-running it refuses again. The consequence is user-observable: after a genuine
omp regression, `.audit/evidence/omp-receipt.json` keeps its stale `runtime: PASS` and
`derive_support_state` keeps returning `supported`, while the failing evidence exists only in the
run directory. The pre-train assertions that pinned the opposite (`planes["runtime"] == "FAIL"`,
`evidence_level == "static"`) were deleted from `tests/test_evidence_settlement.py:321-343` in this
same train, so nothing now holds the line.

Reachability searched: `_is_preservable_settlement` (definition + this guard), the two live driver
failure branches in `scripts/drivers/omp.py`, `PortableVerifier.evidence`
(`scripts/verify-portable.py:462-470`), every `update_durable=` call site
(`scripts/verify-portable.py:510,518,535,555`), the four refusal tests, and the CLI prescription
strings in `docs/research/arena-495-index-repair-2026-10-18.md`. I could not rule out that another
writer bypasses `write_verification_evidence`; nothing in `scripts/` does.

Remedy (behavior preserved, one branch): refuse only when the current row shows no live attempt —
`current.evidence_level == "static"` (or a run-kind flag threaded from `refresh-static`) — and let
`offline`/`observed_live` non-passing rows through, which is exactly the pre-train contract.
Smallest test that fails today and passes after:
`ScenarioResult(id="runtime-child-spawn-omp", evidence_level="offline", verdict="FAIL")` against the
`_omp_live_root` durable live row must write and leave `planes["runtime"] == "FAIL"`.
Net obligation removed: the guard stops needing to infer "was this a live run?" from a
passing-settlement predicate it borrowed from the preservation path.

## MAJOR — a test whose name asserts the behaviour the train removed, and the support-state consequence lost its pin

`tests/test_evidence_settlement.py:316` is still named
`test_durable_refresh_drops_a_settlement_once_the_runtime_surface_moved`, but the body now asserts
`REFUSING to overwrite the durable receipt`. The name states the deleted behaviour. I ran the
moved-surface case (`/tmp/thermo-695/probe/static_pass_probe.py`): a static refresh after
`driver_revision` moved is REFUSED, where pre-train it downgraded the row to `static`, set
`planes["runtime"] = "UNTESTED"`, and `derive_support_state(...) == "packaged"`. The two deleted
`derive_support_state` assertions were the only pins on "a stale claim stops saying verified".

User-observable: `refresh-static --host all` — the repair command documented in
`docs/research/arena-495-index-repair-2026-10-18.md:280-281` and repeated in the receipt/index
refusal text — now exits 1 on any tree where the omp surface moved, with a prescription that loops.
Reachability searched: `refresh-static` callers in docs/CI, `preserve_observed_settlements`
(`scripts/evidence_durability.py:35-52`), `derive_support_state` consumers. Remedy: rename to
`…refuses_a_static_refresh_once_the_runtime_surface_moved`, and add one assertion (or a
documented `--force` downgrade test) that the stale claim reaches `packaged`; the downgrade is the
behaviour the name promised.

## MAJOR — one guard, three tests, and the pair across files is byte-identical

`tests/test_evidence_settlement.py:333-343` and `tests/test_evidence_index_resilience.py:360-373`
are the same test: same `_omp_live_root(tmp_path)` setup, same
`_proof_bar_refresh(..., verdict="FAIL")`, same three assertions (the resilience copy adds one
precondition on `receipt.scenarios`). Canonical owner is `tests/test_evidence_index_resilience.py`
— the guard lives in `scripts/evidence_index.py`, and that file already owns the index-write refusal
matrix. Delete the settlement copy; keep `tests/test_evidence_durability.py:589` as the CLI-surface
pin (it is the only test that asserts the `PSTACK_RUN_OMP_LIVE=1` remedy string).

Related coverage hole from the same edit: `tests/test_evidence_durability.py:491-580` switched its
host from `omp` to `grok` so the refresh would stay allowed, which is correct — but it leaves no
CLI-level test of `refresh-static --host omp` *succeeding* through the preserve branch. The
method-level `test_durable_refresh_preserves_an_unchanged_observed_settlement`
(`tests/test_evidence_settlement.py:295`) still covers it; the CLI arm does not. Remedy: parameterize
the partial-refresh test over `("grok", no-live-rows, UNTESTED)` and `("omp", live-row preserved,
PASS)` instead of hardcoding one host, so the `elif preserved` branch has a CLI pin too.

## MAJOR — the new scanner rule has no test, and the prose test that stands in for it asserts a document instead of the scanner

`scripts/scan-host-boundary.py:163-175` adds `is_host_routing_directive` /
`_affirmative_imperative` with two regexes and a negation gap. Nothing calls it from a test:
`grep -rn "is_host_routing_directive\|host routing" tests/` returns zero hits. The only new test in
that area, `tests/test_scan_host_boundary.py:149-165`, reads `skills/poteto-mode/SKILL.md` as text
and asserts substrings; it would pass with the directive rule deleted, and it would pass with the
rule broken.

The rule is in fact over-eager. Probed directly:

    'Use Grok Build as the host adapter.'   -> Grok Build host routing name   (intended)
    'Open the Grok Build docs.'             -> Grok Build host routing name   (false positive)
    "Grok Build's defaults apply."          -> None                          (intended)
    'Use one of `Grok Build` docs.'         -> Grok Build host routing name   (carve-out miss)

The docstring promises "never a mere host mention", and `_affirmative_imperative` carries a `use one
of` carve-out that cannot fire for the phrasing it was written for. `run_scan` covers
`skills/`, `schemas/`, `agents/`, `droids/` (`scripts/scan-host-boundary.py:315-320`), so a
legitimate line such as "Read the Grok Build release notes." in any shared skill now fails the gate.
Two constants added with the rule are dead: `ROUTING_IMPERATIVES` (`:154`) and
`QUOTED_PROHIBITION_CARVE_OUTS` (`:158-160`), the latter duplicated by the hardcoded tuple at
`:185-187`.

Remedy: delete the prose test, and add four `scan_file` cases — neutral mention → no violation,
bare imperative → violation, negated imperative → no violation, and the intended `use one of`
carve-out → no violation; then either fix or delete the unreachable carve-out and the two dead
constants. Net obligation removed: the rule stops being maintained blind and the prose no longer
has two owners.

## MAJOR — `test_localized_readmes_agree_on_portable_authority_and_host_scope` is a second copy of the docs, not a behaviour pin

`tests/test_architecture_documentation.py:91-125` asserts thirteen exact sentences across two
languages ("multi-harness reference port" / "多 Agent Harness 可移植参考实现", "Grok Build is one host
adapter", four headings, three caveat lines). None of these describe system behaviour: nothing a
user runs changes when README prose changes, so a failure reports "someone reworded a sentence", not
a defect. It creates a three-way lockstep: any README edit requires the matching Chinese edit *and*
this file. The train already paid that cost — the README headings were renamed to "Grok Build first
session"/"Grok Build 第一次会话" and this test now cements those exact strings as the required state,
while the same train's `test_portable_router_selects_the_active_host_not_grok` forbids Grok-scoped
prose elsewhere.

Exactly two assertions in it carry drift value: the host-set equality against
`pstack.package.json["host_targets"]` (catches a descriptor host added without README coverage) and
the presence of the guide path. The latter is the weaker half of a behaviour already owned by
`test_documented_relative_links_resolve_within_repository` (`:65-76`), which resolves relative links
but only scans `_doc()`, never the READMEs. Smallest case the new test misses: delete
`docs/architecture/harness-neutral-authority-2026-10-21.md`; both READMEs still contain the path
string, the assertion passes, and a user clicks a dead link.

Remedy: keep the host-set equality, extend the existing link-resolution loop to `README.md` and
`README.zh-CN.md`, delete the twelve sentence assertions. Net obligation removed: one fewer copy of
each README paragraph that must be edited in three places.

## MINOR — a new test that requires an ambient npm CLI (#709 class)

`tests/test_verify_portable.py:301-311` (`test_doctor_resolves_openspec_from_repo_root_not_caller_cwd`)
`chdir`s to `tmp_path` and then lets `PortableVerifier.doctor` invoke the real `openspec list --json`
(`scripts/openspec_change.py:35-40`, bound to `ROOT` by `scripts/verify-portable.py:240-242`). It
therefore reads state outside the repo twice: the `openspec` binary on `PATH` (here
`~/.local/share/mise/installs/npm-fission-ai-openspec/…`, ambient) and the working tree's in-progress
change set. Proof that this is load-bearing, not incidental:

    PATH=/usr/bin:/bin .venv/bin/python -m pytest tests/test_verify_portable.py \
      -k resolves_openspec_from_repo_root   ->  1 failed  (assert False is True, doctor returned False)

The test currently passes on the vacuous arm: all three changes in `openspec list --json` report
`status: complete`, so `_active_openspec_changes(ROOT) == []` and the scenario is "No active OpenSpec
change; nothing to validate". A developer with one in-progress change gets the validating arm; a
developer without the CLI gets a red suite.

Remedy: keep the scenario-PASS assertion but make the dependency explicit — drop a six-line fake
`openspec` on `PATH` that answers `{"changes": []}` only when `cwd` is the repo root (which also
pins the repo-root binding harder than the current PASS), or monkeypatch
`verify_portable._active_openspec_changes` with a resolver that records `cwd`. Behaviour preserved:
doctor still fails from a foreign cwd.

## MINOR — docstring and doc-content assertions in the boundary-scanner test, in the wrong owner

`tests/test_scan_host_boundary.py:176-187` reads `scripts/verify-harness.py` and asserts two
docstring phrases, plus `docs/verification-test-tiers.md` and two unrelated sentences in
`skills/maintain-verification-skill/SKILL.md`. The scanner file is the wrong owner for all three
(rubric 6 — logic in the canonical layer). Worse, the doctor's actual claim surface is its stdout:
an overclaiming `print` added while the docstring stays honest passes this test, and a reworded but
equally honest docstring fails it. The maintain-skill assertions have nothing to do with host
boundaries and are unreachable from the test's name.

Remedy: move the maintain-skill/doc assertions to the doc owner test, and pin the doctor claim by
running `scripts/verify-harness.py` and asserting on its output (or delete the docstring assertion).
Behaviour preserved: the same strings the operator reads are still checked.

## MINOR — fixtures read the live source by line index

`tests/test_scan_host_boundary.py:124-137` and `:145-147` do
`(ROOT/"skills/poteto-mode/SKILL.md").read_text().splitlines()[128]` to obtain the carved sentence.
Any insertion above line 129 makes the test fail with a message about the wrong thing, and the pin
cannot catch the duplication it exists to protect: the reviewed tuple is hardcoded twice
(`scripts/scan-host-boundary.py:158-160` dead constant and `:185-187` live copy). The two
`ValueError` drift guards at `:193-197` are themselves untested — rewriting line 129 to a different
sentence with one token produces an uncaught `ValueError` out of `scan_file` rather than a named
violation.

Remedy: express the carved sentence as a local literal in the test (it is the reviewed artefact) and
assert `scan_file` suppresses it, then separately assert the shipped file *contains* it via a string
search rather than an index; add the `ValueError` case or replace the raise with a violation.
Behaviour preserved: the carve-out still only suppresses the reviewed sentence.

## MINOR — an OR chain that accepts the drift the train is removing

`tests/test_verify_harness_guides.py:253-261` replaced `"## First session" in text or "## 第一次会话"
in text` with a four-way disjunction that also accepts `"## Grok Build first session"` and
`"## Grok Build 第一次会话"`. The English README now carries the Grok-scoped heading, so the
disjunction is what makes the suite green. The same file's siblings forbid Grok-scoped prose in
shared surfaces, and the disjunction would equally accept `"## 第一次会话"` inside the *English*
README — cross-language drift is now unreachable by this test. Remedy: key the expectation per file,
e.g. a `{README.md: "## Grok Build first session", "README.zh-CN.md": "## Grok Build
第一次会话", "docs/guide/01-setup.md": "## First session"}` mapping, so a rename fails loudly instead
of landing in a growing OR.

## Required checks — direct answers

1. Source-text assertions: `tests/test_architecture_documentation.py:91-125`;
   `tests/test_scan_host_boundary.py:124-137,145-147` (live source by line index), `:149-165`,
   `:168-174`, `:176-187`. Each is named above with the behaviour it fails to pin.
2. Duplicate across files: `tests/test_evidence_settlement.py:333-343` ≡
   `tests/test_evidence_index_resilience.py:360-373`. Canonical: the resilience file (guard lives in
   `scripts/evidence_index.py`). The poteto-mode prose assertions are also duplicated:
   `tests/test_verify_harness_playbooks.py:52-61` (canonical, stricter — bans any `*-tools.md`) and
   `tests/test_scan_host_boundary.py:149-165` (weaker duplicate; delete).
3. Docs test verdict: a copy, not a behaviour pin — except the host-set equality and the link, which
   should move into the existing link-resolution test.
4. Invariant proof: static-drop is proven; the live-observed-FAIL case is the missed, reachable
   case (BLOCKER above). The "same-ID non-live" test uses a `FAIL` row, so it cannot distinguish a
   correct guard from one that only blocks failing rows.
5. Hermeticity: one offender, `tests/test_verify_portable.py:301` (ambient `openspec` CLI + active
   change set); proven red with `PATH=/usr/bin:/bin`. No changed test reads `HOME`, `expanduser`, or
   a live plugin mirror; `tests/test_evidence_durability.py:596` copies in-repo `.audit/evidence`,
   which is repo state, not ambient.
6. 1000-line threshold: none. Largest changed test is `tests/test_evidence_settlement.py` at 757
   lines; `tests/test_evidence_durability.py` is 634; the scanner sources are 377 and 379.
