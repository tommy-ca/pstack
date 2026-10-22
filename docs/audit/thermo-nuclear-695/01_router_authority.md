# Lane: shared router and instruction authority (BASE..HEAD)

## Scope pin

- BASE `ef3405282e4afd2636923043ca59aac8a09d4170`
- HEAD `10025900e8cb481540ce6f61f32d6b73ff638b3f`
- 10 commits, 7 files in lane, +63/-23 lines, `profiles/*.json` unchanged in the range
  (`git diff --stat ef34052..1002590 -- profiles` is empty).
- Line counts at HEAD (none near 1000): poteto-mode 155, setup-pstack 199,
  maintain-verification-skill 42, reflect 69, grok-transcript 9,
  harness-neutral-authority doc 37, verification-test-tiers 350.

## Verdict

The train did land one canonical source for the two facts that actually gate host
behaviour — `skill_order` and `plugin_manifest` now live only in `profiles/<host>.json`,
are consumed by `scripts/route_resolver.py::resolve_skill_order`, and the router prose
defers to them instead of enumerating them. That is a real deletion of a duplicated
convention and it is enforced by a test.

It did **not** land a general rule. It landed a per-file scrub of exactly one file plus a
text denylist scoped to that file, and left the same defect class live in the sibling
canonical skills touched by the same series (`reflect`), in the Grok-scoped setup skill,
and in the new architecture doc. `skills/reflect/references/grok-transcript.md` is not a
second convention that replaces the first — it is the correct home for a host fact — but
the shared body that points at it re-creates the coupling the doc forbids.

## Q1 — Is host selection single-sourced?

Yes for skill order and manifests; no for references and model tiers.

Single-sourced, verified:

- `profiles/<host>.json` carries `skill_order` (list of
  `{need, primary_pstack, secondary_user, fallback_builtin, notes}`) and
  `plugin_manifest`. `scripts/route_resolver.py` is the consumer
  (`resolve_skill_order`, `resolve_skill_order_with_shadow`); `scripts/eval_decision_routing.py`
  and `scripts/verify_rollback_equivalence.py` exercise it.
- `skills/poteto-mode/SKILL.md:15` and `:19` now name no host file at all; the
  `references/<host>-tools.md` mapping is a naming convention, qualified with
  "(when present)" — correct, because `profiles/claude.json`, `profiles/copilot.json`
  exist with no matching reference file.
- Behaviour pin: `tests/test_verify_harness_playbooks.py::test_poteto_mode_first_todo_requires_host_map`
  asserts `identify the active host`, `profiles/<host>.json`, `references/<host>-tools.md`
  in the first todo, and `re.search(r"[A-Za-z0-9]+-tools\.md", skill) is None` over the
  whole router. `tests/test_scan_host_boundary.py::test_portable_router_selects_the_active_host_not_grok`
  adds a five-string denylist. Both pass at HEAD; I ran
  `scripts/scan-host-boundary.py -v` → `PASS ... Scanned 143 files ... 0 boundary leaks`.

Not single-sourced:

- **Antigravity model tiers.** `setup-pstack/SKILL.md:12` is the only place in the tree
  that names `.antigravity-plugin/models.json` and the `pro`/`flash`/`flash_lite`/
  `inherit` binding. `grep -n "models.json\|flash_lite" profiles/antigravity.json
  skills/poteto-mode/references/antigravity-tools.md` returns nothing; the profile
  declares `plugin_manifest: .antigravity-plugin/plugin.json` and
  `runtime_conventions.default_model: inherit`, no tier binding. So the file's own new
  rule at `setup-pstack/SKILL.md:8` — "resolve the declared model/effort catalog and
  native setup through `profiles/<host>.json` and its host reference" — points at two
  artifacts that both lack the fact. Duplicate-owner direction is available (profiles
  `bindings` / `runtime_conventions`), and the current home is drift-invisible:
  `DEFAULT_EXEMPTIONS` exempts `skills/setup-pstack/**`.
- **Manifest enumeration.** The rest of `setup-pstack/SKILL.md:12` repeats
  `.codex-plugin/plugin.json`, `.omp-plugin/package.json`, `.opencode-plugin/package.json`
  — all three are already `plugin_manifest` in the corresponding profile. A second owner
  for a machine-readable field, inside a prose paragraph.
- **Host-reference naming for reflect.** `reflect/SKILL.md:23` names
  `references/grok-transcript.md` inline; `reflect/references/` also carries
  `judgment-reviewer.md:20`, `divergent-reviewer.md:21`, `tooling-reviewer.md:33`, which
  define "a skill counts as used" only for `.grok/skills/`, `~/.grok/skills/`, or
  plugin-installed paths. That is a Grok-only detection rule inside prompts that are
  shipped to every host, and it is not in a `*-tools.md` or `*-transcript.md` file — it
  is buried in the reviewer templates, so nobody will find it when they port reflect.

