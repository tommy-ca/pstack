# Bounded Driver Core Disk Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse AST-normalized driver cores across verifier subprocesses with an optional bounded disk cache while preserving all revision and error behavior.

**Architecture:** Extend `_driver_core(path, src)` after its existing process-local memo lookup. The disk layer is a best-effort cache of one derived core; source reads and revision folding remain unchanged. Cache records are versioned JSON and private to the user; misses, corruption, or I/O failures fall through to the existing parse path.

**Tech Stack:** Python standard library (`hashlib`, `json`, `base64`, `os`, `stat`, `sys`, `tempfile`, `pathlib`), pytest, existing frozen durability harness.

## Global Constraints

- No new dependencies.
- Keep `_driver_core(path: Path, src: bytes) -> bytes` and caller contracts unchanged.
- Preserve `RecipeError` for invalid UTF-8 or syntax; never cache a failed parse.
- Preserve basename-sensitive published module docstrings.
- Always hash current source bytes; never cache whole `SurfaceRevisions` or bundles.
- Cache is disposable and non-authoritative: filesystem failures must not alter correctness.
- Use unique same-directory temporary files and `os.replace`; no cross-process lock.
- Bound cache storage to 256 records and 32 MiB; the frozen suite must improve by >=5% beyond the measured baseline noise.

---

### Task 1: Add black-box cross-process cache contracts

**Files:**
- Modify: `tests/test_evidence_durability.py` near `test_driver_core_is_memoised_by_content_not_by_location`
- Read-only reference: `scripts/portability_schema.py`, `_driver_core`, `_update_driver_digest`, and `compute_surface_revisions`

**Interfaces:**
- The persistence test consumes `_disposable_copy(tmp_path)`, `ROOT`, `subprocess`, and `compute_surface_revisions` behavior.
- The basename test invokes `_driver_core` in independent Python processes using identical bytes under a published-doc basename and an ordinary basename.
- Both require real versioned cache records; the persistence test also corrupts a record, and a third test verifies an unavailable cache path preserves the normalized core.

- [x] **Step 1: Write the failing tests**

```python
def test_driver_core_disk_cache_persists_and_tracks_source_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy_root = _disposable_copy(tmp_path)
    cache_home = tmp_path / "cache-home"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    driver = copy_root / "scripts" / "drivers" / "base.py"
    program = (
        "import sys; from pathlib import Path; "
        "from scripts.portability_schema import compute_surface_revisions; "
        "print(compute_surface_revisions(Path(sys.argv[1]), 'grok').driver_revision)"
    )

    def run_revision() -> str:
        proc = subprocess.run(
            [sys.executable, "-c", program, str(copy_root)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return proc.stdout.strip()

    first = run_revision()
    cache_dir = cache_home / "pstack" / "driver-core"
    assert list(cache_dir.glob("*.json"))
    assert run_revision() == first

    driver.write_bytes(driver.read_bytes() + b"\nCACHE_PROBE = 'changed'\n")
    assert run_revision() != first


def test_driver_core_disk_cache_keeps_published_docs_basename_sensitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache_home = tmp_path / "cache-home"
    monkeypatch.setenv("XDG_CACHE_HOME", str(cache_home))
    source = tmp_path / "same-source.py"
    source.write_bytes(b'"""published docs"""\ndef probe():\n    return 1\n')
    program = (
        "import json, sys; from pathlib import Path; "
        "from scripts.portability_schema import _driver_core; "
        "src = Path(sys.argv[1]).read_bytes(); "
        "print(json.dumps([_driver_core(Path('verify-portable.py'), src).decode(), "
        "_driver_core(Path('ordinary.py'), src).decode()]))"
    )

    def run_cores() -> list[str]:
        proc = subprocess.run(
            [sys.executable, "-c", program, str(source)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(proc.stdout)

    first = run_cores()
    assert "published docs" in first[0]
    assert "published docs" not in first[1]
    assert first[0] != first[1]
    cache_dir = cache_home / "pstack" / "driver-core"
    assert len(list(cache_dir.glob("*.json"))) >= 2
    assert run_cores() == first
```

The persistence test overwrites a generated record with malformed JSON and confirms the revision remains stable. `test_driver_core_cache_unavailable_path_preserves_core` points `XDG_CACHE_HOME` at a regular file and asserts the exact normalized core is returned despite cache setup failure. Cache-path tests reject direct and intermediate symlinks plus group- or world-writable ancestors before creating cache children.


- [x] **Step 2: Run both tests before implementation**

Run: `uv run pytest -q tests/test_evidence_durability.py::test_driver_core_disk_cache_persists_and_tracks_source_bytes tests/test_evidence_durability.py::test_driver_core_disk_cache_keeps_published_docs_basename_sensitive`

Expected: both FAIL because current merged main has only the process-local memo and writes no disk records. Failures must be the missing-record assertions, not an import, fixture, or subprocess error.

### Task 2: Implement the smallest safe disk layer

