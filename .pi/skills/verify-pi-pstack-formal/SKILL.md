---
name: verify-pi-pstack-formal
description: "Maintain bounded source-contract mutation verification for the Pi candidate; no TLC/SMT proof or native child/sandbox correctness is currently claimed."
disable-model-invocation: true
---

# Pi candidate — bounded formal-contract verification

This is the existing project-local `create-formal-verification-skill` / `maintain-formal-verification-skill` artifact. **Current method: exhaustive enumeration of 53 fixed invalid source-contract mutants.** That is a finite source-validator check, *not* a formal proof of Pi execution, sandbox security or a Pi state machine.

## Target and source relation

The verified *source contract* is `scripts/verify_pi_candidate.py::check_contract` and `bounded_negative_controls`, which call existing `scripts/portability_types.py` / `scripts/portability_schema.py` types. Inputs are `skills/setup-pstack/profiles/pstack-pi.json`, its generated `profiles/pstack-pi.json` mirror, `references/pi-essential-extensions.json`, `references/pi-verdict-pstack.example.json` and `.pi/settings.json`. The existing bounded mutation suite must run at the exact HEAD and record the implementation/contract digests; pre-existing results are stale after a code or policy change.

## Bounded properties proved by source tests

1. Reject four false candidate-support promotions.
2. Reject 17 falsely `verified` bindings.
3. Reject 17 duplicate capability bindings.
4. Reject four unsafe candidate configurations (second delegation engine, credential policy, headless allow, automatic unreviewed package installation).
5. Reject one `human.gate` native promotion without proof.
6. Reject ten `pi-verdict` authorization bypass declarations (gate absent/wrong/off, deny-floor off, headless ask bypass, ignored child launch, fallback rescue, claimed child interception, gate disabled, classifier treated as human authorization).

Total **53** enumerated negatives. This establishes ONLY that these invalid JSON mutations are refused by PStack's validator. It does not prove the real Pi extension or the operating system behaves accordingly.

## Native properties requiring a future code-bound formal model

For extension version pins and concrete source locations in the implemented actor code, specify transition invariants: an absent/denied `subagent_launch` never reaches Running; no child widens an inherited policy ceiling; an ambiguous/headless ask never grants mandatory `human.gate`; Cancelled/TimedOut children never become Accepted; join/stop/drain maintain explicit terminal state; no new child launches after drain; `provider/id` selects exactly that provider or fails; retries/restarts cannot double-count proof; worktree/credential effects remain confined.

**These properties have not been formally checked against the actual Pi 1.5.0 + pi-subagents runtime**. Select TLC, SMT or code-level verification only after selecting a small *source-linked* model, declaring bounds/environment assumptions and demonstrating a deliberate broken variant. Do not derive a human-gate proof from pi-verdict's classifier. Pi-subagents v0.87.0 adds relevant drain/provider behavior but remains an unverified candidate upgrade.

## Launch / doctor / drive

- `python3 scripts/verify_pi_candidate.py check` validates source manifest and policy.
- `python3 scripts/verify_pi_candidate.py model` executes the 53 fixed mutations; a rejected mutant means PASS **for the bounded source suite only**.
- `python3 -m pytest -q tests/test_pi_candidate_profile.py tests/test_pi_authorization_contracts.py` exercises the source and false-PASS regression.
- No formal checker is installed or run by this skill; native checker result = **NOT_RUN**.
- Missing required checker/installed Pi = **BLOCKED**. An accepted mutant = FAIL.

## Evidence and maintenance

Record exact source revision, package pins, executed command, exit code, rejection class counts, and the changed source hash. If source/manifest changes, re-run and re-review the model; no copy-forward PASS. Reserve formal VERIFIED for a real checker receipt with version, bounded model, source mapping, counterexample and replay. The current finite test suite is static/contract evidence. It leaves no managed child or workspace to clean.

See [functional Pi feature map](../verify-pi-pstack/features/extension-package.md) and [existing Pi requirements](../../../openspec/changes/2026-11-05-pi-standalone-candidate/specs/pstack-portability/spec.md) for separate runtime-level claims.
