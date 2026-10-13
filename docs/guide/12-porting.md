# Port pstack to another agent harness

Official pstack at the immutable pin in [`UPSTREAM`](../../UPSTREAM) is canonical. This repository is a **reference port**. Its Grok implementation is evidence for how to adapt a host, not an intermediate specification that other hosts must copy.

The host map is the primary adapter document, defined under the cross-harness contract [`pstack-portability`](../../openspec/specs/pstack-portability/spec.md).

## Keep the pstack meaning

Preserve the canonical principles, skills, router behavior, playbook intent, role boundaries, ordering, and verification rules. Focus on less code, not loc. Port host-dependent mechanisms only.

The architecture is intentionally small:

```text
canonical pstack
    ↓
portable capabilities
    ↓
host adapter
    ↓
conformance evidence
```

Do not add a universal scheduler, task database, session manager, provider gateway, or workflow DSL just to make hosts look alike.

The principles that matter most during a port are **Laziness Protocol**, **Model the Domain**, **Boundary Discipline**, **Build the Lever**, **Prove It Works**, **Separate Before Serializing Shared State**, and **Encode Lessons in Structure**.

## Discover, do not count

Enumerate the canonical principle, playbook, and relevant skill inventory from the recorded pin. The reference canonical pin establishes 23 principles as leaf skills and 23 `principle-*` skills. Do not use a literal number as the permanent source of truth for future pins.

For every relevant canonical artifact record one state:

```text
preserve
adapt
exclude
gap
```

An exclusion needs a reason such as packaging, host-specific, domain-pack, or policy.

Track pin conformance separately from upstream freshness. The port can conform to its immutable pin while newer canonical changes remain to be classified.

## Capability checklist

For the new host, document these capabilities from live docs/source and runtime evidence where possible. Map primitives such as Spawn a child (`agent.spawn`), Join / wait (`agent.join`), and Overnight loop (`schedule`). Write `gap` when a capability is absent:

| capability | question |
|---|---|
| `agent.spawn` | How does the parent create a child and select a role/model? |
| `agent.join` | How does the parent wait for terminal results? |
| `agent.message` / `agent.cancel` / `agent.resume` | Which lifecycle operations exist? |
| `workspace.isolated` | Can a writer get an independent writable tree/workspace? |
| `workspace.readonly` | Is no-write enforcement hard, soft, or prompt-only? |
| `human.ask` / `human.gate` | How are product questions and irreversible-action gates represented? |
| `plan.update` | What is the host-native progress state? |
| `schedule` | Can long-running work wake later, and in what context? |
| `monitor` | Can a process/PR/condition be watched without polling loops? |
| `session.persist` / `session.resume` | What state survives a turn or session boundary? |
| `verify` / `evidence.capture` | How is real-artifact proof captured and retained? |

Each binding records:

```text
implementation: native | shim | version-gated | gap
enforcement: hard | soft | advisory
verification: verified | static-only | unverified | stale
```

Write `gap` instead of inventing a host field.

Grok's detailed reference mapping remains [`grok-tools.md`](../../skills/poteto-mode/references/grok-tools.md). Codex, OMP, OpenCode, and Antigravity have their own mapping/packaging surfaces (`codex-tools.md`, `omp-tools.md`, `opencode-tools.md`, `antigravity-tools.md`); they do not inherit Grok semantics.

## Preserve the composed skills

### Swarm

```text
frame → fan-out → join → validate evidence → aggregate → report
```

Use independent workers for independent slices or declared race arms. Every brief names the goal, scope, verification method, and output contract. A dropout or missing evidence is a gap, never PASS.

### Arena

```text
frame rubric → independent candidates → cross-judge → pick → graft → verify
```

Declare the rubric before generation. Separate candidate writes. Verify the synthesized result after grafting.

### Interrogate

```text
intent → independent reviewers → consensus/disagreement map → lead judgment
```

Reviewers do not mutate the artifact. Multi-model review is useful when available, but the portable invariant is independent adversarial review plus explicit synthesis.

## Build the verification lever

Use **Build the Lever** and **Prove It Works** together. A deterministic script, codemod, generator, driver, or project verification skill is preferable to hand repetition and often preferable to fan-out.

When a project lacks a reliable proof path, use `create-verification-skill` to produce a small driver with:

```text
Launch
Doctor
Drive
Proof Bar
Evidence
Cleanup
```

and a feature map. Drive the real artifact. Compilation or agent self-report is not runtime proof.

## Keep durable state host-owned

Use the host's native task, agent, scheduler, session, and persistence state. Do not create a second pstack scheduler/database to hide a host limitation. Record the limitation as a gap.

## Support states

Use these states instead of calling every mapping "supported":

```text
candidate → mapped → packaged → verified → supported
```

A host is supported only after its required capability bindings have static and runtime conformance evidence.

## Port sequence

1. Pin canonical pstack.
2. Generate canonical inventory and classify drift.
3. Map the semantic capability surface.
4. Package skills/roles for the host.
5. Adapt host-dependent call sites at the adapter boundary.
6. Add static adapter checks.
7. Prove live spawn/join, isolation, independent verification, and representative playbooks.
8. Prove `swarm`, `arena`, `interrogate`, and a real verification lever.
9. Only then mark the harness supported.
10. Add domain packs last.

## Reconciled pilot contract

Evidence gathered during the Codex pilot reconciled core contract expectations:

1. Prompt-only read-only posture is advisory. It must not be reported as hard isolation.
2. Package descriptors are static metadata. They must not contain runtime orchestration fields.
3. Native harness manifests are projected deterministically from `pstack.package.json` using `scripts/project-package.py`.
4. Secondary scale harnesses (OMP and OpenCode) consume the reconciled capabilities and projected manifests directly.

A port that copies another port's host calls is not portable pstack. A thin adapter with strong evidence is.

## Batch 2 acceptance matrix (5 harnesses)

Batch 2 expands the verified host matrix to 5 harnesses across 3 verification planes (Canonical, Adapter, Runtime):
1. **Grok Build** (`grok`): Reference host. Subagent tree with depth 2 and shared workspace.
2. **Codex** (`codex`): Pilot host. Independent workspace git-tree with advisory read-only enforcement.
3. **OMP** (`omp`): Scale host. Subagent-driven, multi-lane execution with model tier binding.
4. **OpenCode** (`opencode`): Scale host. Tool-call delegation and structured multi-lane orchestration.
5. **Google Antigravity** (`antigravity`): Subagent orchestration (`invoke_subagent`, `define_subagent`, `manage_subagents`), background tasks (`run_command` async, `manage_task`, `schedule`), structured human gates (`ask_question`), Gemini model role bindings (`pro`, `flash`, `flash_lite`), and native `.agents/` / plugin rules.

All 5 harnesses are verified via the 3-plane lever engine (`scripts/verify-portable.py run --host <host>`).

