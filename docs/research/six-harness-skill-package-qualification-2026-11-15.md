# Six-Harness Skill Package and Evidence Gates Qualification (2026-11-15)

## Executive Summary

Parent #1383. Resolves #1389.
This document qualifies the Agent Skills specification compliance package across PStack's six declared host environments.
The evaluation covers canonical skills, host-local skills, automation skills, verification drivers, formal contracts, and evidence receipts.
All checks enforce the strict truthfulness contract.
Offline checks are green.
Static receipts are revision-bound.
Native host runs remain UNTESTED where executable credentials are absent.
No static analysis or mock agent execution is labeled as live Swarm, Arena, or Interrogate proof.

## Cryptographic Revision Hashes and Exact Head

The qualification binds to the current Git tree.
The canonical surface hashes recorded in `.audit/evidence/index.json` are:
- `canonical_pin`: `bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7`.
- `spec_hash`: `6a40100eb2d2a576dd4e3a1619fa7b6767c3ee85a839c1ab0c756d1061ba8f6c`.
- `skills_tree_hash`: `6a616a5630d8da6f5a073b2a2d3ba50798f5a596d42a28799f99bf7a456d98bb`.
- `package_descriptor_hash`: `a5168007056331f892900921c75b4e11d7cb9e911ebce776db20eaf91810397f`.
- `driver_revision`: `4361266fa8a05f62124f273dfa120cd48a6aeeec86c1f694ec027e25d39a790c`.
- `package_driver_revision`: `2e0b0c872b16d7db80b3e885b85b93db9f5db2c7e68d54e7fb80258a2b60976b`.
- `boundary_driver_revision`: `ded4475d707124d6db00167347a2a7217255f3b55e689b647f716617e79a82eb`.

## Six-Harness Evidence Status Matrix

The durable receipts in `.audit/evidence/` reflect current reality:

| Host | Support State | Canonical Plane | Adapter Plane | Package Plane | Runtime Plane | Overall Verdict | Freshness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Grok | Packaged | PASS | PASS | PASS | UNTESTED | UNTESTED | FRESH |
| Codex | Packaged | PASS | PASS | PASS | UNTESTED | UNTESTED | FRESH |
| OMP | Packaged | PASS | PASS | PASS | PASS | PASS | FRESH |
| OpenCode | Packaged | PASS | PASS | PASS | UNTESTED | UNTESTED | FRESH |
| Antigravity | Packaged | PASS | PASS | PASS | UNTESTED | UNTESTED | FRESH |
| Droid | Candidate | NOT_COVERED | NOT_COVERED | NOT_COVERED | NOT_COVERED | NOT_COVERED | FRESH |

OMP runtime retains observed live settlements:
- `runtime-child-spawn-omp`
- `runtime-child-cancel-omp`
- `runtime-isolation-omp`

All other hosts truthfully report UNTESTED runtime plane.
Running `python3 scripts/verify_portable.py check-staleness --host all` confirms ALL FRESH across all six hosts.

## Package Sync and Manifest Validation

Manifest projection check via `python3 scripts/project_package.py --check`:
- Grok manifest `.grok-plugin/plugin.json`: PASS.
- Codex manifest `.codex-plugin/plugin.json` and `models.json`: PASS.
- OMP manifest `.omp-plugin/package.json`: PASS.
- OpenCode manifest `.opencode-plugin/package.json`: PASS.
- Antigravity manifest `.antigravity-plugin/plugin.json`, `models.json`, and 21 commands: PASS.
- Droid manifest `.factory-plugin/plugin.json`, `marketplace.json`, and 22 roles: PASS.
- Pi package `.pi/package.json`: PASS.
- Zero drift between canonical `pstack.package.json` and host projections.

## Offline Contract and Negative Control Suites

1. `tests/test_scaffold_verification_skill.py`: 131 passed.
Includes negative control mutation tests:
- Missing coverage section.
- Missing model choice section.
- Missing code-under-test pin.
- Missing property or invariant declaration.
- Missing state or input bound declaration.
- Missing bounded exploration versus unbounded proof distinction.
- Missing deliberate failing mutant or counterexample.
- Missing failure-first verdict lattice.
- Missing effect-level receipt or exit code.
- Missing isolated scratch behavior declaration.
- Driver missing doctor, drive, cleanup, or all command.
- Driver missing 60-second timeout bound.

2. `tests/test_skill_frontmatter.py`: 67 passed.
Validates all 84 Agent Skills across 10 declared roots.
Enforces name, description, compatibility, allowed-tools, and nested duplicate key rejection.

3. `scripts/verify_harness.py`: PASS.
Validates 22 named playbooks, 24 principles, and root plugin descriptor.

4. `scripts/worktree_protocol.py check`: PASS.
Validates worktree confinement.

5. `scripts/scaffold_verification_skill.py --audit`: PASS.
Validates 10 verification skills across all hosts.

6. `scripts/llm_wiki.py check` & `verify-sources`: PASS.
Validates structural integrity, cryptographic digests, and bidirectional graph connectivity.

## Truthful Verification Rule

A structural PASS is not a runtime PASS.
A bounded model is not an unbounded proof.
A static source inspection is not a live Swarm or Arena execution.
Verdicts reduce strictly using FAIL > BLOCKED > UNTESTED > PASS.
This matrix closes Unit 6 and finalizes Epic #1383.
