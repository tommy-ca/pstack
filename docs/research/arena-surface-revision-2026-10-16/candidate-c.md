# Candidate C — semantic-surface digest for `scripts/portability_schema.py`

Design only. No repository edits, branches, commits, or pushes were made.
Trunk 419fb36 (`refactor(portability): decompose role policy and resolver hot paths (#468)`).

Prototype used for every measured claim in this document: `/tmp/proto_digest2.py`,
`/tmp/proto_digest3.py` (throwaway, outside the repo; loads
`scripts/portability_schema.py` from an arbitrary path so mutated copies never touch the
working tree).

---

## 1. Position

Replace the **byte contribution** of `scripts/portability_schema.py` to
`compute_surface_revisions`' `driver_revision` (`scripts/portability_schema.py:691-709`, the
`for fname in (...)` loop that does `hasher.update(driver_file.read_bytes())` at line 703) with a
**sha256 over a normalized semantic surface of the module itself**: its declared
vocabularies, its capability universe, its plane-dependency table, and the *decisions* its
validators make over an exhaustive corpus built from those vocabularies.

The other six driver files and `scripts/drivers/*.py` keep byte hashing. `SurfaceRevisions`
gains no field; `.audit/evidence/*/receipt.json` keeps its schema; the staleness path
(`VerificationReceipt.evaluate_plane_staleness`, `check_evidence_durability` at
`scripts/portability_schema.py:945`) is untouched. The only observable change is *which*
`driver_revision` value a given module produces — which is the lever.

```
driver_revision = sha256(
    "canonical-index.py"  + bytes(canonical-index.py)   ...
    "portability_schema.py" + schema_surface_digest().encode()   <-- was .read_bytes()
    "scripts/drivers/x.py"  + bytes(...)
)
```

## 2. What is extracted and normalized

`schema_surface_digest()` is defined **inside `portability_schema.py`** (rejected: a
separate `scripts/surface_digest.py` — see §7). It builds four sections and hashes
`sha256("\x00".join([A, *B, *C, *D]))`.

### A — declared vocabularies (name-keyed, type-tagged, order-normalized)

Read by attribute access off the live module object, never from source text. The 20
normative constants, each tagged by container type so `tuple → list` and
`frozenset → tuple` are visible:

`SUPPORT_STATES`, `IMPLEMENTATION_STATUSES`, `ENFORCEMENT_LEVELS`, `VERIFICATION_STATUSES`,
`ADAPTATION_MODES`, `HOSTS`, `CONFORMANCE_PLANES`, `MANDATORY_SUPPORT_FLOOR`,
`CONDITIONAL_CAPABILITIES`, `PORTABLE_CAPABILITY_UNIVERSE`, `SETTLEMENT_PROMOTIONS`,
`REQUIRED_CAPABILITIES`, `FORBIDDEN_ORCHESTRATION_FIELDS`, `REQUIRED_TOOL_MAPPINGS`,
`ALLOWED_TOOL_MAPPINGS`, `DEFAULT_SKILLS_DIRS`, `DEFAULT_PLUGIN_MANIFESTS`,
`PLANE_SURFACE_DEPENDENCIES`, `SKILLS_HASH_IGNORED_DIRS`, `SKILLS_HASH_IGNORED_SUFFIXES`.

Normalization rule: **sort elements, except for a named `ORDER_SENSITIVE` list that is
itself part of the payload.** Today that list is exactly `("SUPPORT_STATES",)` — justified
by `SUPPORT_STATES.index(profile.support_state)` at line 1014 / `derived_idx` at 1015 in
`check_evidence_durability`, where position, not membership, decides accept/reject. Every
other constant is read by membership, `dict.get`, `sorted()` (for
`PORTABLE_CAPABILITY_UNIVERSE`), or `any()` over keys (`SETTLEMENT_PROMOTIONS` in
`_is_preservable_settlement`), so a pure reorder of those literals is a refactor and must
stay neutral. Adding a name to `ORDER_SENSITIVE` re-proves, which is correct: declaring a
new order-sensitive vocabulary *is* a semantic claim.

Values are stringified with `str()`; dicts keep their keys sorted and tuples nested under
them sorted by the same rule. This is deliberately *not* JSON-round-tripped through the
values' own types — a `str()` view cannot silently normalize two different types into one
representation, and the type tag carries the container distinction that matters.

