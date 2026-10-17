# JEV provider options — verified access and integration boundaries

> Status: research / design only (2026-10-17). This file does not implement a live network adapter, grant model/skill execution authority, or verify entitlement. See PStack #515/#519/#520/#521, QStack #1786/#1789/#1791.
> Source baseline: pstack main audited at 3f06c934d17fb0fc05b0cd093ff838fa068a6699; refresh exact SHA before implementing. Provider catalogs, free-tier availability, and pricing are dynamic.

## 1. The source-grounded service distinction

| Service | JEV model ID | API endpoint | Access/pricing as published | Supported inference protocol |
| --- | --- | --- | --- | --- |
| OpenCode Console (formerly Zen) | `jev-1.13-free` | `https://opencode.ai/inference/systemone/v1/systemone` | Free **for a limited time**; availability/limits not guaranteed | TypeSafe-style System One |
| OpenCode Console | `jev-1.13` | Same System One endpoint | $0.042/M input tokens; zero listed output price | TypeSafe-style System One |
| OpenRouter | `typesafe/jev-1.13` | `https://openrouter.ai/api/alpha/decisions` | $0.042/M input tokens; $0/M output | OpenRouter Decisions API (alpha) |
| OpenRouter | `typesafe/jev-1.14` | Same Decisions API | $0.042/M input tokens; $0/M output; latest pinned listed version as of 2026-10-17 | OpenRouter Decisions API (alpha) |
| OpenRouter | `~typesafe/jev-latest` | Same Decisions API | Mutable alias and billable; verify resolved model snapshot | OpenRouter Decisions API |
| Direct TypeSafe | provider-chosen, verified at runtime | Per official TypeSafe API/SDK | Consult TypeSafe current plan; no assumed free entitlement | System One native |
| OpenCode **Go / Go Plus** | **No JEV entry in current Go catalog** | Go coding-model endpoints are NOT the JEV endpoint | Subscription $10 / $40 per month for listed coding models | Not an eligible JEV decision provider at this snapshot |

Primary sources:
- OpenCode Console models, pricing, JEV System One example, and limited-time qualifier: https://opencode.ai/v2/docs/console/models/
- OpenCode Go and its distinct model list/subscription: https://opencode.ai/v2/docs/console/go/
- OpenRouter JEV 1.14 listing: https://openrouter.ai/typesafe/jev-1.14
- OpenRouter Decisions API example: https://openrouter.ai/blog/insights/what-is-jev/
- TypeSafe typed System One SDK reference: https://github.com/typesafe-ai/typesafe-sdk-python

**Important:** OpenCode Console JEV free access does not imply that a $10/$40 OpenCode Go subscription includes JEV, and the zero *output* price on OpenRouter does **not** make requests free. None of the hosted Jev models are generative coding workers. Use host-model catalog/capabilities separately for `/setup-pstack` worker/Swarm/Arena/Interrogate roles.

## 2. Keep a single semantic contract and narrow provider I/O

Existing owners: `scripts/decision_adapter.py` exposes `SemanticDecisionProvider.decide(request)`, `DecisionOutcome`, and `ProviderObservation`; `scripts/route_resolver.py` owns deterministic/semantic route precedence; `openspec/specs/pstack-jev-decisions/spec.md` owns bounded egress, mapping, and controlling eligibility. **Do not** introduce a second generic router, an OpenCode-specific execution-policy fork, a model gateway framework, or provider wire types into shared PStack core.

