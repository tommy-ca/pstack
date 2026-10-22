# PR #717 — thermo-nuclear detail report (lane: fixture-HOME hermeticity)

Revision under review: `pr-717` head `e18ba483856473c77cf26323b1f018921a8ef309` vs `main`
`10025900e8cb481540ce6f61f32d6b73ff638b3f`. Diff = 4 files, +148/−21. Working tree during
review was `main`; every read of a PR-modified file was taken with `git show pr-717:<path>`,
and every unmodified file cited (`scripts/package-lifecycle.py`,
`scripts/sync-antigravity-plugin.py`, `scripts/select_checks.py`,
`scripts/portability_types.py`, `tests/test_select_checks.py`) is byte-identical across the
diff base, so the citations hold at both revisions.

Scratch trees: `/tmp/pr717` (head, mutation-tested) and `/tmp/pr717-base` (pristine head) via
`git archive pr-717`. No repo files were modified; no git state was mutated.

Interpreter: `/home/tommyk/projects/pstack/.venv/bin/python` (3.14.8).

## Verdict on the five required checks

1. **Ambient-read isolation — PASS with two named residuals.** Every path the doctor
   scenarios can read is enumerated below; the two `$HOME`-derived readers are provably
   bound to the fixture (empirically, not by inspection alone). No BLOCKER leak exists in
   the current scenario set. Two residuals are unproven rather than leaking: the OpenSpec
   scenario, which the new test stubs out, and any future `XDG_*`/non-`Path.home()` reader,
   which a HOME-only binding would not cover.
2. **Test teeth — PASS for the bound seams, with a demonstrated blind spot.** Mutations that
   unbind either bound scenario, unbind the seed install, or delete the fail-closed guard all
   turn the new tests red (table below). A mutation that adds an ambient read of a path the
   test does not hand-seed leaves the invariance test green while flipping the doctor verdict
   on a real home — the test proves invariance for the two mirrors it writes, not for the
   doctor.
3. **Seam judgment — temporary HOME is the right lever today, but it is under-applied and
   unrecorded.** `--target-dir` is *not* an equivalent alternative: it silently drops the
   freshness/projection comparisons that make the check meaningful, and
   `sync-antigravity-plugin.py` has no equivalent flag at all.
4. **DSH fixture — regeneration justified, no hash bypass.** The `probe_scope_hash` bump is
   forced by `_probe_scope_hash`'s own scope; the timing churn is explicitly excluded from
   equality by the candidate test, so it is noise, not laundering. The new
   `pstack_revision` pins a commit that is an ancestor of neither `main` nor `pr-717`.
5. **Ad-hoc switches — three.** `PSTACK_DOCTOR_HOME`, cleanup keyed to that env var, and a
   documented path trick in the workflow that keeps the module out of `select_checks`'
   registry.

## Check 1 — ambient reads, enumerated

The doctor is `PortableVerifier.doctor()` (`scripts/verify-portable.py:231-261`) plus
`_doctor_checks()` (`:263-408`). Scenarios and every filesystem root they touch:

| Scenario | Line | Roots read | HOME-derived? |
|---|---|---|---|
| seed install | 245-252 | `ROOT/skills`, `ROOT/agents`, `ROOT/pstack.package.json`; writes `$HOME/<host rel>` | **bound** (`env`, :250) |
| `doctor-canonical-index` | 268-273 | `ROOT` only | no (`canonical-index.py` has no `HOME`/`expanduser`/`Path.home`) |
| `doctor-openspec-validation` | 279-290 | `ROOT` + the `openspec` CLI's own state | **no — see residual R1** |
| `doctor-adapter-static` | 330-335 | `ROOT` (text scan) | no |
| `doctor-scan-host-boundary` | 338-343 | `ROOT` (text scan) | no |
| `doctor-package-projection` | 346-351 | `ROOT` | no |
| `doctor-package-lifecycle-<host>` | 354-360 | `ROOT` + `Path.home()/<rel>` via `package-lifecycle.get_plugin_dir` (`scripts/package-lifecycle.py:71-75`) | **bound** (`env`, :359) |
| `doctor-profile-<host>` | 365-372 | `ROOT/profiles/<host>.json` (the `"~/.omp/plugins"` string is validated, never expanded) | no |
| `doctor-antigravity-sync` | 377-383 | `ROOT` + `sync-antigravity-plugin.LIVE_PLUGIN_DIR` (`scripts/sync-antigravity-plugin.py:19`) | **bound** (`env`, :382) |
| `doctor-evidence-durability-<host>` | 387-406 | `evidence_root` + `ROOT` | no |

