## 1. Forge-neutral orchestrate

Depends: none. Lane A.

- [x] 1.1 Extend `test_forge_neutral_pr_path_without_graphite` so it reads `playbooks/orchestrate.md` and fails if that playbook requires Graphite `gt` as the frontier source.
- [x] 1.2 Run that test and confirm it fails on the current tree.
- [x] 1.3 Rewrite orchestrate stack-safety onto `references/github-pr-fallback.md` (`origin pr` / `gh pr`, `git rebase` onto the parent branch). Workers still never restack.
- [x] 1.4 Re-run the forge-neutral test and confirm it passes.

## 2. Rhai example

Depends: none. Lane B. Independent of section 1.

- [x] 2.1 Remove `capability_mode` from the `agent()` example in `docs/guide/11-grok-workflows.md`. Keep `agent_type: "pstack:how-explorer"`.
- [x] 2.2 Add a pytest assertion that the example omits `capability_mode` and still names `pstack:how-explorer`.

## 3. Babysit wording

Depends: none. Lane C.

- [x] 3.1 Replace babysit "cloud one plus a local one" with worktree versus shared-cwd babysitters.

## 4. Spec sync and gates

Depends: 1.4, 2.2, 3.1.

- [x] 4.1 Copy the two spec deltas into `openspec/specs/pstack-github-pr-fallback/spec.md` and `openspec/specs/pstack-grok-workflows/spec.md`.
- [x] 4.2 Run `python3 scripts/verify-harness.py`, `uv run --with pytest pytest -q tests/test_verify_harness.py tests/test_release.py`, `grok plugin validate .`, and `openspec validate pstack-forge-neutral-leftover --type change --strict`.
