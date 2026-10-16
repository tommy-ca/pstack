# Candidate A — Split-module: pure domain/validator surface vs hashing/evidence machinery

Trunk: `419fb36` (`refactor(portability): decompose role policy and resolver hot paths (#468)`)
Scope: this is a DESIGN. No repository file, branch, commit, push or receipt was touched. All
measurements below were taken on disposable copies under `/home/tommyk/.tmp-pstack-429/arena/`
(`proto/` = split prototype, `battery.py` = both-direction coverage battery, `migrate-demo.py` =
offline receipt migration demonstration).

**One-line design.** Move the fingerprint recipe out of `scripts/portability_schema.py` into a new
`scripts/surface_revisions.py`; stop fingerprinting that module's *bytes*; fingerprint instead the
three things that actually decide whether a live claim survives — the **values** of the declarative
rule constants, the **settlement-admission matrix**, and a **declared probe set** of gate
configurations (`EVIDENCE_GATE_PROBES`). Comments, annotations, refactors and reworded errors move
none of those, so they cost zero live re-proof; a loosened rule, guard or staleness branch moves
them, so the affected live claims still go stale.

| Rubric | How this design answers it |
|---|---|
| 1. Integrity preserved | A claim-affecting edit moves `driver_revision` (§6.1: 15 of 17 measured edits, including every guard removal `verify-portable.py check-evidence` relies on). Residual: behaviour exercised by no declared probe is not observed — named exactly in §10 |
| 2. Regeneration cost | All five measured neutral edits (comment, annotation, refactor, error reword, helper hoist) leave `driver_revision` untouched and every plane fresh → zero live re-proof. One-time migration for the recipe change is offline and guarded (§7) |
| 3. Minimal diff, no new concept | Same `driver_revision` field, same receipt schema, same plane dependency map, same nine `SurfaceRevisions` fields; no second hash system, no receipt kind, no config flag. The "new concept" is three data/decision blocks inside the existing recipe (§3) — every block is measured to earn its place (§6.2) |
| 4. Offline-testable | §5: five neutral edits must leave `SurfaceRevisions` byte-identical, one loosening edit must stale exactly `adapter`+`runtime`, plus a probe-declaration test. All offline, ~1 s each, on `_disposable_copy` |
| 5. Honesty | §10 states the exact residual (rules exercised by no declared probe; message-level edits invisible) and the compensating controls, instead of claiming full coverage |

---

## 1. Defect, with mechanism (all measured at 419fb36)

`driver_revision` is computed by `compute_surface_revisions` (`scripts/portability_schema.py:601-734`)
and is one of the inputs of the `adapter` and `runtime` planes
(`PLANE_SURFACE_DEPENDENCIES`, line 462). Its input set is the **bytes** of seven named scripts plus
`scripts/drivers/**/*.py`; the seventh name is `portability_schema.py` itself (block `:690-707`, the
name at `:698`).

* All five canonical receipts are fresh at trunk: stored `driver_revision` is
  `42e76079a9f3a70326c42ac56ea114e59f2b6037be117635ea714cc341b4fb6d` and recomputing yields exactly
  that value for grok/codex/omp/opencode/antigravity (verified by direct recomputation).
* Appending one comment line to `scripts/portability_schema.py` changes its bytes
  (`sha256` `06c3407a1749…` → `a6326fcba246…`), therefore changes `driver_revision`, therefore
  `check-evidence` fails for four hosts with `driver_revision mismatch`, therefore repair requires
  live runs on those hosts (omp needs `PSTACK_RUN_OMP_LIVE=1`).
* The same comment on `scripts/model_role_resolver.py` / `model_role_policy.py` changes nothing,
  because those files are not in the input set.

