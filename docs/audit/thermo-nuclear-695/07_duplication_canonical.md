# Lane: duplication, canonical-layer leaks, file-size ceilings

Revisions reviewed (read-only; no repo mutation):
- BASE `ef3405282e4afd2636923043ca59aac8a09d4170`
- main HEAD `10025900e8cb481540ce6f61f32d6b73ff638b3f`
- PR #717 head `e18ba483856473c77cf26323b1f018921a8ef309` (local `pr-717`)
- PR #718 head `4befddd9a11639de71c0d47135d2ff6f847e4e3d` (local `pr-718`, data-only)
- PR #719 head `9c4b680229429b6b61c166ef888632830818e09c` (local `pr-719`)

Commands used: `git diff <rev>..<rev> -- <path>`, `git show <rev>:<path>`, `git grep <pat> <rev> -- <glob>`,
`grep -rn` over the working tree (== main HEAD), and one Python digest computation
(`scripts.surface_revisions._driver_core`) against exported blobs under `/tmp/thermo-695/`.
Nothing was written to the repository.

---

## Duplicates table (owner A, owner B, canonical)

| # | Copy A | Copy B | Canonical owner |
|---|---|---|---|
| 1 | `scripts/evidence_durability.py:45` `prior = {s.id: s for s in previous.scenarios if _is_preservable_settlement(s)}` | `scripts/evidence_index.py:150` — byte-identical line | `scripts/evidence_durability.py` (`preserve_observed_settlements`) |
| 2 | `scripts/evidence_index.py:15` imports private `_is_preservable_settlement` from `scripts.evidence_durability` | `scripts/portability_schema.py:77,132` already re-exports it in the facade `__all__` | `scripts/portability_schema.py` (the import home every other consumer uses) |
| 3 | `scripts/openspec_change.py:63-65` `_repo_root()` + function-local `from pathlib import Path as _Path` | `ROOT = Path(__file__).resolve().parents[1]` in 20 scripts, e.g. `scripts/evidence_index.py:29` | module-level `ROOT` in `openspec_change.py` |
| 4 | `scripts/scan-host-boundary.py:158-160` `QUOTED_PROHIBITION_CARVE_OUTS` (**dead**) | `scripts/scan-host-boundary.py:185-187` inline literal tuple; expected sentence `:189-191`; `tests/test_scan_host_boundary.py:127,135,143` `splitlines()[128]` | none — the constant is never read; delete all copies and key the carve-out on the sentence |
| 5 | `scripts/scan-host-boundary.py:154` `ROUTING_IMPERATIVES` (**dead**) | `:172` and `:176` both inline `r"\b(open\|read\|use\|route)\b"` | `ROUTING_IMPERATIVES` (build one pattern from it) |
| 6 | `scripts/scan-host-boundary.py:150-152` `HOST_INSTALL_PATHS = {"~/.grok/installed-plugins": ...}` | `profiles/grok.json:5` `"plugins_dir": "~/.grok/installed-plugins"` — already loaded by `load_profiles()` in the same module (`:140-147`) | `profiles/<host>.json` |
| 7 | `scripts/verify-portable.py:328` `-c` string rebuilding `HarnessProfile` field-by-field (`host, support_state, bindings, skills_dir, plugins_dir, plugin_manifest, evidence_ledger, tool_mappings, skill_order, runtime_conventions, setup`) | `scripts/portability_types.py` `@dataclass HarnessProfile` (pr-719 adds `setup`) | `scripts/portability_types.py` (needs `HarnessProfile.from_dict`/`load_profile`) |
| 8 | `scripts/verify-harness.py` — 13 hand-edited `setup-pstack-grok` occurrences (6 path constructions + 5 failure strings + 2 messages) | `skills/setup-pstack-grok/` (the directory itself) | one module constant in `verify-harness.py` |
| 9 | `scripts/portability_types.py:29-30` (pr-719) `SETUP_SOURCES`, `SETUP_EFFORT_MODES` | `schemas/portability/setup-projection.schema.json:11,28` same two enums | one owner + a test asserting equality (neither today) |
| 10 | `scripts/portability_types.py:29` `SETUP_SOURCES` (`host-cli/host-catalog/inherit/none`) | `scripts/model_role_policy.py:31` `VALID_DISCOVERY = {"unverified","catalog","live"}` (+ `model-role-policy.schema.json:84`) — second per-host model-knowledge vocabulary | neither; axes overlap and already disagree for `omp` (`discovery=catalog`, `setup.source=none`) and `grok` (`discovery=catalog`, `setup.source=host-cli`) |
| 11 | `tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json` wall-clock/byte fields (`context_ms`, `total_context_ms`, `context_ops`, `context_bytes`) | asserted key tuples `tests/test_eval_blinded_pstack_dsh_candidate.py:136-172` (excludes all four) | the test's asserted key set — the fixture should not record what nothing reads |

