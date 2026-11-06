# Proposal: one harness-neutral setup-pstack skill, references for host-specific setup

## Why
Upstream Cursor PStack has one `setup-pstack` skill, whose engineering intent is model availability discovery, budget/role choices, validation, safe persistence, confirmation and optional verification skills. This reference port currently splits that behavior across a 6 KB neutral `skills/setup-pstack/SKILL.md` and a 15 KB Grok-only `skills/setup-pstack-grok/SKILL.md`, plus four Grok-only references. Nine typed host profiles exist both in `profiles/` and `skills/setup-pstack/profiles/`; the latter is labeled canonical in the sync tests while `resolve_profiles_dir()` prioritizes root in repository checkouts.

We can remove the extra *public skill* without combining host-specific commands into a shared body. Existing port schemas, model role resolver and packaged profiles make a new setup framework unnecessary.

## Scope
- Keep **one invocable `/setup-pstack`** that retains canonical upstream flow: detect -> load -> select budget/roles (within proven host capabilities) -> validate -> write/projection or explicit no-write -> confirm -> optional verification skills.
- Move Grok implementation instructions to `skills/setup-pstack/references/grok.md`; move `defaults.toml`, `resolve-model.md`, `resolve-effort.md` and `effort-ladder.md` into `skills/setup-pstack/references/grok/`.
- Evolve existing `SetupProjection` to name a validated `reference` for `host-cli`, retiring `setup.skill` in a bounded migration after all readers and packages are migrated.
- Preserve the existing `pstack.package.json#roles` role registry, `scripts/model_role_resolver.py` precedence, explicit host support/GAP and Grok safe native writes.
- Keep all nine machine-readable profiles in `skills/setup-pstack/profiles/`, NOT `poteto-mode/references/`. Treat root `profiles/` as a deterministic compatibility *projection*, then remove only after its consumers and release packaging are proven migrated.
- Reconcile existing `pstack-setup-overlays` capability, setup projection schema, test/doctor callers, packaging and docs before retiring the Grok skill.

## Non-goals
No generic agent orchestration, scheduler, process/agent lifecycle, new router, model-provider catalog, reimplementation of upstream playbooks, automatic model installation, candidate host feature promotion, QStack imports, broad new adapter framework, or changes to upstream Cursor semantics. No Grok-specific prompt/options, model slugs, file paths or effort enums in shared SKILL prose.

## Sources
- Canonical [Cursor setup-pstack at applied pin `88d47514`](https://github.com/cursor/plugins/blob/88d47514b82e7c44f00f2b2a72ff6dd12158038c/pstack/skills/setup-pstack/SKILL.md); [observed current upstream `2776ddd`](https://github.com/cursor/plugins/blob/2776ddd2355d6d6c8747d3964600f28daf62f049/pstack/skills/setup-pstack/SKILL.md). The two observed setup bodies differ in one Arena cross-judge-pool sentence: latest explicitly skips parent-family values and runs one other-family judge. Do NOT mark that candidate semantic change as applied until upstream pin reconciliation.
- Port [setup-pstack](https://github.com/tommy-ca/pstack/tree/main/skills/setup-pstack), [setup-pstack-grok](https://github.com/tommy-ca/pstack/tree/main/skills/setup-pstack-grok), [profile resolver](https://github.com/tommy-ca/pstack/blob/main/scripts/setup_pstack.py), [typed setup schema](https://github.com/tommy-ca/pstack/blob/main/schemas/portability/setup-projection.schema.json).
- Already-completed foundations: #703 (host-neutral entry), #937/#938/#939/#940/#941/#942 (packaged profiles and conformance), #429/#438 (role and precedence). Do not reopen or duplicate.
- Review: [Cursor Swarm](https://github.com/cursor/plugins/tree/main/pstack/skills/swarm), [Arena](https://github.com/cursor/plugins/tree/main/pstack/skills/arena), [Interrogate](https://github.com/cursor/plugins/tree/main/pstack/skills/interrogate), and the two [Thermos](https://github.com/cursor/plugins/tree/main/thermos/skills) review skills.

## Delivery
Parent #948; #949 source inventory -> #950 OpenSpec -> (#951 merge and #952 profiles in parallel) -> #953 exact-head verification. This PR is SPEC-FIRST and makes **no shipped setup behavior changes**. CI/live review and implementation delivery have their own acceptance gates.
