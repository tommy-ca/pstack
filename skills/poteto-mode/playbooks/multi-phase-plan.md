### Multi-phase or multi-PR plan

**You own the plan, not the code. The plan is a checklist an owner runs box by box and the operator audits from the evidence.** The plan is the deliverable. Do not implement.

1. When the change is one or two files with an obvious approach, skip the plan. Say so and stop.
2. Settle open questions by prototype before you write, per `playbooks/prototype.md`. Ask the operator only about a product or preference call that no run can settle.
3. Write the plan file. Open with what changes, the PR ids in landing order, and the dependency graph. Give each PR section a unique parenthesized identifier in its title, like `## Task name (task-id)`. Start each section with `**Depends on.** None.` or comma-separated parenthesized identifiers. Validate the plan graph with `bun skills/poteto-mode/scripts/check-plan.mjs <plan.md>`. Then one section per PR. One PR is one change with its own evidence (the **sequence-verifiable-units** principle skill).
4. Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Each live box drives the real interface with a concrete scenario and a pass predicate. The perf box names the metric, the probe, the trunk baseline measured first, and the number that fails. A PR that changes an interaction waits for the operator's review before merge.
5. Hand back the plan path and stop. Execution starts on the operator's explicit go.

### PR Section Skeleton

````markdown
## <Task as a verb phrase> (task-id)

**Depends on.** None.

**Files.**

- [ ] Edit `<path>`.
- [ ] Create `<path>`.

**Build.**

- [ ] <One change. Name the symbol and the file.>

**You see.**

- [ ] <One observable result, with the exact log line or screen state.>

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] <Test file and the case it gains.> Run `<command>`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `resolved-model` at the PR head.

- [ ] Lane 1. Regression lane against trunk. Run the load-bearing scenario at trunk and head. Pass when <predicate>.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. <What is measured at trunk and head.>
- [ ] Probe. <Command or procedure run at trunk and head.>
- [ ] Baseline. Record the trunk value first.
- [ ] Rule. <Head against trunk, with the number that fails.>

**Review gate.** The operator reviews before merge.

- [ ] Post review artifacts in chat. Stop at merge-ready.

**Merge.**

- [ ] Clean verdict and bugbot triage done.
````

**Reply:** the plan path, the PR ids with their dependencies and the review-gated set, and what stays unproven.
