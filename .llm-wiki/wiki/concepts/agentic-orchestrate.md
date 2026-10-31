# Agentic Orchestrate Architecture

## Overview
In upstream release 0.15.36 (commit #1043), canonical PStack retired the `orch` CLI and SQLite store (`skills/poteto-mode/scripts/orch/orch.ts`, `store.ts`), replacing it with agentic coordination where the parent chat acts as the coordinator owning briefs, queue draining, and stack frontier tracking.

## Core Rules

1. **Host-Owned State:**
   - The coordinator MUST NOT create a playbook-local store, SQLite database, or parallel queue.
   - Durable state (units, claims, PRs, verification rows) lives in canonical host state and git forge.
2. **PR-Scoped Ownership:**
   - Exactly one designated worker owns each PR branch.
   - Global stacker write access is removed. Workers never rebase or retarget upstream PRs directly.
3. **Independent Verification:**
   - Each PR requires an independent verifier (`pstack:independent-verifier`) on a distinct model family from the worker.
   - Verifier records exact-head receipts (`live-ui-verified`, `unit-test-verified`, `type-check-only`, `verifier-blocked`, `verifier-failed`).
4. **Immediate Output Externalization:**
   - Units push branches and publish receipts immediately upon verification rather than batching to end of run.
