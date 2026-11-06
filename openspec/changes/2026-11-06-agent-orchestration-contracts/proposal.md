# Mu + Dogsled agent orchestration: source-pinned intent

## Why

Mu and Dogsled expose distinct, useful patterns for durable agent work. Mu is a task-DAG and coordination control plane; Dogsled is a placement, admission, job, and child-lifecycle execution plane. PStack already provides harness-neutral workflow policy and host-bound agent operations; QStack must continue to consume PStack rather than create another development router. This change extracts the *contracts* and falsifiable safety rules, not their storage engines.

Parent: [agent orchestration epic #916](https://github.com/tommy-ca/pstack/issues/916). Detailed issues #917-#922.

## What changes

- Source-pinned semantic inventory, with adoption dispositions and explicit owner boundaries.
- Requirements, design, code/data flows, typed model proposals and negative conformance scenarios in this OpenSpec change.
- Verification/negative-mutation matrix for the existing create-verification-skill and create-formal-verification-skill workflows.
- Opt-in candidate adapter interface; no assertion that Mu or Dogsled is installed in any host.
- Explicit swarm/arena/interrogate and Thermos review acceptance criteria; missing live tests remain BLOCKED or UNTESTED.

## Source pins (observed 2026-11-06)

- Mu: `mu-crew/mu@73fb53d4e38c9717be5642460b2344c76cfe6349` — [README](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/README.md), [architecture](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/ARCHITECTURE.md), [ops log](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/ops-log.md), [task DAG](https://github.com/mu-crew/mu/blob/73fb53d4e38c9717be5642460b2344c76cfe6349/docs/architecture/dag.md).
- Dogsled: `oisin-ee/dogsled@5e28a8c72272f8d8a91f86c4691a43f4bca6d551` — [architecture](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/design.md), [lifecycle](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/lifecycle.md), [unit requests](https://github.com/oisin-ee/dogsled/blob/5e28a8c72272f8d8a91f86c4691a43f4bca6d551/docs/unit-requests.md).
- Target: `tommy-ca/pstack@5a06e40f89d43a59ce35814f02add68f710ff70c`.
- Canonical: `cursor/plugins@2776ddd2355d6d6c8747d3964600f28daf62f049` (PStack and Thermos).
- Downstream: `tommy-ca/qstack@918b3c57c75e1caae3f44a686bed6e8c3619ee0c`; [authority](https://github.com/tommy-ca/qstack/blob/918b3c57c75e1caae3f44a686bed6e8c3619ee0c/AGENTS.md).

Mu package metadata and Dogsled LICENSE identify MIT licensing. This change links and paraphrases concepts, copying no runtime implementations.

## Scope, status, and non-goals

**Status: DRAFT — contracts and research only.** No executed host probes, model-checker run, actual agent swarm, or adapter deployment is claimed.

No second orchestrator, persisted task store, daemon, queue, model router, CLI supervisor, schema migration, web portal, or import of either upstream code. No changes to qorch's quant-research authority or QStack's installed-dependency direction. No writing claims about upstream defects from mere file size, documentation, or theoretical failure modes.

## Decision test

Only implement an opt-in adapter when native PStack host capabilities prove insufficient for a named workflow, and when the additional safety contract can be observed with a real negative-control test. Prefer one simple adapter over abstracting two backends in advance.
