# PR #719 setup production code — detail report

Lane: `Pr719SetupCore`. Base `ef3405282e4afd2636923043ca59aac8a09d4170`, main `10025900e8cb481540ce6f61f32d6b73ff638b3f`,
PR head `9c4b680229429b6b61c166ef888632830818e09c` (`pr-719`). Reviewed tree extracted read-only with
`git archive pr-719 | tar -x -C /tmp/thermo-695/wt719`; the shared checkout sits on `main`, so every citation below is
from the extracted head tree, not the working copy. Commits in range: `6b16c46` (feat) and `9c4b680` (evidence pins).

Measured facts about the patch itself: `scripts/setup_pstack.py` +43/−3 (245 → 285 lines), `scripts/portability_types.py`
+57 (664 → 721), `schemas/portability/setup-projection.schema.json` new (33), `scripts/portability_schema.py` +4,
`scripts/scan-host-boundary.py` +2/−1, `scripts/verify-harness.py` 13/13 (rename only), six `profiles/*.json` +7 each,
`tests/test_setup_projection.py` new (299). No file in the patch crosses 1000 lines; the largest touched file is
`portability_types.py` at 721.

Verification actually run (all read-only, in the extracted tree, interpreter `/home/tommyk/projects/pstack/.venv/bin/python`):

- `pytest tests/test_setup_projection.py tests/test_scan_host_boundary.py tests/test_portability_schemas.py -q` → 68 passed.
- `pytest tests/test_architecture_documentation.py -q` → 7 passed (so the new schema name is in the documented inventory).
- Five probes (`/tmp/thermo-695/probe*.py`) that feed synthetic profiles through `resolve_setup_projection`,
  `HarnessProfile.validate`, and the JSON schema. Their outputs are quoted verbatim where they carry a finding.

---

## Answers to the six required checks

**1. Declared projection or host-branching script?** Declared projection. `git diff main...pr-719 -- scripts/setup_pstack.py`
added lines contain **zero** host-name literals (grep for `grok|codex|omp|opencode|droid|antigravity|claude|copilot` over the
added lines returns nothing). The only conditionals in the new resolver are field-driven: `raw is None` (setup_pstack.py:44),
`raw.get("source") == "host-cli" and profile.get("support_state") == "candidate"` (:46-47), `projection.skill and not
skill_path.is_file()` (:53), and the catalog path predicate (:58-61). That is the right shape. The model that would delete
the remaining branches is not a new one: the profile already declares `setup.catalog` / `setup.overlay`, so the *one*
table that would remove them is a host→(catalog path, overlay dir) table derived from `profiles/*.json#setup`, replacing
`scan-host-boundary.py:150-153` and the four `models_file = ROOT / ...` literals in `project-package.py`.

**2. Second model registry / scheduler / role planner?** No. Nothing in the new code enumerates roles: `SetupProjection`
holds `source/effort/skill/catalog/overlay` and no role key; `SETUP_SHAPES` (portability_types.py:34-39) is a 4-row matrix
of source → field permission. `pstack.package.json#roles` still yields exactly 22 role ids and `generate_role_catalog`
(project-package.py:315-331) fails closed when a host catalog's role set differs from the descriptor, so the catalog the
profile now points at (`profiles/codex.json#setup.catalog` = `.codex-plugin/models.json`) is a *projection* of the
canonical roles, not an independent registry. `.codex-plugin/models.json` and `.antigravity-plugin/models.json` are
byte-identical to `main` (`git diff main...pr-719 -- .codex-plugin .antigravity-plugin` is empty) — the PR only names
their paths. The per-host *model choices* still live in `CODEX_ROLE_MODELS` / `ANTIGRAVITY_ROLE_MODELS` in
project-package.py, which is a pre-existing model-choice table, not a role registry.

**3. Does the negative control reject a non-Grok host writing `~/.grok/`?** At the skill/document level, yes. At the
model level, no. `test_setup_write_target_flags_shared_surface` (tests/test_scan_host_boundary.py:183-188) is a real
control: a `skills/sample/SKILL.md` containing `` `~/.grok/pstack-models.toml` `` is flagged by the scanner, and
`test_setup_entry_is_host_neutral_and_dispatches` pins that the shared entry carries no host path. But
`test_non_grok_projection_carries_no_grok_path` (tests/test_setup_projection.py:71-78) renders the six *shipped* profiles
and asserts they match the six *constant* `GOLDEN` values — it is a fixture comparison, not a control. No code path
rejects a profile that declares Grok's write targets for another host. Probe 1, exact output:

```
1. NON-GROK WRITES ~/.grok ACCEPTED: SetupProjection(source='host-cli', effort='live-enum',
   skill='setup-pstack-grok', catalog='~/.grok/pstack-models.toml', overlay='~/.grok/roles')
```

