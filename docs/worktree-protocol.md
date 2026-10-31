# PStack Worktree Confinement and Consistency Protocol

## 1. Objective and Mandate

To maintain strict repository containment, eliminate accidental data loss during cleanups, and ensure reproducible multi-agent sessions, all git worktrees in PStack must follow this protocol:

1. **Designated Root:** All secondary worktrees must be strictly placed under `<repo_root>/.worktrees/<slug>`.
2. **Zero Arbitrary Workspaces:** Worktrees and agent workspaces must **never** be created at arbitrary external locations (such as `/tmp`, user home directories, sibling folder trees, or uncontained paths).
3. **Traversal and Escape Prevention:** Any path containing `..` or attempting to escape `.worktrees/` via symlinks or relative references is rejected fail-closed.
4. **Automated Enforcement:** Both CI and local tooling (`scripts/worktree_protocol.py`) validate registered worktrees against this protocol.

---

## 2. Directory Layout Contract

```
<pstack-repo-root>/
├── .git/
├── .worktrees/               <-- Strict boundary for all secondary worktrees
│   ├── feat-auth/            <-- Canonical slug for branch feat/auth
│   ├── fix-issue-123/        <-- Canonical slug for branch fix/issue-123
│   └── upstream-cursor/      <-- Pinned reference clones
├── scripts/
│   └── worktree_protocol.py  <-- Protocol verification and lifecycle helper
└── tests/
    └── test_worktree_protocol.py
```

---

## 3. Tooling and Verification

### Check Conformance
To verify that all currently registered worktrees adhere to the protocol:
```bash
python3 scripts/worktree_protocol.py check
```

### Canonical Worktree Path Resolution
To resolve the authorized path for a branch without arbitrary naming:
```bash
python3 scripts/worktree_protocol.py get-path <branch-name>
```

### Confined Creation
To create a worktree guaranteed to reside within `.worktrees/`:
```bash
python3 scripts/worktree_protocol.py add <branch-name> [--base <ref>]
```

### List Confined Worktrees
To enumerate all registered confined worktrees (in text or JSON format):
```bash
python3 scripts/worktree_protocol.py list [--json]
```

### Confined Safe Removal
To remove a worktree strictly verified to reside within `.worktrees/`:
```bash
python3 scripts/worktree_protocol.py remove <branch-or-slug> [--force]
```

---

## 4. Failure Modes and Enforcement

If any worktree is registered outside `<repo_root>/.worktrees/`, `worktree_protocol.py check` immediately fails with exit code `1` and lists the violating worktree path:
```
FAIL: 1 worktree protocol violation(s) found:
  - VIOLATION in worktree [feature at /tmp/external-wt]: Worktree path '/tmp/external-wt' is outside designated worktree root '.../.worktrees'. Arbitrary worktree locations are strictly prohibited.
```