So today the *interpreter of evidence* is pinned by bytes exactly like the *producers of evidence*.
Text-only edits to the interpreter are indistinguishable from semantic ones, and both cost a live
six-host re-proof. The module is also the most-edited file in this program (#468, #465, #456), which
is why this lever matters.

## 2. Module boundary — exact names

### 2.1 New: `scripts/surface_revisions.py` (hashing/evidence machinery, ~420 lines prototype)

| Symbol | Kind | Origin |
|---|---|---|
| `SURFACE_DRIVER_FILES: Tuple[str, ...]` | constant (6 names) | the inline tuple at `portability_schema.py:690`, minus `portability_schema.py`, hoisted and named |
| `SURFACE_DRIVER_DIR = "scripts/drivers"` | constant | was inline |
| `compute_surface_revisions(root, host, profile_path=None) -> SurfaceRevisions` | function | moved verbatim from `portability_schema.py:601-734`, minus the schema entry, plus the `decisions` feed |
| `rule_surface_digest() -> str` | new | digest of the *values* of the rule constants |
| `_rule_payload() -> Dict[str, Any]` | new | `{"SETTLEMENT_PROMOTIONS": SETTLEMENT_PROMOTIONS, …}` — keys are literals here (stable vocabulary), values are direct references (a domain rename fails loudly at import) |
| `SETTLEMENT_ADMISSION_MATRIX: Tuple[Tuple[str, str, str, str], ...]` | new | 32 `(plane, level, verdict, outcome)` branches |
| `settlement_admission_decisions() -> Dict[str, Any]` | new | per branch, the sorted capabilities `_is_observed_settlement` admits |
| `gate_probe_decisions() -> Dict[str, Any]` | new | per `EVIDENCE_GATE_PROBES` entry: `{"gate": {"accepted": bool, "derived": str?}, "derived": str}` |
| `surface_decisions() -> Dict[str, Any]` | new | `{"rules": …, "settlements": …, "probes": …}` — the whole fingerprinted decision projection |
| `_gate_decision(root, profile, revisions)` | new | composed gate verdict, structure only (never message text) |
| `_probe_pin()`, `_gate_pin(spec)`, `_probe_receipt(spec, pin)`, `_probe_bindings(spec, host)`, `_jsonable(value)` | new helpers | synthetic probe root; no reads from, no writes into, the checked-in tree |

`compute_surface_revisions` keeps its signature and its other nine fields byte-for-byte; only the
`driver_revision` recipe changes:

```python
hasher = hashlib.sha256()
for fname in SURFACE_DRIVER_FILES:          # fact producers only
    ...
for p in sorted(drivers_dir.rglob("*.py")):
    ...
hasher.update(b"decisions")
hasher.update(json.dumps(surface_decisions(), sort_keys=True).encode("utf-8"))
driver_revision = hasher.hexdigest()
```

`driver_revision` stays **host-independent** (same value for all hosts), as today.

### 2.2 Changed: `scripts/portability_schema.py` (pure domain/validator)

Removed: `compute_surface_revisions` (`:601-734`), the 7-name inline tuple, `import hashlib` (line 9;
no other use remains).
Added (declarative data, next to `SETTLEMENT_PROMOTIONS`): `PROBE_RECEIPT`,
`PROBE_MISSING_RECEIPT`, `EVIDENCE_GATE_PROBES: Dict[str, Dict[str, Any]]` — nine entries, eight
refusing configurations plus one positive control:

`ceiling_state_above_evidence`, `dangling_receipt_reference`, `receipt_host_mismatch`,
`scenario_pin_absent`, `stale_driver_revision_refuses_claim`,
`stale_package_descriptor_refuses_supported` (refusals) and `verified_from_live_settlement`,
`omp_offline_only_stays_packaged`, `plane_failure_stays_packaged` (one accept, one refusal, one refusal).
Each entry carries compact data (`host`, `claimed`, `bindings: none|floor|universe`, `evidence_ref`,
optional `receipt_host`, `planes`, `scenarios`, `stale_field`, `write_receipt`); the machinery expands
it into a receipt on a temporary root.

`check_evidence_durability` (`:945`) and `derive_support_state` (`:801`) gain a two-line lazy import,
the only cycle-breaker needed:

```python
if current_revisions is None:
    from scripts.surface_revisions import compute_surface_revisions  # lazy: no import cycle
    current_revisions = compute_surface_revisions(root, profile.host)
```

Everything else stays put and stays unfingerprinted-by-bytes: all constants, all dataclasses,
`ValidationError`, `evaluate_plane_staleness` (`:584`), `check_scenario_pins` (`:908`),
`preserve_observed_settlements` (`:770`), `_is_observed_settlement` (`:736`),
`PLANE_SURFACE_DEPENDENCIES` (`:462`), `SurfaceRevisions` (`:446`), `VerificationReceipt` (`:541`).

### 2.3 Cutover of callers (no shims, no re-exports)

| Caller | Change |
|---|---|
| `scripts/verify-portable.py:35-50` | drop `compute_surface_revisions` from the schema import; `from scripts.surface_revisions import compute_surface_revisions` |
| `scripts/prove-omp-vertical-slice.py:73` | same migration |
| `tests/test_evidence_durability.py:14` | same migration |
| `scripts/package-lifecycle.py`, `sync-antigravity-plugin.py`, `model_role_policy.py`, `model_role_resolver.py`, `project-package.py`, `scaffold-verification-skill.py` | unchanged (they import domain constants only) |
| `scripts/verify-portable.py` `CHECK_SELECTION_TABLE` | add `("scripts/surface_revisions.py", ("tests/test_evidence_durability.py", "tests/test_portability_schemas.py"), ())`; keep the existing `scripts/portability_schema.py` row (still the schema/verdict/durability tests) |

## 3. The new fingerprint input set, and why each item is there

`driver_revision = sha256( drivers ‖ rule values ‖ settlement matrix ‖ gate probes )`

| Item | Verdict | Justification |
|---|---|---|
| `scripts/canonical-index.py` | keep | runs against the repo and writes canonical-plane facts (pin, inventory, drift) into receipts |
| `scripts/verify-portable.py` | keep | the run driver: `drive()` dispatches the per-host probes and writes the receipt |
| `scripts/verify-harness.py` | keep | the adapter/runtime harness checks whose PASS lines are the observed facts |
| `scripts/adapt-harness.py` | keep | produces the adapter-plane projection a live run compares against |
| `scripts/scaffold-verification-skill.py` | keep | creates the per-host verification skill that performs the live proof |
| `scripts/skill_frontmatter.py` | keep | parses the frontmatter the live proof depends on; its semantics gate skill acceptance |
| `scripts/drivers/**/*.py` | keep (unchanged) | the per-host probe implementations — the actual observations |
| **`scripts/portability_schema.py`** | **remove bytes** | it executes no host command, records no observation and writes no verdict into a receipt; it only *interprets* facts that the drivers already wrote. Its remaining claim-relevance is carried by the three decision inputs below |
| `rule_surface_digest()` | add | the declarative rule *values* (`SETTLEMENT_PROMOTIONS`, `MANDATORY_SUPPORT_FLOOR`, `CONDITIONAL_CAPABILITIES`, `PORTABLE_CAPABILITY_UNIVERSE`, `PLANE_SURFACE_DEPENDENCIES`, `HOSTS`, four enum tuples, `DEFAULT_SKILLS_DIRS`, `DEFAULT_PLUGIN_MANIFESTS`, `SKILLS_HASH_IGNORED_*`, `EVIDENCE_GATE_PROBES`, …): editing a rule is always a claim-affecting edit, and a value digest is immune to comments, reformatting and refactors |
| `settlement_admission_decisions()` | add | every branch of the promotion predicate (`plane × evidence_level × verdict × outcome`); measured to be the only thing that catches edits that loosen `_is_observed_settlement` |
| `gate_probe_decisions()` | add | nine declared configurations with their gate verdicts: the ceiling rule, dangling refs, cross-host receipts, absent scenario pins, driver/package staleness, omp offline-only, plane failure, plus one positive control. These are the guards that turn facts into claims |
| `scripts/surface_revisions.py` itself | **not hashed** | it *is* the recipe: any change to it moves every `driver_revision` (fail closed) — hashing it would be self-referential. Its correctness is proven by the offline tests |
| live evidence (`.audit/evidence/*-receipt.json`) | **not hashed (deliberate)** | see §9 alternative 4: including it is a bootstrapping bug, not extra integrity |

## 4. How the adapter and runtime planes react

`PLANE_SURFACE_DEPENDENCIES` is untouched, so the blast radius is the same shape as today:

* `adapter` = `profile_hash, driver_revision, boundary_driver_revision`; `runtime` = `skills_tree_hash,
  profile_hash, package_descriptor_hash, manifest_hash, driver_revision`; `canonical` and `package`
  do not read `driver_revision` and are unaffected by any schema edit.
* **Neutral edit** (comment, annotation, refactor, error-message reword, helper hoist): none of the
  four decision inputs moves → `driver_revision` identical → `evaluate_plane_staleness` returns no
  reasons for any plane → `check-evidence` exit 0, derived support states unchanged, zero live runs.
* **Claim-affecting edit** (rule value, predicate branch, guard, staleness branch): `driver_revision`
  changes → for every host whose claim binds a receipt, `stale_map["adapter"]` and `stale_map["runtime"]`
  become `driver_revision mismatch (…)`, so `check_evidence_durability` raises
  `Profile <host> evidence is stale for claimed <state>` for `verified`/`supported` hosts; `omp`
  (packaged) and `droid` (candidate) keep passing because their claims never consult
  `driver_revision` in the freshness block — exactly as today.
* Because `driver_revision` stays host-independent, a claim-affecting schema edit stales all hosts at
  once (as a byte edit does today). That is strictly narrower than today: *only* claim-affecting edits
  do it, instead of every edit.
* The migration (§7) changes every stored `driver_revision` once, and is repaired offline in the same
  commit, so no host is left stale by the split itself.

## 5. The exact offline test (proves both directions)

In `tests/test_evidence_durability.py` (reusing `_disposable_copy`, line 344), replacing the
`scripts/portability_schema.py` entry of the parametrize list at line 369:

```python
NEUTRAL_SCHEMA_EDITS = {
    "comment": lambda s: s + "\n# validation-only note about the settlement gate\n",
    "annotation": lambda s: s.replace(
        "def _is_observed_settlement(scenario, capability: Optional[str] = None) -> bool:",
        'def _is_observed_settlement(scenario: "ScenarioResult", capability: Optional[str] = None) -> bool:',
    ),
    "refactor": lambda s: s.replace(                      # behaviour-identical rename + hoist
        '    outcome = scenario.settlement.terminal_outcome\n'
        '    if outcome == "success":\n'
        "        return True\n"
        "    return capability is not None and outcome in SETTLEMENT_PROMOTIONS.get(capability, ())",
        '    terminal_outcome = scenario.settlement.terminal_outcome\n'
        "    admitted = SETTLEMENT_PROMOTIONS.get(capability, ()) if capability is not None else ()\n"
        '    if terminal_outcome == "success":\n'
        "        return True\n"
        "    return terminal_outcome in admitted",
    ),
    "message_reword": lambda s: s.replace(
        'f"Dangling evidence path for {profile.host}: {ref}"',
        'f"Evidence path {ref} for {profile.host} does not exist"',
    ),
    "helper_hoist": lambda s: s.replace(
        "    derived_state = derive_support_state(profile, root, current_revisions=current_revisions)",
        "    revisions = current_revisions\n"
        "    derived_state = derive_support_state(profile, root, current_revisions=revisions)",
    ),
}


@pytest.mark.parametrize("edit_name", sorted(NEUTRAL_SCHEMA_EDITS))
def test_validation_only_schema_edit_stays_hash_neutral(tmp_path: Path, edit_name: str) -> None:
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "codex")
    # Same construction as test_driver_source_change_invalidates_adapter_and_runtime (line 369):
    # VerificationReceipt(run_id="driver-fingerprint-regression", host="codex", …,
    #                     surface_revisions=fresh, planes={p: "PASS" for p in CONFORMANCE_PLANES})
    receipt = _codex_receipt(fresh)
    schema = copy_root / "scripts" / "portability_schema.py"
    original = schema.read_text(encoding="utf-8")
    edited = NEUTRAL_SCHEMA_EDITS[edit_name](original)
    assert edited != original, "edit under test did not apply"

    schema.write_text(edited, encoding="utf-8")
    after = compute_surface_revisions(copy_root, "codex")

    assert after == fresh                                 # direction 1: nothing moved
    assert {p for p, r in receipt.evaluate_plane_staleness(after).items() if r} == set()


def test_behaviour_affecting_schema_edit_invalidates_adapter_and_runtime(tmp_path: Path) -> None:
    """Loosening the settlement predicate must stale the claims that relied on it."""
    copy_root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(copy_root, "codex")
    receipt = _codex_receipt(fresh)
    schema = copy_root / "scripts" / "portability_schema.py"
    original = schema.read_text(encoding="utf-8")
    loosened = original.replace(
        "        and scenario.verdict == \"PASS\"\n",
        "",                                              # a settlement now admits a FAILED scenario
        1,
    )
    assert loosened != original

    schema.write_text(loosened, encoding="utf-8")
    edited = compute_surface_revisions(copy_root, "codex")

    assert edited.driver_revision != fresh.driver_revision            # direction 2
    stale_map = receipt.evaluate_plane_staleness(edited)
    assert {p for p, r in stale_map.items() if r} == {"adapter", "runtime"}
    assert all(stale_map[p][0].startswith("driver_revision mismatch") for p in ("adapter", "runtime"))

    schema.write_text(original, encoding="utf-8")                     # and it is reversible
    assert compute_surface_revisions(copy_root, "codex") == fresh


def test_declared_gate_probes_refuse_what_they_declare() -> None:
    from scripts.surface_revisions import gate_probe_decisions

    decisions = gate_probe_decisions()
    assert decisions["verified_from_live_settlement"]["gate"]["accepted"] is True
    for probe in (
        "ceiling_state_above_evidence",
        "dangling_receipt_reference",
        "receipt_host_mismatch",
        "scenario_pin_absent",
        "stale_driver_revision_refuses_claim",
        "stale_package_descriptor_refuses_supported",
        "omp_offline_only_stays_packaged",
        "plane_failure_stays_packaged",
    ):
        assert decisions[probe]["gate"]["accepted"] is False, probe
```

Both tests are offline, need no host binary, take ~1 s each, and reuse the existing fixture helpers.
The third test is what keeps the probe declarations honest: it fails if a probe is edited to hide a
weakening (the probe *values* are also in `rule_surface_digest()`, so editing them moves the
fingerprint as well).

## 6. Measured evidence (prototype, disposable copies of 419fb36)

### 6.1 Both directions, 17 behaviour edits + 5 neutral edits

`python3 battery.py` in `/home/tommyk/.tmp-pstack-429/arena`. Baseline
`driver_revision = 4935e7860791c44f9a5b14740988da9c50a96ae5ab0242387f22eb0373ac2a7e` (prototype; the
merged value will differ because the prototype file differs slightly from the final implementation).

Neutral — all `unchanged`: `comment-only`, `type-hint-only`, `refactor-equivalent` (rename + hoist in
the predicate), `message-reword` (`ValidationError` text), `helper-extraction` (hoist a local in
`check_evidence_durability`).

Claim-affecting — `CHANGED` (15 of 17): `settlement:drop-verdict-check`, `settlement:drop-plane-check`,
`settlement:drop-evidence-level`, `rule-data:promotion-flip`, `rule-data:floor-drop-verify`,
`rule-data:hosts-drop-droid`, `gate:drop-ceiling`, `gate:drop-dangling-guard`,
`gate:drop-host-mismatch`, `gate:drop-scenario-pin`, `staleness:ignore-driver-revision`,
`staleness:ignore-package-descriptor`, `derive:drop-omp-live-requirement`,
`derive:drop-plane-pass-requirement`, `derive:drop-derived-staleness-check`.
Invariant preserved: a comment on `scripts/verify-harness.py` still moves `driver_revision`.

The two `unchanged` cases are `gate:drop-refs-guard` and `gate:drop-stale-details`; §10 explains why
they are outcome-neutral (the ceiling rule refuses the same configurations) rather than holes.

### 6.2 Marginal value of each added input (measured by removing one block at a time)

| Block removed | Behaviour edits still caught |
|---|---|
| none (design as proposed) | 15 / 17 |
| `gate_probe_decisions()` | 6 / 17 |
| `settlement_admission_decisions()` | 12 / 17 |
| `rule_surface_digest()` | 13 / 17 |

Every block earns its place; the probes are 9 of the 15 catches and are the integrity core.

### 6.3 Migration demonstration (`migrate-demo.py`, zero live runs)

```
pre-split recipe, recomputed from HEAD bytes : 42e76079a9f3a70326c42ac56ea114e59f2b6037be117635ea714cc341b4fb6d
post-split recipe (migration target)         : 4935e7860791c44f9a5b14740988da9c50a96ae5ab0242387f22eb0373ac2a7e

before migration: grok/codex/opencode/antigravity FAIL (driver_revision mismatch), omp PASS, droid PASS
guard           : codex-1791322741-shim-fail-receipt.json left stale (90309fc4223e != pre-split recipe)
rewritten       : 5 receipts (grok, codex, omp, opencode, antigravity)
index.json      : 5 host entries revision-migrated (.audit/evidence/index.json mirrors the receipt surface)
after migration : all six hosts PASS — grok supported, codex verified, omp packaged,
                  opencode verified, antigravity verified, droid candidate
```

The index step is required, not cosmetic: `test_durable_receipts_exist_for_all_five_hosts` fails with
`index revisions stale for grok` until `.audit/evidence/index.json` carries the migrated
`driver_revision` for each host. With both steps applied, `tests/test_evidence_durability.py` is
**1 failed / 55 passed**, the single failure being the intended contract change of §6.4.

The post-migration output is identical to the trunk `check-evidence` matrix recorded in
`/home/tommyk/.tmp-pstack-429/ce-all.txt` — the facts did not change, only the recipe.

### 6.4 Existing suites in a post-cutover, post-migration copy

`pytest tests/test_evidence_durability.py tests/test_portability_schemas.py tests/test_verify_portable.py`
→ **5 failed, 93 passed**. Attribution, measured rather than assumed:

| Failure | Attribution |
|---|---|
| `test_evidence_durability.py::test_driver_source_change_invalidates_adapter_and_runtime[scripts/portability_schema.py]` | **intended**: it asserts exactly the behaviour this design removes (a comment in the schema file moving `driver_revision`). `scripts/portability_schema.py` leaves that parametrize list; the tests in §5 take over its contract |
| `test_verify_portable.py::{test_portable_verifier_antigravity, test_portable_verifier_droid, test_portable_verifier_drives_verification_skill_scaffolding_across_hosts, test_portable_verifier_cli_host_all_doctor}` | **copy artifacts**: the same four fail identically in a *pristine* copy of 419fb36 prepared with the same reduced file selection (`.audit/evidence` minus 849 run artifacts, no `.venv`/`.git`), with no design change applied |

`tests/test_evidence_durability.py` alone, post-cutover and post-migration, is **1 failed / 55 passed**
(only the intended entry). Every other durability test — all six profiles, all staleness directions,
all synthetic-root gates — passes against the new recipe.

## 7. Regeneration cost and the one-time migration

* Steady state after the split: **claims-affecting** validator edits invalidate adapter+runtime claims
  and need re-derivation (offline: `check-evidence` re-runs and either passes or names the host to
  demote); **validation-only** edits are free — that is the whole point of the lever.
* One-time cost: changing the recipe changes the stored `driver_revision` of every fresh receipt
  (5 files) and of the five host entries in `.audit/evidence/index.json`, which mirrors the receipt
  surface. The design repairs that **offline**, not with six live runs, and guards it:
  1. recompute the pre-split recipe from the parent commit's bytes
     (`git show HEAD~1:scripts/<driver>.py`) and assert it equals each receipt's stored value;
  2. only then rewrite `surface_revisions.driver_revision` in that receipt, and the matching entry in
     `.audit/evidence/index.json`;
  3. leave every receipt whose stored value differs (e.g. the stale
     `codex-1791322741-shim-fail-receipt.json`) exactly as it is.
  The guard can never launder a genuinely stale receipt, because a receipt is only rewritten when the
  bytes that produced it still hash to its stored value. The rewritten fingerprints, the guard output
  and the post-migration `check-evidence` matrix go in the PR body as the migration evidence. This is
  also the reason `.audit/evidence` is not part of the fingerprint (§3, alternative 4).
* If a reviewer prefers zero receipt edits, the alternative is one live run per host — and the
  `driver_revision` still moves, so the receipts must be rewritten either way. Offline migration is
  the only variant that does not require the live proof the arena exists to avoid.

## 8. Diff size estimate

| File | Lines | Nature |
|---|---|---|
| `scripts/surface_revisions.py` | **+421 new** (~120 moved verbatim from `portability_schema.py:601-734`; ~300 new: docstring/imports ~45, `_rule_payload` 27, `rule_surface_digest`/`_jsonable` 25, matrix 30, `_gate_decision` 10, probe runner 90, `surface_decisions` 15, remaining moved body ~120) | split + decision projection |
| `scripts/portability_schema.py` | **−134 / +78 / −1 import** (remove `compute_surface_revisions` and the inline tuple; remove `import hashlib`; add `PROBE_*` + `EVIDENCE_GATE_PROBES`, 72 lines measured; add two lazy imports with comments) | boundary |
| `scripts/verify-portable.py` | +2 / −1 | import migration + one `CHECK_SELECTION_TABLE` row |
| `scripts/prove-omp-vertical-slice.py` | +1 / −1 | import migration |
| `tests/test_evidence_durability.py` | +1 / −1 import, +~95 (two new tests + probes test, minus the removed parametrize entry) | contract |
| `.audit/evidence/*-receipt.json` | 5 × 1 field | one-time recipe migration |
| `.audit/evidence/index.json` | 5 × 1 field | one-time recipe migration |
| **net** | **≈ +465** (of which ~370 is the new module and its tests) | no new dependency, no schema change, no new receipt field |

## 9. Rejected alternatives (mandatory rationale)

1. **Normalise the schema's bytes (AST with comments/docstrings/annotations stripped) before
   hashing.** Rejected: it fixes comments but not refactors — renaming a local or hoisting a call
   changes the AST, and rubric 2 requires refactors to be free; and it introduces a canonicalisation
   layer whose own correctness is unaudited (a second hashing system in substance). It hashes source
   text, not behaviour.
2. **Exemption/allowlist registry (hash only the functions of `portability_schema.py` thought to
   matter).** Rejected: a new concept (a per-function fingerprint registry), unmechanisable judgement
   ("is `derive_support_state` still claim-relevant?"), and it silently drops coverage for everything
   not listed. The split already gives a *mechanical* boundary: whatever the machinery consumes stays
   fingerprinted, whatever only interprets facts is not.
3. **Remove `portability_schema.py` from the input set and stop there (split with no replacement).**
   Rejected: measured — the rule surface then has no coverage at all (rule edits, promotion-table
   flips, guard removals invalidate nothing; 6 of the 15 measured catches disappear), which is the
   rubric-1 violation the arena forbids. This is the minimal-but-wrong variant; the three decision
   inputs are what make the split honest.
4. **Fingerprint a decision digest over the checked-in receipts (`.audit/evidence/**`).** Rejected as
   a bootstrapping bug, not as a nicety: `compute_surface_revisions` runs *before* a refresh writes
   the new receipt, so the freshly written receipt would be stale the moment it lands, and a change in
   any host's evidence would move every host's fingerprint — trading text-edit re-proofs for
   evidence-refresh re-proofs. The declared probes give the same rule coverage with no live input.
5. **Add a "schema tag" to the receipt and compare tags instead of bytes.** Rejected: a new receipt
   field (rubric 3 forbids a new receipt kind) and the same integrity hole as alternative 3 — a tag
   that is not derived from behaviour cannot observe a loosened rule.
6. **Bless the current state: rewrite the receipts (or run with `--allow-stale`) whenever the schema
   changes.** Rejected: `--allow-stale` removes the gate; blanket receipt rewriting is laundering.
   The *narrow* version of this — the guarded one-time recipe migration of §7 — is kept, because it
   runs only when the bytes that produced each receipt still hash to the stored value, so it cannot
   mask drift.
7. **Keep the bytes but hash a normalised *runtime* projection (e.g. re-emit the module through
   `compile()`/bytecode).** Rejected: bytecode still moves for type hints and reordering, is
   version-dependent (a new CPython would stale every receipt for no semantic reason), and inherits
   alternative 1's unaudited canonicalisation.

## 10. Honest residual (what this design does not catch)

The fingerprint now covers: driver bytes; the **values** of the declarative rules; the 32-branch
settlement matrix; and nine declared gate probes. It does **not** cover:

* validator behaviour on a configuration that is neither a rule value nor a declared probe. Measured
  examples: `gate:drop-refs-guard` ("claims verified but declares no evidence references") and
  `gate:drop-stale-details` — both are outcome-neutral *on all declared configurations*, because the
  derived-state ceiling refuses the same shapes, so no decision moves. A rule that only a host shape
  absent from `EVIDENCE_GATE_PROBES` would exercise (a new harness, a new plane verdict, a new
  scenario shape) is likewise invisible.
* diagnostics: a reworded `ValidationError` is deliberately invisible (rubric 2 needs that), so an
  edit that changes *which* refusal fires without changing accept/reject is not fingerprinted. This is
  a conscious trade, not an oversight: the assertion this design protects is "the same claims are
  accepted and refused", not "the same error text appears".

Compensating controls, all existing or one line long: CI check selection routes
`scripts/portability_schema.py` to `tests/test_portability_schemas.py`,
`tests/test_verdict_reduction.py` and `tests/test_evidence_durability.py`
(`scripts/verify-portable.py:189-197`), so a claim-affecting edit that demotes a host fails
`test_all_six_profiles_pass_evidence_durability_and_freshness` immediately; and
`EVIDENCE_GATE_PROBES` is the extension point — every new host or claim shape should add its refusing
configuration there, which is data (six lines) and is itself fingerprinted and asserted by
`test_declared_gate_probes_refuse_what_they_declare`. That is also the natural consumer of #444's
offline parity fixtures.

## 11. Implementer checklist

1. Create `scripts/surface_revisions.py` (prototype reference:
   `/home/tommyk/.tmp-pstack-429/arena/proto/scripts/surface_revisions.py`).
2. Delete `compute_surface_revisions` from `scripts/portability_schema.py`; add `PROBE_RECEIPT`,
   `PROBE_MISSING_RECEIPT`, `EVIDENCE_GATE_PROBES`; add the two lazy imports.
3. Migrate the three caller imports; add the `CHECK_SELECTION_TABLE` row.
4. Replace the `scripts/portability_schema.py` parametrize entry with the two new tests; add the
   probe-declaration test.
5. Run the guarded one-time receipt migration; capture the guard output and the six-host
   `check-evidence` matrix as migration evidence.
6. Run `pytest tests/test_evidence_durability.py tests/test_portability_schemas.py
   tests/test_verdict_reduction.py tests/test_select_checks.py` and a full offline suite.
