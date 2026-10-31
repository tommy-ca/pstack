# LLM Wiki Reference Engine Arena Decision: Baseline vs Adapters vs Migration

**Document Date:** 2026-10-31  
**Logical Parent:** [Epic #871](https://github.com/tommy-ca/pstack/issues/871)  
**Issue:** [Issue #873](https://github.com/tommy-ca/pstack/issues/873)  
**Status:** BINDING ARCHITECTURE DECISION; implementation/evidence assertions corrected 2026-10-31. This remains a **design choice**, not a completed migration, runtime benchmark or security proof.  

---

## 1. Executive Summary

Following the comprehensive reference engine architecture audit in [PR #878](https://github.com/tommy-ca/pstack/pull/878) ([`docs/research/llm-wiki-reference-evaluation-2026-10-31.md`](llm-wiki-reference-evaluation-2026-10-31.md)), this Arena Decision resolves the architecture choice among three candidate topologies for PStack's LLM Wiki:

- **Option A (Keep Canonical Baseline):** Retain and harden PStack's pure Python standard library compiler (`scripts/llm_wiki.py`), local Markdown repository (`.llm-wiki/`), and deterministic indexing.
- **Option B (Optional Upstream Engine Adapters):** Build optional adapters to run Atomicstrata compiler as an untrusted candidate producer and/or Geronimo binary as an optional read/BM25 indexer.
- **Option C (Full Migration):** Replace PStack's Python CLI entirely with Geronimo Rust engine or Atomicstrata Node.js compiler.

### Binding Decision

**Option A is selected as the canonical baseline.**  
**Option B is deferred without active implementation (resolving Issue #875 as `not_planned`).**  
**Option C is decisively rejected.**

---

## 2. Decision Criteria and Evaluation Matrix

| Criterion | Weight | Option A: Python Stdlib Baseline | Option B: Optional Adapters | Option C: Full Migration |
| :--- | :--- | :--- | :--- | :--- |
| **Six-Host Portability** | CRITICAL | **DESIGN FIT** (stdlib and no provider dependency; six-host/OS observed-live matrix NOT MEASURED here) | **RISK** (Requires Node >= 24 or cargo/rustc toolchain; breaks zero-install host guarantee) | **FAIL** (Mandatory heavy runtimes break offline CLI and lightweight agent setups) |
| **Cold Start & Latency** | HIGH | **NOT MEASURED** (stdlib Python likely lightweight; no pinned cold-start benchmark evidence in this decision) | **MEDIUM** (Node/cargo spawn adds process overhead and IO latency) | **MEDIUM** (Geronimo binary is fast once compiled, but build step is expensive) |
| **Mutation Authority & Safety** | CRITICAL | **POLICY FIT** (no external publisher required; repository write authority must still be enforced by Git permissions/review gates) | **MEDIUM** (Requires strict candidate containment and unprivileged execution) | **FAIL** (External engine claims publisher/ledger authority; conflicts with QStack governance) |
| **Maintenance Burden (KISS/YAGNI)** | HIGH | **PASS** (Single ~280-line Python script; standard unit tests with pytest) | **FAIL** (Dual-engine maintenance, schema synchronization, and mock harness baggage) | **FAIL** (Full upstream dependency tracking, foreign language tooling, breaking release cycles) |
| **Audit Vulnerability Remediation** | HIGH | **PENDING MAINLINE** (source-inspected overwrite defect existed at decision main; successor #881 proposes tested hardening, not yet merged) | **MEDIUM** (Fixes Python gaps but adds cross-language bridge attack surface) | **UNKNOWN** (Imports upstream vulnerabilities and external node module supply chains) |
| **Rollback & Data Integrity** | HIGH | **DESIGN FIT** (plain Git Markdown and reversible diffs; crash-consistent source+activity-log commit is not implemented) | **PASS** (External indexes remain disposable) | **FAIL** (Complex database migrations and opaque storage layers complicate rollback) |

---

## 3. Detailed Rationale

### 3.1 Adherence to KISS and YAGNI
PStack's LLM Wiki exists to maintain durable project memory, architecture decisions, requirements, and cross-references in plain Markdown for human and AI pairing. The current Python standard library implementation (`scripts/llm_wiki.py`) accomplishes this with zero third-party dependencies, sub-second execution, and transparent Git tracking. Introducing an external compiler (Node >= 24) or Rust engine introduces speculative complexity for features (BM25 search, vector embeddings, ACP/MCP daemon servers) that PStack does not currently require.

### 3.2 Six-Host Offline Portability Contract
PStack's built-in host identity registry defines six supported adapters: Grok Build, Codex, OMP, OpenCode, Antigravity, and Droid. Design support must not be confused with observed-live six-host conformance in this decision. Each host runs in varying container, sandbox, or bare-metal configurations. Requiring Node 24+ or Rust toolchains breaks the zero-install baseline and introduces friction for developers in constrained environments.

### 3.3 Mutation Authority and QStack Seams
As established in [PR #878](https://github.com/tommy-ca/pstack/pull/878) and QStack issue #2624, knowledge governance requires unambiguous mutation authority. PStack and QStack rely on Git diffs and explicit review; QStack `knowledge/operations.jsonl` is a governed authoritative operation ledger, whereas PStack `.llm-wiki/log.md` is a human activity journal with no atomic source+event transaction. External compilers that autonomously write to knowledge repositories violate this gate.

### 3.4 Audit Gaps Require a Mainline Patch (Issue #874)
The security audit conducted in S0 identified three concrete issues in `scripts/llm_wiki.py`:
1. Mutable raw source destination on identical basename.
2. Direct non-atomic file writes to `index.md`.
3. Lack of strict path containment checks to prevent `../` traversal or symlink escapes.

These gaps have a previously CI-tested stdlib patch in closed-but-unmerged PR #879. Its base branch was deleted after #878 merged; successor [PR #881](https://github.com/tommy-ca/pstack/pull/881) reapplies those tested files onto current main for independent review. **The decision's mainline did not contain the patch**, and simple symlink preflights do not cover adversarial concurrent directory replacement. No external engine is required to fix these gaps.

---

## 4. Downstream Impact on Issue Graph

1. **Issue #873 (A0):** Resolved and closed by this decision record.
2. **Issue #875 (F2 - Optional upstream engine adapters):** Formally resolved as `not_planned`. No adapter code will be added to PStack core. External candidate producers remain purely conceptual or out-of-tree plugins.
3. **Issue #874 (F1 - Verification and safety hardening):** Authorized to proceed immediately on Option A baseline. Implement raw source overwrite refusal, atomic writes, path confinement, and negative regression tests.
4. **Issue #876 (F3 - Specs, semantic blocks, and wiki navigation):** Authorized to proceed on Option A baseline upon completion of F1.
5. **Issue #877 (V0 - Final verification and acceptance):** Final gate covering F1 and F3.


## 5. Evidence and correctness errata (2026-10-31)

- This ADR made a **design choice**, not a measured, externally reproduced three-way Arena. No equal-corpus upstream benchmark, independent model fanout or side-by-side SDK/binary run is attached. Replace historical `PASS` wording with *design fit* where only source inspection supports a claim.
- The initial Python `ingest_file` used `dest.write_bytes`, and `check_wiki` did not enforce frontmatter types. Closed-but-unmerged #879 cannot be counted as mainline implementation. Its source fixtures and bounded checks are preserved in successor #881.
- `.llm-wiki/log.md` is a human log, not QStack's canonical `knowledge/operations.jsonl` or a transactional ledger. Neither the current nor proposed structural checker proves claim entailment, raw+log atomic durability or all filesystem races.
- Source-pinned requirements, schemas and state invariants from Atomicstrata and Geronimo are recorded in `openspec/changes/2026-10-31-llm-wiki-reference-contracts/`. These are explicit future contracts unless verified against actual runtime code. The binding Option A / deferred Option B decision remains unchanged.
