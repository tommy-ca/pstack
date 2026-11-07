---
name: maintain-formal-verification-skill
description: "Bring a project's formal verification back in line with the code after the code changes: find the commits that touched verified code, update the model, harness, or properties to describe the code as it is now, rerun, and say whether each failure is drift in the verification or a bug in the code. Use for /maintain-formal-verification-skill, \"is the model still true to the code\", or after merges and refactors that touched verified code without rechecking it."
disable-model-invocation: true
---

# Maintain a formal verification skill

A formal check proves a property of what it describes. When the code changes and the verification does not, the check can keep passing while it describes code that no longer exists. That pass is the dangerous case, because it looks like a proof. This skill is the upkeep loop for a verify skill that `/create-formal-verification-skill` generated, or for any project-local skill that runs a model checker, prover, or code-level verifier against named code. The project-local skill handles a change that an agent makes while it uses that skill. This skill handles the changes that skipped it: merges, edits made without the skill, and drift that builds up across many commits.

## Outcomes

Give each check one outcome, and say which:

- **in sync**: no change since the last sync alters what the check describes, and the check passes.
- **updated**: the code changed, the verification now describes the new code, and the check passes.
- **bug**: the verification describes the current code, and the code breaks the property. This is a finding about the code. It is not drift.
- **blocked**: the check could not be brought back in line or could not run. Say exactly why.

A check can be both updated and bug: the update makes the verification describe the code again, and then the property fails on it.

## Edit scope

Edit only the verification: models, harnesses, property files, feature maps under `features/`, driver scripts, and the verify skill `SKILL.md` itself. Never edit product code during a maintenance run, unless the user asks you to. When a property fails on the current code, do not weaken the property or the model to make it pass. Report the failure.

Keep the skill body under 24,000 bytes to preserve Antigravity compatibility.

## Upkeep Pass

1. **Find the checks.**
   Locate project-local formal skills (`verify-*-formal` or named formal checkers) in the active harness's native skills directory (`skills_dir` in `skills/setup-pstack/profiles/<host>.json` or repository `profiles/<host>.json`, resolved canonically via `scripts.setup_pstack.resolve_profiles_dir`). Read each one found. Collect the covered code paths, the property, the bounds, the command, the feature map in `features/`, and the commit where it was last confirmed to describe the code. If no verify skill exists, stop and point at `/create-formal-verification-skill`.

2. **Run it as it is.**
   Run the verification driver (`./scripts/driver.sh all` or the documented drive command) before changing anything. A pass here does not mean the code is correct; it means the old description holds or passes trivially. A failure can be drift or a real regression.

3. **Read every change to covered code.**
   Diff the covered files from the sync commit to the current commit (`git diff <sync-commit>..HEAD -- <covered-paths>`). Review commit messages and investigate structural movements (renamed functions, split files, new callers reaching the guarded state). Classify each change:
   - **No effect:** formatting, comments, or unmodeled helper paths.
   - **Verification no longer describes the code:** an atomic step was split, a branch added/removed, state variables modified, or bounds altered. The model or harness must change.
   - **Promise changed on purpose:** intentional API or behavior update supported by commit messages or tests. The property must be updated, citing that evidence.
   - **Promise broken:** code changed without intent to alter the invariant. A failure is a bug candidate.

4. **Update from the code, not from the result.**
   Update the model, bounded test harness, feature map, and driver so that each changed part again corresponds directly to real code. Do not shape the update to force a pass. Change properties only when intentional evidence warrants it. Record old wording, new wording, and rationale.

5. **Rerun and judge each result.**
   - **Pass:** confirm the check has not lost the ability to fail. Introduce a deliberate break in the property or code mutant (e.g. removed check or inverted branch) and verify that the checker flags it. Then revert the break.
   - **Fail:** replay the counterexample trace against the real code. If the check is a TLA+ model, visualize the trace with the pstack `/statechart` skill to locate the shortest path to the invariant violation. If impossible in the code, fix the model. If reproducible, report it as a bug with the introducing commit, minimal step sequence, and harm statement. Reduce verdicts using the failure-first lattice: FAIL > BLOCKED > UNTESTED > PASS.

6. **Update the verify skill.**
   Update `SKILL.md`: refresh covered files, bounds, assumptions, feature maps, driver references, and the sync commit. Set the sync commit to the commit that was checked. Never advance the sync commit for a blocked check. Ensure the 7 required sections (`Launch`, `Doctor`, `Drive`, `Proof bar`, `Evidence`, `Cleanup`, `Helpers`) and the feature map (`features/README.md`) remain structurally valid. Run `scripts/scaffold_verification_skill.py --check --target-dir <skill-dir>`.

## Architectural Discipline: SOLID, KISS, DRY, YAGNI

Maintenance must preserve structural cleanliness:

- **Single Responsibility (SRP):** Maintain clean separation between the formal specification/model and the execution driver.
- **Open/Closed (OCP):** Add new invariants or sub-features as new markdown files in `features/` without mutating existing verified flows.
- **Liskov Substitution (LSP):** Maintain uniform driver interfaces (`doctor`, `drive`, `cleanup`, `all`) across updates.
- **Interface Segregation (ISP):** Keep abstract provers and bounded code-level falsifiers decoupled.
- **Dependency Inversion (DIP):** Anchor formal models to public invariants, not brittle private implementation details.
- **KISS & YAGNI:** Avoid adding speculative state variables or complex proof branches not necessitated by the target code.
- **DRY:** Ensure properties, bounds, and sync commits are defined canonically once in `SKILL.md`.

## Report

Tell the user, for each check:
- The outcome (`in sync`, `updated`, `bug`, or `blocked`) and the evaluated commits.
- What changed in the verification and why (code drift or intentional promise change with citations).
- The rerun result, including the negative mutant used to demonstrate that the check can still fail.
- Each bug found in plain language: counterexample steps, introducing commit, and user harm.
- Any remaining unverified areas or gaps.

Put verification updates in a standalone commit separate from any product code changes.
