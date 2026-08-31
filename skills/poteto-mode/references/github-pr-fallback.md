# GitHub-native PR fallback

Use this map when `command -v gt` fails. Detect once per run. Do not invent Graphite. Official playbooks stay Graphite-first. This file rewrites the CLI only.

Bundled `/pr-babysit` is still skipped. `playbooks/babysit.md` stays.

## Detect

```bash
command -v gt
```

If that prints a path, keep using `gt`. If it fails, use the table below for every Graphite call site in the current playbook.

## Call sites

| Playbook says | GitHub native |
|---|---|
| `gt` submit / create a PR | `gh pr create --base <base> --head <branch> --title <title> --body <body>` then `gh pr view <n> --json url,number,baseRefName` |
| Stack follow-ups with Graphite | Independent work: `--base main`. Dependent work: `--base <parent-branch>`. Push the parent first. |
| `gt restack` / `gt sync` | `git fetch origin` and `git rebase` onto the parent branch. Then `gh pr view`. |
| `gt submit --merge-when-ready` | Independent PR targeting protected trunk: `gh pr merge <n> --squash --auto` only after `playbooks/shipping.md` independent verify. |
| `gt merge` | `gh pr merge <n> --squash` after a passing independent-verifier verdict. |
| Graphite UI / stack order | `gh pr list` and `gh pr view <n> --json number,baseRefName,headRefName,url`. |
| `gt track` | No-op. Git already has the branch. |
| CI watch | `gh pr checks <n>` and `gh pr view <n>`. |

Open every PR ready, never draft. If create defaults to draft, `gh pr ready <n>`.

## Do not

- Do not run `gh pr merge --auto` when the PR base is another feature branch. GitHub would merge the child into the parent as soon as checks are green and collapse the stack.
- Do not enable GitHub auto-merge on a stack of PRs. Land bottom-up with one `gh pr merge` per verified PR after its parent is on trunk.
- Do not call `gt` after detect failed.
- Do not switch babysit to bundled `/pr-babysit`.

## Land path without a PR

If the operator's overlay says merge to `main` and SSH-push with no GitHub PR, do that. This map is for playbooks that open or ship PRs.