The HOME-derived readers are exactly two, and the binding reaches both. Proven, not assumed:

```
HOME=/tmp/fixture-proof python -c "from pathlib import Path; print(Path.home())"
  -> /tmp/fixture-proof
HOME=/tmp/fixture-proof python -c "<import sync-antigravity-plugin>"
  -> LIVE_PLUGIN_DIR= /tmp/fixture-proof/.gemini/config/plugins/pstack
```

`sync-antigravity-plugin.py --check` reaches `check_live_sync()` only (`main()`, :473-475);
the `shutil.which("agy")` ambient probe lives in `audit_live_plugin()` (:170-178), which the
`--check` path never calls. `source_tree_guard()` (git status, worktree refusal) is likewise
`--sync`-only. So r6 reads no ambient tool and no repo-state guard.

**Residual R1 — the one doctor scenario no test proves.** `resolve_openspec_change` shells
out to the `openspec` CLI (`scripts/openspec_change.py`, `_active_openspec_changes`) with the
parent's inherited environment; the fixture HOME is not applied to it, and
`tests/test_verify_portable.py:74-78` monkeypatches the resolver to `state="none"`, so the
repo gate and the local suite never exercise it. It is not a plugin-mirror read, so it is
outside #709's literal scope — but it is the one doctor input whose ambient sensitivity the
PR leaves unproven.

**Residual R2 — a HOME-only binding is not a sealed environment.** `env={"HOME": ...}`
(`:359`, `:382`) redirects only `HOME`. `XDG_CONFIG_HOME`, `XDG_DATA_HOME`,
`XDG_CACHE_HOME`, `TMPDIR` and every `PSTACK_*` remain ambient, and this repo already has a
live `XDG_CACHE_HOME` reader (`scripts/surface_revisions.py:92-94`). No doctor scenario
reaches it today (r7 reads the evidence dir; `compute_surface_revisions` is a `drive()` path),
so this is a latent class, not a leak.

## Check 2 — mutations that must turn the tests red, and which ones do

Run in `/tmp/pr717` with `pytest -q tests/test_verify_portable.py -k "hermetic or fixture_install_fails"`.

| Mutation | Result |
|---|---|
| A: drop `env={"HOME": fixture}` from r4b (`:359`) | **red** — `assert verifier.doctor(...) is True` fails on the stale home |
| B: drop `env` from r6 (`:382`) | **red** — r6 fails on the clean home (no live plugin dir) |
| D: drop `env` from the seed install (`:250`) | **red on both tests**, and it demonstrates the hazard: the seed then installs into the *real* `$HOME`, and the fail-closed test still returns `doctor=True` |
| F: delete the fail-closed block (`:253-257`) | **red** — `doctor()` returns `True` vacuously, which is exactly the bug the guard exists for |
| E: add a doctor scenario that reads `$HOME/.omp/agent` (a path the test never seeds) | **stays green** |

Mutation E is the blind spot, and it is not contrived: `scripts/prove-omp-native-package.py:437`
reads `Path.home()/".omp"/"agent"`, so this shape of ambient read already exists in the repo.
With the mutation in place the invariance test passes (`1 passed`), while the same build run
against a home that has `~/.omp/agent` returns `doctor_ok=False` with
`('doctor-ambient-probe', 'FAIL')`. The test therefore falsifies two hardcoded paths, not the
proposition "the doctor verdict is invariant to ambient HOME".

