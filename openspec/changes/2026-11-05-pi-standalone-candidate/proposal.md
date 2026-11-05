# Pi standalone candidate adapter for PStack

Status: **proposed / specification-only**. This change is additive and does not enroll a seventh host. Epic #894.

## Why

PStack supports six shipped harnesses and has a 17-capability semantic contract. The user's minimal Pi setup currently relies on unrelated extensions with overlapping orchestration, skill and quality functions. Native standalone Pi is not OMP. A blind profile copy or an extra generic orchestration layer would violate host ownership and falsely promote unverified behavior.

## What Changes

Specify a candidate standalone Pi 1.5.0 host mapping using native Pi tools and a small optional extension profile: pi-subagents 0.85.0 for delegated agent execution, pi-better-sandbox 0.14.1 for explicitly enabled guard profiles, and pi-web-access for research. Treat @zenspc/pi-pstack as an **evaluated transitional bundle**, not canonical authority; prefer projecting canonical tommy-ca/pstack skills/agents.

Reuse the existing host-identity/profile/evidence/verification and self-contained LLMWiki structures. Add no extra scheduler, router, role registry, task database, engine or wiki compiler.

## Impact

- Source-grounded 17-capability candidate matrix and classification of the original 17 installed extensions.
- Explicit typed profile/projection implementation and negative tests **as subsequent tasks**, not fictitious completed functionality.
- Candidate-native verification and formal proof gates requiring real execution evidence before promotion.
- Curated knowledge and dependency graph without replacing existing docs or archived OpenSpec history.

## Non-goals

- No runtime adapter, Pi package installation or live subagent proof in this specification PR.
- No modification of the six built-in host definitions, package host_targets, canonical skills or upstream pin.
- No claim of hard sandbox security from a prompt, install command, or static package README.
- No overlapping work with independent unmerged PRs #502 and #540.

## Source/evidence

See docs/research/pi-1-5-standalone-pstack-audit-2026-11-05.md and issue #894. All capability evidence here is **static-only/unverified**. This PR does not satisfy the observed-live promotion gate.
