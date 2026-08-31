## Context

Retrospective artifact for the archived `pstack-sync-from-upstream` change. The proposal describes a small standard-library script that exposes the pinned upstream tree, prints the documented refresh recipe, and optionally reports commits since the pin before fast-forwarding the sparse clone. The design handoff was omitted from the archive.

## Goals / Non-Goals

**Goals:**

- Make the shipped `UPSTREAM` pin and six-step refresh recipe inspectable from one script.
- Keep the default command local and deterministic; reserve network access for `--log`.
- Leave copying from upstream operator-owned rather than silently overwriting the port.

**Non-Goals:**

- No automatic source copy or merge.
- No dependency beyond the Python standard library.
- No promise that a network-backed `--log` works without operator credentials.

## Decisions

1. `--pin` prints the recorded commit, `--recipe` is the default local output, and `--log` is the explicit network path.
2. The script reads the repository's `UPSTREAM` metadata instead of duplicating the pin.
3. Tests exercise `--pin` and `--recipe` against the shipped metadata; network behavior remains an operator check.
4. The guide and `UPSTREAM` point to the script as the canonical refresh entry point.

## Verification

The archived tasks record the script, guide/metadata links, local CLI tests, and the `--log` output scenarios. This artifact summarizes those completed decisions retrospectively.
