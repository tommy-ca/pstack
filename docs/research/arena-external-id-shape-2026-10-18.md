# Arena record: the declared external host id rule shape (issue #446, program #429 contested seam)

Measured at `d8910b0` (lane `feat/446-host-identity-registry`). **Reconciled as `B+`** — candidate B as
the base, with the two grafts below: both carriers of the rule fixed in one move, which is the seam's
own invariant. `A`, `B` and `C` stay here as the measured alternatives.

**Landed at `4aeccee`** (`fix(portability): the external-id rule refuses a reserved namespace and a
trailing newline (#446)`) by the lane owner, on top of the four Act-Ons. Three deliberate,
non-semantic deviations from the landing copy measured below: comment/docstring wording (the owner's
names the path sites the newline could reach), the new test additionally asserts `is_valid_host_id` is
False for the refused ids and that `acme:pi` stays declarable, and the census test spells
`set(SCANNED_ONLY_HOST_NAMES)` instead of the `{"pi"}` literal so the seam owns that name. Measured
after landing, by the parent and independently by the owner: landed `EXTERNAL_HOST_ID_PATTERN` and
`RESERVED_NAMESPACES` are identical to `synthesis/shape.py` (0 disagreements over an 89-vector
adversarial sweep; the owner ran 29), the schema's `$defs.external.pattern` is the module's string, and
the two carriers agree on `acme:copilot`/`beta:copilot`/`acme:grok`/`acme:pi` = valid,
`grok:codex`/`pi:aa`/`"acme:copilot\n"`/`"acme:copilot/../x"`/`copilot` = refused. The owner's gate at
the landing head: `tests/test_host_identity.py` 18 passed (the new case red on the pre-landing tree),
full offline suite 746 passed / 10 skipped / 0 failed, `refresh-static --host all` 6/6 PASS with five
receipts plus `index.json` restamped, probe scope untouched so no DSH re-record.

Scope: the rule a *declared* (non-built-in) harness host id must satisfy — `EXTERNAL_HOST_ID_PATTERN`
in `scripts/host_identity.py` and the same string in `schemas/portability/host-id.schema.json`, which
four host-bearing schemas `$ref` and six Python surfaces import. The seam's own claim (`:46-48`) is one
rule with two carriers: "the pattern is JSON-Schema syntax, so the schema carries it verbatim instead
of restating the rule".

Harness: `/tmp/arena-external-id-shape/` (`brief.md`, `candidate-a|b|c/`, `synthesis/`, `evidence/`).
Reproduce with the repo venv interpreter (`/home/tommyk/projects/pstack/.venv/bin/python`, `jsonschema`
4.26.0; the ambient `python3` 3.12 is an ansible-tool venv with no `jsonschema` and silently weakens
every schema leg to N/A):

```
python verify.py probe                      # rule table, carrier parity, delta vs today's schema
python verify.py pytest --rule A|synth      # pinned suite, control vs graft modelled in process
python candidate-b/probe.py                 # arm B's own probe
```

## The reconciled rule (`B+`)

One string, both clauses inside it, rendered from the module's own tuples:

```
SCANNED_ONLY_HOST_NAMES: Tuple[str, ...] = ("pi",)
RESERVED_NAMESPACES: Tuple[str, ...] = KNOWN_HOSTS + OBSERVER_HOSTS + SCANNED_ONLY_HOST_NAMES

EXTERNAL_HOST_ID_PATTERN = (
    r"^(?!(?:" + "|".join(RESERVED_NAMESPACES) + r"):)"
    r"[a-z][a-z0-9-]{1,31}:[a-z][a-z0-9-]{1,47}(?!\n)$"
)
```

`is_external` keeps the seam's one-liner shape with B's `fullmatch`; nothing is added to the predicate,
because both clauses now live in the string the schema carries verbatim. `acme:grok` stays valid (the
name label is scoped by the namespace), `grok:acme` does not, and `acme:copilot`/`beta:copilot` remain
two distinct identities.

Rendered: `^(?!(?:grok|codex|omp|opencode|antigravity|droid|claude|custom|mock|pi):)[a-z][a-z0-9-]{1,31}:[a-z][a-z0-9-]{1,47}(?!\n)$`
(121 chars).

## Candidates and their measured ledgers

