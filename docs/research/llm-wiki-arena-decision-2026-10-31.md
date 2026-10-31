# LLM Wiki Reference Engine Arena Decision: Baseline vs Adapters vs Migration

**Document Date:** 2026-10-31  
**Logical Parent:** [Epic #871](https://github.com/tommy-ca/pstack/issues/871)  
**Issue:** [Issue #873](https://github.com/tommy-ca/pstack/issues/873)  
**Status:** BINDING DECISION RECORD  

---

## 1. Executive Summary

Following the comprehensive reference engine architecture audit in [PR #878](https://github.com/tommy-ca/pstack/pull/878) ([`docs/research/llm-wiki-reference-evaluation-2026-10-31.md`](file:///home/tommyk/projects/pstack/docs/research/llm-wiki-reference-evaluation-2026-10-31.md)), this Arena Decision resolves the architecture choice among three candidate topologies for PStack's LLM Wiki:

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
| **Six-Host Portability** | CRITICAL | **PASS** (Zero external dependencies; runs on Linux, macOS, Windows across all 6 supported hosts) | **RISK** (Requires Node >= 24 or cargo/rustc toolchain; breaks zero-install host guarantee) | **FAIL** (Mandatory heavy runtimes break offline CLI and lightweight agent setups) |
| **Cold Start & Latency** | HIGH | **PASS** (< 0.2s startup; pure Python stdlib; instant execution in agent loops) | **MEDIUM** (Node/cargo spawn adds process overhead and IO latency) | **MEDIUM** (Geronimo binary is fast once compiled, but build step is expensive) |
| **Mutation Authority & Safety** | CRITICAL | **PASS** (Exclusive pstack/qstack git authority; no external daemon or rogue CAS updates) | **MEDIUM** (Requires strict candidate containment and unprivileged execution) | **FAIL** (External engine claims publisher/ledger authority; conflicts with QStack governance) |
| **Maintenance Burden (KISS/YAGNI)** | HIGH | **PASS** (Single ~280-line Python script; standard unit tests with pytest) | **FAIL** (Dual-engine maintenance, schema synchronization, and mock harness baggage) | **FAIL** (Full upstream dependency tracking, foreign language tooling, breaking release cycles) |
| **Audit Vulnerability Remediation** | HIGH | **PASS** (Raw source overwrite refusal, atomic write, and path confinement fixed directly in Python) | **MEDIUM** (Fixes Python gaps but adds cross-language bridge attack surface) | **UNKNOWN** (Imports upstream vulnerabilities and external node module supply chains) |
| **Rollback & Data Integrity** | HIGH | **PASS** (Plain Git Markdown files; zero binary database lock-in; trivial diff and rollback) | **PASS** (External indexes remain disposable) | **FAIL** (Complex database migrations and opaque storage layers complicate rollback) |

---

## 3. Detailed Rationale

### 3.1 Adherence to KISS and YAGNI
PStack's LLM Wiki exists to maintain durable project memory, architecture decisions, requirements, and cross-references in plain Markdown for human and AI pairing. The current Python standard library implementation (`scripts/llm_wiki.py`) accomplishes this with zero third-party dependencies, sub-second execution, and transparent Git tracking. Introducing an external compiler (Node >= 24) or Rust engine introduces speculative complexity for features (BM25 search, vector embeddings, ACP/MCP daemon servers) that PStack does not currently require.

### 3.2 Six-Host Offline Portability Contract
PStack guarantees seamless operation across six distinct host environments: Cursor, Windsurf, Claude Code, Grok, Codex, and OpenCode. Each host runs in varying container, sandbox, or bare-metal configurations. Requiring Node 24+ or Rust toolchains breaks the zero-install baseline and introduces friction for developers in constrained environments.

### 3.3 Mutation Authority and QStack Seams
As established in [PR #878](https://github.com/tommy-ca/pstack/pull/878) and QStack issue #2624, knowledge governance requires unambiguous mutation authority. PStack and QStack rely on standard Git commits, PR review gates, and explicit operations logs (`knowledge/operations.jsonl` in QStack, `.llm-wiki/log.md` in PStack). External compilers that autonomously write to knowledge repositories violate this gate.

### 3.4 Audit Gaps are Resolved in Place (Issue #874)
The security audit conducted in S0 identified three concrete issues in `scripts/llm_wiki.py`:
1. Mutable raw source destination on identical basename.
2. Direct non-atomic file writes to `index.md`.
3. Lack of strict path containment checks to prevent `../` traversal or symlink escapes.

All three issues are straightforwardly solved in pure Python stdlib with negative regression tests. None of these gaps justify adopting an external engine.

---

## 4. Downstream Impact on Issue Graph

1. **Issue #873 (A0):** Resolved and closed by this decision record.
2. **Issue #875 (F2 - Optional upstream engine adapters):** Formally resolved as `not_planned`. No adapter code will be added to PStack core. External candidate producers remain purely conceptual or out-of-tree plugins.
3. **Issue #874 (F1 - Verification and safety hardening):** Authorized to proceed immediately on Option A baseline. Implement raw source overwrite refusal, atomic writes, path confinement, and negative regression tests.
4. **Issue #876 (F3 - Specs, semantic blocks, and wiki navigation):** Authorized to proceed on Option A baseline upon completion of F1.
5. **Issue #877 (V0 - Final verification and acceptance):** Final gate covering F1 and F3.
