# Thermo-Nuclear Code Quality Review: Detail Report 02
## Subsystem: Worktree Audit & Untracked File Hygiene

- **Target Modules**:
  - [`skills/poteto-mode/scripts/worktree-audit.sh`](file:///home/tommyk/projects/pstack/skills/poteto-mode/scripts/worktree-audit.sh)
  - [`scripts/drivers/omp.py`](file:///home/tommyk/projects/pstack/scripts/drivers/omp.py)
  - [`scripts/sync-antigravity-plugin.py`](file:///home/tommyk/projects/pstack/scripts/sync-antigravity-plugin.py)
  - [`scripts/verify-decision-contract.py`](file:///home/tommyk/projects/pstack/scripts/verify-decision-contract.py)
- **Base Revision**: `329acf2`
- **Head Revision**: `0517eb2`
- **Reviewer**: Thermo-Nuclear Code Quality Reviewer
- **Status**: HIGH RISK / LATENT FALSE-PASS DEFECT IDENTIFIED

---

### 1. Concrete Structural Finding: Incomplete Coverage of `-uall` Untracked File Hygiene

In PR #644 (refs #638), `skills/poteto-mode/scripts/worktree-audit.sh` line 135 was hardened by passing `-uall` to `git status --porcelain`:

```bash
# Pass -uall so repository status.showUntrackedFiles=no cannot hide user data.
porcelain=$(git -C "$wt" status --porcelain -uall 2>/dev/null)
```

This prevents user scratch files from being hidden when `git config status.showUntrackedFiles no` is set, avoiding accidental worktree deletion.

However, an exhaustive audit of all `git status` callers across the codebase reveals that multiple critical verification and driver routines still invoke `git status --porcelain` **without `-uall`**.

#### Vulnerable Caller 1: `scripts/drivers/omp.py` Line 143 (`_isolation_residue`)
```python
def _isolation_residue(repo: Path, worktree_base: Path) -> Dict[str, Any]:
    ...
    status_code, status_out = _git(repo, "status", "--porcelain")
    tree_clean = status_code == 0 and not status_out.strip()
```

**Impact**:
When evaluating isolation residue in an OMP driver run, if `repo` has `status.showUntrackedFiles = no` configured:
- If a leaked subagent creates untracked files or directories in the parent repository, `git status --porcelain` returns an empty string.
- `tree_clean` evaluates to `True`.
- The driver reports that parent checkout isolation succeeded even though the parent directory was polluted by the child agent!
- **Verdict**: False PASS on runtime isolation boundary.

#### Vulnerable Caller 2: `scripts/sync-antigravity-plugin.py` Line 287
```python
status = _git(source, "status", "--porcelain", "--", *SYNCED_PATHS)
```

**Impact**:
If untracked files exist in a synced plugin path (for instance, an untracked script or agent definition) and `status.showUntrackedFiles = no` is configured, `status.stdout` will omit the untracked file. Sync may proceed without warning the author that uncommitted files exist in the published surface.

#### Vulnerable Caller 3: `scripts/verify-decision-contract.py` Line 279
```python
["git", "-C", str(root), "status", "--porcelain", "--untracked-files=normal"]
```
Passing `--untracked-files=normal` only shows top-level untracked directory names, rather than every individual untracked leaf (`--untracked-files=all` / `-uall`).

---

### 2. Consumer Reachability Analysis

- `_isolation_residue` in `scripts/drivers/omp.py`: Called by `OmpDriver.drive()` to verify child workspace isolation.
- `sync-antigravity-plugin.py`: Invoked during package lifecycle checks and plugin deployment.
- `verify-decision-contract.py`: Invoked during decision plane contract verification.

---

### 3. "Code Judo" Remedy

Standardize on canonical porcelain status invocations across all python drivers and scripts:
1. In `scripts/drivers/omp.py`: Update `_isolation_residue` to pass `"-uall"`:
   ```python
   status_code, status_out = _git(repo, "status", "--porcelain", "-uall")
   ```
2. In `scripts/sync-antigravity-plugin.py`: Update the dirty check:
   ```python
   status = _git(source, "status", "--porcelain", "-uall", "--", *SYNCED_PATHS)
   ```
3. In `scripts/verify-decision-contract.py`: Pass `"-uall"`.
4. Add regression tests asserting that `_isolation_residue` catches untracked child files even when `status.showUntrackedFiles = no` is configured in `repo`.

#### Behavior Pin
- If untracked files exist anywhere in the monitored tree, `status_out` is non-empty regardless of repo config.
- `tree_clean` is `False` whenever untracked child files exist.
- Clean trees remain `tree_clean: True`.

#### Net Maintained Obligation
Eliminates latent false-pass risks in workspace isolation verification and plugin deployment.