Mutation D also produced an observable side effect worth recording: unbound seed installs
write into the *tester's* real `~/.omp/plugins/pstack` (observed mtime change on
`package.json`). The current code binds the seed, so this is a hazard the tests now pin, not a
live defect — but it is why the seed's `env=` is load-bearing and not incidental.

## Check 3 — is a temporary HOME the right seam?

**`--target-dir` is not the alternative.** `package-lifecycle.py` already accepts
`--target-dir` (`:644`), but `verify_plugin()` branches on it (`:353-375`): with
`target_base=None` it runs `check_all_projected()` *and* `freshness_errors(live_dir)`; with a
target base it runs `verify_plugin_at_dir()` only. Passing `--target-dir` to the doctor would
therefore delete both the projected-manifest conformance check and the installed-copy drift
comparison — the very "same package-lifecycle logic" #709 requires the gate to keep.
Consumers of that seam: `tests/test_package_lifecycle.py:142` (`prove --target-dir`), the
`prove`/`update`/`uninstall` CLI actions, and `scripts/package-lifecycle.py:560-637`. And
`sync-antigravity-plugin.py` has no install-root parameter at all, so an explicit-parameter
design would have to invent a second CLI surface for it.

**What HOME buys:** one lever that both scripts already honour through
`Path.home()`/`expanduser` (verified above), keeping every command line byte-identical to the
pre-PR gate — so the "same logic" requirement is satisfied by construction rather than by a
second code path. **What it costs:** the binding is invisible from the command line, which
matters because the command line *is* the durable artifact (finding 3 below), and it only
covers `HOME`, not the XDG trio.

Given that, the honest seam is still HOME — applied once for the whole doctor — not a new
`--install-root` flag on two scripts. If the scripts later grow an install-root parameter,
the move to make is inside `verify_plugin()`: teach it to take a *base* while keeping the
`target_base is None` comparison set, then the doctor passes it explicitly. That is a bigger
change than this issue needs.

## Check 4 — the DSH scoring candidate fixture

`tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json` is regenerated:
`pstack_revision` `9c27c63…` → `af9775a…` (:5), `provenance.probe_scope_hash` `8c31c0c…` →
`98cd36a…` (:27), `total_context_ms` (41) and fourteen per-case `context_ms` rows.

The hash change is **forced, not evasive**: `_probe_scope_hash()`
(`scripts/eval_blinded_pstack.py:259-281`) folds `scripts/verify-portable.py` into the
fingerprint (scope list at :276-279), and `tests/test_eval_blinded_pstack_dsh_candidate.py:146`
asserts `recorded == live == _probe_scope_hash(ROOT)`. Any behavioural edit to
`verify-portable.py` must move the pin; leaving it stale would red the suite.

The timing churn is **not** a bypass either: `test_run_is_deterministic`
(`tests/test_eval_blinded_pstack_dsh_candidate.py:88-98`) pops `total_context_ms`,
`pstack_revision` and every `context_ms` before comparing, and
`test_candidate_table_matches_the_live_run` (:114-117) compares an explicit key list that
excludes them. So the 15 wall-clock numbers are recorded-but-unasserted by design.

Two quality observations, not blockers:

- `pstack_revision` now names `af9775a81faad1d8dec02476a43f15a6299809ca`, which
  `git merge-base --is-ancestor` reports as reachable from neither `pr-717` nor `main` — an
  amended-away commit. Since the field is popped before every comparison, it is decorative
  metadata that rots on each amend. Pin the merged head or drop it.
- The frozen artifact self-describes as `"provider": "deterministic-offline"` and carries 15
  wall-clock values that every test deliberately ignores. Recording measurements nothing
  reads is maintenance with no consumer.

## Check 5 — ad-hoc conditionals and env switches

- `scripts/verify-portable.py:241` — `injected = os.environ.get("PSTACK_DOCTOR_HOME")`. Only
  consumer: `tests/test_verify_portable.py:127`. A verification tool's verdict now depends on
  an ambient variable, and the variable is unvalidated (a stale or foreign directory is
  accepted). The test already constructs `PortableVerifier` directly, so a constructor
  keyword costs one argument and deletes the global.
