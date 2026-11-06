# Design: smallest semantic boundary

## Existing ownership, not new architecture

~~~text
Pinned official Cursor PStack (canonical intent)
                |
       extract semantic delta
                v
pstack-reference-port + pstack-playbooks OpenSpec
                |
      classify preserve/adapt/exclude/gap
                v
Existing PStack skill/playbook content + host capability maps
                |
           verify / review
                v
Source-linked evidence and recorded differences
                |
        optional downstream consumer
                v
QStack quant overlay (never reverse dependency)

Agent orchestration runtime / worker state / placement: OUTSIDE THIS FLOW
~~~

There is **no** PStack dispatcher, event store, scheduling service or shared runtime API added here. The upstream Orchestrate playbook remains a host-native *workflow description*. Its coordinator/worker semantics do not turn PStack into the implementation owner for external job lifecycles.

## Atomic semantic building blocks

| Atom | Canonical PStack source | Invariant preserved by the port |
| --- | --- | --- |
| Engineering intent | poteto-mode / principles | explicit goal, source of truth, smallest useful work |
| Scoped work brief | poteto-mode playbooks/orchestrate | goal, path ownership, acceptance and independent verification |
| Parallel coverage | skills/swarm | partition/race declared; missing lanes are gaps |
| Comparative synthesis | skills/arena | frozen brief, rubric, isolated candidates; judge evidence or declared skip |
| Adversarial falsification | skills/interrogate | retain only independently rerun failures |
| Verification authoring | create/maintain-verification-skill | concrete project target and reproducible observed checks |
| Formal checking | create/maintain-formal-verification-skill | target-code transition mapping, bounds and negative mutants |
| Quality judgment | thermos reviews | changed-diff correctness, security and simplification |

Additional source observations from Mu/Dogsled are classified as external **reference-only** in references/source-crosswalk.md, not adopted interface/API obligations.

## Minimal data model: a documentation record, not a runtime schema

~~~ts
type Disposition = "preserve" | "adapt" | "exclude" | "gap" | "reference-only";
type EvidenceLevel = "source-only" | "offline-checked" | "observed-native";
interface SemanticDecision {
  sourceRepo: string;
  sourceCommit: string;
  sourcePath: string;
  canonicalPstackPath?: string;
  semanticClaim: string;
  disposition: Disposition;
  evidenceLevel: EvidenceLevel;
  rationale: string;
}
~~~

These are conceptual field definitions for source attribution. Reuse existing inventories and delta formats; do **not** implement a second registry, persist this as a live event schema, or add a new validator until a real consumer demands it.

## Data flow (research and spec management)
Source revision -> cited source path -> atomic claim -> canonical alignment check -> classify -> existing OpenSpec capability -> review/falsifier -> evidence tier -> accepted semantic delta or explicit gap.

## Code and authority flow (existing runtime only)
User intent -> existing poteto-mode playbook selection -> existing swarm/arena/interrogate composition when selected -> host-native tools as declared/observed by profiles -> existing verification skill -> evidence-bound result. No Mu/Dogsled library, daemon or API is called by this spec.

## Conflict rules
- Canonical upstream beats third-party precedent for PStack behavior.
- The recorded applied UPSTREAM pin beats an unpromoted candidate; show candidate drift separately.
- Host-specific adaptations cannot silently become portable semantics.
- Source text, offline contract tests and observed-native behavior are three different evidence levels; no implied promotion.
- Specs are maintained in OpenSpec; docs/wiki may link to, but must not override, active specs.

## Traceability
See requirements in specs/pstack-reference-port/spec.md and specs/pstack-playbooks/spec.md. Reuse openspec/specs/pstack-portability/spec.md and openspec/specs/pstack-sync-from-upstream/spec.md for existing capability/evidence and pin rules. Do not clone those requirements in a new pstack-agent-orchestration capability.
