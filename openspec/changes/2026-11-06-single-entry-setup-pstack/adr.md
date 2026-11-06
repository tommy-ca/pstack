# ADR: Setup is one skill with host-specific references; profiles stay packaged with setup

- Status: Proposed — requires review and verification prior to implementation.
- Date: 2026-11-06
- Epic: #948
- Existing authoritative capability: `openspec/specs/pstack-setup-overlays/spec.md`.

## Decision
1. **One public setup skill.** Keep `skills/setup-pstack/SKILL.md` as the operator-facing entry. Integrate existing Grok instructions under `skills/setup-pstack/references/` and delete `setup-pstack-grok` only after all callers are updated.
2. **Two kinds of reference are distinct.** `poteto-mode/references/<host>-tools.md` describes execution-time tool bindings. `setup-pstack/references/<host>.md` owns configuration discovery, native UI, validation and safe file writes. Neither is a model catalog or role registry.
3. **Packaged profiles are canonical.** Keep machine-readable `skills/setup-pstack/profiles/*.json` because packaged skill consumers need them. The root `profiles/` mirror must become a mechanically generated compatibility output, never a second editable authority. Preserve it until every root consumer and installer is migrated and separately verified.
4. **Typed reference dispatch.** A host's `setup` projection, not a hardcoded shared branch, points to its native setup reference. Resolve the active host by observed host surface + an exact declared `host` ID, validate the reference path under the packaged setup skill and fail closed if absent, candidate, wrong host, or unsafe.
5. **Upstream semantics first.** Reuse canonical Cursor's setup intent and local role/model resolver, translating only the approved capabilities to each host. Grok effort enum, TOML paths, and model defaults remain exclusively in Grok references and native helper functions.

## Alternatives considered
- Move nine profiles into `poteto-mode/references/`: **reject**. Cross-cutting typed host declarations should not become execution/playbook prose; this would break current setup packaging and conflate authorship.
- Move all Grok instructions into shared `setup-pstack/SKILL.md`: **reject**. Would violate host-neutrality and boundary scanner.
- Keep a separate user-invocable Grok setup skill indefinitely: **reject**. Duplicate entry/description and policy surface; higher maintenance cost.
- Immediately remove root `profiles/`: **reject for this change**. Tests and Antigravity package currently expect the mirror.
- Introduce a runtime `SetupProvider` class/SDK: **reject** under YAGNI. A typed path and existing pure resolver suffice.
- Shift setup to QStack or create a generic scheduler: **reject**. Wrong ownership and reverse dependency.

## Consequences
Migration needs a bounded compatibility interval for `setup.skill`, careful package/doctor/test changes, and a final-head verification gate. No implementation/API is deemed proven by this ADR. Existing user-owned native configuration is preserved by default.
