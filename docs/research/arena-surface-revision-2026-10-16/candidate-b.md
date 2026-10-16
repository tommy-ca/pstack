# Candidate B — SEPARATE REVISION (`validator_revision`)

Trunk: `419fb36` (repo `/home/tommyk/projects/pstack`). Design only: no edits, no branches, no commits.
Direction taken: **keep byte hashing**, remove `scripts/portability_schema.py` from `driver_revision`, give it
its own revision that gates static/offline claims only, never live ones.

---

## 1. Verdict up front

| Property | Result |
|---|---|
| `grok`/`codex`/`opencode`/`antigravity` after a comment-only edit to `portability_schema.py` | **fully neutral**: `check-evidence --host <h>` stays exit 0, zero action. (`grok` is the reproduced acceptance case.) |
| `omp` after the same edit | `check-evidence --host omp` exits 1 until **one offline restamp** of `.audit/evidence/omp-receipt.json` + `index.json` revision blocks — **zero live runs** (`PSTACK_RUN_OMP_LIVE=0`), live settlements preserved by `preserve_observed_settlements` (`portability_schema.py:770-799`). |
| `droid` | nothing (profile `candidate`, no `evidence_ref`, no receipt). |
| Live re-proofs required by comment/refactor/type-hint edits | **0** |
| Live claims invalidated by a *behavior-affecting* validator edit | **none** — this is the exact weakening, stated in §8. |

`check_evidence_durability` hard-fails any profile claiming `verified`/`supported` when a receipt is stale on
`canonical`/`adapter`/`runtime` (`portability_schema.py:993-1008`), and `derive_support_state` demotes on the same
three planes (`:857-870`). Those are the only paths that can force host runs, and after this change none of them
reads the new field.

---

## 2. How the coupling works today (grounding)

* `SurfaceRevisions` (`scripts/portability_schema.py:446-459`) — 10 fields, `to_dict()` = `asdict`.
* `PLANE_SURFACE_DEPENDENCIES` (`:462-484`): `adapter` and `runtime` both list `driver_revision`; `canonical` lists
  `canonical_pin, spec_hash`; `package` lists `package_descriptor_hash, manifest_hash, package_driver_revision`.
* `compute_surface_revisions` step 8 (`:689-709`) hashes **file bytes** of `canonical-index.py`, `verify-portable.py`,
  `verify-harness.py`, `adapt-harness.py`, `scaffold-verification-skill.py`, `skill_frontmatter.py`,
  **`portability_schema.py`** (`:698`), plus `scripts/drivers/*.py` → one `driver_revision`.
* `VerificationReceipt.__post_init__` (`:556`) rebuilds `SurfaceRevisions(**self.surface_revisions)`; the receipt
  schema closes `surface_revisions` with `additionalProperties: false` (`schemas/portability/receipt.schema.json:50-74`).
* `evaluate_plane_staleness` (`:584-598`) compares receipt vs current per plane; `check_evidence_durability` turns that
  into the hard failure above; `derive_support_state` (`:803-870`) re-derives `packaged`/`verified`/`supported`.
* `check_scenario_pins` (`:908-942`) is the only place that resolves a binding to an individual
  `ScenarioResult`: it skips bindings with no `scenario_id` (`:919-921`) and, for `verified` rows, requires
  `_is_observed_settlement(scenario, capability)` (`:736-756`).
* Evidence on disk: `grok|codar|omp|opencode|antigravity-receipt.json` + `index.json` (5 host entries). `droid` has no
  receipt. `full-suite-20261012-receipt.json` is not a `VerificationReceipt` (no `surface_revisions`);
  `codex-1791322741-shim-fail-receipt.json` is one but is referenced by no profile/ledger — it needs no migration
  and must keep loading (see §5, default-safe field).

Consequence of the current coupling: any byte change to the 1031-line validator — comment, docstring, `Optional[str]`
→ `str | None` — flips `driver_revision`, stales `adapter` + `runtime`, and demands a live re-run on six hosts.

