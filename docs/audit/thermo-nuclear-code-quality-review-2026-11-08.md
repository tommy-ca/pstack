# Thermo-Nuclear Code Quality Review: Summary Report

**Date**: 2026-11-08  
**Scope**: Whole-repo maintainability, dead files, duplication, verification tools, style hygiene, and CI coverage  
**Base Revision**: `main` (`bcfac38`)  
**Verdict**: CONDITIONAL PASS with actionable remediation items  

---

## Executive Summary

A comprehensive thermo-nuclear review was conducted across the PStack codebase.
The review evaluated codebase hygiene, duplicate files, verification tool drivers, frontmatter integrity, and test coverage.
Overall architecture adheres strictly to typed contracts, clean boundaries, and zero Python files exceeding the 1000-line ceiling.
However, four concrete areas require remediation:
1. Obsolete scratch and planning files persist in untracked workspace directories.
2. The Pi verification driver cleanup command violated a fail-closed authorization contract.
3. The `thermo-nuclear-code-quality-review` skill contains style contract violations and lacks frontmatter validation.
4. Eleven fast, hermetic safety tests are omitted from the offline CI workflow.

---

## Detailed Findings Overview

### Finding 1: Ephemeral Scratch Files and Stale Hidden Directories
The `.audit/` directory accumulates ephemeral run files from past sessions that are excluded from git.
Examples include `decisions.tsv`, `explanation.md`, and obsolete issue summaries from October 2026.
Similarly, `.planning/` and `.commandcode/` hold legacy artifacts from earlier experiments.
These files add unnecessary clutter and disk usage.
Remediation: Purge obsolete ephemeral non-evidence files and maintain a clean workspace.
Full details: [01_useless_files_and_duplicates.md](/tmp/pstack-thermo/01_useless_files_and_duplicates.md)

### Finding 2: Pi Candidate Driver Cleanup Authorization Regression
The Pi verification driver `.pi/skills/verify-pi-pstack/scripts/driver.sh` was recently updated with standard verbs.
The `cleanup` verb returned exit code 0 with a static string.
This broke an authorization contract tested by `tests/test_pi_authorization_contracts.py`.
Pi lacks native background process or worktree tracking.
The contract mandates that Pi cleanup must fail closed with exit code 2 and emit an explicit diagnostic message.
Remediation: Restore the exit code 2 fail-closed behavior in both Pi verification drivers.
Full details: [02_pi_driver_and_authorization_contract.md](/tmp/pstack-thermo/02_pi_driver_and_authorization_contract.md)

### Finding 3: Frontmatter Gaps and Style Violations in Thermo Skills
The skill `skills/thermo-nuclear-code-quality-review/SKILL.md` contains long dash characters and mid-sentence colons.
The repository style rules strictly prohibit long dashes and require short declarative sentences.
In addition, `disable-model-invocation: true` was missing from its frontmatter.
`tests/test_thermos_skills.py` tested the other two thermo skills but omitted this one.
Remediation: Cleanse the skill file of style violations, add the frontmatter flag, and expand unit test coverage.
Full details: [03_thermo_skills_and_style_hygiene.md](/tmp/pstack-thermo/03_thermo_skills_and_style_hygiene.md)

### Finding 4: High-Value Hermetic Tests Omitted from Offline CI
Thirty-one test files outside `.github/workflows/portability-offline.yml` pass cleanly in an offline environment.
Key safety tests were not wired into CI, including profile parity and Pi authorization contracts.
Wiring these tests into offline CI prevents regressions from escaping local runs.
Remediation: Wire eleven fast hermetic test files into the portability-offline workflow and update select-checks.
Full details: [04_offline_ci_coverage_expansion.md](/tmp/pstack-thermo/04_offline_ci_coverage_expansion.md)

---

## Proposed Remediation Sequence

We propose executing these remediations via a focused GitHub Epic with four stacked work units:

- **Unit 1**: Restore fail-closed Pi driver cleanup and pass `test_pi_authorization_contracts.py`.
- **Unit 2**: Cleanse `thermo-nuclear-code-quality-review` style violations and add frontmatter test coverage.
- **Unit 3**: Purge obsolete scratch directories and prune non-evidence ephemeral files in `.audit/`.
- **Unit 4**: Wire hermetic safety tests into `portability-offline.yml` and update `select_checks.py`.
- **Unit 5**: Run full multi-harness verification gate and close the Epic.
