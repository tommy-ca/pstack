# ADR Review Manifest

- Status: completed for the **spec-only** change; implementation decisions remain provisional
- Review date: 2026-10-11

## Review Summary

Reviewed the repository-level ADR inventory `adr/0001` through `adr/0018` against OMP source facts, the portable orchestration contract and the proposed native package choices. This OpenSpec change introduces **no new accepted platform-wide architecture decision**: it preserves the host-owned state, one portable descriptor, canonical semantic boundary, exact-match route resolution, and truthful evidence principles already in force. A native OMP package format remains an **empirical design choice** pending the clean install proof in #290; the provisional Arena preference is not itself an accepted ADR.

## In-Force ADRs Reviewed

- `adr/0005-playbooks-are-not-rhai-workflows.md` — playbooks remain Markdown, not a new harness workflow DSL.
- `adr/0006-host-owned-durable-orchestration-state.md` — no second scheduler, session manager or orchestration database.
- `adr/0007-openspec-archive-chain-gate.md` — requires design + ADR manifest before archiving completed changes.
- `adr/0009-semver-grokbuild-not-calver.md`, `adr/0010-adapter-not-sibling-version.md`, `adr/0011-single-plugin-repo-not-catalog-folder.md` — preserve version identity and single-plugin repository.
- `adr/0012-portable-package-descriptor-and-projection.md` — one portable descriptor and native manifest projections. OMP provider validity must be proven without inventing a competing descriptor.
- `adr/0015-symmetric-host-reference-mappings-and-harness-retirement.md` — host-specific lookup and mapping live under the appropriate adapter boundary.
- `adr/0017-minimal-routing-proof-lifecycle.md` — shared route resolver, explicit proof levels and loss-aware lifecycle.
- `adr/0018-verification-skill-scaffold-and-audit.md` — executable verification skills and exact evidence attribution.

Other files in the inventory were inspected for status/supersession: `ADR-0001` is superseded by accepted `ADR-0003`; `ADR-0002` by accepted `ADR-0004`; `ADR-0008` is **Proposed**, so its claimed supersession of `ADR-0006` is not treated as an accepted override. The Antigravity- and Codex-specific ADRs do not normatively define OMP.

## New Durable ADRs Created

- None — no new decision has passed the native OMP package and runtime evidence gate. If #290 proves that the accepted projection architecture cannot produce a loader-recognized OMP package, its implementation PR MUST evaluate an additive adapter projection or a new superseding ADR; previous accepted ADRs remain immutable.

## Semantic block architecture review

The new companion `semantic-building-blocks.md` and `pstack-portability` delta **document existing boundaries**, not new durable types: canonical Markdown principles/playbooks/roles, 17 portable capability identifiers, existing profile/binding/schema/receipt artifacts, host-owned execution/state and proof gates. Accepted ADR-0005, ADR-0006, ADR-0012 and ADR-0017 continue to control the design. Swarm/Arena/Interrogate are composites; native OMP `workpool` is an optional host mechanism, not a new portable primitive. The accepted flat-port Orchestrate adaptation remains explicit and canonical nested parity is not claimed. No new ADR accepted by this spec-only change.

## Verification scope

- **Completed:** source inspection, pinned design, formal requirements/scenarios and issue graph (#288–#294, #296–#298), spec draft PR #295.
- **Not completed:** native OMP install/discovery, model-backed task/eval child execution, full multi-agent Swarm/Arena/Interrogate run, actual acceptance conformance. Do not use this review manifest as a runtime receipt.
