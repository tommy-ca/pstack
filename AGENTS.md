# AGENTS.md

- For OpenSpec propose, apply, verify, and archive workflows, use the local `openspec-git-discipline` skill. It enforces proposal commits before apply and merge-before-archive discipline.
- Follow poteto-mode for planning before coding.
- Verify work with lever proofs across all declared harnesses.
- Follow SOLID, KISS, DRY, and YAGNI principles on every change.
- For changes to Agent Skills, agent definitions, AGENTS.md or harness rules/configs, run the pinned read-only Agnix guard (`mise run verify:agnix:policy`, then `mise run verify:agnix` when installed). This proves static configuration only; continue to require behavioral and formal evidence separately.
