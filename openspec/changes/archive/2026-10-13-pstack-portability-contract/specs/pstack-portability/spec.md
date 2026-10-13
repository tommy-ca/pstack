# pstack-portability Specification

## Purpose

Define the smallest portable contract that preserves canonical pstack intent across agent harnesses without introducing a second workflow runtime.

Official `cursor/plugins/pstack` at the immutable `UPSTREAM` pin is the canonical source. This repository is a reference port. Grok Build is the strongest reference adapter in this tree; Codex and Claude Code have mapping/packaging surfaces whose runtime support must be proven separately.

## ADDED Requirements

### Requirement: Canonical intent is upstream-owned

Feature: pstack-portability

Principles, skills, router behavior, playbook intent, roles, ordering, and verification rules MUST derive from the pinned official pstack tree. A host adapter MUST NOT become an intermediate source of truth for another host.

A port MUST track `pin_conformance` (covering the immutable pin) and `upstream_freshness` (unclassified newer changes). A port MAY pass pin conformance while reporting upstream drift.

#### Scenario: reference port is not canonical

- **GIVEN** this repository
- **WHEN** portability behavior is reviewed
- **THEN** official pstack at `UPSTREAM` is the canonical authority
- **AND** this repository is reference evidence for host adaptation
- **AND** Codex, Claude Code, or future adapters do not normatively derive from the Grok mapping

### Requirement: Portable core stays small

The portable core MUST consist of canonical principles, skills, playbook intent, router semantics, roles, verification contracts, and the following host-bound semantic capabilities:

```text
agent.spawn
agent.join
agent.message
agent.cancel
agent.resume

workspace.shared
workspace.isolated
workspace.readonly

human.ask
human.gate
plan.update

schedule
monitor
session.persist
session.resume

evidence.capture
verify
```

The portability layer MUST NOT introduce a generic scheduler, task database, session manager, workflow DSL, provider gateway, or orchestration runtime when the host already owns those concerns.

#### Scenario: new harness

- **GIVEN** a new agent harness
- **WHEN** pstack is ported to it
- **THEN** the porter maps the semantic capabilities to native primitives, shims, version-gated behavior, or explicit gaps
- **AND** canonical playbooks are not rewritten as a new workflow language

### Requirement: Adapter bindings are typed and evidence-backed

A harness adapter MUST classify each required capability with:

```yaml
implementation_status: native | shim | version-gated | gap
enforcement: hard | soft | advisory
verification_status: verified | static-only | unverified | stale
```

A documentation or source-code observation MAY establish `static-only`. A claim about live host behavior requires runtime evidence before it is `verified`.

A prompt-only "do not write" posture is advisory and MUST NOT be reported as hard read-only enforcement.

#### Scenario: weaker substitute

- **GIVEN** a playbook requires hard isolation or read-only behavior
- **WHEN** the host offers only a prompt convention
- **THEN** the binding records the weaker enforcement strength
- **AND** the adapter does not claim semantic equivalence silently

### Requirement: Canonical coverage is discovered, not counted

Portability verification MUST enumerate principles, playbooks, and relevant skills from the pinned canonical tree. Generic portability specs and tests MUST NOT encode literal inventory counts as the source of truth.

Every relevant canonical artifact MUST be classified as:

```text
preserve
adapt
exclude
gap
```

An `exclude` record MUST name a reason class such as packaging, host-specific, domain-pack, or policy.

#### Scenario: canonical adds an artifact

- **GIVEN** a new canonical pin contains an added principle, playbook, or skill
- **WHEN** the coverage lever runs
- **THEN** the artifact appears unclassified until the port records preserve, adapt, exclude, or gap
- **AND** a stale hardcoded count cannot hide it

### Requirement: Durable orchestration state remains host-owned

Playbooks MUST use the host's canonical task, agent, scheduler, session, and persistence state where those concepts exist. pstack MUST NOT create a competing durable orchestration store merely to erase a host gap.

Conceptual durable state includes work units, owners, claims, frontier, verification, gates, decisions, and retry state.

#### Scenario: host lacks durable field

- **GIVEN** a playbook needs durable state the host cannot represent
- **WHEN** the adapter executes that playbook
- **THEN** it records an explicit gate or gap
- **AND** it does not add a parallel pstack database by default

### Requirement: Swarm is a composition, not a harness primitive

The `swarm` skill MUST preserve this semantic shape:

```text
frame -> fan-out -> join -> evidence validation -> aggregate -> report
```

Workers MUST receive independent slices or explicitly declared race arms. Each brief MUST name goal, scope, verification method, and output contract. Missing or invalid worker evidence becomes a dropout or gap; a gap does not count as PASS.

Required host capabilities are `agent.spawn` and `agent.join`. Workspace isolation is required when workers write overlapping-risk state.

#### Scenario: host cannot parallelize

- **GIVEN** a swarm whose independence is required
- **WHEN** the host cannot create independent child contexts
- **THEN** the adapter reports a gap
- **AND** sequential reasoning in one context is not labeled equivalent

### Requirement: Arena is independent generation plus synthesis

The `arena` skill MUST preserve:

```text
frame rubric -> independent candidates -> cross-judge -> pick base -> graft -> verify
```

The rubric MUST exist before candidates run. Candidate writes MUST be separated. The synthesized artifact MUST be verified after grafting. Arena requires no special host API beyond ordinary spawn/join and, when writers are involved, workspace isolation.