---

## Findings (prose)

### 1. [BLOCKER] The static-refresh refusal is a second, divergent copy of the preservation decision, and it kills the prescribed recovery path.

`scripts/evidence_index.py:150-166` (HEAD) recomputes what `scripts/evidence_durability.py:45-53`
already computes. The canonical function decides preservation *including two early returns*: host
mismatch (`:39-40`) and a stale runtime plane (`:42-43`) both yield "preserve nothing". The new guard
reads the same prior set independently and, whenever the canonical function declined for a staleness
reason, sees prior live rows that the static receipt cannot re-observe and calls `sys.exit`
(`docker:evidence_index.py:158`). So for any host whose durable receipt carries `observed_live` rows,
`refresh-static` refuses exactly when the runtime plane is stale — which is the only condition
`refresh-static` exists to repair. `check_staleness_action` and `index_row_mismatch`
(`evidence_index.py:200,222`) still prescribe `refresh-static --host all` / `--host <h>`;
`docs/verification-test-tiers.md:85` and `docs/research/arena-f2-seam-2026-10-17.md:32` both describe
`refresh-static --host all` as the 8-failed → 81-passed recovery step. Worse, the loop is
`for h in hosts:` in `scripts/verify-portable.py:522` and the refusal is `sys.exit` inside the first
offending host, so `--host all` aborts mid-run (omp is 4th of 6 alphabetically) and leaves the
inventory trailing with later hosts unrefreshed — the partial state the module's own error texts go
out of their way to avoid.

Consumers searched: `preserve_observed_settlements` (scripts/verify-portable.py:52,
tests/test_evidence_settlement.py:32,463,472), `_is_preservable_settlement`
(scripts/evidence_index.py:15, scripts/portability_schema.py:77,132), `write_verification_evidence`
(verify-portable `evidence()` path, tests), `refresh-static`/`check-staleness` CLI verbs
(verify-portable.py:475,540; docs above). Could not rule out: external callers of the script CLI.

Behavior to preserve: (a) the checked-in omp receipt's live rows survive any static refresh;
(b) a static refresh still restamps stale canonical/adapter/package planes;
(c) the refusal text still names the live re-proof command.
Evidence today: `tests/test_evidence_durability.py:587-634` pins (a) and (c); the *pre-existing*
partial-refresh test was retargeted `omp` → `grok` (`:534-547`, comment at `:537-539`), which is the
proof that (b) no longer holds for the only host with live rows.

