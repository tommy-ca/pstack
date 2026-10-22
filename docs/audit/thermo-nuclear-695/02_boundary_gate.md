# Scripts boundary lane — python scripts touched by the merged train

Scope pin: BASE `ef3405282e4afd2636923043ca59aac8a09d4170`, main HEAD
`10025900e8cb481540ce6f61f32d6b73ff638b3f`. Train commits in this lane:
`6611f28` (#710, scan), `4bfe369` (#715/#713, openspec cwd), `2120445` (#716/#714),
`1002590` (#720, evidence), `c075de0` (#708, absorbed), `1d492f1` (#702, verify-harness).
Interpreter: `/home/tommyk/projects/pstack/.venv/bin/python`. Nothing in the repo was
edited; every experiment ran against copies in `/tmp/thermo-695/`.

Correction to the lane brief: `scripts/scan-host-boundary.py` is **not** a new file. It
exists at BASE with 304 lines; the train adds +73/−0 for 377 at HEAD (`git cat-file -e`
on the BASE blob succeeds).

## Measurements (base → head)

| unit | base | head |
|---|---|---|
| `scan-host-boundary.py` file | 304 | 377 (+73) |
| `scan_file` | 31 lines | 53 lines |
| `evidence_index.write_verification_evidence` | 81 | 96 |
| `verify-portable.PortableVerifier.doctor` | 144 | 144 (kwarg only) |
| `verify-harness.main` | 281 | 283 (docstring + one string) |
| `openspec_change._active_openspec_changes` | 25 | 26 |
| `openspec_change._validate_named_change` | 10 | 11 |
| files over 1000 lines after the diff | none | none (max: `verify-portable.py` 576; its own test pins < 750) |

`scripts/scan-host-boundary.py --check --json` at HEAD: `scanned_files: 143`,
`violations_count: 0`, exit 0.

## Finding 1 [MAJOR] — the live-drop guard reads state that two undocumented in-place mutations produced

`scripts/evidence_index.py:150-161` (head). After `preserved = preserve_observed_settlements(previous, receipt)`
at line 142, the new code builds `prior` from `previous.scenarios` and `current_by_id`
from `receipt.scenarios` and calls `_is_preservable_settlement` on both. That is correct
today only because of two side effects that are invisible from the call site:

1. `preserve_observed_settlements` calls `previous.validate()` and `current.validate()`, and
   `ScenarioResult.validate()` (`scripts/portability_types.py:537-538`) coerces
   `settlement: dict` → `ChildSettlement` **in place**. `_is_observed_settlement`
   (`portability_types.py:560-566`) requires `isinstance(scenario.settlement, ChildSettlement)`,
   so the predicate answers *False* for a receipt freshly parsed from JSON and *True* after
   validation. Measured on the repo's own fixture (`tests/test_evidence_settlement.py`
   `_omp_live_root`/`_proof_bar_refresh`): `prior` ids are `[]` before the preserve call and
   `['runtime-child-spawn-omp']` after it, on the identical scenario object.
2. `preserve_observed_settlements:51` rewrites `current.scenarios[i] = replace(candidate, …)`,
   which is why the widened #720 guard does not classify a *repaired* row as dropped.

Consequence: `previous.host != current.host` returns at line 39-40 **before** validation, so
in that branch the guard's `prior` map is empty and it silently permits the overwrite instead
of refusing. And if either helper is ever made pure — the obvious "clean up the in-place
mutation" refactor — the guard fails in one of two directions with no test to catch it: a pure
`validate()` reopens #714/#720 silently (static refresh overwrites live settlements), while a
pure `preserve_observed_settlements` makes every legitimate refresh exit 1 with a false
"cannot be re-observed by a static refresh".

Consumers searched: `write_verification_evidence` is called from
`scripts/verify-portable.py:464` only; `_is_preservable_settlement` is already re-exported by
the `scripts/portability_schema` facade (`import` at :77, listed in `__all__` at :132), so the
new `from scripts.evidence_durability import _is_preservable_settlement` (`evidence_index.py:15`)
is a second import edge for a symbol this file's own import block already has a facade for
(`from scripts.portability_schema import (… check_evidence_durability, settle_planes, …)`).
Tests pinning behavior: `tests/test_evidence_settlement.py:296-312`
(`test_durable_refresh_preserves_an_unchanged_observed_settlement`, asserts `preserved_from`,
`planes.runtime == PASS`, `check_evidence_durability(...) == supported`),
`:314-333` and `:335-345` (both refusal paths), `tests/test_evidence_index_resilience.py:180-187`,
`tests/test_verify_portable.py:515-570`.

Remedy (code judo): move the question into its owner. `preserve_observed_settlements` already
computes `prior` and already validates both receipts; make it return
`Preservation(preserved: list[str], dropped: list[str])` from that single traversal and let
`write_verification_evidence` keep zero knowledge of `_is_preservable_settlement`. The caller
then reads `if not preservation.dropped: if preservation.preserved: …`, the private import
disappears, the second traversal of the same pair disappears, and the "dropped" semantics for
the host-mismatch and stale-runtime early returns become explicit decisions instead of an
accident of `validate()` ordering. Fixture mutation at `tests/test_evidence_settlement.py:463,472`
(and any `== [scenario_id]` assertion) is the only test-visible cost.

## Finding 2 [MAJOR] — the carve-out is keyed on a line number and repeats one fact three times

`scripts/scan-host-boundary.py:158-161,183-198`. `QUOTED_PROHIBITION_CARVE_OUTS` holds the
`(path, 129, token)` triple and has **zero consumers repo-wide** (grep for the identifier
across the tree returns only its definition; pycache aside). `_is_carved_prohibition` then
re-hardcodes the same triple at :185-187 and the same sentence at :189-191, so one reviewed
fact lives in three places, one of which is dead. The line number makes the exemption depend
on prose placement in a 774-character paragraph of `skills/poteto-mode/SKILL.md:129`.

Measured failure modes (module loaded from the head file, scenario written into a temp root):

- Sentence reworded in place (`Do not open` → `Avoid opening`): `scan_file` **raises**
  `ValueError: carve-out content drifted at skills/poteto-mode/SKILL.md:129`. `run_scan` has
  no handler, so `scripts/scan-host-boundary.py --check` — which `verify-portable.py:299-304`
  runs as the `doctor-scan-host-boundary` step — dies with a traceback instead of reporting a
  graded violation.
- Paragraph reflowed so the sentence sits on its own line: one violation, i.e. a pure
  formatting edit turns the boundary gate red.
- Line 129 itself is 774 characters; any rewrap of that paragraph is a live risk.

Also structurally: the 21 lines at :283-304 are three detectors in one per-line body, each
constructing the identical `Violation(file_path=…, line_number=idx, token=…, category=…,
snippet=line.strip()[:160])`, and :192-195 is an unreachable branch (`token not in scanned_line`
cannot hold at the only call site, :295, which already guards `path in line`).

Remedy: key the exemption on the sentence, not the line, and strip it once per line. A
`REVIEWED_PROHIBITIONS: Tuple[Tuple[str, str], ...]` of `(rel_path, sentence)` plus
`_uncarved(rel_path, line) -> str` applied once before the detectors replaces
`QUOTED_PROHIBITION_CARVE_OUTS`, `_is_carved_prohibition`, the `raise` paths and the
unreachable branch, and collapses the three detectors into one `for token, category in
_line_rules(line)` loop.

Worked and measured in `/tmp/thermo-695/proposed.py`: 377 → 358 lines (−19), whole-tree scan
still `143 files / 0 violations`, and all five pinned install-path behaviours identical
(`tests/test_scan_host_boundary.py:106-146`):
"open evil path" flags, "negated non-carved" flags, "exact carved sentence" clean,
"legit + extra evil" flags, "evil then legit" flags. Two deliberate deltas: a reworded
sentence becomes a graded violation instead of a crash, and a moved sentence stays exempt
instead of flagging. No test asserts the `ValueError` (grep `carve-out` in `tests/` returns
docstrings only), and both deltas are fail-closed.

## Finding 3 [MAJOR] — the routing guard silently misses the directive it exists to catch

`scripts/scan-host-boundary.py:171-181`. The docstring promises "the same clause", but
`_affirmative_imperative` searches the whole line: `re.search(NEGATION_GAP + verb, line)` only
requires *some* negated routing verb anywhere on the line, not one attached to the host name.
Measured: `is_host_routing_directive("Do not use host emulation. Open Grok Build plugins first.")`
returns `None`. A live routing instruction is therefore allowed whenever an unrelated negated
verb precedes it in the same physical line — and shared skill prose is
exactly one long line per paragraph here (SKILL.md:129 is 774 chars).

`is_host_routing_directive:165` additionally sniffs two string shapes into silent exemptions
(`(?!['’]s?\b)`, `(?!:)`), so "Use Grok Build's skill order." passes while "Read the Grok Build
docs." flags. Those are the very forms the sibling test forbids by name
(`tests/test_scan_host_boundary.py:160-161`), so the guard is weakest exactly where the repo
has already been bitten.

Remedy: apply the negation test per sentence — split on `(?<=[.!?])\s+`, require the routing
verb and the negation in the same sentence that names the host. In `/tmp/thermo-695/proposed.py`
this is one `any(... for sentence in re.split(...) if HOST_ROUTING_NAME in sentence)`; measured
it now flags the cross-sentence case, still suppresses "Do not open the Grok Build plugin dir.",
and still suppresses the possessive form. No test pins the old false negative.

## Finding 4 [MINOR] — a host display name is hardcoded three times inside the host-agnostic scanner

`scripts/scan-host-boundary.py:151,165,167,289`. `"Grok Build"` appears in the install-path
label, in the routing regex, in the returned category, and again as `token="Grok Build"` at
:289. Every other host fact in this file is derived: `HARNESS_NAMES` comes from
`scripts/host_identity.py`, and the vocabulary comes from `profiles/*.json`. host_identity's
own docstring states the contract this violates — "the portability core used to declare the
host set in ten places … every surface imports it instead of keeping its own copy".

There is no canonical owner for the *display* name today: `scripts/drivers/grok.py:2,13`,
`scripts/scaffold-verification-skill.py:4` and `scripts/project-package.py:132` hardcode it too.
Consumers searched: no `display_name` key in `scripts/host_identity.py` or `profiles/*.json`
(grep), so nothing currently resolves it. Remedy: one `DISPLAY_NAMES` mapping in
`scripts/host_identity.py` (or a `display_name` field in `profiles/<host>.json`), and let the
routing rule iterate it, which also makes the guard cover the other seven hosts instead of
only Grok. Behavior pin today: whole-tree scan 143/0; the display name is not asserted anywhere
by token, so this is additive.

## Finding 5 [MINOR] — one module, two cwd contracts, and a lambda in the caller to bridge them

`scripts/openspec_change.py:35,63-78` (head). `_active_openspec_changes(cwd=None)` passes
`cwd=None` to `subprocess.run`, i.e. inherits whatever directory the caller happened to be in,
while its sibling `_validate_named_change(cwd=None)` resolves `_repo_root()`. That asymmetry is
what forces `scripts/verify-portable.py:241` to read
`active_resolver=lambda: _active_openspec_changes(cwd=str(ROOT))` — a wrapper whose only job is
to inject the default the module should already have. The consequence is a latent half-fix for
#713: the doctor's `openspec validate` is bound to the repo root, but any `openspec list`
reached through `validate_openspec_change(None)` still runs in the ambient cwd
(`tests/test_verify_portable.py:344-345,367-368` exercise exactly that path with a monkeypatched
`subprocess.run`, so they cannot see it).

`_repo_root()` also duplicates the `Path(__file__).resolve().parents[1]` line that 20 sibling
scripts declare at module level (grep `parents\[1\]` in `scripts/`), and hides a function-local
`from pathlib import Path as _Path` alias in a module that needs no other `Path`.

Remedy: module-level `ROOT = Path(__file__).resolve().parents[1]` at the top like every sibling,
default both helpers to it, and delete the lambda in `verify-portable.py`. Behavior pins that
must stay green: `tests/test_verify_portable.py:301-313`
(`test_doctor_resolves_openspec_from_repo_root_not_caller_cwd`, the #713 regression test) and
`:344-406`, all of which monkeypatch `subprocess.run` and ignore the `cwd` value, so the change
is invisible to them; `_validate_named_change` keeps its current effective cwd.

## Finding 6 [MINOR] — two dead constants that read as configuration

`scripts/scan-host-boundary.py:154` (`ROUTING_IMPERATIVES`) and `:158-160`
(`QUOTED_PROHIBITION_CARVE_OUTS`). Neither identifier has a single consumer: `grep -rn` across
the tree returns only the definitions themselves. `_affirmative_imperative:173,176` re-inlines
the tuple's four verbs into two separate regexes, so the constant is not merely unused, it is
stale-by-construction the moment someone edits it. The second is covered by Finding 2; the
first should be a module-level `ROUTING_VERB = r"\b(?:open|read|use|route)\b"` used by both
regexes or deleted.

## Finding 7 [MINOR] — a fifth responsibility lands in an already busy writer with a third refusal style

`scripts/evidence_index.py:95-190`, 81 → 96 lines. The function already owned receipt write,
index load, index backfill, durable reconciliation and index write; the diff adds the live-drop
refusal and a `elif preserved:` branch, which nests a third level under
`if _file_or_denied(durable_file): try … except … else:`. It also introduces a refusal
mechanism inconsistent with its immediate neighbour: the unreadable-durable branch sets
`reusable = False`, prints "REFUSING" and falls through to `print("Evidence captured …")`
(exit 0), while the new dropped branch calls `sys.exit(...)`. Two adjacent refusals, two exit
semantics, one function.

Remedy, after Finding 1: the durable branch becomes
`preservation = reconcile_previous(previous, receipt)` from the owner plus one
`if refusal: sys.exit(refusal)` in the caller, and the reconciliation body moves to a helper —
the caller drops to roughly its base length and the refusal style is uniform. Behavior pins:
`tests/test_evidence_settlement.py:296-345`, `tests/test_evidence_index_resilience.py:150-200`,
`tests/test_verify_portable.py:515-570`.

## Finding 8 — duplication across the existing scanners, and the canonical owner

`scripts/scan-host-boundary.py` is not the only forbidden-token scanner in the repo, and the
train adds a *fourth* exemption model:
`scan-host-boundary.py` uses glob exemptions (`DEFAULT_EXEMPTIONS`) plus the new line-keyed
carve-out; `scripts/verify-harness.py:125-155,383-398` scans a whole tree for `FORBIDDEN`
patterns with per-pattern path predicates (`allows_cursor_rules_mention`,
`allows_cursor_compat_scanner`), including `~/.cursor/rules/` — the same *class* of token the
new code adds as `HOST_INSTALL_PATHS`; and the mention-level allowlist it calls,
`leftover_mention_allowed`, lives in `skills/swarm/scripts/partition.py:562-569` and is the
repo's established answer for "a reviewed negative mention of a forbidden token".
`scripts/project-package.py:70-93` is a further hand-maintained copy of
`KNOWN_HOST_PRIMITIVES` whose comment claims the scripts are "not importable by module name",
which is no longer accurate (the scanner itself imports `scripts.host_identity` through
`sys.path`).

The new `_is_carved_prohibition` is therefore neither new nor minimal — it re-derives a
mention-allowlist concept with a line number and an exception. Canonical owners to name:
`skills/swarm/scripts/partition.py:leftover_mention_allowed` for reviewed-mention exemptions,
`scripts/host_identity.py` for host names/ids, `profiles/<host>.json` for host paths
(`profiles/grok.json:5` already declares `plugins_dir: "~/.grok/installed-plugins"`, so the new
`HOST_INSTALL_PATHS` literal duplicates a value the scanner already loads). Consumers of the
scanner that constrain any movement: `scripts/select_checks.py:29,180`,
`scripts/verify-portable.py:299-304`, `scripts/surface_revisions.py:434` (hashes the file as a
driver), `tests/test_scan_host_boundary.py`, `tests/test_host_identity.py:311`,
`tests/test_verdict_reduction.py:35`, `tests/test_droid_integration.py:44`,
`tests/test_select_checks.py:162-226`. Anything that renames the script or its `--check` CLI
contract is a breaking change; internal helper reshaping is not.

Note: moving install paths into `extract_forbidden_vocabulary` from `plugins_dir` would be the
bigger judo, but `tests/test_scan_host_boundary.py:124-138` deliberately calls
`scan_file(..., vocab={})` and still expects an install-path token, so that test pins
install-path detection as independent of vocabulary. Either keep the static table (recommended,
smallest) or rewrite that test to the new owner — do not silently drop the pin.

## Lanes with no finding

- `.grok/skills/verify-pstack/scripts/absorbed.py:25-30`: data-only replacement of one needle with
  three. Verified against the tree: `grok-tools.md` no longer occurs in
  `skills/poteto-mode/SKILL.md` (count 0), and the three new needles occur 1, 3 and 2 times, so
  the swap removes a dead assertion and adds live ones. The runner (`line_errors`, `check`) is
  unchanged.
- `scripts/verify-harness.py:1-12,316-324`: docstring plus a comment plus one error string. Zero
  new branches, `main()` 281 → 283. The rename is honest (the gate is Grok-adapter-scoped and
  the docstring now says its exit 0 is not a six-host verdict). Note that
  `tests/test_scan_host_boundary.py:174-190` pins this prose by substring, which is the existing
  test-of-a-docstring pattern, not something this diff introduced.
- `scripts/verify-portable.py:241`: the diff is a one-line kwarg inside `doctor`, which stays at
  144 lines and gains no branch. Its only defect is the asymmetry described in Finding 5.
- File-size rule: no file in this lane crosses 1000 lines; the largest is `verify-portable.py`
  at 576, and its own test (`tests/test_verify_portable.py:413`) holds it under 750.
