# Forge-neutral PR operations

Use this map when a playbook needs PR, stack, check, thread, or merge commands. Resolve the forge once per run. GitHub CLI (`gh`) is the default. If `command -v origin` succeeds and Origin can resolve the repository, use `origin pr ...` for every PR operation; otherwise stay on `gh` and record the fallback. Never require Graphite (`gt`).

Bundled `/pr-babysit` is still skipped. `playbooks/babysit.md` stays host-native.

## Resolve

```bash
command -v origin
```

If that prints a path and Origin resolves the repository, keep using `origin pr`. Otherwise use `gh` for the table below.

## Call sites

| Need | Resolved forge |
|---|---|
| Create a PR | `origin pr create --status open --base <base> --head <branch>` or `gh pr create --base <base> --head <branch>` |
| View a PR | `origin pr view <n>` or `gh pr view <n> --json url,number,baseRefName,headRefName` |
| Stack follow-up | Rebase onto the exact parent tip and create or retarget with `--base <parent-branch>`. Independent work uses `--base main`. |
| Rebase or restack | `git fetch origin` and `git rebase` onto the selected parent branch, then view the PR through the resolved forge. |
| Merge one verified PR | `origin pr merge <n> --squash` or `gh pr merge <n> --squash` after a passing independent-verifier verdict. |
| Merge when ready | Root PR targeting protected trunk only: use the selected forge's `--auto` after independent verification and an explicit user request. |
| Stack order | `origin pr list`/`origin pr view` or `gh pr list`/`gh pr view <n> --json number,baseRefName,headRefName,url`. |
| CI and threads | Use `origin pr checks <n>` / `origin pr thread list <n>` or `gh pr checks <n>` / `gh pr view <n>`; Grok wakes use `monitor` and `/loop` → `scheduler_create`. |

Open every PR ready, never draft. With Origin pass `--status open`; with `gh` use the host's ready flag or `gh pr ready <n>`.

## Do not

- Do not run the selected forge's `--auto` when the PR base is another feature branch. That would collapse the stack.
- Do not enable auto-merge on a stack. Land bottom-up with one verified PR at a time after its parent reaches trunk.
- Do not introduce a repository-local watcher or replace Grok `monitor` with a compatibility utility.
- Do not switch babysit to bundled `/pr-babysit`.

## Land path without a PR

If the operator's overlay says merge to `main` and SSH-push with no PR, do that. This map is for playbooks that open or ship PRs.
