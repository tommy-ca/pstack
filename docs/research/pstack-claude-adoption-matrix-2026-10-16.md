# Fork adoption matrix (issue #434)

Source: `michael-denyer/pstack-claude@94f5ce95abe8a9dec976967d79941f631cf477cd`, `tools/forks.json`.
Canonical: `cursor/plugins/pstack` at `UPSTREAM` pin `1dcc2bacde73ddd284803b7af28164d0436198fc`.
Local: trunk `90d9feb`.
Status: lane-level triage from pin-relative inspection. `diverged` means counterparts exist on both sides without line-by-line verification. Full per-file diff review remains open.

## skill-policy (19 rows)

| Ledger path | Canonical | Local | Proposed |
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

## code-contract (17 rows)

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

## playbook-policy (12 rows)

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

## Counts

adapt 38, preserve 3, exclude 2, gap 3, policy-fork 2. Total 48.

## Not done

Per-file line diffs, license/NOTICE disposition, source-to-test evidence. The ledger JSON `review_state`/`proposed_adoption` fields are unchanged by this matrix; promoting this triage into the ledger is a separate reviewed step.