### B — decisions over the declared domain (the exhaustive part)

Each probe is a *call* to a public decision site with a fixed input; each row is the
**normalized outcome**, never the code:

| probe | inputs | rows |
|---|---|---|
| `Binding.validate` | `HOSTS`(+6 sentinels) × `PORTABLE_CAPABILITY_UNIVERSE`(+6) × `IMPLEMENTATION_STATUSES`(+6) × `ENFORCEMENT_LEVELS`(+6) × `VERIFICATION_STATUSES`(+6) | 264,600 |
| `ScenarioResult.validate` | `CONFORMANCE_PLANES`(+6) × 4 verdicts(+6) × 4 evidence levels(+6) | 810 |
| `_is_observed_settlement` | capability(+6) × 4 terminal outcomes × 3 levels × 4 verdicts | 1,008 |
| `VerificationReceipt.evaluate_plane_staleness` | one mutated dependency at a time across all 10 `SurfaceRevisions` fields | 10 |

Sentinel ring per slot: `None, 0, "", "\x00unknown", [], {}` — the out-of-domain and
type-error paths.

Outcome key normalization, all three rules load-bearing:

```
ok                                       -> "ok"
non-ValidationError                        -> "err:<ClassName><MRO>"
ValidationError                            -> "err:ValidationError<MRO>:<hits>"
```

* `<MRO>` is `",".join(c.__name__ for c in type(err).__mro__[1:])`. **Measured:** with a
  type-name-only key, mutating `class ValidationError(ValueError)` →
  `class ValidationError(Exception)` leaves the digest **unchanged** (blind); with the MRO
  suffix it **differs**. The MRO suffix is therefore mandatory, not decorative.
* `<hits>` is the sorted set of *field/vocabulary names* the message names, matched
  word-bounded against the dataclass field names and vocabulary names. This projects prose
  onto rule identity, so `"Invalid enforcement level: …"` → `"Bad enforcement level, try
  again: …"` stays neutral (**measured SAME**) while swapping the `capability` and
  `implementation_status` checks differs (**measured DIFFERS**).
* Prose projection risks only false *positives* (a rewrite that stops naming the tested
  field re-proves), which is the safe direction; it cannot hide a rule change.

### C — decisions that need a filesystem

Built on a **synthetic root** created under `tempfile.TemporaryDirectory` per digest call,
with fixed relative paths; rows carry outcomes only, never paths:

* `derive_support_state` ladder: 12 root shapes (receipt plane combos × `observed_live`
  present/absent × stale/fresh `driver_revision`) × 60 profile shapes (universe fully/partly
  bound × `tool_mappings` present/absent × mandatory `verified|gap|static-only` × five
  claimed `SUPPORT_STATES`) → 2,160 rows, each recording the returned state string or the
  exception class.
* `check_evidence_durability`: `check_freshness ∈ {True, False}` per profile shape →
  outcome key plus the set of planes flagged stale per ref.
* `preserve_observed_settlements` / `_is_preservable_settlement` / `_is_observed_settlement`:
  in-memory receipt pairs (host match/mismatch, runtime fresh/stale, verdict, level,
  settlement outcome) → returned id list plus the resulting `evidence_level` and
  `preserved_from`.

The receipt JSON in the fixture is a **hard-coded literal dict** using the real
`SurfaceRevisions` key names, not `SurfaceRevisions.to_dict()`. That is what makes a
dataclass field rename land: `SurfaceRevisions(**rdata)` raises, the outcomes flip, the
digest moves. A fixture built from the dataclass would be blind to exactly that rename.

### D — extractor identity and coverage registry

The extractor's version integer, the list of registered public symbols (20 section-A
constants + 15 behavioral symbols measured today), and the explicit exemption list with a
one-line reason each.

A fail-closed assertion parses the module with `ast` and requires every **public**
module-level name (no leading underscore) to be either registered or explicitly exempted.
Private helpers are free: they are covered behaviorally through their public callers, which
keeps helper extraction neutral. **Measured:** renaming `MANDATORY_SUPPORT_FLOOR` to
`SUPPORT_FLOOR_BASE` (module still valid) surfaces `['SUPPORT_FLOOR_BASE']` as unregistered
→ hard error; adding `def validate_new_rule(x)` surfaces `['validate_new_rule']` → hard
error.