#### Scenario: arena requires prior rubric and isolated writes

- **GIVEN** an arena run with N candidates
- **WHEN** candidates are spawned
- **THEN** each candidate writes to an isolated workspace
- **AND** the cross-judge scores against a pre-declared rubric
- **AND** the synthesized artifact is verified before acceptance

### Requirement: Interrogate is independent adversarial review

The `interrogate` skill MUST preserve independent reviewer contexts, a shared review contract, aggregation of consensus and disagreement, deduplication, and lead judgment. Reviewers MUST NOT auto-apply changes.

Model diversity is a useful adapter choice, not a portable semantic requirement.

#### Scenario: interrogate prevents auto-mutation

- **GIVEN** an interrogate review panel with diverse reviewers
- **WHEN** reviewers return findings
- **THEN** the reviewers do not auto-apply code edits
- **AND** the lead reviewer synthesizes findings into act on, consider, noted, or dismissed

### Requirement: Lever verification is the preferred proof pattern

The combination of **Build the Lever**, **Prove It Works**, and `create-verification-skill` defines the portable verification pattern. The port MUST prefer a deterministic lever over hand repetition.

For non-trivial work, the adapter MUST prefer the smallest rerunnable script, codemod, generator, skill, or driver that does or proves the work. A deterministic lever SHOULD be preferred over subagent fan-out when it can cover the work in one reliable pass.

#### Scenario: completion claim

- **GIVEN** an implementation is declared done
- **WHEN** verification is available on the real artifact
- **THEN** the verifier drives that artifact through Launch, Doctor, Drive, Proof Bar, Evidence, and Cleanup
- **AND** compilation, static checks, or child self-report alone do not substitute for runtime proof

### Requirement: Supported harness is a proven state

A harness MUST transition through explicit lifecycle states:

```text
candidate -> mapped -> packaged -> verified -> supported
```

A harness is `supported` only when it has an adapter profile, an installation/packaging path where needed, static conformance, and runtime conformance for its required capabilities.

A mapping document alone is not support.

#### Scenario: partial adapter

- **GIVEN** a Codex or Claude mapping exists
- **WHEN** no runtime conformance evidence is recorded
- **THEN** the harness remains mapped or packaged
- **AND** documentation does not call it supported

### Requirement: Verification has three planes

The port MUST keep these verdicts separate:

```text
Canonical: pin, inventory coverage, upstream drift
Adapter: bindings, manifests, forbidden fields, role mappings
Runtime: live spawn/join, isolation, scheduling where claimed, independent verification, representative playbooks
```

`scripts/verify-harness.py` MAY remain a Grok/static adapter verifier. It MUST NOT be treated as the universal portability verifier.

#### Scenario: three plane separation

- **GIVEN** canonical, adapter, and runtime verification checks
- **WHEN** adapter static checks pass but runtime checks fail
- **THEN** runtime conformance reports FAIL
- **AND** static adapter PASS cannot be used to declare the harness supported

### Requirement: Port architecture follows pstack principles

Portability changes MUST apply core design constraints: Laziness Protocol (smallest adapter), Model the Domain (explicit types), Boundary Discipline (host syntax stops at adapter), Build the Lever (automated conformance), Prove It Works (runtime proof for runtime claims), Separate Before Serializing Shared State (isolate writers), and Encode Lessons in Structure (repeated rules become checks).

#### Scenario: boundary enforcement

- **GIVEN** a new host adapter implementation
- **WHEN** host-specific configuration or syntax is processed
- **THEN** host primitives stop at the adapter boundary
- **AND** canonical playbooks remain host-neutral

### Requirement: Pilot reconciliation precedes scale

Contract differences discovered during the pilot harness MUST be reconciled and documented before scaling to secondary harnesses.

The pilot reconciliation MUST:
1. Reconcile tool mapping to portable capabilities rather than reference host call sites.
2. Enforce RFC 2119 separation between package descriptors and runtime orchestration.
3. Validate deterministic projection of native manifests.
4. Distinguish between global portability requirements and harness-specific compatibility utilities.

#### Scenario: pilot reconciliation gate

- **GIVEN** a completed pilot implementation for Codex
- **WHEN** scaling to OMP or OpenCode
- **THEN** the portability contract is reconciled against observed pilot evidence
- **AND** secondary harnesses build directly on the reconciled contract

## Minimal data model

```yaml
Capability:
  id: string
  required_postconditions: [string]

Binding:
  host: string
  capability: string
  implementation_status: native | shim | version-gated | gap
  primitive: optional string
  enforcement: hard | soft | advisory
  verification_status: verified | static-only | unverified | stale

Adaptation:
  canonical_artifact: string
  mode: preserve | adapt | exclude | gap
  reason: optional string

Evidence:
  claim: string
  kind: static | runtime | external
  artifact: string
```

## Conformance floor

A harness seeking `supported` status MUST prove at least:

1. load/invoke pstack;
2. route one playbook;
3. update progress state;
4. spawn and join one worker;
5. fan out independent workers;
6. isolate a writer when required;
7. perform independent verification;
8. execute swarm;
9. execute arena;
10. execute interrogate;
11. run a real verification lever;
12. report unsupported optional capabilities explicitly.

Scheduling is required only when the adapter claims support for long-running playbooks that depend on it.
