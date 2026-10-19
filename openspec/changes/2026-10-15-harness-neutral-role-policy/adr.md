# ADR Review Manifest

- Status: accepted (Gate #445 fulfilled)
- Review date: 2026-10-19
- Change: 2026-10-15-harness-neutral-role-policy

## In-Force ADRs Reviewed

- `adr/0006-host-owned-orchestration-state.md` - routing hooks MUST NOT introduce a parallel orchestration store; this change keeps hook deployment idempotent and state host-owned.
- `adr/0012-portable-package-descriptor-and-projection.md` - `pstack.package.json` stays the package authority; the policy schema references roles without duplicating them.
- `adr/0014-portable-verification-skills-architecture.md` - verification skills stay host-scoped; the resolver produces plans, never runtime verdicts.
- `adr/0016-codex-models-roles-mapping-and-terra-elimination.md` - Codex model/role facts live in `profiles/codex.json` and projected manifests; the policy doc MUST NOT override them (precedence resolved in #437).
- `adr/0019-post-archive-completeness.md` / `adr/0020-skip-specs-exception-to-post-archive-completeness.md` - archive chain requirements for G8.

## New Durable ADRs Created

- `adr/0021-harness-neutral-model-role-policy.md` - harness-neutral role policy from typed profiles, not host forks (Status: accepted via Gate #445).

## Precedence Resolution (Resolved and locked in #437)

- Precedence hierarchy: explicit invocation > project override > user override > host-role override > host-tier default > parent inheritance (tested and verified in `tests/test_model_role_policy.py`).
- `spec.md` "MUST NOT duplicate tier names" forbids definition duplication; host tier bindings remain permitted.