## 3. Why hygiene edits cannot move it, and semantic edits must

**Nothing in the digest is derived from source text.** Section A reads attributes off the
imported module; B/C call functions; D parses only *names* to check coverage. Therefore:

* Comments, blank lines, reflowed docstrings: not read anywhere. (The module docstring is
  rewritten in the prototype's neutral set — SAME.)
* Type hints: inert at runtime here. No `get_type_hints`, no pydantic, no
  `dataclasses.field` metadata consumer in this module; dataclass defaults and `str`-typed
  validations do not consult annotations. Adding `UNUSED_ALIAS: tuple[str, ...] = HOSTS`
  and `# type:` comments — SAME.
* Refactors: renaming locals, extracting a private helper, inlining one, replacing a loop
  with a comprehension, reordering independent statements — decisions preserved, so every
  probe row is byte-identical. **Measured SAME** for all of: comment+annotation+unused
  helper; rewritten module docstring; local rename + `for p in [p for p in …]` rewrite;
  extracted helper function added and called. (The prototype applied the comment,
  annotation, and unused-helper cases as one combined append; the other cases were applied
  and measured individually. Individually they are the same argument: none of the three is
  read by any section.)

And the converse, all **measured DIFFER**:

| edit | section that catches it |
|---|---|
| append `"trial"` to `SUPPORT_STATES` | A (+ B rows) |
| reorder `SUPPORT_STATES` | A (order-sensitive) |
| delete `"agent.resume"` from `CONDITIONAL_CAPABILITIES` | A (+ B via universe) |
| add `"profile_hash"` to the `package` tuple of `PLANE_SURFACE_DEPENDENCIES` | A (+ B staleness rows) |
| delete the `enforcement` membership check in `Binding.validate` | B |
| swap the `capability` and `implementation_status` checks | B |
| neuter `evaluate_plane_staleness` | B |
| add `"monitor": ("cancelled",)` to `SETTLEMENT_PROMOTIONS` | B (`_is_observed_settlement`) |
| weaken `_is_preservable_settlement` to `return True or …` | C |
| gutter the `derive_support_state` staleness gate to `if False:` | C |
| change `ValidationError`'s base class | B (MRO rule) |
| drop a present driver filename from the `driver_revision` loop | `driver_revision` *value* changes → receipts mismatch (measured: `64f6bbf7…` → `faebdd1b…`) |

## 4. The failure mode where a behavioral change does NOT move the digest, and the bound

Stated as escape classes, each with its bound. This is where the direction is honestly
weaker than raw bytes, and the weakening is named rather than papered over.

**Class 1 — inputs outside the probed corpus.** Bound: the corpus is *exhaustive over every
value of every closed vocabulary the module declares*, plus a fixed sentinel ring
(`None, 0, "", "\x00unknown", [], {}`) for the out-of-domain and type-error paths. Nothing
in this module parses structured strings, compares magnitudes, or interprets dates, so the
"a rule that differs only on some exotic value" surface is thin. Residual exposure: a *new
rule inside an existing validator* that keys on a value axis not in the corpus (e.g. a
domain that adds a rich string syntax). The coverage assertion does **not** catch that —
it fires on new *symbols* only. Mitigation is procedural and named: any rule that reads a
new input kind must add a probe axis, and this is stated in the extractor's docstring
next to `ORDER_SENSITIVE`.

**Class 2 — behaviour with no outcome consequence.** Message prose that still names the
tested field, log/comment noise, and the `stale_details[:5]` ordering of
`check_evidence_durability`'s message. Deliberately neutral: prose is not a validation
outcome and is not a claim the receipts assert. This is a real weakening of "any edit that
can change validation outcomes invalidates" — the honest reading is that the digest
tracks *outcomes*, not *text*, and prose-only edits stay fresh by design.

**Class 3 — behaviour whose only effect is on values the module returns but the digest does
not record.** `compute_surface_revisions`' produced hashes, for example. Bound: these are
self-protecting by value comparison — `driver_revision` and friends are stored in every
receipt and compared by `evaluate_plane_staleness`, so *any* change that alters a produced
value makes every receipt mismatch and forces re-proof. The only escape is an edit that is
value-neutral on the current tree, such as deleting a filename for a file that is absent:
behaviourally inert today, and it becomes visible the moment the file exists.

**Class 4 — the extractor itself.** A rewritten extractor that returns a constant makes the
digest vacuous, and by construction the digest cannot see that; neither can the value
comparison once the receipts have been regenerated against it. Bound: (a) the offline
sensitivity test (§6, direction 2) fails against a vacuous extractor, because it asserts
~12 named mutations *do* move the digest; (b) the first run after such a rewrite shows an
unexplained `driver_revision` change on every host. Stated threat model: **this lever
defends against accidental staleness-blindness for hygiene edits, not against an adversary
who rewrites both the extractor and the receipts.**

**Class 5 — refactors that move a covered public symbol.** Renaming or relocating
`Binding.validate`, `check_evidence_durability`, or a section-A constant is *not* neutral:
the coverage assertion raises and `check-evidence` hard-fails. Fail-closed, and deliberate
— a public rename is a contract change for the other six drivers, not a pure refactor.

Net claim, bounded: **a comment, docstring, type-hint, or internal-refactor edit cannot
change the digest; every edit to a declared vocabulary, the capability universe, the
plane-dependency table, or a validator's decision moves it — with the escape classes 1–5
above, none of which is a silent path to a stale live claim except class 2 (prose, by
design) and class 1 (new value axes inside existing validators, procedural bound).**

## 5. Wiring and landing cost

* `compute_surface_revisions`: for the `portability_schema.py` entry only, feed
  `schema_surface_digest().encode("utf-8")` where `driver_file.read_bytes()` went; keep the
  filename prefix and the other six files byte-hashed.
* Cost per digest: **measured 0.2–1.0 s** wall clock, 294,410 probe rows (264,600 + 810 +
  1,008 + 10 + 2,160 + ~800 preservation rows, and ~1,640 durability rows). `check-evidence`
  calls `compute_surface_revisions` once per host → [INFERENCE] ~1–6 s added per full
  six-host sweep. No caching proposed; it is not needed and a cache is a new failure mode.
* **One-time regeneration is unavoidable and must be stated**: the `driver_revision` value
  changes for every host on landing, so all six `.audit/evidence/<host>-receipt.json` files
  go stale once. Five hosts are offline-reproducible with an ordinary run; OMP requires
  `PSTACK_RUN_OMP_LIVE=1`. This is the cost of the lever, not a property of it: after
  landing, hygiene edits are free. Land it alongside the next scheduled live re-run rather
  than as a standalone proof round.

## 6. The exact offline test (both directions)

New file `tests/test_surface_digest_neutrality.py`, reusing the existing
`_disposable_copy(tmp_path)` helper and the `compute_surface_revisions(copy_root, "codex")`
pattern from `tests/test_evidence_durability.py:352-423`. No live host, no network.

**Fixtures.** `fresh = compute_surface_revisions(copy_root, "codex")`; a
`VerificationReceipt` built from it; the digest read from two different `tmp_path` roots to
assert path-independence (rows are outcome strings only, so this must hold — it is asserted,
not assumed, and it is the one property the prototype did not measure across distinct
tmp roots).

**Direction 1 — neutral stays fresh.** Parametrized `(old, new)` source-edit table applied
to `copy_root/scripts/portability_schema.py`, each asserting
`compute_surface_revisions(copy_root, "codex").driver_revision == fresh.driver_revision`:

1. append `"\n# hygiene comment\n"`;
2. rewrite the module docstring's first line;
3. append `UNUSED_ALIAS: tuple[str, ...] = HOSTS  # type: ignore\n`;
4. append an unused private helper `def _unused_helper(x): return x`;
5. rename a local and rewrite `for p in sorted(...)` as a list-comprehension loop;
6. extract a new private helper and call it from `Binding.validate`'s caller-side path;
7. rewrite a raised message's prose while keeping the field/vocabulary name in it.

**Direction 2 — semantic edit invalidates.** Same mechanism, asserting
`driver_revision != fresh.driver_revision` **and** that the mismatch actually gates:
`s = receipt.evaluate_plane_staleness(edited)` has non-empty `adapter` and `runtime` lists,
each reason starting with `"driver_revision mismatch"`, and every other plane empty —
exactly the assertions the existing byte-hash test already makes, so the contract is
reused rather than restated. Cases: `SUPPORT_STATES` appended; `SUPPORT_STATES` reordered;
`CONDITIONAL_CAPABILITIES` entry removed; `MANDATORY_SUPPORT_FLOOR` entry removed;
`PLANE_SURFACE_DEPENDENCIES` dependency moved between planes; a `Binding` membership check
deleted; two membership checks swapped; `evaluate_plane_staleness` neutered;
`_is_preservable_settlement` weakened; the `derive_support_state` staleness gate gutted;
`ValidationError` base class changed; a present driver filename dropped from the
`driver_revision` list (here the assertion is on the *value*, i.e. it must also differ).

**Direction 3 — fail-closed coverage.** `pytest.raises(SurfaceCoverageError)` (or whatever
the extractor raises) for: a renamed public constant; a renamed public validator; a newly
added public function; a section-A constant deleted.

**Direction 4 — integration, both ends of the gate.** On a `_disposable_copy`:
`python scripts/verify-portable.py check-evidence --host codex` with an appended comment →
**exit 0**; with one enum entry appended → **exit 1**. Offline only; `check-evidence`
validates receipts and freshness, it never touches a live host.

**Direction 5 — amended existing test.** `tests/test_evidence_durability.py`'s
`test_driver_source_change_invalidates_adapter_and_runtime` keeps
`scripts/portability_schema.py`'s comment-append case only if it is moved to a new
neutral-expectation counterpart; the path must leave the byte-hash parametrization
(`scripts/verify-portable.py`, `verify-harness.py`, `adapt-harness.py`,
`scaffold-verification-skill.py`, `skill_frontmatter.py`, `drivers/base.py`,
`drivers/codex.py` stay) and the appended-comment case joins direction 1.

The prototype already exercises directions 1–3 in substance: 6/6 neutral mutations SAME,
11/11 semantic mutations DIFFER, 2/2 coverage cases fire. What the repo test adds is the
disposable-copy plumbing and the check-evidence exit codes.

## 7. Diff size estimate

Measured against the prototype's actual code (extractor sections A–D, outcome normalization,
lexicon, registry, coverage check, digest wrapper):

