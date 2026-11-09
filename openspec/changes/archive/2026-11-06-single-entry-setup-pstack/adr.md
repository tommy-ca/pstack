# ADR: one setup skill, conventions not extra reference configuration

- Status: Proposed, reviewed for scope; implementation not executed.
- Date: 2026-11-06
- Source authority: official Cursor PStack applied `UPSTREAM` pin `88d47514`.
- Epic: #948. Existing living spec: `openspec/specs/pstack-setup-overlays/spec.md`.

## Decision
1. Keep `skills/setup-pstack/SKILL.md` as the only user-visible setup skill. Move existing Grok setup instructions and four reference assets under `skills/setup-pstack/references/`; preserve host-native behavior, native questions, safe writes and upstream optional ordinary **and formal** verification offers.
2. A validated `host-cli` profile selects `references/<matched-profile-filename-stem>.md` by **convention**, not an additional `SetupProjection.reference` field or a second skill. Resolve a file only after exact matching of the profile's declared `host`; never interpret user-supplied host strings as a filesystem path. Confine references beneath the setup skill and reject symlinks, nonfiles and out-of-tree targets.
3. Remove the existing `SetupProjection.skill` field in the same implementation wave as updating all readers, package projections and tests. No permanent `skill | reference` compatibility union, no dual router, and no speculative provider SDK. A pre-merge draft had proposed `reference`; deep review rejects it under KISS/YAGNI.
4. `skills/setup-pstack/profiles/` is the editable machine-readable host-profile authority, including setup/capability fields. Root `profiles/` stays a deterministic byte-exact **generated compatibility mirror** until the installed/runtime consumers no longer need it. Keep these profiles out of `poteto-mode/references/`; that directory describes tool consumption.
5. Host-specific setup source modes remain distinct: `host-cli` may perform observed native probes and bounded writes; `host-catalog` describes projected host files, not a runtime write; `inherit` omits per-role model override; `none`/no block declare a gap or block. Candidate hosts cannot assert a live `host-cli` capability.
6. Existing role registry, model precedence resolver, optional verification authoring skills, and portability conformance schemas are reused verbatim as policy authorities. The setup skill will not gain any scheduler, executor, agent lifecycle or QStack reverse dependency.

## Alternatives
- **Add `SetupProjection.reference`**: REJECT — duplicates a reference filename deterministically derivable from a validated profile file and needs another schema field, ambiguity rule and reader migration. Only one CLI-probing host is currently proven.
- **Move profiles to `poteto-mode/references`**: REJECT — mixes typed machine data with human tool guidance, risks packaging/discovery regressions.
- **Inline Grok 15KB of commands into shared setup**: REJECT — leaks host-specific semantics and defeats the already-delivered boundary #703.
- **Delete root profiles immediately**: REJECT — Antigravity packaging and existing tests explicitly require both trees; deprecation needs a separately evidenced gate.
- **Keep `setup-pstack-grok` as public alias forever**: REJECT — permanent two-entry drift; migrate callers first and document rollback for external users.
- **Introduce `SetupProvider`, executor, model catalog or scheduler**: REJECT — YAGNI and outside PStack's canonical semantic scope.

## Risks and responsibilities
Compatibility is a coordinated source-and-package migration, not a silent change to user-owned config. Existing `~/.grok` managed overlays remain scoped. `inherit-parent` for a Grok *model* omits the model override; the same string for *effort* removes the managed overlay but may leave shipped frontmatter effort active. Never claim direct parent-effort inheritance without native proof.

Production acceptance requires package mirror parity, staged/profile filename checks, strict OpenSpec validation (if available), regressions/mutation tests and real native smoke observations. Missing reviewer, checker or host is NOT_RUN/BLOCKED, not a green approval.