with the input being a synthetic `acme:evil` profile, `support_state: mapped`. And the invariant the PR *does* add
(candidate hosts must not probe a CLI) is enforced only in this test-only resolver; the production validator accepts it.
Probe 3 output:

```
ACCEPTED candidate declared host + host-cli + ~/.grok: SetupProjection(source='host-cli', ...,
   catalog='~/.grok/pstack-models.toml', overlay='~/.grok/roles')
```

**4. Are user-owned config files preserved on install/uninstall?** Yes, and unchanged by this PR. The only writer,
`sync_grok_role_overlays` (setup_pstack.py:167-193), iterates canonical roles only and touches only
`roles_dir / f"pstack:{role}.toml"`, so any file not named `pstack:<canonical-role>.toml` is untouched; the pin is
`tests/test_setup_pstack.py:102` `test_sync_grok_role_overlays_preserves_user_files`, which passes. Two caveats worth
naming: (a) the function has **no production caller** — grep for `sync_grok_role_overlays|generate_pstack_models_toml|
parse_pstack_models_toml` in the head tree finds only `tests/test_setup_pstack.py`, so "install/uninstall" is a library
contract exercised by tests and executed in practice by the agent following the skill prose, and that end-to-end path is
UNVERIFIED here; (b) the removal path iterates `CANONICAL_ROLES`, so a `pstack:<role>.toml` for a role that was
**deleted** from `pstack.package.json` is orphaned forever. That is pre-existing, but it becomes newly relevant if the
`overlay` declaration is wired to the writer as this PR's model implies.

**5. Does the new schema duplicate constraints in portability_schema.py?** Yes, and it duplicates them *weakly*. The
`source` and `effort` enums in `schemas/portability/setup-projection.schema.json` are a second copy of
`SETUP_SOURCES` / `SETUP_EFFORT_MODES` (portability_types.py:29-30). The canonical enforcement is
`SETUP_SHAPES` + `SetupProjection.validate()` (portability_types.py:34-39, 364-382), because that is what runs in
production: `scripts/verify-portable.py:331` constructs `HarnessProfile(..., setup=d.get('setup')).validate()`. The JSON
schema is executed only from tests (`tests/test_portability_schemas.py:444-465`). The copies have already drifted: the
schema requires `effort` while the dataclass defaults it, and the schema permits `skill`/`overlay` for `source: none`
while the type rejects them. Probe 4, verbatim:

```
A. SetupProjection(source='none') -> SetupProjection(source='none', effort='none', ...)
B. profile with {'source':'none'} validates -> SetupProjection(source='none', effort='none', ...)
C. schema errors for {'source':'none'}: ["'effort' is a required property"]
D. schema verdict for skill on source=none: []      # schema accepts what the type rejects
```

So the double enforcement buys nothing the type does not already enforce, and adds a second contract that can pass a
profile the runtime rejects (`D`) or reject one the runtime accepts (`C`).

**6. Sizes, casts, optionality, silent fallbacks.** Sizes are fine (see head). The casts and fallbacks are itemised in
findings 6-9 below.

---

## Findings

### BLOCKER 1 — the candidate-host rule lives in the one function production never calls
`scripts/setup_pstack.py:44-49` rejects `source == "host-cli"` when `support_state == "candidate"`. The production
profile validator, `HarnessProfile.validate()` (`scripts/portability_types.py:435-504`), calls `self.setup.validate()`
at :498 but never applies this rule, and the rule's own precondition (`is_declared_host`, :441) is already sitting a few
lines above it. Consumers searched: `resolve_setup_projection` — repo-wide grep finds `skills/setup-pstack/SKILL.md:30`
(a docstring one-liner) and `tests/test_setup_projection.py` only; no script, entry point, or CI step calls it.
`HarnessProfile` is called from `scripts/verify-portable.py:331` for every profile in `profiles/`. Behaviour that must be
preserved: `claude`/`copilot` (both `candidate`) must not gain a CLI-probing surface. Evidence it still holds after the
move: `tests/test_setup_projection.py:172-192` (`test_candidate_host_cannot_declare_a_cli_probe`) asserts the rule
directly on the resolver; the same assertion against `HarnessProfile.validate()` would cover both paths. Net maintained
obligation removed: one policy rule, one duplicate read of the raw `support_state`, and the entire question "which layer
enforces setup coherence" collapses into the type. Probe 3 shows today's hole concretely: a `candidate` declared host
with `host-cli` + `~/.grok/*` passes `HarnessProfile.validate()`.

