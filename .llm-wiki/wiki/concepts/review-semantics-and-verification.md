# Review Semantics and Verification Discipline

Upstream 0.15.36 introduces rigorous adversarial review and verification contracts across Arena, Interrogate, Autopilot, and principles.

## Arena Semantics (#986)
- Cross-judge pool requires a different model family relative to the coordinator's own model family.
- If a distinct family is unavailable or candidate families cannot be confirmed diverse, Phase C cross-judging is skipped and the coordinator makes the decision directly from runner artifacts.
- No same-model-family judge may masquerade as independent.

## Interrogate Semantics (#986)
- Reviewer findings must include executable reproduction commands and observed vs expected output.
- The lead adjudicator reruns the reproduction command at exact head before upholding a finding as a blocker.
- Reviewer claims that fail closed or cannot be reproduced are marked BLOCKED or dropped rather than accepted blindly.

## Explain-the-Number Principle
- Before measuring performance, latency, or eval numbers, developers must write down the decision and hypothesis.
- If run-to-run variance exceeds the effect size, measurement stops until the benchmark harness is stabilized.

## Verification Tooling Guardrails
- Verification skills (`create-verification-skill`, `maintain-verification-skill`) require executable negative controls and reproducible CLI commands.
- TLA+ formal verification via Statechart requires verified local runtimes; otherwise TLC is run directly and visualization is labeled GAP.