---

## 3. The change

### 3.1 Field

**Name: `validator_revision`.** Chosen to parallel the existing `driver_revision` / `package_driver_revision` /
`boundary_driver_revision` trio and to name *what* it covers (the admission/validation layer), not *where it lives*.
Placed immediately after `driver_revision` in `SurfaceRevisions`.

```python
# scripts/portability_schema.py:446-459
    driver_revision: str
    validator_revision: str = ""       # default-safe: pre-migration receipts still construct
    package_driver_revision: str
```
A dataclass default is required, not cosmetic: `VerificationReceipt.__post_init__` (`:556`) does
`SurfaceRevisions(**rdata["surface_revisions"])`, so every receipt already checked in under `.audit/evidence/`
(853 files plus `index.json`)
must still load. `""` means *unrecorded*.

### 3.2 Computation (step 8/8b, `:689-709`)

```python
# 8. driver revision  — the PROVERS: unchanged, minus the validator
    for fname in (
        "canonical-index.py",
        "verify-portable.py",
        "verify-harness.py",
        "adapt-harness.py",
        "scaffold-verification-skill.py",
        "skill_frontmatter.py",
    ):                                   # "portability_schema.py" REMOVED
        ...
    driver_revision = hasher.hexdigest()

# 8b. validator revision — the ADMISSION layer, same framing, single file
    v_hasher = hashlib.sha256()
    v_file = root / "scripts" / "portability_schema.py"
    if v_file.is_file():
        v_hasher.update(b"portability_schema.py")
        v_hasher.update(v_file.read_bytes())
    validator_revision = v_hasher.hexdigest()
```
Same `name||bytes` framing as step 8 (no new digest recipe, rubric 3). `scripts/drivers/*.py` stay in
`driver_revision`; `verify-portable.py`/`verify-harness.py` — the code that *produces* live observations — stay in
`driver_revision`, so live planes remain gated on the prover, not on the validator.

### 3.3 Consumers (exhaustive)

| Consumer | Line | Read of `validator_revision` |
|---|---|---|
| `SurfaceRevisions.to_dict()` → receipt + `index.json` serialization | `:458` | writes |
| `VerificationReceipt.__post_init__` | `:556` | loads (default-safe) |
| `compute_surface_revisions` return | `:724-735` | writes |
| `check_scenario_pins` (gate below) | `:908-942` | compares |
| `schemas/portability/receipt.schema.json` `surface_revisions.properties` | `:50-74` | declares (property, **not** `required`) |
| tests (§6) | — | asserts |

Explicit **non-consumers**, and this is the integrity mechanism, not an omission:

* `PLANE_SURFACE_DEPENDENCIES` (`:462-484`) — **unchanged**. `validator_revision` is in no plane tuple.
* `evaluate_plane_staleness` (`:584-598`) — never sees it ⇒ the field can never mark a plane stale, including `runtime`.
* `derive_support_state` (`:803-870`) and the freshness hard-fail (`:993-1008`) — untouched.
* `preserve_observed_settlements` (`:770-799`) — its runtime-plane gate (`:788`) is unchanged, therefore a validator
  edit never drops a carried `observed_live` settlement ⇒ an offline restamp stays offline.
* `verify-portable.py` CLI (`:1057-1105`), `prove-omp-vertical-slice.py:685` — flow through `compute_surface_revisions`;
  no changes.

### 3.4 The gate (the only behaviour `validator_revision` adds)