| arm | rule | 1 bare | 2 coexist | 3 no shadowing | 4 terminator | 5 diff | artifacts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | today's `re.match` + `$` | PASS | PASS | **FAIL** (70 of 222 vectors) | **FAIL** (`"acme:copilot\n"` validates) | 0 | `candidate-a/` |
| B | reserved set + `re.fullmatch`, predicate only | PASS | PASS | PASS (predicate) | PASS (predicate) | 18 | `candidate-b/` |
| C | closed enum, no external ids | PASS | **FAIL** | N/A | N/A | 0 | `candidate-c/` |
| **B+** | B's rule carried in the shared string | PASS | PASS | PASS (both carriers) | PASS (both carriers) | 36 | `synthesis/` |

* **A — the status quo.** Its own probe scores exactly what the parent measured independently:
  criterion 1 PASS (8/8 bare refused by module and schema), 2 PASS, **3 FAIL** — "`grok:codex` and all
  10 reserved-prefix probes accepted", **4 FAIL** — "trailing `\n` accepted by Python and
  Draft202012", 5 PASS at 0 lines. It also probed `omp:x`/`mock:x`/`pi:x` as *refused* and
  `omp:xx`/`mock:xx`/`pi:xx` as *accepted*, which is the length lesson below.
* **B — reserved namespaces + a sound predicate.** 10 reserved labels derived from
  `KNOWN_HOSTS + OBSERVER_HOSTS + ("pi",)`, namespace label only, `re.fullmatch`, pattern bytes
  unchanged. Scores 1-4 PASS, 5 PASS at 18 lines (module 14, schema 2 — a description sentence that
  *documents* the module-only rule — tests 2). It prints its own losses instead of hiding them:
  "schema-pattern carrier alone refuses 0/10 … module is the carrier" and "jsonschema(external)=True"
  for the newline. Its criterion-5 leg measures its own rationale's diff block and printed FAIL on the
  first run (18 declared vs 20 measured), PASS after it reconciled; that leg is self-consistency, not a
  seam measurement.
* **C — the control that has to stay on the table.** `#446` design alternative 1 (fixed enum plus
  `custom`): a new harness waits for a central edit. Coexistence fails by construction; its probe says
  so plainly, and it kept the dead pattern constant documented as dead rather than deleting an unused
  export. Its census lists 14 sites (10 Python tables + 4 host-bearing schemas); the *post-#446* count
  is smaller, because the enum is already centralised: `schemas/portability/host-id.schema.json`
  `$defs.known.enum`, `scripts/portability_schema.py:331` `DEFAULT_SKILLS_DIRS`, `:340`
  `DEFAULT_PLUGIN_MANIFESTS`, `scripts/package-lifecycle.py:60` `HOST_PLUGIN_REL_PATHS`,
  `scripts/project-package.py:385` `TARGET_MAP`, `scripts/drivers/__init__.py:19` `DRIVER_REGISTRY`,
  `scripts/scaffold-verification-skill.py:43` `HOST_DETECT_ORDER` — seven edits per host, before the
  driver exists. B+ pays none of them for a declared host, which is what unblocks #442 Copilot in
  `candidate` state.

## The defect, reproduced

`scripts/host_identity.py:52` compiled `^[a-z][a-z0-9-]{1,31}:[a-z][a-z0-9-]{1,47}$` and matched with
`re.match`. In Python `$` also matches *just before* a trailing newline:

| probe | result |
| --- | --- |
| `EXTERNAL_HOST_ID_RE.match("acme:copilot\n")` | `True` on A |
| `EXTERNAL_HOST_ID_RE.fullmatch("acme:copilot\n")` | `False` |
| `jsonschema` Draft202012, same pattern string, live `$defs.host` / `$defs.external` | accepts `"acme:copilot\n"` |
| the same live validators for the ten valid-length reserved-prefix ids (`grok:codex`, `codex:aa`, `omp:aa`, `opencode:aa`, `antigravity:aa`, `droid:aa`, `claude:aa`, `custom:aa`, `mock:aa`, `pi:aa`) | accept all ten (A has no reserved rule) |
| `"acme:copilot\r"`, `"acme:copilot\r\n"`, `"acme:copilot "`, `"acme:copilot/../x"` | refused in both carriers (the character class, not `$`) |

The id is then interpolated straight into paths — `scripts/verify-portable.py:1056`
`f"{self.host}-receipt.json"`, `:1010`/`:1093` the same pointer, `:668`/`:1168` `profiles/<host>.json`
— so a trailing newline validates and lands inside a filename, while the same id can never compare
equal to the id a profile declares. The seam's comment claims an id "can never be read as a path or a
host name to probe"; A does not hold it.