Remedy (judo): delete the second decision. Have `preserve_observed_settlements` return
`(preserved, dropped)` — it already computes `prior` and already knows why it declined — and have the
writer branch on that single result, re-raising the canonical function's refusal instead of
recomputing the set. That deletes the private import (#2), the duplicated comprehension (#1), and one
of the two meanings of "stale". Then decide explicitly, in one place, whether a stale-live host may be
restamped (and if so, keep the live rows and restamp only the proven planes) or whether every
prescription that names `refresh-static` must be rewritten to name the live gate per host.

### 2. [MAJOR] A Grok-specific prose-semantics island landed in the general boundary scanner, with a pinned markdown line number.

`scripts/scan-host-boundary.py` grew 304 → 377 lines (base → HEAD, +73) almost entirely from one
feature: `HOST_INSTALL_PATHS` (`:150`), `is_host_routing_directive` (`:163`), `_affirmative_imperative`
(`:171`), `_is_carved_prohibition` (`:183`) plus two dead constants (`:154`, `:158`). Two of the three
functions are English-prose heuristics — a negation gap regex (`NEGATION_GAP`, `:156`) deciding whether
a line "routes" to a host — inserted into a module whose existing model is a flat token table
(`KNOWN_HOST_PRIMITIVES`) plus path exemptions (`DEFAULT_EXEMPTIONS`, `is_exempt`).

The carve-out is the sharp edge: it pins `("skills/poteto-mode/SKILL.md", 129, "~/.grok/installed-plugins")`
in three places (constant, inline tuple, test index 128) and `raise ValueError` on drift (`:192-196`).
Any edit that shifts `skills/poteto-mode/SKILL.md` by one line turns a clean `FAIL` report into a
traceback with no exit-code contract, and the sanctioned fix is to hand-edit a line number in a
scanner. `HOST_INSTALL_PATHS` is also a second registry of a path the same module already loads:
`extract_forbidden_vocabulary` reads `profiles/*.json` via `load_profiles` (`:140-147`), and
`profiles/grok.json:5` already declares `plugins_dir: ~/.grok/installed-plugins`.

Behavior to preserve: `~/.grok/installed-plugins` mentioned in shared surfaces is a violation except
the one reviewed prohibition sentence; "Grok Build" as an imperative routing instruction is a
violation; negation, `'s`, and `:`-suffixed mentions are not.
Evidence: `tests/test_scan_host_boundary.py:104-146` pins exactly those five cases (actionable path,
negated path, exact carved sentence, appended second path, preceded second path).

Remedy: (i) delete `ROUTING_IMPERATIVES` and `QUOTED_PROHIBITION_CARVE_OUTS` — they are never read;
(ii) build the imperative pattern once from `ROUTING_IMPERATIVES` instead of inlining the verb list
twice; (iii) replace `HOST_INSTALL_PATHS` with `plugins_dir`/`skills_dir`/`plugin_manifest` values
harvested by `extract_forbidden_vocabulary` from the profiles it already loads — that covers all six
hosts instead of one; (iv) replace the line-number carve-out with a sentence-keyed exemption row
(`{("skills/poteto-mode/SKILL.md", "<exact sentence>"): reason}`), which keeps the same five test
outcomes, drops the drift crash, and removes two of the three synchronized literals.

### 3. [MAJOR] The profile validator is a 1.2 KB `-c` string; PR #719 paid the tax instead of deleting it.

`scripts/verify-portable.py:328` constructs `HarnessProfile` by naming eleven fields inside a nested
`python -c` program string; PR #719's entire verify-portable change is appending
`, setup=d.get('setup')` to it (diff is one line, 496 → 518 chars). This is a duplicated field list
with no guard: before #719 the string omitted `setup`, so the doctor loaded profiles with
`setup=None` and `HarnessProfile.validate()` (`portability_types.py:498-500` at pr-719) never validated
the new block — a malformed `setup` would have passed the doctor silently. `setup` is also the fifth
`Optional[Model | Dict[str, Any]]` field on this dataclass, each with its own `isinstance(..., dict)`
coercion block, so the field list will keep growing.

Consumer reachability: the string is executed per host by `doctor-profile-<host>`
(verify-portable.py:322-330); `HarnessProfile(...)` is constructed explicitly in
`tests/evidence_test_helpers.py:34`, `tests/test_portability_schemas.py:225,267`, and `SetUpProjection`
parsing in `scripts/setup_pstack.py:53` (pr-719). No external contract on the string.

Behavior to preserve: the doctor scenario still fails when any profile field is invalid, and its
`command` still shows a reproducible invocation.
Evidence: `tests/test_verify_portable.py` doctor scenarios; `tests/test_portability_schemas.py:272`
asserts `profile.setup` is typed when loaded by the test helper, i.e. the *other* loader already works.

Remedy: add `HarnessProfile.from_dict(d)` (or `load_profile(path)`) in `scripts/portability_types.py`,
and reduce the doctor command to
`python -c "from scripts.portability_schema import load_profile; load_profile(Path('...')).validate()"`.
That deletes 1.1 KB of string, one duplicated field list, and the class of silent-miss it just caused.
`resolve_setup_projection` can then read `load_profile(...).setup` instead of re-parsing the JSON.

### 4. [MAJOR] `PSTACK_RUN_OMP_LIVE=1` is baked into a host-parameterized refusal message.

`scripts/evidence_index.py:160-162` interpolates `{host}` but hardcodes the OMP driver's live gate, so
`refresh-static --host codex` advises `PSTACK_RUN_OMP_LIVE=1 ... --host codex`. Confirmed OMP-specific:
`scripts/drivers/omp.py` and `tests/test_omp_rpc.py:272` are its only gates. The test
`tests/test_evidence_durability.py:632` pins the literal, so the leak is now contractual. This is the
feature-logic-in-a-general-module class: the writer knows no host's live gate.

Remedy: name the command host-agnostically (`python3 scripts/verify-portable.py run --host {host}`)
and let each profile/driver publish its own live gate (or say "with that host's live gate enabled").
Update the one assertion. No behavior is lost: the message still routes the maintainer to live proof.

### 5. [MAJOR] Checked-in derived evidence is hand-edited per branch; a hash that must move did not.

`boundary_driver_revision` is a digest of `scripts/scan-host-boundary.py`
(`scripts/surface_revisions.py:428-434`, AST-of-module recipe via `_driver_core`). PR #719 edits that
file (exemption rename, new path table) but leaves `boundary_driver_revision` untouched in all six
`.audit/evidence/*.json` (`d3ffcb53…`). Measured with the repo's own recipe:
main's file → `22dc94567356850b83ae6811b35cc168830afdbe08e838db21b58664e56a0eb4`,
pr-719's file → `ac3656740eda2493a7512cd303e0e7a8b023361882660a614eeeaaaa6a5d2f9d`.
Neither equals the recorded value, so the receipts are stale on main already and #719 keeps them
stale — while updating `package_driver_revision` (legitimately: the recipe covers
`portability_types.py`/`portability_schema.py`). No test pins receipt freshness:
`tests/test_evidence_durability.py:94-106` only asserts key sets and index row equality, never that
the recorded revisions match `compute_surface_revisions(ROOT, host)`.

Cross-branch cost, measured: `.audit/evidence/{6 files}` and
`tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json` are rewritten by main HEAD, #717 and
#719 with different values; #718 rewrites the same six receipts entirely. Every one of these four
landings must be re-recorded after the next one, and the fixture re-record is forced by
`_probe_scope_hash` covering `skills/**/SKILL.md` + `verify-portable.py` (which #717 and #719 both
touch). The fixture's unasserted fields (`context_ms`, `total_context_ms`, `context_ops`,
`context_bytes` — excluded from the asserted key tuples at `test_eval_blinded_pstack_dsh_candidate.py:136-172`)
are what turns that obligation into 18-24 lines of pure conflict noise per branch.