```python
def check_scenario_pins(profile, receipts_by_ref, current_revisions: SurfaceRevisions) -> None:
    """... existing docstring ... plus:
    A scenario-pinned claim whose pinned row is NOT an observed_live settlement is admitted by
    the validator revision recorded in its receipt. A different current validator does not
    re-prove or un-prove that static/offline row; it only means the offline admission is owed a
    refresh, which needs no host run. observed_live rows are never gated this way: the current
    validator re-judges them at every check run.
    """
    for binding in profile.bindings:
        scenario_id = binding.scenario_id
        if not scenario_id:
            continue                      # receipt-level (bare-path) claims are never gated
        ...
        live = _is_observed_settlement(scenario, binding.capability)
        if binding.verification_status == "verified" and not live:
            raise ValidationError(...)     # existing :936-942
        if not live:
            recorded = receipt.surface_revisions.validator_revision
            if recorded != current_revisions.validator_revision:
                raise ValidationError(
                    f"Binding for {binding.capability} on {binding.host} pins static/offline "
                    f"scenario {scenario_id!r} admitted by validator_revision "
                    f"{recorded[:8] or 'unrecorded'}..., current "
                    f"{current_revisions.validator_revision[:8]}...; refresh offline "
                    f"(observed_live settlements are preserved, no live run)"
                )
```
Call site: `check_evidence_durability` `:1022` → `check_scenario_pins(profile, receipts_by_ref, current_revisions)`
(`current_revisions` is already computed at `:983`). Signature becomes required (no `None` bypass), which costs 9
mechanical call-site updates in `tests/test_evidence_durability.py` (`:682, :698, :1108, :1114, :1127, :1140, :1143,
:1154, :1200`), each passing that test's own `compute_surface_revisions(ROOT, "omp")` as the current value.

Gate is **fail-closed on the gated set, fail-open on live rows**: `""`/unrecorded counts as a mismatch, but only ever
for a non-settlement pin. Consequence for `omp`: its two pinned static rows — `verify` → `doctor-profile-omp`
(adapter plane, `offline`, binding `static-only`) and `evidence.capture` → `runtime-evidence-capture-omp`
(runtime plane, `offline`, binding `static-only`) — are the only claims in the repo this gate can ever fire on.

### 3.5 Planes it may / may not gate

* **May gate:** claims whose pinned proof is static/offline/legacy, whatever plane they sit on. Gating keys on
  `ScenarioResult.evidence_level` (`:519`, `:530`), the schema's evidence-strength vocabulary, **not** on plane.
  `evidence.capture` is runtime-plane but `offline` evidence with binding status `static-only`; `derive_support_state`
  already refuses to promote on it, so it is a static claim that happens to be recorded on the runtime plane.
* **May not gate:** any claim pinned to a `_is_observed_settlement` row (`observed_live` + typed `ChildSettlement` +
  `PASS`, with `SETTLEMENT_PROMOTIONS` for cancel-style rows, `:59`, `:736-756`), and any *plane* whatsoever —
  structurally impossible, since the field is in no `PLANE_SURFACE_DEPENDENCIES` tuple.

---

## 4. Why this is as far as this direction goes

Byte hashing is **file-granular and change-blind**: it cannot distinguish a comment from a widened predicate. Two
consequences, both unavoidable inside this direction:

1. To be neutral for a comment edit, the validator must leave every plane tuple. Once it does, no hash-based
   mechanism can invalidate a live claim on a validator change — hence `validator_revision` is necessarily a
   *recorded stamp plus a cheap-claim gate*, never a live-claim invalidation. §8 states exactly what that loses.
2. Therefore the second direction of the required proof ("behaviour-affecting edit invalidates") cannot be witnessed
   by `validator_revision` at all — it must come from fixtures that pin the admission predicates' *behaviour*, which
   is what §6 does, and from the fact that a *stricter* validator is self-enforcing: it is applied to the checked-in
   receipts on the very next `check-evidence` run, offline, with no hash involvement.

---

## 5. Migration story for the checked-in receipts

Files to migrate: **`.audit/evidence/{grok,codex,omp,opencode,antigravity}-receipt.json` + `.audit/evidence/index.json`**
(5 host entries with their own `surface_revisions` blocks) = **6 files**. `droid` has no receipt
(`profiles/droid.json` is `candidate` with no `evidence_ref`, `:1-6` of that file); `full-suite-20261012-receipt.json`
is not a `VerificationReceipt`; `codex-1791322741-shim-fail-receipt.json` is referenced by no profile/ledger and needs
no restamp (it keeps loading via the `validator_revision` default).

