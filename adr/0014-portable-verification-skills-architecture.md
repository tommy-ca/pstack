# ADR 0014: Portable Verification Skills & Tooling Architecture across 5 Agent Harnesses

## Context

`create-verification-skill` and `maintain-verification-skill` were authored for Grok Build, hardcoding project-local paths to `.grok/skills/verify-<app>/`. With the expansion to 5 harnesses (Grok Build, Codex, OMP, OpenCode, and Antigravity), verification skills must be generated and maintained in the host's native skill directory:
- Grok: `.grok/skills/verify-<app>/`
- Codex: `.codex/skills/verify-<app>/`
- OMP: `.omp/skills/verify-<app>/`
- OpenCode: `.opencode/skills/verify-<app>/`
- Antigravity: `.agents/skills/verify-<app>/`

We conducted an Arena evaluation across 3 architectural candidates:

- **Candidate 1 (Profile-Driven Unified Generator & Scanner):**
  Maintain a single canonical `create-verification-skill` and `maintain-verification-skill`. Resolve the target harness skill directory dynamically from `profiles/<host>.json` (`skills_dir`) or active workspace markers (`.agents/`, `.codex/`, `.omp/`, `.opencode/`, `.grok/`). Provide a deterministic CLI helper `scripts/scaffold-verification-skill.py` that handles scaffolding and multi-harness verification skill detection.
- **Candidate 2 (Per-Harness Dispatched Skills):**
  Fork verification skills into 5 host-specific variants (`verify-skill-grok`, `verify-skill-codex`, etc.).
- **Candidate 3 (Root-Level Generic `skills/verify-<app>/` with Symlinks):**
  Force all harnesses to look at repository root `skills/verify-<app>/` via symlinks or global harness configurations.

## Evaluation & Interrogate Review

- **Candidate 2** was rejected: Violates DRY, Laziness Protocol, and Encode Lessons in Structure. Forking 5 skill variants creates 5x maintenance burden when verification requirements (Launch, Doctor, Drive, Proof Bar, Evidence, Cleanup) are fundamentally identical across hosts.
- **Candidate 3** was rejected: Host harnesses (such as Antigravity and Codex) do not reliably traverse arbitrary root symlinks or non-standard directory structures; Antigravity specifically discovers progressive skills inside `.agents/skills` or installed plugins.
- **Candidate 1** was selected: Keeps one source of truth. Profiles formally declare `skills_dir`. The generator places skills in the active harness directory or accepts `--host <name>`. `maintain-verification-skill` scans across all 5 standard harness directories. `scripts/scaffold-verification-skill.py` provides deterministic programmatic scaffolding for automation and CI verification.

## Decision

1. Bind verification skill directories to `skills_dir` in `profiles/<host>.json`.
2. Update `skills/create-verification-skill/SKILL.md` to document the 5-harness skill directory matrix and resolution order.
3. Update `skills/maintain-verification-skill/SKILL.md` to scan `.agents/skills/verify-*/`, `.codex/skills/verify-*/`, `.omp/skills/verify-*/`, `.opencode/skills/verify-*/`, and `.grok/skills/verify-*/`.
4. Provide `scripts/scaffold-verification-skill.py` supporting `--host`, `--app`, `--write`, and `--check`.
5. Integrate verification skill scaffolding into `scripts/verify-portable.py` 3-plane checks.

## Status

Accepted.
