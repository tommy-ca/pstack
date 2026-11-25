# Feature: Staging Pipeline Hardening, Dot-File Invariants, and ADR 0017 Loss Prevention
Epic #1470. Critical thermos findings remediation, symlink write guards, command staging, and ADR 0017 compliance.

## Specs
S1. Enforce dot-directory filtering in skill_names() and unify skill_files() traversal to ignore dot-files and prevent symlink target overwrites in copy_skills() (Issue #1471).
S2. Project commands/*.toml in stage_antigravity_package(), extract shared Antigravity staging helper, and eliminate destructive unmanaged skill wipes in sync_live_plugin() (Issue #1472).
S3. Eliminate dead imports across sync and projection modules, refine exception handling in clean_stale_managed_files(), reconcile backlog in todo.md, and refresh 6-harness static receipts (Issue #1473).

## Tasks
- [x] T1: Harden skill discovery, dot-file filtering, and symlink target safety in package_install_staging.py (linked: S1, route: direct inline, commit: 1df0de8)
- [x] T2: Project commands in stage_antigravity_package, extract shared asset staging helper, and enforce non-destructive sync (linked: S2, route: direct inline, commit: 7a1ad89)
- [ ] T3: Remove dead imports, refine exception handling, reconcile todo.md backlog, and refresh 6-harness static receipts (linked: S3, route: direct inline, commit: pending)

## Log
L1. User requested /swarm /pstack:poteto-mode deep review, thermos audit, Graphicle analysis, SOLID/KISS/DRY/YAGNI check, recursive plan, and shipping stacked PRs. Dual thermos pass identified 8 findings across staging and sync.
