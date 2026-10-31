# PStack Six-Harness Architecture and Profiles

PStack formally declares six supported host environments with native adapters and truthful evidence reporting:

1. **Grok (`profiles/grok.json`):**
   - Native agent dispatch, subagent fan-out, persistent session tracking.
   - Host catalog in `.grok/`, overlays in `~/.grok/roles/pstack:<role>.toml`.
2. **Codex (`profiles/codex.json`):**
   - Native plugin packaging and role projection.
   - Worktree isolation and execution boundary.
3. **OMP (`profiles/omp.json`):**
   - RPC driver, native lifecycle management (install, update, uninstall).
   - Obsolete managed file pruning on update with path traversal guards.
4. **OpenCode (`profiles/opencode.json`):**
   - Native plugin and schema compliance.
   - Evidence-based status reporting.
5. **Antigravity (`profiles/antigravity.json`):**
   - Native subagent primitives (`invoke_subagent`, `define_subagent`).
   - Reactive messaging wakeups, workspace isolation (`inherit`, `branch`, `share`).
   - Brain artifacts and session transcript preservation.
6. **Droid (`profiles/droid.json`):**
   - Factory plugin projection and tool mapping.
   - Honest advisor routing and packaging.

## Multi-Harness Conformance Contract

- Portable verification lever: `scripts/verify_portable.py`
- Three-plane verification:
  - Canonical plane (schemas, skills layout, inventory)
  - Adapter plane (tool mappings, profile primitives, forbidden markers)
  - Package plane (lifecycle, projections, descriptors)
- Conformance status: static-only vs observed_live. Unobserved native paths remain UNTESTED or GAP.