**The length lesson (judge correction, kept).** A shade vector with a one-character name label
(`omp:x`) is refused by the *shape* — the name floor is two characters — which hides the shadowing
signal. Read the rule with valid-length labels: `omp:x` refused by shape, `omp:xx` accepted by A. All
counts here use valid-length labels; the reachable shadowing set for A is 70 ids plus the newline.

## Cross-judge verdict

Independent read-only judge (`reviewer` agent, own probes against the seam and both arm probes):

* **Base: B.** "The only arm holding C1+C2 and closing C3/C4 at the enforcement gate, for 18 lines,
  with zero existing-artifact breakage." A fails C3+C4 outright; C fails the task's purpose (C2).
  **Agreement on the base.**
* **Q1 (carrier asymmetry):** land the terminator in the shared string (`(?!\n)$` — one line, no
  names embedded, keeps the `pattern ==` pin, holds in both carriers), and "**do not** embed the
  reserved set in the string". **Partial dissent**, weighed below.
* **Q2 (is the reservation worth landing):** "**land, namespace-label-only.** The seam comment already
  refuses bare names because they would collide with the flat built-in namespace — `grok:evil` reopens
  that exact collision. Failure modes stated honestly: no `split(":")[0] in BUILTIN_HOSTS` dispatch
  exists today, so the dispatch hazard is latent; the live hazard is brand confusion."
  **Agreement.**
* `fullmatch` stays even with `(?!\n)$` — "one word, engine-level fix, survives future pattern edits".
  **Accepted**; the docstring says which carrier each mechanism is for.
* Corrections accepted: the shade vectors above; and my probe's parity column compared
  `is_external` against `$defs.host`, which mis-flagged bare `grok`/`codex`/`claude`/`custom` as
  "carriers disagree" — the harness now compares `is_valid_host_id` vs `$defs.host` and
  `is_valid_receipt_host` vs `$defs.receiptHost` (0 disagreements across all 37 vectors).
* Also accepted: B's rationale over-rejects lookaheads — `\Z` is indeed non-ECMA-262, but `(?!\n)$` is
  valid ECMA-262 and the judge measured `jsonschema` (Python backend) enforcing it. Only the `\Z` half
  of that rejection survives.

**Where the judge and the parent disagree, and the measurement that decides it.** The judge's reason
for keeping the reservation out of the string was that the 10 names would be "duplicated into the
string **with no pin**". That premise does not survive: the module *renders* the string from
`RESERVED_NAMESPACES`, and the lane's existing
`test_the_shared_schema_declares_the_modules_own_set_and_rule` (`defs["external"]["pattern"] ==
EXTERNAL_HOST_ID_PATTERN`) makes the schema's literal red the moment the tuples change — a pinned
mirror, not a duplicate. B's alternative mirrors the same rule as *prose* in the schema's
`description`, which no test pins at all and which the judge itself calls "real" asymmetry for
`\n`. So both clauses go into the string; the schema then states the rule instead of documenting that
only Python enforces it.

## Base, grafts, rejections

* **Base: B** — smallest rule satisfying 1-4 as a predicate, reserved set derived from the tuples
  rather than retyped, `pi`'s one hand-written name named and pinned.