| target | change |
|---|---|
| `scripts/portability_schema.py` | **+~270 / −2 lines**: `ORDER_SENSITIVE`, section-A name tuple, `_tag`/`_surface_outcome`, `LEXICON` + `LEX_RE`, four section builders, `SURFACE_COVERAGE` + exemptions, coverage assertion, `schema_surface_digest()`; plus the one-line substitution inside `compute_surface_revisions` (line ~706) and a docstring note |
| `tests/test_surface_digest_neutrality.py` | **new ~230 lines**: 7 neutral cases, 12 semantic cases, 4 coverage cases, path-independence, two check-evidence exit-code runs |
| `tests/test_evidence_durability.py` | **−1 / +1 line**: drop `scripts/portability_schema.py` from the byte-hash parametrize list; comment-append expectation moves to the new test |
| `openspec/specs/pstack-portability/spec.md` | **+~15 lines**: one requirement — "a validation-only edit to the schema driver must not invalidate live evidence claims; a vocabulary, universe, table, or validator-decision edit must" |
| `.audit/evidence/*/receipt.json` | **6 files**, one `driver_revision` value each (regeneration, not hand-edit) |

Total ≈ **520 lines**, of which ≈230 is test, ≈270 the extractor, ≈20 wiring/spec. No new
module, no new dependency, no new receipt field, no new CLI flag.

