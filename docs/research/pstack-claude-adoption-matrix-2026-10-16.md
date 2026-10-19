# Fork adoption matrix (issue #434)

Source: comparator `michael-denyer/pstack-claude@94f5ce95abe8a9dec976967d79941f631cf477cd`, `tools/forks.json`.
Canonical authority: `cursor/plugins/pstack@1dcc2bacde73ddd284803b7af28164d0436198fc`.
Target source pin: `pstack@3f4cd124f27cab90865df79d18d376e2f4335b2c`. Later merged main `722deb048a809004253a44a9130dfad5f4153591` changes only specification, task-plan, and cache-evidence files outside these pinned counterparts.
Review status: source review covers 36/48 comparator paths against pinned canonical and target counterparts. Remaining rows retain lane-triaged status. Findings are not implementation, runtime or independent acceptance; issue #434 remains open.

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

Current source-reviewed disposition counts (36/48 rows): adapt 25, preserve 1, exclude 2, gap 7, policy-fork 1.

## License disposition (2026-10-16, corrected)

Comparator `michael-denyer/pstack-claude@94f5ce95abe8a9dec976967d79941f631cf477cd` carries `LICENSE` (MIT), a team-kit license file, `LICENSE-thermos`, root `NOTICE.md` and `NOTICE-skills.md`, plus `plugins/pstack/skills/poteto-mode/references/licenses/NOTICE.md`. Its NOTICE attributes pstack-derived skills to cursor/plugins/pstack (Lauren Tan, MIT), team-kit skills to the Cursor team-kit source (Cursor, MIT), and thermos skills to cursor/plugins/thermos (Cursor, MIT), with port modifications under Michael Denyer MIT. Local `LICENSE` is MIT with no NOTICE file.

## Per-file review status

