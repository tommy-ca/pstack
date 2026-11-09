# ADR: Pi PStack is an opt-in skills package; external extensions keep native authority

- Status: Proposed package distribution; committed runtime-proof safety fix.
- Date: 2026-11-07
- Prior art: closed Pi candidate epic #894, merged #901 and #903, existing `pstack:pi` candidate profile.
- Follow-on: #973 → #974/#976 → #975/#977 → #978.

## Decisions
1. **Skills-and-role-definition package, no executable extensions.** A future opt-in native Pi package may export `pi.skills: ["./skills"]` and **`pi.subagents.agents: ["./agents"]`** (confirmed in [pi-subagents v0.86.0](https://github.com/nicobailon/pi-subagents/blob/v0.86.0/docs/agents.md)). Leave `pi.extensions` absent; do not vendor a delegate/sandbox/permission engine. Package metadata and installation remain gated by native discovery proof (#975). Checkout `.pi/settings.json` is already functional as a source declaration, but is not evidence of an installed package.
2. **One canonical role tree with explicit Pi semantic mapping.** Package `pi.subagents.agents` can make PStack's 22 canonical `agents/*.md` *discoverable* without copying them. It does **not** make their foreign frontmatter equivalent: PStack `effort` is not Pi-subagents' `thinking`, `capabilityMode` is not a strict Pi `tools` allowlist, and fresh children do not automatically receive the full Pi base prompt/skill catalog. Use documented `agentOverrides.<name>.thinking/tools/inheritSkills` or source-generated host-local projection only if required by measured behavioral tests; no duplicate handwritten role forest. An independent verifier without a real tool allowlist/sandbox is advisory, **not hard read-only**.
3. **Tier capabilities, not packages by fiat.** Native Pi tools/MCP/sessions support sequential PStack with zero third-party extensions; PStack child workflows require exactly one `pi-subagents` delegate engine. Add `pi-ask-user` only for structured human.ask; add enabled `pi-better-sandbox` and `pi-verdict` for separately verified guarded workflows; add `pi-web-access` only for research. Existing four-engineering manifest describes the guarded interactive candidate, NOT the minimum runtime or an enforced human.gate. Keep all third-party installs separate and explicit.
4. **No runtime PASS from preflight.** A healthy `pi --version` / `pi list` / `pi -p --no-session --no-tools` can establish process/package availability, never live `agent.spawn`, child permission, role/model identity, cleanup, or OS sandbox. The Pi runtime plane remains BLOCKED until an actual child driver produces effect-bound evidence.
5. **No cleanup PASS without tracking.** The existing shell driver cannot prove child/worktree cleanup; return BLOCKED/NOT_VERIFIED until the actor driver tracks resources and confirms their absence.
6. **Separate bounded source mutation from formal proof.** The 53 fixed invalid variants are good negative source controls. A claimed formal runtime invariant requires code-linked checker/model, bounds, broken-variant detection and actual checker receipt.
7. **Candidate release upgrade requires independent test.** Pi-subagents v0.87.0's provider-qualified matching, drain and session fixes warrant a compatibility test, not a silent change to the pinned 0.86.0 version. Record releases as *observed*, not installed.

## Rejected
- Bundling Pi extensions directly into a PStack provider/runtime package: large trust surface, source/runtime authority conflation.
- Keeping both `@zenspc/pi-pstack` and native skills as independent policies: semantic forks and priority collisions.
- Adding `pi-goal`, `pi-dynamic-workflows`, `pi-permission-modes`, second subagent engine or model router by default: overlapping ownership.
- Treating pi-verdict classifier `allow`, `ask_user`, worktree isolation, or installed-but-disabled sandbox as a hard `human.gate`: unsafe false authority.
- Counting Pi preflight/synthetic actors as runtime success or a source-bound mutation test as formal model-checker proof.

## Backward compatibility and safety
No auto-package installs, edits to the user's Pi config, change to six existing shipped adapters, or source-pinned role policy. A future native Pi package manifest must be reviewed against supported Pi v1.5 native syntax, collisions and actual installed project behavior, and shipped as a separate dependency-gated PR. Restore verified previous PStack projection on rollback, never corrupt the user's settings.
