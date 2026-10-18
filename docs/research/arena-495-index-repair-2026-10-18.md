# Arena record: the #495 index-repair shape (issue #495, program #429)

Measured at trunk `163a4e1`. **Selected: base A (the U6 detect-and-prescribe hunk) plus three grafts
from B (project the inventory's missing rows back from the receipts on disk on every writer run; one
row projection that refuses bytes a row cannot stand on; name a failed index write instead of
raising, motivated by C's traceback finding) and one from C's control ledger (the missing-index
message names the remedy) — landed as shape `F`, 283 changed lines (verifier 108+/11−, tests
164+/0−).** A alone (77 changed lines) is the recorded minimal fallback. B as written (286 lines,
repair inside the read verb) loses rubric 3 and 4 on measurement. C is the control and loses rubric 1.

Harness `/tmp/arena-495/arena495.py`, landed with this record as
`docs/research/arena-495-index-repair-2026-10-18/arena495.py`; arm workspaces `/tmp/arena-495/candidates/<X>/` — all outside
the repo (this file is the only thing this pass writes into it). Every command cited below is
re-runnable from the harness; the probe list is in §Probe battery.

Scope: which repair shape the writer/reader pair should take for the **#495 row still open** — the
byte-level repair of the unreadable-durable path. U1 (#500) closed the ordering fault inside the
writer and added the reader-side row↔receipt cross-check; that cross-check *detects* the split and
returns `None` for a host with no row at all.

## Frozen rubric

Stated in `/tmp/arena-495/RULES.md` before any arm produced an overlay:

1. **No silent pass on an orphan receipt** — a host with a durable receipt and no index row must not
   exit 0 as if nothing were wrong.
2. **Repair path terminates** — no loop on corrupt or unwritable state, no traceback, no hang; a
   prescription the shape prints must not reproduce the same refusal when executed.
3. **Single writer preserved** — what writes the index, and does a read verb write it?
4. **Smallest diff** — fewest changed lines that satisfy 1–3.

Tie-break: the boundary a future maintainer can extend without breaking an invariant.

## The defect, reproduced at trunk before the arms

| probe | command | result |
| --- | --- | --- |
| F4 remedy | `rm .audit/evidence/index.json` then `refresh-static --host grok` | exit 0; index rows `['grok']` while `grok, codex, omp, opencode, antigravity` receipts are on disk |
| F4 remedy, then the gate | `check-evidence --host all` on that index | **exit 0**, 5 × `PASS`, droid `NOT_COVERED` — four rows short, gate blind |
| the issue's own row | delete `hosts.grok` row, keep `grok-receipt.json` | **exit 0**, `[grok] PASS` |
| the same with a read-only index | row deleted + `index.json` chmod 444 | **exit 0**, `[grok] PASS` |
| writer window | `index.json` chmod 444, then `refresh-static --host grok` | uncaught `Traceback`, `PermissionError` at `scripts/verify-portable.py:1079`, **after** `durable_file.write_text` at `:1075` — the durable receipt is rewritten and the inventory is left trailing it |
| unreadable index | `[]`, `{not json`, deleted, chmod 000 | exit 1, `… unreadable: AttributeError / JSONDecodeError / FileNotFoundError / PermissionError` — loud, but no verb, command or file action is named: 0 of 12 probe outputs carried a prescription |

The first two rows are the shape the issue calls out: the F4 remedy ("remove the inventory")
re-enters the omit-this-host class at whole-file granularity, and the U1 cross-check does not see it
because a row-less host returns `None` (`scripts/verify-portable.py:1106-1108`).

## Run conditions

* **Invocation shape actually used:** one `task` subagent per arm in a single fan-out, each told its
  arm and a `solutionSpace`; the harness was written and smoke-tested by the parent first, and the
  control arm's battery ran before the others started. Arms saw the rubric and the probe list; they
  did not see each other's designs. Arm A's artifact is a transcription of an existing hunk (PR
  #536), so its "design" is fixed by the branch; the parent transcribed the same hunk independently
  (`candidates/P/`) and the two overlays are **byte-identical** (`diff -q` silent on both files).
* **Model resolution — degenerate arm-set.** No `~/.claude/pstack-models.md` exists on this host and
  the `task` tool exposes no per-arm model pin, so every arm resolved to the session model. The
  invocation shape the skill names (`arena runners: claude-opus-5 / claude-fable-5 / claude-sonnet-5`)
  was **not** available: this is a single-family arm-set and its cross-family-independence claim is
  void. Same defect recorded on PR #536's adversarial round and in the wave-13 arena — the runtime
  offers no model pin, which is a tracked gap, not a judgement this record can make.
* Interpreters: every spawn runs through the repo venv
  (`/home/tommyk/projects/pstack/.venv/bin/python`, 3.14.8, pytest 9.1.1); the ambient `python3` is
  3.12.15 and has no pytest/jsonschema. `PYTHONDONTWRITEBYTECODE=1` on every spawn; the repo was never
  written to.
* **Harness revision 2, and what revision 1 got wrong.** Revision 1's prescription regex swallowed the
  closing backtick of a message's `` `command` ``, so a remedy ran as `--host grok\``, exited 2 from
  argparse, and the recheck reported `loop=True`. That is a harness artifact, not an arm defect. Every
  arm's battery was re-run under revision 2 and **no number in this record comes from revision 1**.
  Revision 2 also sets `TMPDIR=/var/tmp/arena-495-tmp` on every spawn.
* **Disk incident.** `/tmp` is a 7.8 GB tmpfs and saturated at 100% mid-run: pytest's tmpdirs hold
  full-repo disposable copies made by `test_evidence_durability.py`'s own helper, so two or three
  suite runs are tens of gigabytes. Arm A's first pytest run produced `shutil.Error: No space left on
  device` failures and was discarded; ~4 GB of stale pytest tmpdirs were reclaimed and every later
  spawn ran with `TMPDIR` on the disk-backed `/var/tmp` (596 GB free). No verdict rests on a run taken
  during the saturation.
* **Receipt-staleness migration (not a defect).** `scripts/verify-portable.py` is digested into
  `driver_revision`, so *every* arm that edits it moves the fingerprint and the five committed
  receipts go stale on `adapter`/`runtime`. Arm B measured it directly (`C: 87997bd18898 == receipt`;
  `B: 01854aeeeffb != receipt`, stale planes `{adapter, runtime}`). The receipt-freshness tests
  therefore fail in any un-migrated arm copy; the landed units U5/U6 restamped inside their own PRs.
  Un-migrated numbers are kept (`pytest.unmigrated.txt`) and the post-restamp gate is measured
  separately (§Verification).

## Probe battery

Twelve probes, identical for every arm, each restoring the stashed `.audit/evidence` bytes first
(`python3 /tmp/arena-495/arena495.py battery <ARM>`):

| # | probe | mutation | verb under test |
| --- | --- | --- | --- |
| 1 | baseline_all | none | `check-evidence --host all` |
| 2 | orphan_row | delete `hosts.grok` row | `check-evidence --host grok` |
| 3 | orphan_corrupt_bytes | `codex-receipt.json` unparseable | `--host codex` |
| 4 | orphan_unusable_shape | `codex-receipt.json` = `{"run_id": "x"}` | `--host codex` |
| 5 | row_without_receipt | `grok-receipt.json` removed, row kept | `--host grok` |
| 6 | index_list | `index.json` = `[]` | `--host grok` |
| 7 | index_garbage | `index.json` unparseable | `--host grok` |
| 8 | index_deleted | `index.json` removed | `--host grok` |
| 9 | index_denied | `index.json` chmod 000 | `--host grok` |
| 10 | index_readonly_orphan | row deleted + `index.json` chmod 444 | `--host grok` |
| 11 | evidence_dir_denied | `.audit/evidence` chmod 000 | `--host grok` |
| 12 | droid_no_receipt | none | `--host droid` |

Probes 2, 10, 11, 12 are the parent's additions to the issue's two probes; the arms could not see them
beforehand. Each probe records exit code, matched markers, index bytes before/after, receipt bytes
before/after, and — when the arm printed a `verify-portable.py refresh-static | rebuild-index |
repair-index` command — executes it and re-runs the check, comparing the reported reason for an
identical repeat (`loop`). Probe 10 restores the index permissions before executing a printed remedy,
so the denial is exercised during the check verb and the remedy runs against a writable file.

## Candidates and their measured ledgers

| arm | shape | changed lines (verifier / tests) | orphan_row | index_deleted | read-verb index writes | loops | tracebacks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A** | detect + prescribe: `STALE/REBUILD-REQUIRED` + `refresh-static --host <h>`; repair text when the orphan bytes are unusable | **77** (29+/2−, 46+) | exit 1, prescription runs → recheck exit 0 | exit 1, no prescription | none | none | none |
| **B** | repair inside the read verb from the receipt bytes; rows only added | 286 (158+/9−, 119+) | exit 1, **index written** (4→5 rows), "rebuilt it from the durable receipt bytes on disk … re-run this check to confirm"; run 2 and 3 exit 0 | exit 1, index written (rows `[]`→5), stdout carries the `unreadable: FileNotFoundError` line *and* the rebuild line; run 2 and 3 exit 0 | `orphan_row`, `index_deleted` | none | none |
| **C** | control, no change | 0 | **exit 0, PASS** | exit 1, no prescription | none | none | none |
| P | parent's independent transcription of A | 77 | exit 1, converges | exit 1 | none | none | none |
| S | parent's first synthesis (seed only when the index is missing) | 153 | exit 1, converges | exit 1 + prescription converges | none | none | none |
| **F** | **selected**: A + receipts projected back into the inventory on every writer run + one row projection + named remedies and refusal | **283** (108+/11−, 164+) | exit 1, converges | exit 1 + prescription converges | none | none | none |

The parent's first-pass scores (1–5, equal weight, read off the ledgers, not off the arms' own
summaries) — two cells were revised after the cross-judge pass, see §Cross-judge:

| criterion | A | B | C | revised? |
| --- | --- | --- | --- | --- |
| 1. no silent pass on an orphan receipt | 5 | 5 | **1** | — |
| 2. repair path terminates | 5 | 4 | 2 | B → 5 (B does terminate) |
| 3. single writer preserved | 5 | **3** | 5 | — |
| 4. smallest diff that satisfies 1–3 | **5** | 2 | 5 (vacuous) | C → 1 (the control satisfies none of 1–3) |
| **total, resolved** | **20** | **14** | **9** | |

* C fails criterion 1 on two measured probes (`orphan_row`, `index_readonly_orphan`, both exit 0 with
  `[grok] PASS`), scores 2 on criterion 2 (no repair path: 0 of 12 probe outputs carry a prescription,
  and the writer window ends in a traceback after rewriting the durable receipt), and its 0-line diff
  cannot be scored as "fewest lines that satisfy 1–3" because it satisfies none of them.
* B loses criterion 3 on measurement, not taste: `check-evidence` — a read verb — wrote `index.json` on
  2 of 12 probes (rows added, nothing removed; its `write_evidence_index` is one writer *routine*). Its
  repair-and-fail-the-same-invocation semantics are recorded in prose rather than scored as a
  termination defect: verified on a private copy, B terminates (`orphan_row` run 1 exit 1 with the index
  already rebuilt, runs 2 and 3 exit 0; deleted index run 1 exit 1 with all five rows written, runs 2
  and 3 exit 0). Its own rationale states both losses.
* A satisfies 1–3 with one branch and a docstring sentence (29+/2− in the verifier).

## Cross-judge

One read-only judge subagent (`reviewer`) was spawned after the three arms had written their
artifacts; it was given the frozen rubric, the arm paths and the run-condition caveats, and it scored
every criterion with a record pointer. **It recommends A as the base and agrees with all five parent
grafts, preferring F over S.** (Its `(i)–(v)` are the feature list it read out of the S/F artifacts:
grafts 1–4 here; the backtick amendment it asked for became graft 5.) Its scores:

| criterion | A | B | C |
| --- | --- | --- | --- |
| 1. no silent pass | 5 | 5 | **1** |
| 2. terminates | 5 | 5 | 2 |
| 3. single writer | 5 | **2** | 5 |
| 4. smallest diff | 5 | 2 | **1** |
| **total** | **20** | **14** | **9** |

Deciding measurement, quoted from the judge: B's `orphan_row` and `index_deleted` records carry
`index_written True` (a read verb writes the inventory) against A's `index_written True` in 0 of 12,
with identical closure on criterion 1 (`orphan_row` exit 1 both, control exit 0); termination does not
separate A and B in the revision-2 records, writer-purity and size do.

**Two cells where the judge and the parent's first pass differed, and how they were resolved:**

* **C, criterion 4 — parent 5 ("vacuously fewest lines") vs judge 1.** The criterion's own wording is
  "fewest changed lines **that satisfy 1–3**"; the control satisfies none of them, so 0 lines is not
  qualifying. **The judge's reading is adopted**; C totals 9, not 13. The ordering A > B > C is
  identical under either reading.
* **B, criterion 2 — parent 4 ("repairs and fails the same invocation") vs judge 5.** The criterion is
  termination, and B's path does terminate: independently re-derived on a private copy of B's overlay
  (`candidates/H`, parent probe 8) — orphan row run 1 exit 1 with the index already rebuilt, runs 2
  and 3 exit 0; deleted index run 1 exit 1 with all five rows written, runs 2 and 3 exit 0. **The
  judge's 5 is adopted** and the fail-then-succeed semantics moved into the prose above; B totals 14
  either way.

The judge also named two things the parent's pass had not yet done, both now in the artifact:
(1) drop the markdown backticks around the prescribed command — measured below, the extracted text
pasted into `sh -c` exits **127** (`sh: 1: [grok]: not found`) because the shell command-substitutes
first; F's un-backticked text exits 0; (2) **pin** the named index-write refusal, which existed only
as code — `test_a_denied_index_write_is_named_not_raised` now asserts exit 1, the message, the absence
of a traceback and unchanged inventory bytes (measured: all four hold). It also flagged S's stale
assertion (`"unreadable"` vs the `is missing` text) — F already carries the corrected pin, and S stays
in the record only as the measured intermediate.

**What the judge could not verify, and its disposition:**

| judge's gap | disposition |
| --- | --- |
| P's patch-level identity with A | P is the parent's own copy and carries no `patch.diff`; the judge's `diff -r P/files A/files` clean run is the identity evidence, and A's own `patch.diff` is the patch record |
| B's multi-run invariants (`1,0,0` convergence, drop-receipt keeps 5 rows, the 4-row partial rebuild) | closed by the parent re-deriving convergence on a private copy (probe 8); the other two stay as B's own record |
| B's trunk-selection counts (`4 failed, 92 deselected` / `4 passed`) | not re-derived by the parent; recorded as the arm's own measurement, not part of the verdict |
| C's git-present `92 passed` claim | no copy in this arena has `.git`; the control baseline used everywhere is the no-git **1 failed, 91 passed**, and the git-present number is not used |
| the 4th pytest failure behind each arm's tail | identified: for A and B it is `test_durable_receipts_exist_for_all_five_hosts` beside the three named in §Suite (the tail showed three of four `FAILED` lines) |
| F's full suite unrecorded | closed by the post-restamp run in §Suite (F: 1 failed, 96 passed pre-final, final overlay re-run below) |


## Selection and graft

**Base: A** — the U6 hunk as transcribed by arm A and independently by the parent (byte-identical).
It is the only candidate that satisfies 1–3 in 77 lines, and criterion 4 is the rubric's own
tie-breaker for exactly this comparison.

**Graft 1 — from B: the inventory's missing rows are projected back from the receipts on disk
whenever the writer runs.** Not only when the index is absent: a row-less host is put back by the
prescribed `refresh-static --host <host>`, so the reader's prescription is *whole* and the inventory
cannot stay partial. Measured: (`a`) deleted index → one `refresh-static --host grok` restores all
five rows instead of `['grok']`; repair cost falls from **5 commands** (one per host, rows growing
1,2,3,4,5 — measured in P) to **1**. (`b`) one row deleted → the reader exits 1 with
`STALE/REBUILD-REQUIRED`, and that prescribed command restores the row and `check-evidence --host all`
exits 0. (`c`) two rows deleted, then `refresh-static --host grok` → all five rows come back, and each
row equals the receipt it names (`run_id`, `timestamp`, `planes`, `surface_revisions`). Missing rows
only: an existing row is never rewritten, so a row/receipt disagreement stays the cross-check's to
report, and nothing is ever removed.

**Graft 2 — from B: one row projection, and refuse bytes a row cannot stand on.** The row the run
writes and the row the projection writes are now the same code (`evidence_index_row`). Measured basis
on the weaker projection (S, which only checked `"run_id" in data`): (`a`) a receipt file containing
`{"run_id": "x"}` plus an absent inventory produced a junk codex row (`run_id: "x"`, null
`planes`/`surface_revisions`) — an inventory naming a host whose bytes are unusable; with the graft
codex gains no row and the orphan check reports it. (`b`) grok's receipt bytes copied over
`codex-receipt.json` plus an absent inventory produced a codex row carrying **grok's** `run_id`
(`grok-1792278806-f1c4983e`); with B's host check (`receipt.host != host` → skip) codex stays row-less
and is reported. (`c`) one field list instead of two.

**Graft 3 — from C's finding, with B's refusal discipline: name the failed index write instead of
raising.** Trunk tracebacks at `:1079` *after* rewriting the durable receipt. F exits 1 with
`FAILED to write the evidence index at …: PermissionError: … The durable receipt at … is already
written, so the inventory trails it until the file is writable and this check is re-run.` A named
refusal, not a prevention: the split still happens and the reader cross-check still detects it.

**Graft 4 — from A itself: the missing-index message names the remedy.** Trunk's `unreadable:
FileNotFoundError` names no next step; F says the file is missing, that it is the inventory of every
host's durable receipt, and names `refresh-static --host all`. Executing it converges
(measured: remedy exit 0, `check-evidence --host grok` re-check exit 0), including for a host that
writes no durable receipt (`--host droid`: remedy `--host all` → re-check exit 0; `--host droid`
alone writes nothing and would have looped, which is why the message names `--host all`).

**Graft 5 — from the cross-judge's review: the prescribed command is paste-safe.** A's extracted
message wraps the command in markdown backticks (`` `python3 … --host grok` ``). Measured: that text
pasted into `sh -c` exits **127** — the shell command-substitutes, runs the inner command and then
tries to execute its stdout (`sh: 1: [grok]: not found`). F prints the command unquoted, and the same
`sh -c` probe exits 0 with the row restored. Two words changed, no lines.

**Rejected — B's repair inside the read verb.** A repair cannot be automatic if only the writer may
write — that is B's premise and it is coherent — but it costs rubric 3 (measured: the inventory's
bytes change under a check verb) and it makes the repairing invocation exit 1 anyway, so the operator
runs the gate twice to see green. Graft 1 gets the repair through the verb that already owns the
write, and the reader's prescription is what schedules it.

**Rejected — a dedicated `rebuild-index` verb.** It would repair without a read verb writing, but it
adds a verb, an argument surface and a second write path for a repair one `refresh-static --host <h>`
already performs, and rubric 4 prices that. Both arm A and arm B rejected it independently.

**Rejected — write-order inversion (row before durable bytes).** Not attempted this pass. Inversion
moves which side of the window is stale (arm B's rationale says the same); with the rows projected
from the bytes on disk, the split is detected, repaired by one prescribed command, and named when the
write itself fails. Left as the follow-up below.

**Convergence signal:** A, S and F share the same detection text and the parent's independent
transcription of A's hunk is byte-identical to arm A's; B diverges only on *where* the repair lives —
the exact seam this arena was asked about, and measurement decides it.

## Verification

### Frozen battery, selected shape (`python3 /tmp/arena-495/arena495.py battery F`)

All 12 probes: `index_written=false` and `receipts_written=false` for every probe (a read verb never
writes the inventory — criterion 3), no `loop=true`, no `TIMEOUT`, no `Traceback` in any probe's
stdout/stderr. The four probes that must fail loudly do (`orphan_row`, `index_list`, `index_garbage`,
`index_deleted`, `index_denied`, `evidence_dir_denied` → exit 1); `baseline_all` and
`droid_no_receipt` stay exit 0. The two prescriptions the shape prints both converge:

| probe | first run | prescribed remedy | re-check |
| --- | --- | --- | --- |
| `orphan_row` | exit 1, `STALE/REBUILD-REQUIRED`, names `grok-receipt.json` | `python3 scripts/verify-portable.py refresh-static --host grok` → exit 0 | exit 0 |
| `index_deleted` | exit 1, `index … is missing; it is the inventory of every host's durable receipt. Rebuild it with … refresh-static --host all` | `… refresh-static --host all` → exit 0 | exit 0 |

### Parent probes beyond the frozen battery (each measured on a disposable copy)

The cross-judge named two probes it wanted (`orphan_unusable_rowless`, `writer_readonly_index`); both
are already rows 1 and 7 below — probe 1 on a private copy of A's overlay, probe 7 on C and on F.

| # | probe | trunk (control C) | selected shape F |
| --- | --- | --- | --- |
| 1 | row-less + receipt **unusable** (`drop_row:grok` then `grok-receipt.json` = `{not json`) — the combination arm A's rationale flagged as missing from the battery | exit 1, durability line, no prescription | exit 1, `… has no row for grok and its durable receipt … cannot be read as a usable receipt`, **no prescription** → nothing can loop |
| 2 | repair cost after `rm index.json`: `refresh-static` per host | 5 commands, inventory rows `['grok']` → `['codex','grok']` → … → 5 | **1 command**, rows `['antigravity','codex','grok','omp','opencode']` |
| 3 | deleted index + unusable receipt bytes (`codex-receipt.json` = `{"run_id": "x"}`) | n/a | 4 rows written, **no** codex row, codex reported as an orphan |
| 4 | deleted index + a *valid receipt for another host* over `codex-receipt.json` | n/a | codex stays row-less and is reported (`S`, the weaker projection, wrote a codex row carrying grok's `run_id` `grok-1792278806-f1c4983e` — this is the graft that closed it) |
| 5 | one row deleted, then the **prescribed** command (`refresh-static --host grok`) | reader exit 0 (silent); the same command would leave the row missing | reader exit 1 → command exit 0 → `check-evidence --host all` exit 0, all five rows equal to the receipts they name |
| 6 | `check-evidence --host droid` with the index deleted, then the prescribed remedy | exit 1, no remedy named | exit 1 with the remedy named; `refresh-static --host all` → re-check exit 0 (`--host droid` alone writes nothing and would loop — hence `--host all` in the message) |
| 7 | writer window: `index.json` chmod 444 then `refresh-static --host grok` | uncaught `Traceback`, `PermissionError` at `:1079`, durable receipt rewritten (`:1075`) | exit 1, `FAILED to write the evidence index at …: PermissionError: … The durable receipt at … is already written, so the inventory trails it until the file is writable and this check is re-run.` |
| 8 | B's convergence, re-derived on a private copy of B's overlay (`candidates/H`) | n/a (`A`: reader exit 0, silent) | B: orphan-row run 1 exit 1 (index already rebuilt → 5 rows), runs 2 and 3 exit 0; deleted index run 1 exit 1 (all five rows written), runs 2 and 3 exit 0 — terminates, two invocations to green |
| 9 | end-to-end gates after the migration restamp, selected shape (`candidates/G` = F's overlay, `refresh-static --host all` first) | — | `doctor --host all` exit 0 (6 hosts), `check-staleness --host all` exit 0 (`ALL FRESH`), `check-evidence --host all` exit 0 (5 × `PASS` + droid `NOT_COVERED`) |
| 10 | paste-safety: the printed prescription handed to `sh -c` verbatim (private copies of A's and F's overlays, `candidates/KA` and `candidates/K`) | A as extracted: exit **127**, `sh: 1: [grok]: not found` (backticks command-substitute) | F: exit **0**, row restored |

### Suite in the arm copies

Pin selection first, on a private copy of the final overlay (`candidates/K`),
`-k "rebuild_required or missing_index or projection_skips or missing_row_comes_back or denied_index_write"`:

```
5 passed, 92 deselected in 25.65s
```

— A's extracted row-less pin plus the four new ones (missing-index rebuild, projection refuses
unusable/cross-host bytes, a missing row comes back from the prescribed run, the denied index write is
named), all green on the selected shape.


`python3 /tmp/arena-495/arena495.py pytest <ARM> tests/test_evidence_durability.py` (repo venv, no
`.git` in any copy, `TMPDIR=/var/tmp/arena-495-tmp`). Every copy is a no-git extraction, so
`test_a_stat_denied_recorded_receipt_is_refused_not_reported_missing` fails everywhere (its
`select-checks` path runs `git merge-base` → exit 128); that one failure is the control's whole
baseline.

| copy | state | result | failures |
| --- | --- | --- | --- |
| C (control) | trunk, unedited | **1 failed, 91 passed** (195s; reproduced by the arm itself) | the `.git` one |
| A | un-migrated (receipts still at trunk's `driver_revision`) | **4 failed, 89 passed** (177.83s; reproduced at 164.49s) | the `.git` one + 3 fingerprint: `test_durable_receipts_exist_for_all_five_hosts`, `test_docs_changes_do_not_stale_any_plane`, `test_check_staleness_cli_json_output` |
| B | un-migrated | **4 failed, 92 passed** (171.48s) | the same 4 |
| A | post-restamp (`refresh-static --host all` in the copy) | **1 failed, 92 passed** (138.37s) | the `.git` one |
| B | post-restamp | **1 failed, 95 passed** (228.75s) | the `.git` one — B's four pins among the 95 |
| F (selected) | post-restamp | **1 failed, 96 passed** (126.16s) | the `.git` one — carry the final overlay; two later comment-wording edits inside the projection's docstrings change no line count and are stripped by the driver fingerprint |

So the three extra failures in every edited arm are the receipt-staleness migration §Run conditions —
the arm B record measured the mechanism (`driver_revision` moves on any edit to the verifier) — and
the suite is green in the copies that restamped first, which is what a landing does inside its own PR.
Two later runs (C 4 failed/88 passed, F 4 failed/92 passed) were taken while a parent probe had left a
restamped receipt beside an older index row in the copy, and are excluded as contaminated: their extra
failures are the reader's own row/receipt cross-check firing (`… disagrees with … on run_id`), which is
the U1 behaviour working, not a defect.



## Known gaps in the selected shape

* **The projection needs a run.** The reader still only reports: a row-less host stays row-less until
  the prescribed `refresh-static --host <h>` runs, and a deleted inventory stays deleted until
  `refresh-static --host all` runs. That is deliberate — a gate that repairs silently would absorb the
  incident it exists to report — but it means F repairs *at the writer*, never during a check.
* `durable_file.write_text` in the writer is still unguarded: ENOSPC or a denied directory on the
  receipt itself fails before any index logic runs. Out of this arena's scope (the receipt path, not
  the inventory path); measured only as the check verb's `Dangling evidence path` line.
* The projection's coverage is the declared host list (`get_declared_hosts()`), not "every receipt
  file in the directory": a receipt for an undeclared host stays un-inventoried (the run would not
  have listed it either).
* Row/receipt *drift* is reported, never repaired — by design (repairing it would erase the only trace
  of a hand-edit or a foreign writer). Same for a row naming a receipt that is not there.
* Nothing binds a hand-written row to the receipt it names; the reader cross-check is the only gate.
* Single-family arm-set (§Run conditions): the arena's independence claim is void for this run.

## Follow-ups

1. Land the harness with this record (`docs/research/arena-495-index-repair-2026-10-18/arena495.py`)
   if the owner wants the 12-probe ledger re-derivable; the probe list and every command are in this
   record either way.
2. Write-order inversion for the index/durable window (`:1075`/`:1079`) is still the issue's own
   alternative prevention; the arena measured detection, a prescribed repair and a named refusal for
   that window, so inversion should be priced against those rather than re-argued.
3. Model pinning for arena arms: without it every arena on this host is a single-family arm-set, and
   neither the U6 round nor this one can claim independent review.
4. `tests/test_evidence_durability.py`'s `_disposable_copy` copies the whole tree per case (~150 MB);
   on a tmpfs host that saturates `/tmp` in two suite runs (measured). Worth a lighter copy or a
   `TMPDIR` note in the test-tier doc.
5. Fold the parent's one-off probes into the harness's `PROBES` list for the next run: the
   row-less + unusable-receipt combination (today only the row-present corrupt probes are in the
   battery, which is why arm A's repair branch is pinned by pytest but never exercised by the battery)
   and the writer-side read-only-index probe (probe 10 restores permissions before executing a remedy,
   so it measures the check verb's denial, not the writer's).
