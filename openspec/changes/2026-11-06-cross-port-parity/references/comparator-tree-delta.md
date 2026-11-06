# Source inventory: pstack-claude 0.9.95 baseline to November 5, 2026

Status: **complete tree-path inventory**, **partial semantic-hunk classification**, no executable test or model-backed review result.

## Provenance and procedure

- Base: michael-denyer/pstack-claude@88f6d39f228c4f9210d93bbf7e5e40a5c671fd5e (old target comparator, 0.9.95).
- Head: michael-denyer/pstack-claude@d88063f3355a5ecff0e6dbb890a11bab4b08bc2e (2026-11-05).
- GitHub commit compare reports 86 commits and exposes only a **first 300-file list**, which is not complete.
- To recover all **tree-level paths**, fetch GitHub REST /repos/michael-denyer/pstack-claude/git/trees/<base-or-head>?recursive=1 for each revision. Both responses reported truncated=false. Filter type=blob, index by path, compare blob sha and mode; added/deleted paths come from set differences. These are full snapshot path-level changes, **not** rename detection or per-commit/semantic-hunk review.

## Reproducible observed counts

| Metric | Count |
| --- | ---: |
| Base file blobs | 363 |
| Head file blobs | 776 |
| Added paths | 464 |
| Deleted paths | 51 |
| Modified paths (blob SHA or mode changed) | 134 |
| Total changed paths | 649 |
| Added under plugins/pstack/skills/statechart | 410 |
| Other added under plugins/pstack/skills | 11 |

Most added paths are in the statechart compiler distribution. Raw path counts vastly overstate the number of reusable semantic capabilities.

## High-signal changed families and proposed semantic decisions

| Source paths/family | Observation | Preliminary decision | Target owner / verification |
| --- | --- | --- | --- |
| plugins/pstack/skills/statechart/** (410 new paths) | Very large optional compiler/tool distribution | **Exclude full vendoring** until pinned optional qualification: structural cost/host binaries/licenses | Existing #847 statechart qualification; maintain GAP without proven host installation |
| plugins/pstack/skills/poteto-mode/playbooks/orchestrate.md | Agentic Orchestrate evolves; old script store removed | **Preserve canonical agentic intent** and host-local state | Canonical #840 work completed; require new negative behavior to reopen |
| plugins/pstack/skills/poteto-mode/scripts/orch/{orch.ts,store.ts,orch.test.ts} and tla/OrchStoreLock.* | Removed legacy process/store control plane and associated lock model | **Do not resurrect** a second orchestration store or old proof | Existing role/playbook/driver contract |
| plugins/pstack/pi/{agents,agent-tools,config,schedule,slash,path-skills,...} | Pi-specific child/skill/scheduler process mechanics changed | **Extract postconditions only**; do not transplant Pi child manager | pstack:pi candidate; #908 and #909 |
| tests/pi/{agent-defaults,agent-tools-off,agents-launch,agents-run,slash,...} | More lifecycle and configuration test coverage | **Candidate host-local negative fixtures** | Existing verify_pi_candidate.py / native test driver |
| plugins/pstack/hooks and added Grok/Kimi/Muse/OMP/OpenCode projections | Additional port-local host install/start mechanics | **Host-only** unless target independently declares native support | Current six profiles/packaging; no implicit host enrollment |
| plugins/pstack/.codex-plugin/prompts/* (41 removals) | Generated/wrapper prompt packaging changed | **Evaluate but do not mirror deletion** | Target Codex adapter and skill precedence tests |
| plugins/pstack/skills/interrogate/SKILL.md and deleted reviewer references | Review prompt structure changed | **Classify semantic contract before copying** | Canonical Interrogate and exact model-family evidence |
| tools/{forks,sync,upstream,substitutions}.json/mjs | Reference port declares policy forks and transformed source synchronization | **Adopt classification discipline**, not its generator/runtime | Existing scripts/sync_from_upstream.py and OpenSpec |
| lean/Model/WatchPoll.* (modified) | Reference-specific formal mutation checks changed | **Source-only modeling inspiration** | No transfer of proof; source-code mapping required |

These are **preliminary decisions** at family level. Source-file-by-source-file postconditions, license/NOTICE validation, target negative fixtures, exact-head tests and independent reviews are still #907/#908/#909/#911 work.

## Cross-source decision constraints

1. Canonical Cursor pstack@c742dd6 is normative even when the comparator differs.
2. A source path or generated bundle has zero target runtime authority unless current target host profile and native tool execution prove it.
3. Preserve source-derived safety/liveness *invariants* but map code atom boundaries, fairness and process identities to the target.
4. Never create parallel role registries, PStack-QStack callbacks, timers, process supervisors, or receipt stores from reference material.
5. Keep prior completed #429/#840/#894 history immutable; this inventory is additive.