**Step 0 — offline precondition (the honest part).** Before touching any value, prove that nothing in the hashed
surface moved since capture, so the restamp cannot launder a stale prover:

```bash
# legacy definition, run once, NOT shipped: same tuple as :690-709 including "portability_schema.py"
python3 - <<'PY'
import hashlib, json, pathlib
root = pathlib.Path(".")
h = hashlib.sha256()
for f in ("canonical-index.py","verify-portable.py","verify-harness.py","adapt-harness.py",
          "scaffold-verification-skill.py","skill_frontmatter.py","portability_schema.py"):
    p = root/"scripts"/f
    h.update(f.encode()); h.update(p.read_bytes())
for p in sorted((root/"scripts"/"drivers").rglob("*.py")):
    h.update(p.relative_to(root/"scripts"/"drivers").as_posix().encode()); h.update(p.read_bytes())
legacy = h.hexdigest()
assert all(json.loads(pathlib.Path(f).read_text())["surface_revisions"]["driver_revision"] == legacy
           for f in (".audit/evidence/grok-receipt.json", ".audit/evidence/codex-receipt.json",
                     ".audit/evidence/omp-receipt.json", ".audit/evidence/opencode-receipt.json",
                     ".audit/evidence/antigravity-receipt.json"))
assert all(e["surface_revisions"]["driver_revision"] == legacy
           for e in json.loads(pathlib.Path(".audit/evidence/index.json").read_text())["hosts"].values())
print("legacy digest", legacy)
PY
```
This holds today (`check-evidence` is green at trunk), i.e. all driver bytes equal capture bytes, so re-stamping the
revision block from current bytes is a *definitional* update, not a claim about a moved surface.

**Step 1 — restamp the revision block only** (a ~10-line one-shot using `compute_surface_revisions(root, host)`; not
shipped): for each of the 6 files, replace `surface_revisions` with the freshly computed dict, preserving the file's
existing 2-space JSON indent and key order, leaving `run_id`, `timestamp`, `host_version`, `planes`, `scenarios`,
`artifacts`, `claim`, `kind` untouched. Two fields per host change: `driver_revision` (because the tuple definition
changed) and the new `validator_revision`.

Why in-place restamp rather than the existing rewrite path (`PortableVerifier.evidence(..., update_durable=True)`,
`verify-portable.py:994-1035` + `_static_refresh_receipt`, `tests/test_evidence_durability.py:876-886`): that path
restates every scenario as static evidence and rewrites `run_id`/`timestamp`, a much larger diff over five receipts for
no gain. The rewrite path stays the *runtime* answer whenever a real scenario must be re-observed; for a definitional
revision change it is overkill.

**Step 2 — offline verification, no host runs:**

```bash
python3 scripts/verify-portable.py check-evidence        # all five hosts repo-wide
python3 -m pytest tests/test_evidence_durability.py -q
```
`check-evidence` is fully offline (it only reads files and re-derives revisions/staleness). The test
`test_durable_receipts_exist_for_all_five_hosts` (`:80-106`) additionally asserts
`index_data["hosts"][host]["surface_revisions"] == receipt["surface_revisions"]` — the cross-file check that catches a
half-done restamp. `test_all_six_profiles_pass_evidence_durability_and_freshness` (`:109-140`) is what makes the
`omp` obligation self-enforcing afterwards: edit the validator without restamping and `pytest` goes red offline.

**Post-migration steady state:** comment/refactor/type-hint edit to `portability_schema.py` → `grok`, `codex`,
`opencode`, `antigravity`, `droid`: `check-evidence` exit 0, no action. `omp`: one offline restamp of its revision
block (settlements preserved by `preserve_observed_settlements`, `:770-799`, because runtime-plane deps are unchanged).
**No `PSTACK_RUN_OMP_LIVE=1` run, ever, for a validation-only edit.**