## Q2 — Does a shared surface still privilege a Grok fallback?

Yes, two places, both in `reflect`.

`reflect/SKILL.md:23`: "find this conversation's transcript in the host's own reference
(`references/grok-transcript.md` on the Grok adapter)". The parenthetical is the only
concrete artifact named, it is Grok's, and for the other seven profiles no
`references/<host>-transcript.md` exists (`ls skills/reflect/references/` → grok only).
So the instruction's satisfiable branch is Grok and the unsatisfiable branch is everything
else, falling to "pass a tight digest" — which is a degradation the skill admits to.

`reflect/SKILL.md:56`: "hand to Grok Build's `/create-skill` and run its draft / test /
iterate loop". The same train moved the router off exactly this coupling
(`poteto-mode/SKILL.md:29`: "Agent-facing prose and SKILL.md changes follow the
**Authoring a Skill** playbook (`playbooks/authoring-a-skill.md`); host-native authoring
commands are adapter-local"), and `skills/poteto-mode/playbooks/authoring-a-skill.md`
exists and is already the canonical authoring surface
(`grok-tools.md:36`, `codex-tools.md:45` both map it). `automate-me/SKILL.md:11,67,109`
carries the same leftover.

Why nothing caught it — the enforcement seam has a deliberate hole. In
`scripts/scan-host-boundary.py::is_host_routing_directive`:

```python
m = re.search(r"\bGrok Build\b(?![\u2019']s?\b)(?!:)", line)
```

The possessive is excluded. I probed the scanner directly:

- `"hand to Grok Build's /create-skill and run its loop"` → `[]`
- `"hand to Grok Build’s /create-skill and run its loop"` → `[]`
- `"Use Grok Build to author the skill"` → `[('Grok Build', 'Grok Build host routing name')]`
- `"Read references/grok-transcript.md on the Grok adapter"` → `[]`

So the exact string that survives in reflect (and automate-me) is invisible, and the
router is clean only because a per-file test asserts the five strings by hand. Blast
radius of removing the lookahead: `reflect/SKILL.md:56` and `automate-me/SKILL.md:11,67,109`
in scanned paths, plus `setup-pstack/references/resolve-effort.md:5` which is exempt.
That is a two-file cleanup, not a redesign.

## Q3 — Does the new architecture doc restate schema that lives in schemas/?

No. It names owners, not fields: `schemas/portability/` appears as a layer owner
(`harness-neutral-authority-2026-10-21.md:9-15`), with no field list, enum or JSON shape
restated from `profile.schema.json`, `package-descriptor.schema.json` or
`host-id.schema.json`.

What it does duplicate is descriptor and profile *facts*, without the pin its sibling
doc gets:

- `:20` restates `pstack.package.json#host_targets` as a prose list — matches today
  (`['grok','codex','omp','opencode','antigravity','droid']`), duplicates the owner.
- `:20` restates `profiles/droid.json#support_state` ("Droid is a candidate") — matches.
- `:26` restates the `-grokbuild.0` version suffix — matches (`0.15.29-grokbuild.0`).
- `:3` pins its own target at BASE `ef34052…`, not the HEAD that ships it — a normative
  doc that is stale by construction, and nothing checks it.

Duplicate owner: `pstack.package.json` + `profiles/*.json` for the facts,
`tests/test_architecture_documentation.py` for the checking obligation. That test pins
the *other* doc only — `test_host_support_table_reflects_actual_profiles` (:40) parses
the host table out of `harness-adapters-and-jev-2026-10-20.md`,
`test_current_schema_inventory_matches_documented_schema_names` (:28) parses schema names
out of the same file, `test_upstream_source_of_truth_matches_package_pin` (:57) pins
version/`upstream_pin` in the same file. The new entry-point doc is asserted for exactly
four literal strings in `test_localized_readmes_agree_on_portable_authority_and_host_scope`,
none of them the enumerations above. And `run_scan` never scans `docs/`
(`target_dirs = [skills, schemas, agents, droids]`), so a routing directive in either
architecture doc is unpoliced by the boundary seam.

## Q4 — Is the reflect SKILL.md change a deletion or dead weight?

Dead weight, and the capability loss is not real. Two revisions did it: `#710`
(`6611f28`) moved the Grok recipe out and dropped the Cursor branch *and* the digest
fallback; `#712` (`8465b09`) restored the fallback in one line. The diff I review is the
net of both.

Consumer search for the deleted text (Grok sessions path, Cursor `agent-transcripts/`,
`GROK_SESSION_ID`, the three Cursor layouts flat/nested/subagent):

- `cursor` is not a declared identity at all: `scripts/host_identity.py` has
  `BUILTIN_HOSTS = ("grok","codex","omp","opencode","antigravity","droid")` and
  `LEGACY_HOST_ALIASES = ("claude","custom")`. No `profiles/cursor.json`, no
  `cursor-tools.md`. So the Cursor paragraph was documentation for a host this package
  does not claim.
- The Cursor layout knowledge had no in-repo consumer: `grep -rn jsonl` under `skills/`
  returns only the new `grok-transcript.md` plus unrelated Grok sandbox notes
  (`how/SKILL.md:64`, `principle-prove-it-works/SKILL.md:18`).
- `grep -rn GROK_SESSION_ID` returns only the new reference file and
  `tests/test_refresh_hygiene.py`, which uses the literal as fixture text for its
  symlink/refresh harness — not as a contract on `reflect/SKILL.md` content.
- The fallback the deletion could have broken is intact: `reflect/SKILL.md:23` ends
  "pass a tight digest of the session instead", and all three reviewer templates carry
  the slot — `judgment-reviewer.md:7,38`, `divergent-reviewer.md:9,39`,
  `tooling-reviewer.md:21,51` ("Read the active transcript at <ABSOLUTE_PATH> (or use the
  digest below if no path is given)" / `<DIGEST IF FILE PATH UNAVAILABLE>`).

Net maintained obligation removed: the repo no longer maintains a transcript-path
catalogue for a host it does not ship.

Residual inconsistency the deletion exposes but does not cause: six other shared skills
still route readers to Cursor `agent-transcripts/` — `automate-me/SKILL.md:29`,
`show-me-your-work/SKILL.md:57`, `recall/SKILL.md:15`,
`poteto-mode/playbooks/eval.md:22`, `poteto-mode/playbooks/session-pickup.md:5`,
`poteto-mode/playbooks/orchestrate.md:17`, and `poteto-help/SKILL.md:46` still says
"pstack is built for Cursor". Not introduced here, but now reflect is the only member of
that family without the stale line, so the drifted set is inconsistent in the opposite
direction.

## Q5 — 1000-line files, ad-hoc conditionals, thin wrappers

- No file in the diff crosses 1000 lines; largest is `docs/verification-test-tiers.md` at
  350 and none of the four skills exceeds 199.
- The diff is four one-line prose edits plus two small new files (9 and 37 lines). No new
  branch, flag, mode, or control flow anywhere.
- `skills/reflect/references/grok-transcript.md` is an extraction, not a wrapper: it sits
  in the one path class `skills/*/references/**` that the boundary scanner exempts, so it
  is the sanctioned home for a host fact.
- Pre-existing, out of diff, but worth naming because it is the enforcement seam this
  train leans on: `scripts/scan-host-boundary.py` keeps the reviewed carve-out twice —
  `QUOTED_PROHIBITION_CARVE_OUTS` lists `("skills/poteto-mode/SKILL.md", 129,
  "~/.grok/installed-plugins")` and `_is_carved_prohibition` re-derives the same tuple and
  the expected sentence literal, raising `ValueError` if either drifts. Two copies of one
  exception, keyed to a line number. A line-number-keyed exemption is the least durable
  shape available; matching the sentence alone would remove the tuple.

## Proposed remediation sequence

1. `reflect/SKILL.md:56-58` → `../poteto-mode/playbooks/authoring-a-skill.md`, matching
   `poteto-mode/SKILL.md:29`; same edit in `automate-me/SKILL.md:11,67,109`.
2. Delete the possessive lookahead in `is_host_routing_directive` and fix the two files
   it then flags. This converts a hand-maintained denylist of five strings on one file
   into the existing general rule, and the denylist in
   `test_portable_router_selects_the_active_host_not_grok` can go.
3. `reflect/SKILL.md:23` → name the pattern, not the file:
   `references/<host>-transcript.md` in this skill's own directory, plus "present for Grok".
4. Move Antigravity's tier binding into `profiles/antigravity.json` (or
   `antigravity-tools.md`), then delete the host enumeration in `setup-pstack/SKILL.md:12`
   and let the `:8` rule be true.
5. Extend `tests/test_architecture_documentation.py` to parametrize
   `harness-neutral-authority-2026-10-21.md` for the enumerations at `:20` and `:26`, or
   delete those enumerations and read the descriptor. Drop the `:3` BASE-revision claim or
   make it a checked reference.

## Recheck

- `pytest tests/test_scan_host_boundary.py tests/test_verify_harness_playbooks.py tests/test_architecture_documentation.py tests/test_refresh_hygiene.py`
- `.venv/bin/python scripts/scan-host-boundary.py -v` (expect it to fail on
  `automate-me`/`reflect` until step 1 lands, which is the point of step 2)
- `grep -rn "models.json" profiles/ skills/poteto-mode/references/` after step 4