Remedy, shortest first: make the recorded receipt carry the digest the tree actually computes (a
refresh, or a test that fails on mismatch), and strip the four unasserted counters from the committed
fixture so a re-record is the hash line only. If neither is wanted, do not commit derived revisions at
all — the durability check can compare against `compute_surface_revisions` at read time.

### 6. [MINOR] Two per-host model-knowledge vocabularies with no coherence check.

`SETUP_SOURCES` (`portability_types.py:29`, pr-719) and `VALID_DISCOVERY`
(`model_role_policy.py:31`, `model-role-policy.schema.json:84`) both answer "where does this host's
model knowledge come from", and both use the word `catalog` with different meanings. They already
disagree for the same host: `omp` is `discovery=catalog` in
`examples/portability/model-role-policy.example.json` and `setup.source=none` in
`profiles/omp.json`; `grok` is `discovery=catalog` and `setup.source=host-cli`. I could not find any
test asserting a correspondence (searched `tests/test_setup_projection.py`,
`tests/test_portability_schema*.py`, `scripts/model_role_policy.py`). Either state the axis difference
in one line in each module and add one assertion for the pairs that must agree, or rename one side
(`setup.origin`) so the two enums stop reading alike.

### 7. [MINOR] `_repo_root()` and two half-applied `cwd` parameters.

`scripts/openspec_change.py:63-65` adds a helper that duplicates the module-level `ROOT` every other
script declares, with a function-local `from pathlib import Path as _Path` because the module has no
`Path` import. The `cwd` optional (`:35`, `:68`, `:74`) is also applied asymmetrically:
`verify-portable.py:241` passes `cwd=str(ROOT)` for `openspec list`, while
`validate_openspec_change` → `_validate_named_change(resolution.name)` (`:107`) still relies on the
`_repo_root()` default, so the two subprocesses in one scenario use different working directories.
Consumer search: `_active_openspec_changes` (verify-portable.py:91,241),
`_validate_named_change` (verify-portable.py:92, openspec_change.py:107), and the `-c` helper string at
verify-portable.py:243. Tests monkeypatch both by name with `lambda *a, **k`
(`tests/test_verify_portable.py:211-275`), so the signatures are free to change.

Remedy: `ROOT = Path(__file__).resolve().parents[1]` at module level, pass `cwd=str(ROOT)` inline in
both functions, delete `_repo_root` and both `cwd` parameters. Preserves the #713 fix and removes the
divergent default. Behavior pin: `tests/test_verify_portable.py:344-405` exercises both lookup
outcomes with no cwd argument.

