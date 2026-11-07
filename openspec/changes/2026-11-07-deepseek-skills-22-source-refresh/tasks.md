# Tasks: DeepSeek 22-skill OpenSpec source refresh

## Source and specification
- [x] Enumerate existing 16-skill baseline and new 22-skill master source using pinned GitHub API snapshots (SOURCE_STATIC).
- [x] Identify 6 newly added source directories and 8 changed directory objects; retain unchanged originals.
- [x] Build a 22/22 crosswalk with source link, license, target owner, adoption decision and negative triggers.
- [x] Draft new lifecycle, session projection, PR provenance, optional UI and host capability requirements.
- [x] Preserve existing PStack/QStack ownership and 20 semantic atoms; do not duplicate router or evidence type.

## Review and qualification — NOT RUN
- [ ] Run source-level diff on the 8 changed directories and inspect all referenced materials relevant to proposed adoption.
- [ ] Run Swarm on independent source/owner partitions; store true worker identities, pins and receipts.
- [ ] Run Arena on distinct warranted implementation designs and retain scores/selection/negative rationale.
- [ ] Run Interrogate on actual code and negative controls; rerun every accepted finding.
- [ ] Execute the existing PStack verification skill/eval corpus on a pinned checkout and report host-by-host status.
- [ ] Validate intended OpenSpec syntax with the repository's installed schema and checks; report every unavailable tool/gate.

## Implementation — separately gated
- [ ] Implement **only** canonical-owner changes whose current behavior fails a reproducible negative control.
- [ ] Verify no new `dsh-*` skill, router, mandatory platform dependency or duplicate serialized evidence reducer.
- [ ] Rerun exact-head checks, prove rollback/cleanup, and qualify baseline vs candidate across applicable project archetypes.
- [ ] Update QStack reference/compatibility manifests only after independently verified PStack adoption; maintain one-way dependency.