---

## 6. The offline test proving both directions

Add to `tests/test_evidence_durability.py` (helpers already exist: `_disposable_copy` `:344-353`, `ROOT`, the
`check_evidence_durability` import block `:14-33`). No host, no model, no network.

```python
SCHEMA = "scripts/portability_schema.py"
PROVERS = ("scripts/verify-portable.py", "scripts/verify-harness.py", "scripts/drivers/base.py")

def _host_profile(root: Path, host: str) -> HarnessProfile:   # same shape as _omp_profile, :168-182
    d = json.loads((root / "profiles" / f"{host}.json").read_text(encoding="utf-8"))
    return HarnessProfile(
        host=d["host"], support_state=d["support_state"],
        bindings=[Binding(**x) for x in d["bindings"]],
        skills_dir=d.get("skills_dir"), plugins_dir=d.get("plugins_dir"),
        plugin_manifest=d.get("plugin_manifest"),
        evidence_ledger=[Evidence(**x) for x in d.get("evidence_ledger", [])],
        tool_mappings=d.get("tool_mappings"), skill_order=d.get("skill_order"),
        runtime_conventions=d.get("runtime_conventions"),
    )

def test_comment_only_schema_edit_is_hash_neutral(tmp_path: Path) -> None:
    """Direction 1: a validation-only edit costs zero live re-proof and zero staleness."""
    root = _disposable_copy(tmp_path)                                   # :344-353
    fresh = compute_surface_revisions(root, "grok")
    profile = _host_profile(root, "grok")
    assert check_evidence_durability(profile, root, current_revisions=fresh)["derived_support_state"] == "supported"

    schema = root / SCHEMA
    original = schema.read_text(encoding="utf-8")
    schema.write_text(original + "\n# validation-only comment\n", encoding="utf-8")
    edited = compute_surface_revisions(root, "grok")

    assert edited.driver_revision == fresh.driver_revision              # prover surface untouched
    assert edited.validator_revision != fresh.validator_revision        # only the stamp moves
    assert edited == replace(fresh, validator_revision=edited.validator_revision)

    receipt = VerificationReceipt(**json.loads((root / ".audit/evidence/grok-receipt.json").read_text()))
    assert [p for p, reasons in receipt.evaluate_plane_staleness(edited).items() if reasons] == []
    after = check_evidence_durability(profile, root, current_revisions=edited)   # no ValidationError raised
    assert after["derived_support_state"] == "supported"
    assert all(not reasons for planes in after["staleness"].values() for reasons in planes.values())

    schema.write_text(original, encoding="utf-8")
    assert compute_surface_revisions(root, "grok") == fresh             # reversible

@pytest.mark.parametrize("relative_path", PROVERS)
def test_prover_edit_still_invalidates_live_planes(tmp_path: Path, relative_path: str) -> None:
    """Direction 1 guard: the split must not de-hash the code that produces live observations."""
    root = _disposable_copy(tmp_path)
    fresh = compute_surface_revisions(root, "codex")
    receipt = VerificationReceipt(
        run_id="split-guard", host="codex", host_version="test", timestamp="2026-10-16T00:00:00Z",
        overall_verdict="PASS", planes={p: "PASS" for p in CONFORMANCE_PLANES}, surface_revisions=fresh,
    )
    f = root / relative_path
    f.write_bytes(f.read_bytes() + b"\n# changed verification behaviour\n")
    edited = compute_surface_revisions(root, "codex")

    assert edited.driver_revision != fresh.driver_revision
    assert edited.validator_revision == fresh.validator_revision
    assert {p for p, r in receipt.evaluate_plane_staleness(edited).items() if r} == {"adapter", "runtime"}

def test_static_pinned_claim_is_gated_by_validator_revision() -> None:
    """Direction 2 (gate half): a static/offline pin owed a validator refresh fails; a live pin never does."""
    ref = ".audit/evidence/omp-receipt.json"
    receipt = VerificationReceipt(**json.loads((ROOT / ref).read_text(encoding="utf-8")))
    profile = _omp_profile()                                            # :168-182
    revs = compute_surface_revisions(ROOT, "omp")

    check_scenario_pins(profile, {ref: receipt}, revs)                  # matched revision: passes
    stale = replace(revs, validator_revision="0" * 64)
    with pytest.raises(ValidationError, match="admitted by validator_revision"):
        check_scenario_pins(profile, {ref: receipt}, stale)

    # Control: the three observed_live pins are exempt, so a validator mismatch alone never
    # invalidates a live claim.
    live_ids = {s.id for s in receipt.scenarios if _is_observed_settlement(s)}
    live_only = replace(profile, bindings=[b for b in profile.bindings
                                           if not b.scenario_id or b.scenario_id in live_ids])
    check_scenario_pins(live_only, {ref: receipt}, stale)

def test_admission_predicate_is_behaviourally_pinned() -> None:
    """Direction 2 (semantics half). Byte hashing cannot tell a comment from a widened predicate, so the
    predicate's truth table is pinned explicitly: widening `_is_observed_settlement` fails here, offline."""
    def s(level: str | None, verdict: str = "PASS", settlement=None, plane: str = "runtime"):
        return ScenarioResult(id="probe", description="probe", plane=plane, command="probe",
                              exit_code=0, stdout_snippet="", verdict=verdict, duration_s=0.0,
                              evidence_level=level, settlement=settlement)
    settled = _success_settlement()                                     # existing helper, :1053-1060
    assert _is_observed_settlement(s("observed_live", settlement=settled)) is True
    assert _is_observed_settlement(s("observed_live", settlement=settled), "agent.spawn") is True
    for level in ("static", "offline", "legacy", None):                 # a passing call is not a proof
        assert _is_observed_settlement(s(level, settlement=settled)) is False
    assert _is_observed_settlement(s("observed_live", settlement=None)) is False
    assert _is_observed_settlement(s("observed_live", verdict="FAIL", settlement=settled)) is False
    assert _is_observed_settlement(s("observed_live", settlement=settled, plane="package")) is False
```
(`_is_observed_settlement` joins the top-level import block at `:14-33`, next to the other `portability_schema`
names; it is currently imported locally inside a test at `:989`.)