**Files:**
- Modify: `scripts/portability_schema.py` imports and `_driver_core` helper area around line 785
- Test: `tests/test_evidence_durability.py` from Task 1

**Interfaces:**
- Keep `_driver_core(path: Path, src: bytes) -> bytes` unchanged.
- Add private helpers only for selecting the cache directory, validating one record, writing one record atomically, and pruning the directory.

- [x] **Step 1: Add the optional cache lookup**
  1. Keep the current `_DRIVER_CORE_MEMO` lookup first.
  2. Select `$XDG_CACHE_HOME/pstack/driver-core`; use `~/.cache/pstack/driver-core` when `XDG_CACHE_HOME` is unset. Walk the normalized absolute path one component at a time and reject symlinks. On non-POSIX systems, disable disk caching because this code cannot verify directory ACL privacy. On POSIX, accept only root- or effective-user-owned components; reject group- or world-writable components unless the sticky bit protects entries. Create missing directories with mode `0700` and keep the leaf private. If the path is relative, unsafe, unavailable, or unwritable, disable disk caching for this call.
  3. Build the filename from SHA-256 of a format tag, `sys.implementation.cache_tag`, `path.name`, and the exact `src` bytes.
  4. Read a JSON object containing `format`, `python_tag`, `basename`, `source_size`, `source_sha256`, `core_b64`, and `core_sha256`. Validate each field, strict-base64 decode the core, and verify its digest. A missing or invalid entry returns a miss.
  5. On a miss, use the current UTF-8 decode, `ast.parse`, docstring capture, strip, and `ast.unparse` path. Preserve the existing `RecipeError` catch. Store only after that path succeeds.
  6. Store core bytes as base64 JSON, write to a unique same-directory temporary file with private permissions, then `os.replace` it into place. Cache I/O errors are ignored after retaining the computed `core`.
  7. Prune oldest regular files until both 256-entry and 32-MiB bounds hold. A prune race may remove an active entry; that can only cause a miss.
  8. Populate `_DRIVER_CORE_MEMO` as today and return the core.

- [x] **Step 2: Run the focused tests**

Run:
```bash
uv run pytest -q \
  tests/test_evidence_durability.py::test_driver_core_disk_cache_persists_and_tracks_source_bytes \
  tests/test_evidence_durability.py::test_driver_core_disk_cache_keeps_published_docs_basename_sensitive \
  tests/test_evidence_durability.py::test_driver_core_cache_unavailable_path_preserves_core \
  tests/test_evidence_durability.py::test_driver_core_cache_is_disabled_without_posix_permission_checks \
  tests/test_evidence_durability.py::test_driver_core_cache_rejects_symlink_directory_before_writing \
  tests/test_evidence_durability.py::test_driver_core_cache_rejects_symlinked_ancestor_before_writing \
  tests/test_evidence_durability.py::test_driver_core_cache_rejects_world_writable_ancestor_before_writing \
  tests/test_evidence_durability.py::test_driver_core_disk_cache_prunes_to_record_and_byte_bounds
```

Expected: PASS on POSIX; cross-process records are reused and invalidated correctly, basename-sensitive docs stay distinct, corrupt records miss, unavailable or unsafe paths preserve the normalized core, and record/byte limits hold. The simulated non-POSIX check verifies that disk caching is disabled before path creation.

### Task 3: Verify existing contracts and performance

**Files:**
- No additional production files unless a verification failure identifies a real required fix.

- [x] **Step 1: Refresh durable evidence without downgrading OMP**

The edited module is fingerprinted by host receipts and the blinded DSH candidate scope. Refresh static receipts individually, then re-observe OMP through its supported live path; never use `--host all`, which would downgrade OMP's live settlements.

Run:

```bash
for host in grok codex opencode antigravity; do
  uv run python scripts/verify-portable.py refresh-static --host "$host"
done
PSTACK_RUN_OMP_LIVE=1 uv run python scripts/verify-portable.py run --host omp
uv run pytest -q tests/test_evidence_durability.py
```

Expected: static receipts are current, OMP keeps observed-live settlements, and the durability suite passes. The candidate fixture remains stale until after the implementation commit.

- [x] **Step 2: Run five paired frozen-harness measurements**

Run five sequential A/B pairs, alternating order:
- pairs 1, 3, and 5: merged main then candidate;
- pairs 2 and 4: candidate then merged main.
Use the frozen script with `runs=1` and ten unique labels (`iter5-pair-1-main`, `iter5-pair-1-cache`, ..., `iter5-pair-5-main`, `iter5-pair-5-cache`). Candidate calls set `XDG_CACHE_HOME=/home/tommyk/.cache/hc-3/iter5-cache-home`; this path must be absent before the run, so pair 1 measures cold population and later candidate runs measure steady-state reuse. Confirm all output label directories are absent before running.