### BLOCKER 2 — the declared paths are not authoritative anywhere, so the PR adds a fourth copy instead of deleting three
`profiles/grok.json:8-12` now declares `catalog: "~/.grok/pstack-models.toml"` and `overlay: "~/.grok/roles"`. Nothing
reads those values to decide a write. Searched consumers of `.catalog` and `.overlay`: the only reads in the head tree
are `portability_types.py:378` (validator) and `asdict()` in tests. The same two paths remain hard-coded independently in
`scripts/scan-host-boundary.py:150-153` (`HOST_INSTALL_PATHS`), in `scripts/setup_pstack.py:172-193` (the overlay writer
builds `pstack:{role}.toml` from a caller-supplied `roles_dir`), and — for the two hosts whose `setup.catalog` the PR
newly declares — in `scripts/project-package.py:502, 513, 669, 713`
(`models_file = ROOT / ".codex-plugin" / "models.json"` and its antigravity twin, duplicated once in `project_all` and
once again in the `--check` pass). Observable behaviour to preserve: the four projections still land at exactly those
paths, the scanner still flags a host write target on a shared surface, and the overlay writer still preserves user
files. Evidence: `tests/test_scan_host_boundary.py:183-188` (scanner control) and
`tests/test_setup_pstack.py:102` (overlay preservation) both pass today and must keep passing unchanged. Net obligation
removed by wiring the declaration instead: a per-host path table that must be edited by hand for every new host, and the
possibility that `profiles/<host>.json` and the writer disagree — which today fails silently, because the resolver only
validates repo-relative catalogs and the writer never consults the profile at all. The clean move reuses structures that
already exist: `TARGET_MAP` (project-package.py:477-488) is already a host→path table guarded by
`require_builtin_host_keys`, and `extract_forbidden_vocabulary` (scan-host-boundary.py:196-235) already loops over
`profiles/*.json` to derive host vocabulary — so `HOST_INSTALL_PATHS` is the one table in that file that was left
literal. Derive it from `setup.catalog`/`setup.overlay` for `~`-paths and the table deletes itself.

### MAJOR 3 — the resolver's `host` argument is a filename stem, not a host id, and is never validated
`scripts/setup_pstack.py:35` builds `profiles_dir / f"{host}.json"` and never compares the result to the profile's
declared `host` field nor to `is_valid_host_id`. The id spaces have already diverged: `profiles/copilot.json` declares
`"host": "github:copilot"`, and `skills/setup-pstack/SKILL.md:30` documents the call as
`resolve_setup_projection('<host>')`. Probe 6, verbatim:

```
'copilot'         -> None
'github:copilot'  raises ValidationError No harness profile for host 'github:copilot'
'../profiles/grok' -> SetupProjection(source='host-cli', ..., catalog='~/.grok/pstack-models.toml', ...)
is_valid_host_id('copilot') = False
```

So the documented call fails for the one declared host that ships a profile, the working call passes an id the rest of
the system rejects, and any string that normalises onto another host's filename resolves that host's write targets — the
exact "reuse another host's setup" the docstring at :31-32 forbids. Consumers searched: `is_valid_host_id` is used by
`HarnessProfile.validate` (portability_types.py:436) and by the profile schema via `host-id.schema.json`; the resolver
consults neither. Behaviour to preserve: `resolve_setup_projection("grok")`, `("codex")`, `("droid")`, `("omp")`,
`("opencode")`, `("antigravity")`, `("copilot")` keep returning today's results (tests/test_setup_projection.py:62-96).
Remedy: enumerate `profiles/*.json` once and index by the declared `host` field (one module-level dict, same shape as
`CANONICAL_ROLES` at setup_pstack.py:75-81), then `is_valid_host_id` the argument. That deletes the filename-stem
identity, the traversal, and the `str(...)` in the error message.

### MAJOR 4 — the JSON schema is a weaker second copy of `SETUP_SHAPES`, and it is already divergent
Covered in check 5 with probe output. Canonical: `SETUP_SHAPES` (runtime). The schema pins the two enums, which the type
already pins, and expresses the per-source field matrix only in prose descriptions, which nothing enforces. Remedy,
keeping both files: encode the matrix as a `oneOf` of four branches in the schema and add one test asserting the schema's
branches correspond to `SETUP_SHAPES` rows, so drift fails a test instead of silently disagreeing; or drop the enum
copies from the schema and let the type be the only contract. Do not leave `effort` optional in one and required in the
other — pick required, and give `SetupProjection.effort` no default (`portability_types.py:357`).