Both directions are witnessed offline:
* **Neutral edit stays fresh** — direction 1 (`test_comment_only_schema_edit_is_hash_neutral`), plus the existing
  `test_durable_receipts_exist_for_all_five_hosts` / `test_all_six_profiles_pass_evidence_durability_and_freshness`.
* **Behaviour-affecting edit invalidates** — direction 2, split by necessity into the *gate* half (static/offline pins
  fail on a validator mismatch; live pins never do, `test_staticly_pinned_claim_is_gated_by_validator_revision`) and
  the *semantics* half (`test_admission_predicate_is_behaviourally_pinned`; a widened predicate fails a test rather
  than a hash, because a hash cannot see the difference).

Test-file maintenance this forces: remove `"scripts/portability_schema.py"` from the parametrize list at
`tests/test_evidence_durability.py:364` (that assertion — "a schema edit stales adapter + runtime" — is precisely the
behaviour being retired); add `validator_revision` to `expected_keys` (`:66-70`); update the ~10 `check_scenario_pins`
call sites for the new required argument.

---

## 7. Diff size estimate

| File | Change | Lines |
|---|---|---|
| `scripts/portability_schema.py` | field +1, tuple −1, step 8b +6, return +1, `check_scenario_pins` gate +9, call site 1 changed | **≈ +18 / −2** |
| `schemas/portability/receipt.schema.json` | `validator_revision` property (not in `required`) | **+1** |
| `.audit/evidence/{grok,codex,omp,opencode,antigravity}-receipt.json` | +1 key line, 1 value replaced, per receipt | **+10 / −5** |
| `.audit/evidence/index.json` | same, × 5 host entries | **+10 / −5** |
| `tests/test_evidence_durability.py` | 4 new tests (~90), −1 parametrize entry, +1 expected key, 9 call-site args | **≈ +105 / −11** |
| **Total** | 9 files (1 module, 1 schema, 6 evidence, 1 test) | **≈ 140 lines** |

