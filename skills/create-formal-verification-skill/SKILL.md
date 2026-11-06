---
name: create-formal-verification-skill
description: "Generate a project-local skill that formally verifies the code where a bug costs the most and tests reach the least, in any language, with whichever verification tool fits. Use for /create-formal-verification-skill, \"model-check this race\", \"prove this invariant\", or when concurrency, retries, state machines, parsers, or unsafe code need more than tests."
disable-model-invocation: true
---

# Create a formal verification skill

A test checks the cases that someone thought to write. Formal verification checks every case in a stated scope: every order of steps in a model, every input up to a bound, or every input. This skill finds the part of the repo where that matters most, verifies one property of it, and leaves a project-local skill that lets the next agent check a change against that property. Write that skill for an agent who reads it cold, mid-change, and has never seen your work. The user must be able to trust the result and act on it without learning the verification language.

Project-local formal verification skills live under the active harness's native skills directory (`skills_dir` in `skills/setup-pstack/profiles/<host>.json` or repository `profiles/<host>.json`, resolved canonically via `scripts.setup_pstack.resolve_profiles_dir`). Formal verification skill directories and frontmatter use the naming convention `verify-<app>-formal` (or `verify-<property>-formal`).

Use `scripts/scaffold_verification_skill.py --formal --host <host> --app <app> --write` to scaffold a draft at `<skills-dir>/verify-<app>-formal/`. The generator creates `SKILL.md`, `features/README.md`, `features/formal-model.md`, and an executable driver script at `scripts/driver.sh`. Run `scripts/scaffold_verification_skill.py --check --target-dir <skill-dir>` for Tier 1 structural validation.

## Why not a wiki

A wiki is for humans. Agents pay for every token they reread. Write a skill plus a feature map. Use one short file per verified sub-property or model aspect, the same four H2s, and a README that is the sweep order. Keep the map next to the skill at `features/`. Do not grow it into a wiki. Do not put drive recipes in OpenSpec. `openspec/specs` is capability Gherkin, not a formal drive recipe.

## 1. Interview the repo, not the user

Answer these from the codebase and only ask the user what you cannot observe:

- **Target:** what promise does the code make where a break harms users and tests rarely reach it? Concurrency races, distributed retries, state machine deadlocks, parsers, cryptographic handshakes, or resource allocation lifecycles.
- **Tool:** pick the tool that answers the question at the lowest cost:
  - Event order, race conditions, or interleavings: model checkers (TLA+ TLC, Spin).
  - Code-level input domain invariants or memory safety: bounded model exploration or SMT-backed verification (Z3, Kani, Creusot).
  - If no external formal tool fits or installs cleanly: implement an exhaustive bounded finite-state exploration directly against real production code.
- **Observe:** what counterexample trace or invariant violation can be captured? Sequence of steps in the code's terms, minimal failing inputs, violated assertions.
- **Isolate:** formal checks and bounded model runs must execute in isolated scratch environments (`TemporaryDirectory`, `mktemp -d`) with zero persistent side effects.

If the target code does not build or run, report that first before generating. A formal verification skill written against broken code encodes invalid invariants.

## 2. Generate the formal verify skill

Write `SKILL.md` at `<skills-dir>/verify-<app>-formal/` with YAML frontmatter:

- `name: verify-<app>-formal`
- `description`: Use-when triggers only. Name the verified invariant, the code surface, and when to reach for the skill.
- `disable-model-invocation: true`

Keep the generated skill body under 24,000 bytes. Google Antigravity imposes a strict 24,000-byte body limit and truncates oversized skills. `scripts/scaffold_verification_skill.py --check` enforces this bound.

Without frontmatter the skill never registers. To satisfy structural verification standards (`scripts/scaffold_verification_skill.py --check`), write the following required sections:

