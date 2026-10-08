# ADR 0018: Verification Skill Scaffolding, Driver Execution, and Maintenance Audit Architecture

## Context

Issue #259 and its sub-issues #260, #261, and #262 identified hardening and synchronization requirements across portable verification skills and scaffolding tools:
1. Test Tier & Evidence Alignment: Verification skills (`create-verification-skill`, `maintain-verification-skill`) lacked explicit integration with the three verification tiers established in `docs/verification-test-tiers.md` (Offline Contract, Host-Dependent Smoke, Observed Live Conformance) and explicit `evidence_level` tagging (`observed_live`, `offline`, `static`).
2. Driver Helper Gap: `create-verification-skill` mandated shipping executable driver helpers in the skill body, but `scripts/scaffold-verification-skill.py` only generated markdown drafts without an executable driver script or `## Helpers` section.
3. Maintenance Automation: `/maintain-verification-skill` required manual validation of feature map index hygiene, four required H2 headings, and sibling references, without an automated audit lever across the six declared harness skill directories.
4. Execution Bounds: Verification drivers lacked bounded execution timeouts (60s limit per subprocess) and failure-first verdict reduction (`FAIL > BLOCKED > UNTESTED > PASS`).

In Issue #260, an Arena evaluation was conducted to decide among three architectural options:

- **Candidate A (Documentation-Only Updates):**
  Update markdown prose in `create-verification-skill/SKILL.md` and `maintain-verification-skill/SKILL.md` without extending scaffolding or verification levers.
- **Candidate B (Synchronized Contract, Executable Driver Scaffolding & Maintenance Audit Lever):**
  Update both verification skills with explicit test tiers, evidence levels, and timeout bounds; extend `scripts/scaffold-verification-skill.py` to scaffold an executable `scripts/driver.sh` and validate `## Helpers`; add `--audit` CLI mode for automated index and section hygiene across all 6 harness directories.
- **Candidate C (Heavyweight Verification Framework):**
  Introduce a specialized test runner framework and runtime daemon for verification skills.

## Evaluation & Interrogate Review

- **Candidate A was rejected**. Violates Build the Lever and Prove It Works. Updating documentation without updating the scaffolding tool immediately introduces drift between the generator's output and documented standards.
- **Candidate C was rejected**. Violates Laziness Protocol, YAGNI, and Foundational Thinking. A heavyweight test harness daemon adds runtime complexity and process friction across diverse agent environments without providing additional behavioral proof.
- **Candidate B was selected**. Minimizes reader load and maximizes portability. Scaffolding an executable driver script with bounded timeouts directly satisfies the helper mandate. Adding `--audit` to `scripts/scaffold-verification-skill.py` automates the hygiene checks for `/maintain-verification-skill` across all six declared harnesses (`.agents/`, `.codex/`, `.omp/`, `.opencode/`, `.grok/`, `.factory/`) while remaining completely offline-testable.

## Decision

1. Update `skills/create-verification-skill/SKILL.md` and `skills/maintain-verification-skill/SKILL.md` to formally document the 3 verification test tiers, `evidence_level` tagging, 60s bounded command execution, and the `FAIL > BLOCKED > UNTESTED > PASS` reduction lattice.
2. Extend `scripts/scaffold-verification-skill.py` to scaffold an executable `scripts/driver.sh` helper alongside `SKILL.md` and feature maps.
3. Add `## Helpers` to `REQUIRED_SECTIONS` and generated `SKILL.md` in `scripts/scaffold-verification-skill.py`.
4. Add `--audit` mode to `scripts/scaffold-verification-skill.py` to automate feature map hygiene, ordered sweep validation, and required section checks across all six declared harness skill directories.
5. Reconcile verifier constants and durability test suites to test all six declared harnesses uniformly.

## Status

Accepted.