No new module, no new plane, no new receipt kind, no flag, no second hash system.

---

## 8. Honesty: the exact weakening (mandatory)

**W1 — live claims are no longer invalidated by a validator edit. Exact scope.** After this change, a byte edit to
`scripts/portability_schema.py` invalidates **no** `observed_live`-backed claim on any host. An edit that *widens*
admission — `_is_observed_settlement` (`:736-756`) accepting an `offline` level; a capability removed from
`MANDATORY_SUPPORT_FLOOR` (`:30`); `VERIFICATION_STATUSES` (`:19`) widened; `SETTLEMENT_PROMOTIONS` (`:59`) extended —
leaves all five receipts and `index.json` valid and `check-evidence` green, with no regeneration required and no CI
signal. The only things that still notice are (a) a *stricter* validator, which is self-enforcing because the current
validator re-judges the checked-in receipts on every offline `check-evidence` run, (b) the static/offline pin gate,
which fires on OMP's two `static-only` pins only, and (c) §6's behavioural fixture, which is a test, i.e. review-grade
evidence, not a cryptographic gate.

**W2 — what is not lost, stated without absolution.** The current coupling does not actually protect the *truth* of a
live claim: the code that produces live observations (`verify-portable.py`, `verify-harness.py`,
`scripts/drivers/*.py`) is hashed *separately* in `driver_revision` and is unchanged in the docstring-edit scenario, so
the forced re-run re-executes the same observation code; the only variable is the validator's interpretation, which is
applied at check time in both designs. What *is* lost is the detection signal: today every validator edit turns
`adapter`+`runtime` stale on all five receipts, so CI goes red and a reviewer is forced to look at the change. That
signal is real and is what this design trades for zero-cost validation-only edits. It is not replaced by anything of
equivalent strength.

**W3 — neutrality is not total.** For `omp`, any validator byte change requires one offline restamp of
`omp-receipt.json` + `index.json` before `check-evidence --host omp` is green again. That is the deliberate price of
giving `validator_revision` a real consumer instead of shipping an inert field (see rejected alternative 6). The four
bare-path host profiles are fully neutral; `grok` — the reproduced acceptance case — is fully neutral.

**W4 — the removed assertion is a real coverage reduction.** `test_driver_source_change_invalidates_adapter_and_runtime`
loses its `scripts/portability_schema.py` case. The replacement coverage (§6) is behaviour-level and therefore
*stronger in kind* (it detects a widened predicate, which the byte hash never did) but *narrower in extent*: it pins the
predicates named there, not the whole module. A semantic change outside those predicates and outside the gated
static pins stays invisible.

---

## 9. Rejected alternatives (mandatory rationale)

1. **Keep the validator inside `driver_revision` (status quo).** *Rejected:* it is the defect. Its "protection" is
   ritual (§W2) at the price of a live re-run per host per docstring; it violates rubric 2 outright and provably does
   not stop a widening edit, since the attacker simply regenerates receipts the same way.
2. **Comment/docstring-stripping normalized hash (AST or regex pre-pass).** *Rejected:* it needs a second, per-language
   normalization policy and a maintained list of "neutral" constructs, i.e. exactly the "second hash system / new
   abstraction" rubric 3 forbids; and its neutrality claim is a *heuristic*. A one-token semantic edit
   (`evidence_level == "offline"` → `in ("offline",)`, `str | None`, a reordered `SETTLEMENT_PROMOTIONS` literal)
   survives normalization and lands in the "neutral" class with no signal at all. It also overclaims in the other
   direction: normalization cannot promise that a docstring edit is behaviour-free.