File-level source review covers 36/48 comparator paths. The ledger records exact counterpart blobs, semantic rationale, attribution and NOTICE implications, plus a check or explicit gap for each reviewed row. Remaining rows retain lane-level triage. This is not implementation, approval, runtime evidence, or independent acceptance. Issue #434 remains open.



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
| `plugins/pstack/skills/poteto-mode/scripts/bootstrap.ts` | gap | plugins/pstack/skills/poteto-mode/scripts/bootstrap.ts @ `ea4d5c491b1c4fa48b7b47a38d1386db92665a90` | pstack/skills/poteto-mode/scripts/bootstrap.ts @ `d9c63e2007449a80000abe75ecaf7f2a0bd5826b` (present) | skills/poteto-mode/scripts/bootstrap.ts @ `d9c63e2007449a80000abe75ecaf7f2a0bd5826b` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/check-plan.mjs` | preserve | plugins/pstack/skills/poteto-mode/scripts/check-plan.mjs @ `27dae333978389c2b17f888104d0a1878fd1170e` | pstack/skills/poteto-mode/scripts/check-plan.mjs @ `c8626766cee4cc4a2736fe438a1aea5c1f1b28ce` (present) | skills/poteto-mode/scripts/check-plan.mjs @ `66f5fcae04dbb3abeb08b841a92e6f47ec188568` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/check-plan.test.ts` | exclude | plugins/pstack/skills/poteto-mode/scripts/check-plan.test.ts @ `59169bcd5e8081f4c3c28489ef73962ad2fcbc15` | pstack/skills/poteto-mode/scripts/check-plan.test.ts @ `fd966c2b5fb6e99c12070c553906765c7bd900d8` (present) | skills/poteto-mode/scripts/check-plan.test.ts @ `—` (absent) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/orch/orch.test.ts` | adapt | plugins/pstack/skills/poteto-mode/scripts/orch/orch.test.ts @ `2b476c33d4e0db046626b50549b7da6a97d0ee0d` | pstack/skills/poteto-mode/scripts/orch/orch.test.ts @ `538775e37f3ac6fd2dd128883b7f7fe51c1316d5` (present) | skills/poteto-mode/scripts/orch/orch.test.ts @ `9c234de724991083b4644e906a5f1358f8ef8dcc` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/orch/store.ts` | gap | plugins/pstack/skills/poteto-mode/scripts/orch/store.ts @ `439c85331b3eb9da89608e572038a27f8c0acfa0` | pstack/skills/poteto-mode/scripts/orch/store.ts @ `5e6c602fb670a6b5598977f5bf85d717cf797ef7` (present) | skills/poteto-mode/scripts/orch/store.ts @ `5e6c602fb670a6b5598977f5bf85d717cf797ef7` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/package.json` | adapt | plugins/pstack/skills/poteto-mode/scripts/package.json @ `00eb74ed1faae3e05f6ab1d6d4d3bfbec54f56a8` | pstack/skills/poteto-mode/scripts/package.json @ `d8abe49ad0eafd10d302e8c6a9a0a95c5e6fb0ef` (present) | skills/poteto-mode/scripts/package.json @ `1e9a3281b5e204d5c18c469241ec3ebdbd469ef1` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/cli.test.ts` | adapt | plugins/pstack/skills/poteto-mode/scripts/watch-pr/cli.test.ts @ `e7654c617f66b9e29fde296d95ee9219849c9791` | pstack/skills/poteto-mode/scripts/watch-pr/cli.test.ts @ `0656b413e6c180858ca42981105944c45caf9dca` (present) | skills/poteto-mode/scripts/watch-pr/cli.test.ts @ `0656b413e6c180858ca42981105944c45caf9dca` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/cli.ts` | gap | plugins/pstack/skills/poteto-mode/scripts/watch-pr/cli.ts @ `3b937f12b88e9a27fb082d30e44ab77366e8e7c9` | pstack/skills/poteto-mode/scripts/watch-pr/cli.ts @ `ec8a2f27c5ac24866b699e6395e7d1f32e595068` (present) | skills/poteto-mode/scripts/watch-pr/cli.ts @ `ec8a2f27c5ac24866b699e6395e7d1f32e595068` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/fakes.test-helper.ts` | adapt | plugins/pstack/skills/poteto-mode/scripts/watch-pr/fakes.test-helper.ts @ `97e60e09b2d882d4bc008efecaaea9698f5f1d03` | pstack/skills/poteto-mode/scripts/watch-pr/fakes.test-helper.ts @ `84ccf596b01e03e7fb77e73ea82ec3b1738026ad` (present) | skills/poteto-mode/scripts/watch-pr/fakes.test-helper.ts @ `84ccf596b01e03e7fb77e73ea82ec3b1738026ad` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/github.test.ts` | adapt | plugins/pstack/skills/poteto-mode/scripts/watch-pr/github.test.ts @ `2bb7ac1cb8120e77b65b0aa06561654c4cc83598` | pstack/skills/poteto-mode/scripts/watch-pr/github.test.ts @ `4ef39d2a1d2981e205e948b1707f7db96b750280` (present) | skills/poteto-mode/scripts/watch-pr/github.test.ts @ `47750b3605d2097c71c826ef1d20a0f9a086f571` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/github.ts` | gap | plugins/pstack/skills/poteto-mode/scripts/watch-pr/github.ts @ `d5129fb06d14b3ee5b06e48517414407554d1ee4` | pstack/skills/poteto-mode/scripts/watch-pr/github.ts @ `cfc3764a03d35fd5ed6c79818b076329bcd08437` (present) | skills/poteto-mode/scripts/watch-pr/github.ts @ `3c5645b6cf6a3bcc9fd5cf622818fcb2493c9372` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/policy.test.ts` | adapt | plugins/pstack/skills/poteto-mode/scripts/watch-pr/policy.test.ts @ `96c15db1877961af63b413d93c8d3d8d2a068151` | pstack/skills/poteto-mode/scripts/watch-pr/policy.test.ts @ `6dae16da71800fb06eb37a7e3b296a8d27275b08` (present) | skills/poteto-mode/scripts/watch-pr/policy.test.ts @ `6dae16da71800fb06eb37a7e3b296a8d27275b08` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/policy.ts` | gap | plugins/pstack/skills/poteto-mode/scripts/watch-pr/policy.ts @ `fcc774060f9d0efa9d2352f8aa6f84fa0c30395a` | pstack/skills/poteto-mode/scripts/watch-pr/policy.ts @ `cabadb9bf96f4d8c4c0426d77d0cbdab80fbe3e5` (present) | skills/poteto-mode/scripts/watch-pr/policy.ts @ `cabadb9bf96f4d8c4c0426d77d0cbdab80fbe3e5` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/render.ts` | gap | plugins/pstack/skills/poteto-mode/scripts/watch-pr/render.ts @ `48e5750f887f370dfbd2a210dfa07e996100be89` | pstack/skills/poteto-mode/scripts/watch-pr/render.ts @ `0e935839357335f24ab1bbc193d761495646ea99` (present) | skills/poteto-mode/scripts/watch-pr/render.ts @ `0e935839357335f24ab1bbc193d761495646ea99` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/types.compile.ts` | adapt | plugins/pstack/skills/poteto-mode/scripts/watch-pr/types.compile.ts @ `3509160c7881c5a6348c01081a33c4a1cfd9267e` | pstack/skills/poteto-mode/scripts/watch-pr/types.compile.ts @ `1b53279c7f3e5da55703ed17d6ad0616254c5751` (present) | skills/poteto-mode/scripts/watch-pr/types.compile.ts @ `1b53279c7f3e5da55703ed17d6ad0616254c5751` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/scripts/watch-pr/types.ts` | gap | plugins/pstack/skills/poteto-mode/scripts/watch-pr/types.ts @ `d708d5fc0628e0fcdc47a3e88485fe60cc4c2dc5` | pstack/skills/poteto-mode/scripts/watch-pr/types.ts @ `6c94e0a687f8e48f91acffd21f725320dd66e659` (present) | skills/poteto-mode/scripts/watch-pr/types.ts @ `66ffa51e12f352cbe7b8e515caa7e288ed124da2` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/poteto-mode/SKILL.md` | adapt | plugins/pstack/skills/poteto-mode/SKILL.md @ `5278f9de3fd9f9c4ca212746007f5ccb2de77a2e` | pstack/skills/poteto-mode/SKILL.md @ `d5be8a10b745f3676805cb6858b51ab758412069` (present) | skills/poteto-mode/SKILL.md @ `d9dc2c5a5ea822cec1c767ab05d8a0639ea0018a` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/principle-attack-the-premise/SKILL.md` | adapt | plugins/pstack/skills/principle-attack-the-premise/SKILL.md @ `78ca084cf711365494195e7112d47b73ad14cbfe` | pstack/skills/principle-attack-the-premise/SKILL.md @ `f9785ff9fdcf37d1c689e4468da7d611f3b76d4b` (present) | skills/principle-attack-the-premise/SKILL.md @ `f9785ff9fdcf37d1c689e4468da7d611f3b76d4b` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/principle-prove-it-works/SKILL.md` | adapt | plugins/pstack/skills/principle-prove-it-works/SKILL.md @ `3ba219579fc3febfc1a9d32bcd8d937d15d89050` | pstack/skills/principle-prove-it-works/SKILL.md @ `5dc14a3b06f9d579e5c17cd8a7242f432ddb3125` (present) | skills/principle-prove-it-works/SKILL.md @ `7031db24ade7bc65e6679e785d84e46d06ca1887` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/principle-test-behavior-not-implementation/SKILL.md` | adapt | plugins/pstack/skills/principle-test-behavior-not-implementation/SKILL.md @ `23f1fb510764b6b4b08fe9600d67b095a68de4f1` | pstack/skills/principle-test-behavior-not-implementation/SKILL.md @ `f5a603e3a0925cdc6363bcc26dfbf587d9a36ec7` (present) | skills/principle-test-behavior-not-implementation/SKILL.md @ `dd828aa6c15965f64b218683e84bba714d15b5cc` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/recall/SKILL.md` | adapt | plugins/pstack/skills/recall/SKILL.md @ `c8084cdbf4fe3a7d05eea7330d499e3c57e9358b` | pstack/skills/recall/SKILL.md @ `a70062a3f89a8d68b3391bc71fc4c6cc2dfcf6a4` (present) | skills/recall/SKILL.md @ `a6dd56b5ac97dc14934c0df99278b0a217ec6046` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/reflect/SKILL.md` | adapt | plugins/pstack/skills/reflect/SKILL.md @ `49bca6f3b38959d77871d36f91eb3b209618328e` | pstack/skills/reflect/SKILL.md @ `b6bd41afdc831741819b72efa60ef2f10947cc8c` (present) | skills/reflect/SKILL.md @ `23dd9add70d016403d48c2da00ffca5b373303f1` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/setup-pstack/SKILL.md` | adapt | plugins/pstack/skills/setup-pstack/SKILL.md @ `6dd8a25ace99193e2e4485c7a1fe39f105a50027` | pstack/skills/setup-pstack/SKILL.md @ `90a9e575397fb59f4d9a47e6157c2106f4b4a5e2` (present) | skills/setup-pstack/SKILL.md @ `e1996351d657cf25e69ef705e6b9ca0621ba20c8` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/show-me-your-work/scripts/log.sh` | adapt | plugins/pstack/skills/show-me-your-work/scripts/log.sh @ `004ec8d18fc3a141fd753346c65e6fe9babc4775` | pstack/skills/show-me-your-work/scripts/log.sh @ `052e53b7e1090579eaec1d3d59f7a1cd2f2e452a` (present) | skills/show-me-your-work/scripts/log.sh @ `052e53b7e1090579eaec1d3d59f7a1cd2f2e452a` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/show-me-your-work/SKILL.md` | adapt | plugins/pstack/skills/show-me-your-work/SKILL.md @ `9adafb6c48a185db178e343b1653470e78e11790` | pstack/skills/show-me-your-work/SKILL.md @ `d350a150c36ca16382b4aa6d4196b39e67454ad1` (present) | skills/show-me-your-work/SKILL.md @ `d350a150c36ca16382b4aa6d4196b39e67454ad1` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/tdd/SKILL.md` | adapt | plugins/pstack/skills/tdd/SKILL.md @ `67d91899a44c094d999eda716fa9877de245e109` | pstack/skills/tdd/SKILL.md @ `ca6f24c963001d9d518db2936dfe3d12f29b4e94` (present) | skills/tdd/SKILL.md @ `9b70811f0ecad51b2d6e977ee5e799a836aac05e` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/why/references/epistemics.md` | adapt | plugins/pstack/skills/why/references/epistemics.md @ `e483ab1af872548dc69835ddb787101c5eaf310f` | pstack/skills/why/references/epistemics.md @ `b18abf41dfa245ee55e94f1b3a80c0b750eb10cf` (present) | skills/why/references/epistemics.md @ `b18abf41dfa245ee55e94f1b3a80c0b750eb10cf` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/why/references/investigator-prompt.md` | adapt | plugins/pstack/skills/why/references/investigator-prompt.md @ `3f5cbce2389bf8d23ba8a577ace2a21afc1d4172` | pstack/skills/why/references/investigator-prompt.md @ `e1c2bbf52197ff600ba6e4552439e630687b7ae2` (present) | skills/why/references/investigator-prompt.md @ `e1c2bbf52197ff600ba6e4552439e630687b7ae2` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/why/references/synthesizer-prompt.md` | adapt | plugins/pstack/skills/why/references/synthesizer-prompt.md @ `0ad6ef7c7dfb07a00a227468167303cf74d9e006` | pstack/skills/why/references/synthesizer-prompt.md @ `287a350c925c28b44f0e0dc687bb09a843e11100` (present) | skills/why/references/synthesizer-prompt.md @ `287a350c925c28b44f0e0dc687bb09a843e11100` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |
| `plugins/pstack/skills/thermo-nuclear-code-quality-review/SKILL.md` | policy-fork | plugins/pstack/skills/thermo-nuclear-code-quality-review/SKILL.md @ `4d9176be4ac90728c24eb9b29125f45d8d8aecd1` | thermos/skills/thermo-nuclear-code-quality-review/SKILL.md @ `ac76a2bc88bb2d895e83ab1788aa584a82346cfc` (present) | skills/thermo-nuclear-code-quality-review/SKILL.md @ `8c1437ede7765c1b410653f3913ef6b757d11ee8` (present) | Ledger `entries[].source_review` and the shared `source_review_contract` attribution profile |

## Attribution and notices

The comparator carries MIT licensing and NOTICE files: pstack-derived provenance is attributed to Lauren Tan, with comparator modifications by Michael Denyer; the thermos row is attributed to Cursor under `LICENSE-thermos`, not pstack. Per-file notice/source distinctions are recorded for reviewed rows. The target has an MIT `LICENSE` and no `NOTICE`. Attribution findings do not establish verbatim target copying or authorize imports.