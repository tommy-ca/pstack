# Fork adoption matrix (issue #434)

Source: comparator `michael-denyer/pstack-claude@94f5ce95abe8a9dec976967d79941f631cf477cd`, `tools/forks.json`.
Canonical authority: `cursor/plugins/pstack@1dcc2bacde73ddd284803b7af28164d0436198fc`.
Target source pin: `pstack@3f4cd124f27cab90865df79d18d376e2f4335b2c`. Later merged main `722deb048a809004253a44a9130dfad5f4153591` changes only specification, task-plan, and cache-evidence files outside these pinned counterparts.
Review status: source review covers 10/48 comparator paths against pinned canonical and target counterparts. Remaining rows retain lane-triaged status. Findings are not implementation, runtime or independent acceptance; issue #434 remains open.

The lane tables preserve original 2026-10-16 triage labels for history. For rows source-reviewed so far, the per-file pinned evidence table and ledger fields supersede those provisional labels; remaining rows retain lane-level labels. A disposition never authorizes importing comparator code.

## Original lane triage: skill-policy (19 rows)

| Ledger path | Canonical | Local | Initial triage |
| --- | --- | --- | --- |
| plugins/pstack/skills/architect/references/rationale-template.md | present | present, diverged | adapt |
| plugins/pstack/skills/architect/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/blast-radius/SKILL.md | present | absent | gap |
| plugins/pstack/skills/bro/SKILL.md | absent | absent | exclude |
| plugins/pstack/skills/create-verification-skill/SKILL.md | present | absent | gap |
| plugins/pstack/skills/poteto-help/SKILL.md | present | references only, no SKILL.md | gap |
| plugins/pstack/skills/poteto-mode/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/principle-attack-the-premise/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/principle-prove-it-works/SKILL.md | absent | present | preserve |
| plugins/pstack/skills/principle-test-behavior-not-implementation/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/recall/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/reflect/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/setup-pstack/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/show-me-your-work/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/tdd/SKILL.md | present | present, diverged | adapt |
| plugins/pstack/skills/why/references/epistemics.md | present | present, diverged | adapt |
| plugins/pstack/skills/why/references/investigator-prompt.md | present | present, diverged | adapt |
| plugins/pstack/skills/why/references/synthesizer-prompt.md | present | present, diverged | adapt |
| plugins/pstack/skills/thermo-nuclear-code-quality-review/SKILL.md | absent (thermos group, out of pstack scope) | present | policy-fork |

## Original lane triage: code-contract (17 rows)

| Ledger path | Canonical | Local | Proposed |
| --- | --- | --- | --- |
| plugins/pstack/skills/poteto-mode/scripts/bootstrap.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/check-plan.mjs | present | present | preserve |
| plugins/pstack/skills/poteto-mode/scripts/check-plan.test.ts | present | excluded by sync policy | exclude |
| plugins/pstack/skills/poteto-mode/scripts/orch/orch.test.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/orch/store.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/package.json | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/cli.test.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/cli.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/fakes.test-helper.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/github.test.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/github.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/policy.test.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/policy.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/render.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/types.compile.ts | present | present | adapt |
| plugins/pstack/skills/poteto-mode/scripts/watch-pr/types.ts | present | present | adapt |
| plugins/pstack/skills/show-me-your-work/scripts/log.sh | present | present | preserve |

## Original lane triage: playbook-policy (12 rows)

| Ledger path | Canonical | Local | Proposed |
| --- | --- | --- | --- |
| plugins/pstack/skills/poteto-mode/playbooks/autopilot-full.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/autopilot-stack.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/babysit.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/bug-fix.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/feature.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/opening-a-pr.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/orchestrate.md | present | present, diverged | policy-fork |
| plugins/pstack/skills/poteto-mode/playbooks/pause-safely.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/session-pickup.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/shipping.md | present | present, diverged | adapt |
| plugins/pstack/skills/poteto-mode/playbooks/worktree-cleanup.md | present | present, diverged | adapt |

## Current source-reviewed dispositions

Current source-reviewed disposition counts (10/48 rows): adapt 9, exclude 1.

## License disposition (2026-10-16, corrected)

Comparator `michael-denyer/pstack-claude@94f5ce95abe8a9dec976967d79941f631cf477cd` carries `LICENSE` (MIT), a team-kit license file, `LICENSE-thermos`, root `NOTICE.md` and `NOTICE-skills.md`, plus `plugins/pstack/skills/poteto-mode/references/licenses/NOTICE.md`. Its NOTICE attributes pstack-derived skills to cursor/plugins/pstack (Lauren Tan, MIT), team-kit skills to the Cursor team-kit source (Cursor, MIT), and thermos skills to cursor/plugins/thermos (Cursor, MIT), with port modifications under Michael Denyer MIT. Local `LICENSE` is MIT with no NOTICE file.

## Per-file review status

File-level source review covers 10/48 comparator paths. The ledger records exact counterpart blobs, semantic rationale, attribution and NOTICE implications, plus a check or explicit gap for each reviewed row. Remaining rows retain lane-level triage. This is not implementation, approval, runtime evidence, or independent acceptance. Issue #434 remains open.



## Per-file pinned evidence (source review, not acceptance)