Implementation candidates:
1. `PSTACK_JEV_MODE=none|shadow|advisory` remains OFF by default. Operators choose one configured, currently authorized provider/model. Disabled/unsafe/unknown inputs always use the precomputed baseline route.
2. OpenCode Console adapter authenticates with `OPENCODE_API_KEY`, uses `https://opencode.ai/inference/systemone/v1/systemone` and a body with `model`, `state`, `questions`. Free model is `jev-1.13-free`; paid `jev-1.13` requires separate explicit billing approval and bounded budget. Avoid using a Go endpoint or a generic chat-completions client for JEV.
3. OpenRouter adapter authenticates with `OPENROUTER_API_KEY`, sends the same semantic `state` and typed `questions` to `https://openrouter.ai/api/alpha/decisions`, explicitly names model `typesafe/jev-1.14` or pinned 1.13, and normalizes the Decisions API response. OpenRouter's `/api/v1/chat/completions` is NOT the correct JEV interface.
4. Direct TypeSafe transport may remain a third option under #515, depending on measured value. Never require three separate adapters unless observed wire differences justify them; one tiny transport/config switch plus a proven normalizer may be sufficient. All provider behavior stays behind the existing neutral interface.
5. Parse choice keyed by option ID (not list order); validate full question IDs, selected member, probabilities, confidence, requested model versus returned resolved model, usage/cost, and provider identity where returned. For `noul`, use probability, not a fictional universal confidence field. `score` should validate levels/legend. Reject unknown/mismatched shapes to existing `invalid`/`unavailable` outcome.
6. Existing conservative egress ceiling (2,048 UTF-8 state bytes, max 32 choices, max 8,192 total request bytes) and provenance controls remain enforceable. Do not send proprietary repo diffs, secrets, logs, model transcripts, raw code or config to free or paid services.

## 3. Free-first is a cost policy, not implicit billing consent

Use a declarative allowlist (or equivalent direct settings), NOT an auto-discovered unbounded routing engine:

```text
mode: none (default) / shadow / advisory
allowed_jev_endpoints: []                     # closed list, explicit opt-in
primary (evaluation-only): opencode-console/jev-1.13-free
paid_fallback: disabled (default)
paid_fallback (explicit opt-in): openrouter/typesafe/jev-1.14
paid_spend_limit_usd: explicitly operator-set
```

Provider outage, free tier retired, expired credits, 401/402/403/429, missing key, timeout, malformed output, source/policy/model drift, or overbudget => **baseline route**, never silent charged calls. If several providers are explicitly approved, a fallback provider may run only within that declared plan and budget. Do not assume server-side model aliases are stable.

## 4. Verification and promotion

- Offline hermetic fake transport first: same frozen public input, identical PStack choice semantics, provider-specific request/response mapping, authentication header isolation, malformed responses, free-retirement control, no-key and timeout. Prove no unauthorized calls or state changes.
- Version-equivalent parity: OpenCode Console `jev-1.13` vs OpenRouter `typesafe/jev-1.13` before comparing latest 1.14. JEV 1.13 vs 1.14 quality cannot be attributed solely to provider routing.
- Keep per-class calibrated thresholds (living spec requirement, corrective #516), not one global `0.70` controlling threshold. A model/provider version change invalidates stale confidence evidence.
- Run opt-in authenticated smoke with a *public sanitized fixture* only. Capture provider endpoint and resolved model, request/response id where available, SHA, cost, latency, class policy version, and test command; no API keys or raw private context. Without credentials: `BLOCKED/NOT EXECUTED`, not PASS.
- Benchmark whole task costs and p50/p95 wall time versus no-JEV deterministic PStack baseline. Do not declare savings because token price is low without measuring.
- Keep QStack quant-domain and qorch/runtime safety unchanged; JEV must never approve trading risk, order routing, holdout data, research promotion, or capital enable.
- Independent actual Swarm/Arena/Interrogate receipts required for promotion; author-written scenario analysis is not independent multi-model verification.

## 5. Work graph / issue ownership

- PStack #515: native TypeSafe real transport (direct); #516: per-class calibration; #517: experimental fast-role/model-fit research.
- PStack #519: OpenCode Console/Zen JEV 1.13 Free (and explicit paid variant).
- PStack #520: OpenRouter JEV 1.14/1.13 Decisions API with explicit billing.
- PStack #521: consent, safe free-first fallback, parity, rollback and provider-independent exact-head acceptance.
- QStack #1786 parent, #1789 PStack host conformance, #1791 incremental quant/task-fit eval, #1792 independent acceptance.

Promotion is optional: keeping the existing deterministic PStack router unchanged is a valid outcome if JEV provides no measured benefit.