```bash
/home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack iter5-pair-1-main 1
XDG_CACHE_HOME=/home/tommyk/.cache/hc-3/iter5-cache-home /home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack/.worktrees/perf/driver-core-disk-cache iter5-pair-1-cache 1
XDG_CACHE_HOME=/home/tommyk/.cache/hc-3/iter5-cache-home /home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack/.worktrees/perf/driver-core-disk-cache iter5-pair-2-cache 1
/home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack iter5-pair-2-main 1
/home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack iter5-pair-3-main 1
XDG_CACHE_HOME=/home/tommyk/.cache/hc-3/iter5-cache-home /home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack/.worktrees/perf/driver-core-disk-cache iter5-pair-3-cache 1
XDG_CACHE_HOME=/home/tommyk/.cache/hc-3/iter5-cache-home /home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack/.worktrees/perf/driver-core-disk-cache iter5-pair-4-cache 1
/home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack iter5-pair-4-main 1
/home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack iter5-pair-5-main 1
XDG_CACHE_HOME=/home/tommyk/.cache/hc-3/iter5-cache-home /home/tommyk/.cache/hc-3/measure.sh /home/tommyk/projects/pstack/.worktrees/perf/driver-core-disk-cache iter5-pair-5-cache 1
```

Expected: every run passes. Keep only if the median candidate time is at least 5% below the exact-base median (31.2s; at least 1.56s) and all five paired differences favor the cache; this makes the 5% gain exceed observed run-to-run noise. Otherwise remove the cache code/test and record the reverted hypothesis.

The initial full-module runs used different test censuses on base and candidate. They are historical measurements, not the accepted performance comparison. The common-workload remeasurement below supersedes the earlier 21.2% claim without changing the 5% or all-paired-wins gates.

- [x] **Step 3: Review semantic scope and commit implementation**

Run: `sem diff --format json`; inspect the file/entity summary and confirm only the implementation, focused tests, plan, and refreshed durable receipt/index deltas changed before candidate-fixture regeneration. Run `git diff --check`, verify the durability suite, and create a signed implementation commit. This source commit is the revision the candidate fixture must name.

- [x] **Step 4: Refresh candidate evidence and verify the delivered state**

After the implementation commit, run:

```bash
uv run python scripts/eval_blinded_pstack.py --dsh-corpus tests/fixtures/eval_corpus_dsh --dsh-phase candidate --format json --output tests/fixtures/eval_corpus_dsh/scoring_table_candidate.json
uv run pytest -q tests/test_evidence_durability.py tests/test_eval_blinded_pstack_dsh_candidate.py
uv run python scripts/verify-portable.py check-evidence --host all
uv run python scripts/verify-portable.py check-staleness --host all
```

Expected: candidate case/control outcomes and verdict remain stable; the probe-scope hash is expected to change with the fingerprinted source and must match the regenerated result. The candidate revision names the implementation commit; both suites and evidence checks pass. Review only the expected receipt/index and candidate fixture deltas, then sign the evidence commit and verify both commits.

## Controlled common-workload result, 2026-10-18

The baseline is `3f4cd124f27cab90865df79d18d376e2f4335b2c`; the candidate is `6b986dcec7fde7899f2d689f481a7b73b69909f1`. Collection with `-k "not driver_core_disk_cache and not driver_core_cache"` produced identical ordered lists of 104 node IDs on both heads. The nine candidate-only cache cases were excluded from timing, not from correctness verification.

The existing `measure.sh` ran five alternating pairs with unique labels and a private `XDG_CACHE_HOME`. The first candidate run populated the cold cache; later runs reused it. Every measured arm passed the common 104 cases.

| Pair | Order | Base seconds | Candidate seconds |
| --- | --- | ---: | ---: |
| 1 | Base, candidate | 33.3 | 25.3 |
| 2 | Candidate, base | 28.6 | 24.2 |
| 3 | Base, candidate | 30.1 | 21.1 |
| 4 | Candidate, base | 28.9 | 23.1 |
| 5 | Base, candidate | 31.6 | 22.9 |

The paired medians are 30.1s and 23.1s, a 23.3% reduction. Every paired difference favors the candidate. The candidate also clears the original 29.64s threshold, so neither acceptance gate was relaxed.

The durable local program store is `~/.claude/orchestrate/pstack-429/`. `common-workload-544.json` records the exact node IDs, `common-measurement-544.json` records commands and cache state, and `common-result-544.json` records every arm and gate result. The machine logs remain under the unique labels in `~/.cache/hc-3/`.

The native OMP `independent-verifier` returned `PASS+NOTES` on the exact base/head and patch-id `ba59fed4a4c0fcd02b85255e66398ef04e750cfa`. Observed verifier model `openai-codex/gpt-6.1-sol` differed from writer `openai-codex/gpt-6-luna`; both are the same family. Runtime checks covered subprocess reuse, invalidation, malformed records, basename semantics, unsafe paths, and configured bounds. The affected durability and DSH regression suites passed. This does not establish multi-family program acceptance.

[PR #544](https://github.com/tommy-ca/pstack/pull/544) landed as `c1d03e521042735e6c76cea1abdde2039cde0c8b` after the server-enforced head check. The accepted cache remains a trusted-user, best-effort optimization, not a transactional concurrent quota.