The JSON ledger is the detailed record for each source-reviewed row: exact comparator/canonical/target paths, pins and blob hashes; semantic disposition/rationale; attribution and notice implications; and behavior-check or explicit-gap mapping.

| Ledger path | Disposition | Comparator path / blob | Canonical path / blob (status) | Target path / blob (status) | Detailed rationale/check mapping |
| --- | --- | --- | --- | --- | --- |
| `plugins/pstack/skills/architect/references/rationale-template.md` | adapt | plugins/pstack/skills/architect/references/rationale-template.md @ `9ccea423df568bbedeea0c371b9ca6990f1d6b07` | pstack/skills/architect/references/rationale-template.md @ `a10f77f59510c532cd909faaf3bfeee5ffbfd588` (present) | skills/architect/references/rationale-template.md @ `a10f77f59510c532cd909faaf3bfeee5ffbfd588` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/architect/SKILL.md` | adapt | plugins/pstack/skills/architect/SKILL.md @ `9083812759091be7cb94f035d34e2b59228ae321` | pstack/skills/architect/SKILL.md @ `88e23ca105b89e67f4085d0e676c40d4b170a623` (present) | skills/architect/SKILL.md @ `69430fbb75e428e6865a704072edd45294be085d` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/blast-radius/SKILL.md` | adapt | plugins/pstack/skills/blast-radius/SKILL.md @ `8ee5a95c43e710f8b8e3bb975c95b136a844b648` | pstack/skills/blast-radius/SKILL.md @ `b296cce0d746260a53c16e3671cb05bacfe82daf` (present) | skills/blast-radius/SKILL.md @ `1713b283d477530be64e925ede2bdbe5ce2d6e31` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/bro/SKILL.md` | exclude | plugins/pstack/skills/bro/SKILL.md @ `c21e6a4070325a7540f4c1ef4b3b8aac43676138` | pstack/skills/bro/SKILL.md @ `b1701b778639c08bfc306291d70170c525c66a68` (present) | skills/bro/SKILL.md @ `b1701b778639c08bfc306291d70170c525c66a68` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/create-verification-skill/SKILL.md` | adapt | plugins/pstack/skills/create-verification-skill/SKILL.md @ `93ea1bc4d18237bcdbe7c208c60f1c52311d2647` | pstack/skills/create-verification-skill/SKILL.md @ `140d033a001e8d27acd14b06004506c43053b199` (present) | skills/create-verification-skill/SKILL.md @ `3c9424432bf0af82ab33ab4a980baa715dead7c9` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-help/SKILL.md` | adapt | plugins/pstack/skills/poteto-help/SKILL.md @ `94545599432a7ba126357278f06f8e1b99add4fd` | pstack/skills/poteto-help/SKILL.md @ `575d80fbff15d3421e6ef020d3a9cfeb2b0b01f0` (present) | skills/poteto-help/SKILL.md @ `51b9ba201d55e1d5553e608a13f003c0b40ec9a0` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/SKILL.md` | adapt | plugins/pstack/skills/poteto-mode/SKILL.md @ `5278f9de3fd9f9c4ca212746007f5ccb2de77a2e` | pstack/skills/poteto-mode/SKILL.md @ `d5be8a10b745f3676805cb6858b51ab758412069` (present) | skills/poteto-mode/SKILL.md @ `d9dc2c5a5ea822cec1c767ab05d8a0639ea0018a` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/principle-attack-the-premise/SKILL.md` | adapt | plugins/pstack/skills/principle-attack-the-premise/SKILL.md @ `78ca084cf711365494195e7112d47b73ad14cbfe` | pstack/skills/principle-attack-the-premise/SKILL.md @ `f9785ff9fdcf37d1c689e4468da7d611f3b76d4b` (present) | skills/principle-attack-the-premise/SKILL.md @ `f9785ff9fdcf37d1c689e4468da7d611f3b76d4b` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/principle-prove-it-works/SKILL.md` | adapt | plugins/pstack/skills/principle-prove-it-works/SKILL.md @ `3ba219579fc3febfc1a9d32bcd8d937d15d89050` | pstack/skills/principle-prove-it-works/SKILL.md @ `5dc14a3b06f9d579e5c17cd8a7242f432ddb3125` (present) | skills/principle-prove-it-works/SKILL.md @ `7031db24ade7bc65e6679e785d84e46d06ca1887` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/principle-test-behavior-not-implementation/SKILL.md` | adapt | plugins/pstack/skills/principle-test-behavior-not-implementation/SKILL.md @ `23f1fb510764b6b4b08fe9600d67b095a68de4f1` | pstack/skills/principle-test-behavior-not-implementation/SKILL.md @ `f5a603e3a0925cdc6363bcc26dfbf587d9a36ec7` (present) | skills/principle-test-behavior-not-implementation/SKILL.md @ `dd828aa6c15965f64b218683e84bba714d15b5cc` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |

## Attribution and notices

The comparator carries MIT licensing and NOTICE files: pstack-derived provenance is attributed to Lauren Tan, with comparator modifications by Michael Denyer; the thermos row is attributed to Cursor under `LICENSE-thermos`, not pstack. Per-file notice/source distinctions are recorded for reviewed rows. The target has an MIT `LICENSE` and no `NOTICE`. Attribution findings do not establish verbatim target copying or authorize imports.