- **Coverage and sync record:** specify the covered production commit, target code files/functions, the safety and liveness invariants, the finite bound, and the rule for moving the sync commit forward.
- **Model and checker choice:** explain the chosen formal tool, the modeling assumptions, what is abstracted away, and the deliberate broken mutant used as a negative control.
- **Launch:** prepare any dependencies, model files, or scratch environments. For bounded real-code models, launch confirms the environment is ready.
- **Doctor:** one read-only check confirming checker tooling (e.g. Java/TLC jar, SMT solver, Python test harness) is present. If the checker tool is missing, report `BLOCKED` or `UNTESTED`; never report a PASS on an unexecuted model.
- **Drive:** exact command line to run the formal verification and bounded model suite.
- **Proof bar:** every claimed invariant holds across the stated bound. A negative mutant (e.g. removed check or reordered step) MUST fail. Reduce verdicts using the failure-first lattice: FAIL > BLOCKED > UNTESTED > PASS.
- **Evidence:** capture stdout, counterexample traces, state space size, and git revision. Distinguish offline finite trace proof from live host observation.
- **Cleanup:** tear down any temporary files or scratch directories. Ensure no processes linger.
- **Helpers:** reference the driver script at `scripts/driver.sh`. Make it executable. The driver must support `doctor`, `drive`, `cleanup`, and `all`.

## Architectural Discipline: SOLID, KISS, DRY, YAGNI

Formal verification skills and feature maps must follow strict design hygiene:

- **Single Responsibility (SRP):** Each formal skill verifies one cohesive property or state machine. Each feature file in `features/` models one specific sub-property or trace scenario. The driver script handles only execution orchestration (`doctor`, `drive`, `cleanup`).
- **Open/Closed (OCP):** Extend coverage to additional invariants by adding sibling feature files under `features/` and updating the Full sweep order, without destabilizing core driver execution.
- **Liskov Substitution (LSP):** Formal verification drivers across all harnesses conform to the uniform command contract: `doctor`, `drive`, `cleanup`, and `all`. Any test runner can invoke them interchangeably.
- **Interface Segregation (ISP):** Separate high-level abstract models (e.g. TLA+) from concrete bounded code-level falsifiers. Agents execute specific bounded checks independently.
- **Dependency Inversion (DIP):** Depend on stable code contracts, state transitions, and public entry points rather than private ephemeral variables.
- **KISS & YAGNI:** Prefer bounded real-code exploration and concise models over speculative full-system theorem proving when a bounded check proves the invariant.
- **DRY:** Define the sync commit, covered functions, and property statements canonically once in `SKILL.md`.

## Bounded Negative Controls & Failure-First Lattice

A formal check that has never been seen to fail proves nothing. Always provide an explicit negative mutant:

- **Mutation:** introduce a deliberate break in the property or a broken variant of the code it guards (e.g. removed lock, inverted condition, reordered callback).
- **Rejection:** the check MUST reject the mutant and produce a counterexample. If the mutant passes, the verification is flawed.
- **Verdict Lattice:** reduce all verification outcomes with the strict failure-first lattice:
  `FAIL > BLOCKED > UNTESTED > PASS`
  A failed invariant or accepted mutant is FAIL. An unavailable tool or unfulfilled precondition is BLOCKED. An unexecuted model is UNTESTED. Never fabricate or assume a PASS.

## TLA+ Result Interpretation on this Port

If the selected checker is TLA+ TLC, resolve `statechart` through the active host's capability profile:
- Official Cursor PStack 0.15.36 provides `/statechart` for shortest invariant counterexample paths, but this port does not ship that compiler until #847 establishes its dependencies, security checks and host bindings.
- When absent, run TLC directly with the pinned model/config, preserve logs and replay the counterexample against the real code. Record visualization as `GAP`; do not convert absent rendering into a PASS or stop checking the real property.
- For missing Java/TLC, report `BLOCKED`, never a model proof.

## Seed the Feature Map

Create `features/README.md` plus at least one feature markdown file (e.g. `features/formal-model.md`).
- Follow the shape in `skills/create-verification-skill/references/feature-map-example/`.
- `features/README.md` must contain `## Full sweep` and `## Features` listing all sibling markdown files in sweep order.
- Each feature file must contain exactly four H2 sections in order:
  1. `## Sub-features`
  2. `## How to get to it (user POV)`
  3. `## Driving it with <harness>`
  4. `## Gotchas`

## Prove It Before Handoff

Follow the generated skill once, as the next agent would, on a scratch change that breaks the property in real code. Confirm that it catches the break. Drop the scratch change and verify that the check returns to PASS (or flags pre-existing findings).
Tell the user what you verified, which tool was used, the bounds, what the check found in plain words, and how to run it. Point the user to `/maintain-formal-verification-skill` for subsequent code synchronization.
