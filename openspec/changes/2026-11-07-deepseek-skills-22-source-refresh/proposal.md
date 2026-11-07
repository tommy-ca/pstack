# Proposal: refresh DeepSeek Harness reusable-skill evidence from 16 to 22

## Why
The living `pstack-reusable-skill-patterns` requirement still requires an inventory of sixteen DeepSeek Harness skills pinned to `d7432673`. DeepSeek Harness `master` at `fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159` contains twenty-two skill directories: six new since that baseline, and eight older directories with changed tree object IDs. The original adaptation decision survives, but the baseline is stale.

## What Changes
- Update the **existing** OpenSpec capability and add a pinned 22/22 source-to-owner crosswalk; preserve the 2026-10-11 archive unchanged.
- Formalize optional lifecycle, session-projection, responsive UI, artwork, macOS signing, and PR-description boundaries without vendoring DeepSeek wrappers.
- Declare Swarm for independent source/owner scans, Arena for comparing integration alternatives, and Interrogate for running real-code negative controls. These are **existing PStack skills**; no new dispatcher or state engine.
- Define acceptance and unperformed tests honestly. This is a **specification-only** update, not a runtime adaptation or validated improvement.

## Capabilities
- **Modified:** `pstack-reusable-skill-patterns`.
- **No new capability:** host/tool eligibility stays with `poteto-mode`/playbooks/adapters; existing verification and evidence reducers remain authoritative.

## Scope and source probes
- GitHub directory inventory: `GET /repos/deepseek-ai/deepseek-harness/contents/.agents/skills?ref=fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159` — **SOURCE_STATIC**, 22 directories with `SKILL.md`.
- Prior source inventory at `d743267388641bc76f17c45ce8b4c231aed1d32c` — **SOURCE_STATIC**, 16 directories.
- PStack live specification: `openspec/specs/pstack-reusable-skill-patterns/spec.md` on main — **SOURCE_STATIC**, says sixteen.
- Prior epic: https://github.com/tommy-ca/pstack/issues/305 (closed); existing changes and receipts must not be rewritten or called fresh.
- PStack fork base observed `01c5406dfa4da460708fdffabd06438263eb8462`, upstream cursor/plugins `6b0300214a09fd6029cfb7077043125758cd1fd2`.
- Source license: DeepSeek Harness MIT, `LICENSE` at the same pinned repository. Reference concepts and rewrite requirements; no substantial copied instruction bodies.

## Out of scope
- Adding 22 `dsh-*` skills; creating a second router, registry, verifier or worker manager.
- Mandating Cordis, pnpm, 390px minimum widths, a fixed GitHub PR template, official `gh stack`, Chinese pairing, live model credentials, GIF demonstrations, or macOS signing across projects.
- Changing the upstream fork pin, QStack quant-domain doctrine, or closed epic #305; suggesting unavailable hosts passed runtime tests.

## Done when
A full 22/22 provenance/decision crosswalk and new negative-trigger requirements are reviewable; previously changed directories are marked re-review rather than automatically adopted; a follow-up implementation/eval pass can prove or reject each proposed adaptation against the existing host matrix and negative controls.
