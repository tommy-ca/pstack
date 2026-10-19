# ADR 0021: Harness-neutral role policy from typed profiles, not host forks

Status: **accepted** (accepted 2026-10-19 via Gate #445)
Date: 2026-10-15 (accepted 2026-10-19)

## Context

`tommy-ca/pstack` already owns the capability and package projection schema. `pstack-claude` supplies a useful source-of-truth generator, per-role model/effort configuration and Pi equivalence tests, but also carries explicit policy forks and a distinct local control plane. A copied fork would compromise canonical ownership and existing pstack/qstack boundaries.

## Decision proposal

Choose a declarative, stable-ID role model and minimal pure resolver layered onto existing `profiles/`, schemas, `pstack.package.json`, `scripts/project-package.py` and evidence receipts. Each harness resolves actual model identifiers and effort using its live capability catalog and native APIs. Keep agent lifecycle/worktree/session state host-owned. Claude and Copilot are independent adapter candidates with separate native evidence. No generic orchestration runtime.

## Rejected candidates

- Copy `pstack-claude` runtime and policies wholesale: mixed authority and duplicate controls.
- Central provider gateway or workflow DSL: violates existing portability boundary / YAGNI.
- Retain untyped prose-only role mapping: lacks negative-path validation and projection drift proof.

## Consequences

- One new schema and minimal resolver/validator effort; existing profiles and manifests remain authoritative for hosts.
- Independent receipts are required per host and version before any capability is called verified.
- Cross-family judge diversity, live model availability and read-only enforcement cannot be inferred from labels.
- RFC decision accepted via Gate #445 with complete test, schema, projection, and evidence verification.