### MAJOR 5 — a host-path allowlist was extended to the shared entry instead of migrated
`scripts/verify-harness.py:132` becomes
`return parts[:2] in (("skills", "setup-pstack"), ("skills", "setup-pstack-grok"))`. After the split,
`skills/setup-pstack/` contains exactly one file, `SKILL.md`, and grep finds no `cursor` mention in it; the neutrality
test forbids host paths there. Meanwhile `leftover_mention_allowed`
(`skills/swarm/scripts/partition.py:562-569`) has no case for `~/.cursor/rules/`, so this whole-file allowance is the
*only* escape for that pattern. Net effect: the shared entry skill may now mention `~/.cursor/rules/` — a host write
path — and both guards pass it, which is a regression in exactly the boundary the rest of this PR tightens. Behaviour to
preserve: `skills/setup-pstack-grok/SKILL.md:191,193,195` must keep its `~/.cursor/rules/` prohibitions green
(`tests/test_verify_harness.py` and the `verify-harness.py` main loop). Remedy: replace, do not extend — drop the
`("skills", "setup-pstack")` tuple.

### MAJOR 6 — the resolver's error contract is not what its module declares
`setup_pstack.py:51` calls `SetupProjection(**raw)` directly, unlike `HarnessProfile.__post_init__`
(portability_types.py:429-433) which converts `TypeError` to `ValidationError`. Probe 2 and 5, verbatim:

```
2. unknown key raises: TypeError SetupProjection.__init__() got an unexpected keyword argument 'overlay_dir'
non-dict setup raises AttributeError | 'str' object has no attribute 'get'
malformed profile raises JSONDecodeError
```

Three boundary failures produce three exception types from a function whose neighbouring branches all raise
`ValidationError`; `raw.get(...)` at :46 runs before any shape check. The `overlay_dir` case is a plausible typo, and no
test in `tests/test_setup_projection.py` feeds an unknown key or a non-dict block through the resolver. Remedy: build the
typed value through the same coercion `HarnessProfile.__post_init__` uses (a two-line `_coerce` shared by both), and let
one `ValidationError` escape. Net obligation removed: three exception types a caller must know about.

### MINOR 7 — optionality that the guard should already have removed
`setup_pstack.py:52-54` computes `root / "skills" / str(projection.skill) / "SKILL.md"` *before* testing
`projection.skill`, so `str(None)` is evaluated on every non-`host-cli` host; the cast exists only to satisfy the type
checker on a path that is discarded. And `:58-61` waives the existence check for `catalog.startswith("~") or
Path(catalog).is_absolute()`, which conflates "host-home write target that may not exist yet" (the documented case, and
the only one the schema description names) with "any machine-absolute path" — probe 1's third case shows
`/etc/other-host/models.json` accepted with no existence check and no schema-documented reason. Remedy: guard the skill
first and build the path after it; classify the catalog once (`repo` | `host-home`) and waive only `host-home`.

### MINOR 8 — positional booleans in the matrix, silent default on `effort`
`portability_types.py:34-39` types the matrix as `Dict[str, Tuple[bool, bool, bool, str]]`; the three booleans are only
distinguishable by position at both the definition and the unpack at :369. A `NamedTuple` (`skill: bool, catalog: bool,
overlay: bool, effort: str`) costs four lines and removes the ordering trap. Relatedly `effort: str = "none"` (:357)
silently supplies "this host exposes no per-role effort" to a block that simply forgot the key — probe 4 case A/B. The
`SETUP_SHAPES` check at :380 catches a *wrong* effort but cannot catch an *absent* one.

### MINOR 9 — new type imported through the compatibility facade, and not declared there
`setup_pstack.py:21` imports `SetupProjection, ValidationError` from `scripts.portability_schema`, whose docstring
(portability_schema.py:1-5) scopes it to "modular decomposition and backwards compatibility (#603)". New code has no
backwards-compatibility need: the type is defined in `portability_types.py:351`. The PR added the import at
portability_schema.py:53 but did not add `SetupProjection` or any `SETUP_*` constant to that module's `__all__`
(:80-156), even though `__all__` lists every other re-export — so the facade now exports names it does not declare.
Remedy: import from `scripts.portability_types` in `setup_pstack.py` and drop the four facade lines. (Note, adjacent but
pre-existing and out of scope: `require_builtin_host_keys` is in that same `__all__` and is not imported there either.)

---

## Test-quality notes inside this lane

`tests/test_setup_projection.py:293-299` (`test_every_builtin_profile_setup_block_is_typed`) and `:59-63`
(`test_golden_setup_projection_per_builtin_host`) compare the same six profiles against the same six `GOLDEN` constants
from two directions. One of them is redundant; the `GOLDEN` dict is itself a second copy of every profile's setup block,
so the honest framing is "one pinned copy, asserted once". Neither test can fail for a reason the other would not catch.

`tests/test_setup_projection.py:196-203` is named `test_resolver_tolerates_an_absent_home_catalog` but passes a
`tmp_path` absolute path, so it exercises the `.is_absolute()` arm of the predicate and never the `~` arm that the name
describes. Both arms currently behave identically, which is why the conflation in finding 7 goes uncaught.

UNVERIFIED in this lane: real install/uninstall of a host home (no production caller exists — see check 4), and any
native host acceptance of the projected catalogs.
