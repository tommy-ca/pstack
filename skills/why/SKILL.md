---
name: why
description: "Use for 'why does X work this way', 'why we picked Y', design rationale, regressions, postmortems, or data-backed thresholds. Returns a cited read on decisions and tradeoffs. Use how for runtime behavior."
disable-model-invocation: true
---

# Why

Answer from the record, not the code: read the commits and PR discussions that introduced the target and each later change, and other sources if the trail is thin. Cite what the authors wrote, mark your own inferences as inferences, and say what the record does not answer.

For multi-source investigations spanning issue trackers, documents, observability, or error traces, discover available MCP evidence sources and spawn parallel investigators using role `why-investigators` (`subagent_type: "pstack:why-investigators"`). Synthesize citations and confidence with role `why-synthesizer` (`subagent_type: "pstack:why-synthesizer"`).