* **Graft 1 (A's arm as a property, argued by the seam): one string, two carriers.** Both clauses move
  into `EXTERNAL_HOST_ID_PATTERN`. Measured: over 222 vectors,
  `is_external`/`is_valid_host_id`/`is_valid_receipt_host` are **identical between B and B+** (0
  differing vectors), so the graft moves no behaviour the predicate already had — it moves the
  *carrier*: `"acme:copilot\n"` and the reserved-prefix class go from schema-accepted to
  schema-refused (`today_schema=True → False` on exactly those two classes).
* **Graft 2 (B): the derived reserved set, `SCANNED_ONLY_HOST_NAMES`, and `pi`'s provenance** pinned
  against `scripts/scan-host-boundary.py:88`. A seventh built-in reserves itself with no list to edit.
* **Graft 3 (B's test sketch): reserve-vector pin per carrier.** B pinned `f"{name}:probe"` through the
  predicate only; B+ runs those vectors through `is_external` **and** the schema validator, plus the
  newline/space/traversal set. This is the pin HushedDormouse asked for ("refused in Python *and* per
  the schema this repo actually validates with"), and it is 16 of B+'s 36 lines.
* **Rejected, from B's rationale:** `\Z` in the shared string (not ECMA-262, breaks the carrier it
  fixes while the `pattern ==` pin stays green); a hand-typed reserved list; `re.match` plus a
  `"\n" not in host_id` guard; rejecting the whole mechanism.
* **Rejected, from the judge's Q1:** leaving the reservation predicate-only. See the dissent above —
  the stated drift objection is answered by the existing equality pin, and the alternative leaves
  descriptor files validated by any JSON-schema consumer accepting `grok:codex`.
* **Not grafted from B:** nothing in its predicate beyond `fullmatch` (kept) — B's reserved branch is
  redundant once the string carries the lookahead.
* **Not grafted from C:** everything except the rejection; its census is the honest cost of the closed
  path and is why C stays on the table as the alternative a reviewer may still prefer.

### Landing diff (measured with `diff -u` against `d8910b0`)

| file | added | removed |
| --- | --- | --- |
| `scripts/host_identity.py` | 16 | 2 |
| `schemas/portability/host-id.schema.json` | 1 | 1 |
| `tests/test_host_identity.py` | 16 | 0 |
| **total** | **33** | **3** |

B+ does not win criterion 5 (A 0, B 18, B+ 36 changed lines): 16 of its lines are the parity pin that
neither A nor B has, 1 is the schema's rule string, and the module's extra lines over B are the
render plus its comment. It wins criteria 3 and 4 *on both carriers*, which is the seam's contract.

These are the numbers for the arena's landing copy; the landed commit's hunks are larger, because the
owner's comment wording is longer and its test carries two extra assertions:
`git show --stat 4aeccee` reports `scripts/host_identity.py` 32 changed lines (18 here),
`schemas/portability/host-id.schema.json` 4 (2 here), `tests/test_host_identity.py` 29 (16 here), plus
the five restamped `.audit/evidence/*.json` that any landing in this lane carries. The criterion-5
ranking is unchanged either way: A 0 < B 18 < B+ (~36).

## Verification

| probe | result |
| --- | --- |
| `verify.py probe` (37 vectors: bare, alias/builtin, reserved, declared, edge) | scorecard 1-5 PASS; `CARRIERS DISAGREE` count **0** (module `is_valid_host_id` == `$defs.host`, `is_valid_receipt_host` == `$defs.receiptHost`); delta vs today's schema exactly `grok:codex` and `acme:copilot\n` (`True → False`) |
| 222-vector three-way differential (A vs B vs B+) | A-vs-B/B+ 71 vectors differ; **B vs B+ 0**; `match` == `fullmatch` on the fixed pattern for all 222 |
| `verify.py pytest --rule A` (control: module untouched) | `17 passed` |
| `verify.py pytest --rule synth` (B+ modelled in process: module attributes + the schema's pattern string intercepted on read) | `17 passed` — including the `pattern == EXTERNAL_HOST_ID_PATTERN` pin, which reddens with the module patched and the schema not (observed: `1 failed, 16 passed` before the intercept was added) |
| arm B probe | 1-4 PASS, 5 PASS at 18 lines, schema-carrier losses printed |
| landing head `4aeccee` (after the handoff, repo read-only to the arena) | landed pattern/reserved set identical to `synthesis/shape.py`, 0 disagreements over 89 vectors, schema `$defs.external.pattern` == module pattern, both carriers agree on the accept/refuse sets above; owner-reported gate: 18 passed in the seam test file, 746 passed / 10 skipped / 0 failed offline, `refresh-static --host all` 6/6 |
| repo state | `git status --short` in `pstack` shows only this note; the 446 worktree is clean; `PYTHONDONTWRITEBYTECODE=1` and `TMPDIR=/var/tmp/arena-extid-tmp` throughout |

Limits, stated not implied: the `pytest --rule synth` leg models the landing in process, so it does
**not** execute the landing's own new pin function — the parity probe asserts the same vectors
through the real jsonschema registry instead. Nothing under `/home/tommyk/projects/pstack` was
written except this note.

## Run conditions

* Invocation shape: `/arena` Phase A-E run by the parent worker — one fan-out of three arms in a
  single `task` call (`sonic` for A and C, `task` for B), one read-only cross-judge (`reviewer`),
  parent pick/graft/verify. Known deviations: the judge was spawned while arms A and C were still
  empty (they had produced nothing for ~5 minutes); it was told to reconstruct A from the seam source
  and census C itself, and by the time it reported, both arms had delivered. Recorded as a caveat on
  the verdict's independence, not as a clean Phase C.
* Model pinning: this runtime's `task` API exposes agent types, not model slugs, and
  `~/.claude/pstack-models.md` is absent, so the arena's model pool could not be used. Every arm and
  the judge resolved to the parent runtime's default model — a **degenerate model arm-set**; the arms
  differ by content (three different rules), which is what the pick rests on. The judge is a different
  agent type with an independent read and its own probes, but not a different model family.
* Dropouts: none in the end. A and C were delayed ~5 minutes because `/tmp` (a 7.8G tmpfs) was 100%
  full — pytest tmpdirs holding full repo copies (`test_evidence_durability.py`) had consumed it,
  which broke every write into `/tmp/arena-external-id-shape/*`. The parent freed 203M mid-run, paged
  both arms, and both delivered artifacts. `TMPDIR=/var/tmp/...` for anything pytest-shaped on this
  box, or `/tmp` refills in 2-3 full-suite runs.
* Environment: Python 3.14.8, `pytest` 9.1.1, `jsonschema` 4.26.0, `referencing`, all from
  `/home/tommyk/projects/pstack/.venv`.

## Known gaps

* **The string is hand-mirrored.** `$defs.external.pattern` must be re-rendered when the tuples change.
  The existing equality pin makes drift red, but the edit is still manual; a generator step is the
  obvious follow-up and was not built (one string is not yet worth a generator).
* **`(?!\n)$` is Python-motivated.** ECMA-262 `$` was already an end-of-input assertion, so JS
  consumers see no change; the lookahead exists because Python's `$` is not, and both carriers run
  Python `re` today. It stays harmless if the schema moves to a spec-conformant engine.
* **`\r` is refused by the character class, not by the terminator** (observed in both carriers). A
  future pattern that admitted `\r` would need its own clause.
* **`split(":")[-1]` callers are not protected.** The rule reserves the namespace label only; a caller
  keying on the name label could still misread `acme:grok` as built-in `grok`. Nothing in the tree does
  this today (no `split(":")` on host ids outside `is_external`).
* **`pi` is reserved but not registered.** `scan-host-boundary.py:88` scans `pi` as a harness name while
  `KNOWN_HOSTS` does not carry it, so `pi` can be neither a bare id nor a namespace. That asymmetry is
  #446's, untouched here; the reserved set tracks whatever `HARNESS_NAMES` becomes.
* **`{"pi"}` is still spelled twice after the landing.** The landed module exports
  `SCANNED_ONLY_HOST_NAMES = ("pi",)` and `scan-host-boundary.py:88` keeps its own literal
  (`HARNESS_NAMES = set(KNOWN_HOSTS) | set(OBSERVER_HOSTS) | {"pi"}`). The seam's census test pins the two
  sets equal, so drift is caught, but the clean cutover is for the scanner to import the name. The lane
  owner left it deliberately — the scanner is outside that unit's file scope — and flagged it to the
  lead; it is the one piece of the rule that still has a second declaration.
* **No benchmark surface**, so none was run; the landing diff is the measurement.

## Artifacts

| path | what |
| --- | --- |
| `/tmp/arena-external-id-shape/brief.md` | Phase A framing: rubric, seam facts, environment measurements, per-arm contract |
| `/tmp/arena-external-id-shape/candidate-a/` | arm A: `shape.py` (seam bytes), `probe.py`, `rationale.md` |
| `/tmp/arena-external-id-shape/candidate-b/` | arm B (base): `shape.py`, `probe.py`, `rationale.md` |
| `/tmp/arena-external-id-shape/candidate-c/` | arm C (control): `shape.py`, `probe.py`, `rationale.md` |
| `/tmp/arena-external-id-shape/synthesis/shape.py` | the `B+` rule, importable |
| `/tmp/arena-external-id-shape/synthesis/verify.py` | probe + carrier-parity + patched-pytest harness |
| `/tmp/arena-external-id-shape/synthesis/landing/` | the landing copy (`scripts/`, `schemas/`, one new test) the 36-line diff is measured against |
| `/tmp/arena-external-id-shape/evidence/` | arm-B probe output, `B+` probe output, both pytest legs, the 222-vector differential |

The measurement tables above are the record. The harness paths are scratch on a tmpfs that is wiped on
reboot, so none of them is a live pointer: what the arena reconciled is pinned in-tree by
`tests/test_host_identity.py::test_a_reserved_namespace_and_a_trailing_newline_are_refused_by_both_carriers`,
which exercises the reserved set, the terminator vectors and the traversal forms through the module and
through the schema this repo validates with (`docs/research/arena-f2-seam-2026-10-17/f2_arena.py` is the
one arena harness kept in-tree; this record's harness is not, by the landing lane's choice).
