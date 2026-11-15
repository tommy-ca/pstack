# Pinned Agnix static guard

## Sub-features

Agnix metadata, active skill roots, AGENTS.md, agent definitions, rules, and generic Droid prompt hygiene, plus config anti-suppression.

## How to get to it (user POV)

Run `bash .codex/skills/verify-agnix-pstack/scripts/driver.sh all` in a prepared checkout.

## Driving it with Codex

Run `mise exec -- python scripts/agnix_guard.py`. The checked binary is resolved from the reviewed mise install, not PATH.

## Gotchas

Agnix static lint cannot establish live agent invocation, runtime isolation, or cross-host semantic parity. It does not replace dedicated profile or droid verifiers.