## 8. Mandatory rationale — alternatives rejected, and why

1. **Keep raw bytes, re-prove on every edit (status quo).** Rejected as the design, kept as
   the baseline to beat. It cannot distinguish a comment from a deleted validator check, so
   every hygiene edit carries a six-host live proof. That is the cost issue #444 exists to
   remove.
2. **Comment/whitespace normalizer over source text** (strip comments and blank lines, then
   hash). Rejected: needs a tokenizer in the hash path (new machinery for a partial fix),
   and it only rescues the comment case — a docstring rewrite, an added type hint, or a
   local rename still re-proves, so rubric item 2 ("comment-only, refactor, or type-hint
   edits") is not met.
3. **AST canonicalization** (`ast.dump`, `include_attributes=False`, docstrings stripped).
   Rejected: node kinds, names, and statement order remain, so every refactor changes it;
   that is strictly *more* sensitive than bytes to helper extraction and loop rewrites,
   which is the failure mode we are fixing. Normalizing "enough" to be refactor-neutral
   means discarding structure — at which point the decisions themselves are the only
   honest content, which is this design.
4. **Signature/skeleton hash of the module** (names + arg counts + literal operands, no
   bodies). Rejected: blind to rule swaps and reorderings (measured relevant: swapping the
   `capability` and `implementation_status` checks), and brittle to renames. It buys
   refactor tolerance by giving up the property the gate exists for.
5. **Exclude `portability_schema.py` from `driver_revision` entirely** (smallest possible
   diff: delete one tuple entry). Rejected: pure integrity loss with no bound at all — a
   deleted validator rule would leave every live claim fresh. Fails rubric 1 outright.
6. **A second, parallel hash: a new `semantic_digest` receipt field** alongside
   `driver_revision`. Rejected by rubric 3 (no second hash system, no new receipt kind) and
   on merit: the raw field would still go stale on a comment, so the new field would have to
   *suppress* the failing check — that is weakening integrity dressed as an addition. It
   also permanently doubles the surface to keep in sync.
7. **Record a surface snapshot file and diff it at check time.** Rejected: a snapshot of
   extracted values in a file *is* the digest in a bigger container, plus a new artifact
   class to keep fresh.
8. **Property-based / generative fuzzing as the digest's corpus.** Rejected as the digest
   mechanism: a digest must be reproducible byte-for-byte, and a randomized corpus is not.
   Here the validation domain is finite and small, so exhaustive enumeration is both
   cheaper to reason about and strictly stronger for the values that matter. (Fuzzing
   remains a good *test-side* idea; it is not the lever.)
9. **`inspect.getsource` over `validate` bodies (normalized).** Rejected: that is variants
   2/3 with an extra indirection, and it re-imports the source-text coupling that makes
   comments cost a re-proof.
10. **Per-file allowlist or `--allow-stale` bypass for the schema driver.** Rejected: any
    edit can ride a bypass; the freshness gate must stay unconditional and value-based.
11. **Enums-and-tables only (section A without the decision probes).** Rejected as an
    insufficient subset, and this is the crisp reason the full direction was needed:
    section A is blind to every validator body. Measured — the deleted `enforcement`
    membership check and the gutted `derive_support_state` staleness gate move the digest
    *only* because sections B/C exist; with A alone both would stay fresh while live claims
    survive a real behavioural change.
12. **A separate module `scripts/surface_digest.py` added to the driver list.** Rejected
    in favour of defining the extractor inside `portability_schema.py`: a separate file
    brings an import cycle (`surface_digest` → `portability_schema` → `compute_surface_revisions`
    → `surface_digest` at call time) and, if added to `DRIVER_REVISION_FILES`, makes a
    *comment* in the extractor cost a full re-proof — contradicting the property the
    extractor exists to provide. Extractor semantics stay guarded by the offline
    sensitivity test plus the first-run value mismatch (§4, class 4).

## 9. Evidence ledger (design-stage, all measured)

| claim | how measured |
|---|---|
| hygiene edits neutral (4 hygiene mutations, one measured as a combined append) + 1 lexicon-neutral prose case | prototype, `digest(mutated) == digest(base)` |
| semantic edits differ (10 cases via the digest surface + base-class MRO case) | prototype, `digest(mutated) != digest(base)` |
| driver-list edit is caught by value, not by the digest surface | prototype copy of `scripts/` + `scripts/drivers/`: `driver_revision` `64f6bbf7…` → `faebdd1b…` after deleting `"skill_frontmatter.py"` |
| base-class change is blind without the MRO rule | `ValidationError(Exception)` mutation: SAME with type-name key, DIFFERS with MRO key |
| message prose can be neutral without hiding rule changes | word-bounded field-name projection: prose rewrite SAME, rule swap DIFFERS |
| coverage assertion fires | renamed constant → `['SUPPORT_FLOOR_BASE']`; new public fn → `['validate_new_rule']` |
| probe volume / runtime | 294,410 rows, 0.2–1.0 s per digest |
| fixture degeneracy risk is real | first prototype run silently collapsed every ladder row to one value because all synthetic roots shared a path; unique roots per shape fixed it and exposed the two ladder/preservation blind spots |

Claims labelled [INFERENCE]: six-host digest cost in a full `check-evidence` sweep, and
path-independence of the digest **until the offline test asserts it**. Everything else in
this ledger was run, not reasoned.