### 8. [MINOR] `verify-harness.py`'s rename is 13 synchronized literals.

The pr-719 diff there is mechanical: six path constructions plus five failure-message prefixes changed
from `setup-pstack` to `setup-pstack-grok`, and `allows_cursor_rules_mention` (`:129`) now compares
`parts[:2]` against a 2-tuple. Nothing structural was added, but the rename shows the obligation:
`GROK_SETUP_SKILL = ROOT / "skills" / "setup-pstack-grok"` (or better, read `profiles/grok.json`'s
`setup.skill`, which pr-719 introduced precisely so this path has one owner) turns the next rename into
one line and makes `setup-pstack-grok` non-magic in the checker.

---

## File-size ceilings (touched files over 700 lines)

| File | base ef3405 | main | pr-717 | pr-719 |
|---|---|---|---|---|
| `TEST-PLAN.md` | 1133 | 1133 | 1133 | 1134 |
| `scripts/portability_types.py` | 664 | 664 | 664 | **721** |
| `tests/test_evidence_settlement.py` | 762 | 757 | 762 | 762 |
| `tests/test_verify_portable.py` | 639 | 651 | **728** | 651 |

Crossed 700 inside this set: `scripts/portability_types.py` (664 → 721, +57 in pr-719) and
`tests/test_verify_portable.py` (651 → 728, +77 in pr-717). Nothing crossed 1000; `TEST-PLAN.md` was
already 1133 and gains one line.
Largest absolute movers below 700: `scripts/scan-host-boundary.py` 304 → 377 (+73, feature-specific
logic in a general scanner — finding 2), `scripts/verify-portable.py` 576 → 617 in pr-717,
`scripts/evidence_index.py` 364 → 379, `scripts/openspec_change.py` 110 → 117,
`scripts/verify-harness.py` 506 → 512. `skills/setup-pstack/SKILL.md` shrank 206 → 61 with 199 lines
moved into the new `skills/setup-pstack-grok/SKILL.md` (a clean split, not a duplication).

`scripts/portability_types.py` crossing 700 matters less as a number than as a signal: pr-719 adds the
*third* thing of its kind to that file (a dataclass + closed enum tuple + matrix), and
`HarnessProfile` now carries a fifth `Model | Dict` optional field with its own coercion block. If it
keeps growing, `SetupProjection`/`SETUP_*` is the natural first extraction — they have exactly one
consumer today (`setup_pstack.resolve_setup_projection`, `verify-portable`'s profile child) and no
dependency on the receipt machinery.

## New abstractions with exactly one implementation

- `is_host_routing_directive` (scan-host-boundary.py:163) — one caller (`scan_file:283`) and it wraps
  a single `re.search` + one predicate; not an interface, but it is a named seam for one regex.
- `_affirmative_imperative` (:171) — one caller; holds two of the three inline verb regexes.
- `_is_carved_prohibition` (:183) — one caller.
- `resolve_setup_projection` (setup_pstack.py:28, pr-719) — one implementation and its real consumer
  is documentation (`skills/setup-pstack/SKILL.md:30` tells agents to call it) plus tests. It earns
  its place only if the doctor also uses it instead of the `-c` string (finding 3).
- `SetupProjection` — one implementation, two consumers; keep.
- No identity/pass-through wrappers found beyond `_repo_root()` (finding 7), which is exactly one.

## Shortest deletion with the most maintained obligation removed

Delete the carve-out island, not the scan. Concretely: remove `ROUTING_IMPERATIVES`,
`QUOTED_PROHIBITION_CARVE_OUTS`, `_is_carved_prohibition`, and the two inline verb regexes; make
`HOST_INSTALL_PATHS` fall out of the profiles the scanner already loads; key the one sentence-level
exemption on the sentence instead of line 129. About 40 lines and five synchronized literals
(`:154`, `:158`, `:185-187`, the expected sentence, `tests/test_scan_host_boundary.py:127`'s
`splitlines()[128]`) collapse into one table row, and a markdown edit stops being able to crash the
scanner with a `ValueError` traceback. The five existing test outcomes are unchanged, so this is a
pure obligation removal in a general-purpose module.
Runner-up, if only one line may change: `scripts/evidence_index.py:150-166` → the canonical
`preserve_observed_settlements` result (finding 1), which also deletes the private-import seam.
