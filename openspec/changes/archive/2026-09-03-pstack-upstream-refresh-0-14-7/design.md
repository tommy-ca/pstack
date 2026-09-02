## Context

The local tree is a host adapter for Cursor's pstack, not a byte-for-byte mirror. The tracked upstream pin is `6fecddba65801f9b9c08b8b328d998ee5b09d290`; the upstream cache now reports three pstack commits after that pin and `origin/main` at `efa2a531985e0a8084d36ff3cf87233be8a9f34b`. The delta is 27 pstack paths: forge-neutral landing guidance, Fable 5.1 wording/defaults, four skill metadata changes, TypeScript schema guidance, and an upstream logo/manifest bump.

The local adapter owns Grok `spawn_subagent`, `monitor`, `scheduler_create`, depth-one parent fanout, `.grok-plugin` metadata, Codex/Claude manifests, Benny paths, release checks, and OpenSpec evidence. Existing ADR review found no in-force decision that this refresh supersedes: ADR-0008 supersedes ADR-0006, ADR-0004 supersedes ADR-0002, and ADR-0003 supersedes ADR-0001. ADR-0005, ADR-0007, ADR-0009, ADR-0010, and ADR-0011 remain applicable.

## Goals / Non-Goals

**Goals:**

- Port the upstream behavioral delta from `efa2a531` into shared skills, playbooks, guides, and tests.
- Make PR and stack instructions forge-neutral: GitHub `gh` by default, Origin only when its CLI resolves the repository, and no Graphite prerequisite.
- Preserve Grok host-native monitoring, scheduling, fanout, safety, and manifest boundaries.
- Make the upstream pin, recipe, manifests, and local verification evidence agree.
- Keep the intentional omissions explicit and testable.

**Non-Goals:**

- Do not copy Cursor-only `.cursor-plugin` or `assets/logo.png` into an adapter repository.
- Do not restore `skills/make-bot-ui`; local `figure-it-out` remains its replacement.
- Do not replace Grok host mappings with Cursor Task calls or Fable model slugs.
- Do not change Codex compatibility utilities into Grok runtime dependencies.
- Do not add dependencies, perform release tagging or remote pushes, or publish/update production or installed marketplace state; the tracked `.claude-plugin/marketplace.json` version update is in scope.
- Do not repair unrelated historical OpenSpec task records; that is a separate approved change.

## Decisions

### Refresh by semantic file groups, not wholesale copy

Use the sparse upstream cache as the source of truth for the 27-path diff, then manually port only textual intent into the adapted files. Preserve local-only files and host mappings. The logo is packaging-specific and is excluded; `make-bot-ui` is intentionally excluded by the local harness.

### Resolve the forge once and retain parent-base stacks

Update `HARNESS.md`, the active shipping/PR playbooks, and the bugbot reference to select Origin when its CLI resolves the current repository and otherwise use `gh`. Remove Graphite-first and `gt submit` requirements. Stack children continue to use explicit parent branches; only a root PR targets protected trunk, and `--auto` is not used for children. This changes stale documentation, not Grok runtime primitives.

### Preserve host-native Grok orchestration

Keep `monitor`, `scheduler_create`, `spawn_subagent`, the depth-one fanout contract, and adapter-specific role/effort frontmatter. Apply upstream additions such as regression lanes and dual-sided performance validation around those primitives. Keep `scripts/orch` and `scripts/watch-pr` as Codex-only compatibility surfaces.

### Apply supported metadata and schema guidance selectively

Add `disable-model-invocation: true` only to the retained upstream skills that received it: `how`, `typescript-best-practices`, `unslop`, and `why`. Add TypeScript `paths` for `**/*.ts` and `**/*.tsx`, plus the upstream schemas-before-guards rule and Zod example. Do not import unsupported upstream paths or replace the local Grok skill frontmatter shape.

### Use the next adapter version without changing version grammar

Set the upstream foreign key to `0.14.7` and initialize the adapter counter at `0`, yielding `0.14.7-grokbuild.0`. Update root, Grok, Codex, Claude, and Claude marketplace versions together. This follows ADR-0009/0010 and does not move existing tags.

## Risks / Trade-offs

- Manual adaptation can miss a textual upstream change. Mitigation: keep the 27-path upstream diff as the checklist, search for stale Graphite-first terms, and run the harness plus targeted contract tests.
- Removing Graphite-first language may leave a compatibility reference with a historical filename. Mitigation: retain the file only as a forge-neutral compatibility map and test its new contract; remove any obsolete live `gt` requirement.
- Upstream wording may assume Cursor model/runtime features. Mitigation: port concepts, not Cursor calls, and keep the local adapter verification gate authoritative.
- `--log` requires network access. Mitigation: verification separately uses the recorded pin and only treats a successful cache fast-forward as freshness evidence.

## Migration Plan

1. Create and validate this intent-driven change before implementation.
2. Apply the file-grouped refresh and metadata/version updates.
3. Run `python3 scripts/verify-harness.py`, `python3 tests/test_verify_harness.py`, `python3 tests/test_release.py`, targeted sync commands, and strict validation for the active change.
4. Review the diff for host-boundary regressions and leave release/push actions to an explicitly authorized operator.
5. Archive only after the separate archive-task-hygiene change has repaired its two transparent external-verification gaps and all strict archive checks pass.

Rollback is a normal revert of the refresh files; no database, remote, or installed-plugin state changes are part of this change.

## Open Questions

None. The approved split keeps historical archive hygiene separate from the upstream refresh, and existing ADRs cover host boundaries and version identity.