- `:260` — `if not injected: shutil.rmtree(...)`: cleanup ownership is derived from
  "was the env var present", so one boolean carries two unrelated decisions (who owns the
  directory, whether it is disposable).
- `.github/workflows/portability-offline.yml:27-31` — `working-directory: tests` plus a bare
  `test_verify_portable.py`, with a comment stating it is done so the module "must not
  register as an offline gate module in select_checks' workflow scan". The scan is a regex
  for `tests/[\w./-]+\.py` (`scripts/select_checks.py:88`), mirrored by
  `tests/test_select_checks.py:41-44`, so the step really does hide the module from the
  registry it is pretending not to be in.
- `-k "hermetic or fixture_install_fails"` is name-coupled, but safely: `pytest -k` with no
  match exits 5, so a rename reds the step rather than silently skipping it (verified).

## Ranked findings with remedies

### 1. MAJOR — bind the fixture for the whole doctor, not two scenarios
`scripts/verify-portable.py:354-360`, `:377-383`; docstring claim at `:264`.

Only r4b and r6 receive `env={"HOME": fixture}`; the other seven scenarios inherit the ambient
HOME. The docstring says "ambient-HOME readers are bound to `fixture_home`", but that is true
only for the two readers someone remembered. Mutation E shows the consequence: a new
HOME-reading scenario leaves `test_doctor_is_hermetic_against_ambient_plugin_mirrors` green
while flipping the verdict on a developer machine.

Consumer search for the remedy: `run_command()`'s `env` parameter (`:176`, `:181`, `:190`)
has exactly three call sites at head — the seed (`:250`), r4b (`:359`) and r6 (`:382`) — so
widening its use inside `_doctor_checks` is local. Behaviour pin: with `env={"HOME": fixture}`
injected into
*every* doctor subprocess by a `run_command` subclass, `doctor(check_durability=False)` for
`omp, antigravity, grok, codex, droid, opencode` returns identical `(id, verdict,
stdout_snippet)` triples for all six hosts versus today's build (`identical=True`,
`stock_ok=bound_ok=True` for each). Re-run with `check_durability=True` so the r7 evidence
scenario participates: `omp` (8 scenarios) and `antigravity` (9 scenarios) again compare
`identical=True`, every verdict `PASS` including `doctor-evidence-durability-<host>`. The
remedy removes the obligation to remember a per-
scenario `env=` — the fixture becomes the default for the phase, so a new doctor scenario is
hermetic unless it explicitly opts out.

### 2. MAJOR — delete `PSTACK_DOCTOR_HOME`
`scripts/verify-portable.py:241-242`, `:259-261`.

Consumer search: `grep -rn PSTACK_DOCTOR_HOME` at head matches only the docstring, the read,
and `tests/test_verify_portable.py:127`; no docs, workflows, scripts or other fixtures consume
it. Behaviour pin: `test_doctor_fails_closed_when_fixture_install_fails` passes with the value
supplied as a constructor keyword instead (same symlinked-mirror refusal, same recorded seed
row, verified by mutation F returning `doctor=True` when the guard is removed). The remedy
removes an ambient global that can silently re-point the verdict of the repo's own
verification tool, plus the two-state cleanup boolean.

### 3. MAJOR — record the HOME binding in the scenario
`scripts/verify-portable.py:359`, `:382`; `run_command` records `command=" ".join(cmd)`
(`:220`); `ScenarioResult` has no env field (`scripts/portability_types.py:510-517`); the seed
row is `record=False` (`:251`).