3. **Whitelist by symbol — hash only the admission functions** (`_is_observed_settlement`, `check_scenario_pins`,
   `check_evidence_durability`, `derive_support_state`, `PLANE_SURFACE_DEPENDENCIES`). *Rejected:* incomplete by
   construction, and it needs a function-level extractor (new concept, new failure modes). The outcomes are also
   decided by unnamed neighbours the list will not contain: `MANDATORY_SUPPORT_FLOOR` (`:30`), `VERIFICATION_STATUSES`
   (`:19`), `SETTLEMENT_PROMOTIONS` (`:59`), `ScenarioResult.validate` (`:522-535`), `_is_preservable_settlement`
   (`:758-768`), `SurfaceRevisions.to_dict` (`:458`). Any of those can change what is admitted while every listed
   function is byte-identical.
4. **A `--allow-stale` / `--force` flag in CI instead of touching the hash.** *Rejected:* this throws away the
   freshness signal for *every* driver and *every* host, not just the validator, and leaves the stale receipts
   indistinguishable from fresh ones; it is the maximal violation of rubric 1 at the minimum diff.
5. **Move the admission logic to another file ("split by responsibility" instead of by field).** *Rejected as the
   primary mechanism:* the only place byte hashing can express a boundary is the file, so the split is tempting — but
   `scripts/drivers/*.py` is hashed wholesale (`:704-708`), so moving rules there keeps the coupling (no neutrality),
   and moving them to an unhashed module (`scripts/admission_rules.py` or similar) is *strictly weaker* than this
   design: no recorded revision at all, no gate, and a much larger diff (import churn across `verify-portable.py`,
   `verify-harness.py`, `prove-omp-vertical-slice.py`, the tests). Same or worse integrity for more churn.
6. **Record `validator_revision` but never gate on it (inert variant, or scope the gate to `verified` rows).**
   *Rejected as the primary design, retained as a one-line fallback:* `check_scenario_pins` already forbids a
   `verified` row from pinning non-live evidence (`:936-942`), so a `verified`-only scope can never fire — the field
   becomes decoration that no code reads (dead weight; and rubric 4's "behaviour-affecting edit invalidates" direction
   would then have no consumer outside the fixture). If the program insists on literal neutrality for `omp`, that is
   the one-line change: keep the field, drop the gate, and §W3 disappears at the cost of an inert field. This is the
   honest boundary of the direction, offered as a choice rather than hidden as a detail.
7. **`schema_revision` / `checker_revision` as the field name.** *Rejected:* `schema_revision` collides with the
   existing `spec_hash`/`schemas/portability/*` vocabulary (`spec_hash` already covers the spec, and the receipt
   schema is a different artifact class); `checker_revision` under-describes the file, which also holds the receipt
   dataclasses and the revision computation itself. `validator_revision` names the layer consistently with the
   neighbouring `*_driver_revision` fields.

---

## 10. Rubric scorecard

| # | Criterion | Outcome |
|---|---|---|
| 1 | Integrity preserved (behaviour-affecting edit invalidates the affected live claims) | **Not met literally — see §8 W1/W2.** A validator edit invalidates no live claim; live claims are re-judged by the current validator on every check, and the widening-detection burden moves to fixtures. |
| 2 | Regeneration cost of comment/refactor/type-hint edits | **Met:** zero live re-proof. 4/6 hosts need nothing at all; `omp` needs one offline restamp; `droid` has no receipt. |
| 3 | Minimal diff, no new concept | **Met:** +1 field, +1 property, ~20 product lines, 6 evidence files, no new module/plane/receipt kind/hash recipe. |
| 4 | Offline-testable both directions | **Met as far as byte hashing allows** (§4, §6): direction 1 by the revision split + staleness, direction 2 split into the static-pin gate and the admission-predicate fixture. |
| 5 | Honesty | **Met:** §8 states W1-W4 exactly, including the removed assertion and the non-total neutrality of `omp`. |
