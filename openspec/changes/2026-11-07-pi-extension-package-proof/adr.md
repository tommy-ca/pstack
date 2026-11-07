# ADR: Pi PStack is an opt-in skills package; external extensions keep native authority

- Status: Proposed package distribution; committed runtime-proof safety fix.
- Date: 2026-11-07
- Prior art: closed Pi candidate epic #894, merged #901 and #903, existing `pstack:pi` candidate profile.
- Follow-on: #973 → #974/#976 → #975/#977 → #978.

## Decisions
1. **Skills-only package.** Prefer native Pi `package.json#pi.skills` to project canonical `./skills` for opt-in distribution; leave `pi.extensions` absent. Do not vendor `pi-subagents`, `pi-verdict`, `pi-better-sandbox` or another executor into PStack. Add actual package metadata only after live Pi package-discovery proof (issue #975); source-only `.pi/settings.json` remains the safe developer-checkout mode.
2. **Role definitions are not necessarily skills.** Pi recognizes packages' explicit resource manifest. `pi-subagents` may require configured `agentScanDirs`. A loaded PStack skill does not prove `agents/*.md` resolution. Test a package-installed project separately from checkout `../agents` discovery; do not silently introduce a generic wrapper extension to compensate.
3. **Exactly one owner per capability.** Pi native tools/MCP/sessions first, one `pi-subagents` delegate engine, one configured sandbox owner, one `pi-verdict` adjudicator and one `pi-ask-user` structured selection. Optional `pi-web-access` only when research requires it. Keep installed third-party extensions out of project settings by default until reviewed, versioned and explicitly opted in.
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