A receipt produced by a hermetic run is indistinguishable from one produced against the
developer's live mirrors: the stored command is `python … package-lifecycle.py verify --host
omp`, and the seed row never reaches the receipt. Since #709 is precisely about a verdict whose
provenance was ambiguous, the artifact of record should say which home decided it. Remedy is a
string, not a schema: put `HOME=<fixture>` (or `[hermetic home]`) into the description/command
of the bound scenarios. Consumer search: `ScenarioResult.command` is read by two assertions
that test substring membership — `tests/test_verify_portable.py:244` and `:254`, both on the
*openspec* scenarios, not the bound ones — plus receipt renderers (`scripts/evidence_index.py`)
that print it. None parses it, so a suffix on r4b/r6 is behaviour-neutral for existing
assertions.

### 4. MINOR — stop hiding the module from `select_checks`
`.github/workflows/portability-offline.yml:23-31`.

The step's own comment says the relative invocation exists so the module does not register as
an offline gate module. The premise is partly real and partly not: running the whole module in
an extracted (non-git) tree gives `4 failed, 32 passed` here — `test_check_rules_typed_named_tuple_and_typed_dict`
needs `git merge-base main HEAD`, and the two `drive()` tests FAIL in that tree — so the module
is not offline-safe as a unit. The stated remedy ("put the hermetic cases in their own module")
is therefore the right one, and the path trick is what lets the gate run them while the
registry denies it: list `tests/test_verify_portable_hermetic.py` as a normal `tests/…` path
and drop both the `working-directory` and the comment. Cost, verified:
`OFFLINE_GATE` in `tests/test_select_checks.py:41-44` is derived from the workflow with the
same regex, so no test edit is needed — the entry appears by itself. Benefit: the workflow
scan and the workflow reality stop disagreeing, the `-k` name coupling goes away, and
`tests/*.py` selection of the new file stays usual.

### 5. MINOR — reuse the canonical mirror map in the test
`tests/test_verify_portable.py:80-83`.

`mirrors` re-declares two entries of `package-lifecycle.HOST_PLUGIN_REL_PATHS`
(`scripts/package-lifecycle.py:60-67`). A moved relative path or a new host reader silently
un-tests the invariance claim (Mutation E's premise). Remedy: import the canonical map and seed
every entry it declares (`stale_home / rel`), keeping `hosts=("omp","antigravity")` for
runtime. Consumer search: `HOST_PLUGIN_REL_PATHS` is already imported by tests that assert
builtin host coverage (`scripts/host_identity.require_builtin_host_keys`), so importing it into
a test is an established use.

### 6. MINOR — resolve the fixture path
`scripts/verify-portable.py:242`.

`tempfile.mkdtemp(...)` is used unresolved, and the very next step installs through
`package-lifecycle.install_plugin`, which refuses any target whose leaf or ancestor is a
symlink (`is_owned_deploy_target` → `_traverses_symlink`, `scripts/package-lifecycle.py:82-112`),
with the docstring explicitly naming macOS `/var` -> `/private/var` as a refusal case
(`:90-92`). On such a host the seed refuses, the guard fails the doctor closed, and both new
tests go red for a platform reason. Remedy: `Path(tempfile.mkdtemp(...)).resolve()`.
Evidence status: Linux-verified only; the failure mode on a symlinked `TMPDIR` is
[INFERENCE] from the cited refusal code, not executed here. The same shape already exists in
`prove_lifecycle()` (`:570-571`), so this is inherited, not introduced.

### 7. MINOR — provenance of the regenerated DSH table
`tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json:5`.

`af9775a…` is an ancestor of neither `main` nor `pr-717`; nothing asserts the field
(`tests/test_eval_blinded_pstack_dsh_candidate.py:93` pops it). Pin the final head, or drop the
field so the fixture stops claiming a revision no reader can resolve.

## Dispositions

- Findings 1-3: recheck by re-running the new tests plus the six-host bind-all comparison;
  the first two are one-file edits, the third is a string.
- Finding 4: recheck by `python -m pytest -q tests/test_select_checks.py` and reading
  `offline_contract_tests()` output for the new module.
- Findings 5-7: recheck by `pytest -q tests/test_verify_portable.py` and
  `pytest -q tests/test_eval_blinded_pstack_dsh_candidate.py`.
- Nothing here asks for a behaviour change to the doctor's verdict, and no seam is proposed
  for deletion other than `PSTACK_DOCTOR_HOME`, whose single consumer is enumerated.
