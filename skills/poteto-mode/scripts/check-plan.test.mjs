import { describe, expect, it } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SCRIPT = join(import.meta.dir, "check-plan.mjs");
const RULE =
  "Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.";

function section(title, depends) {
  const lanes = Array.from(
    { length: 10 },
    (_, index) =>
      `- [ ] Lane ${index + 1}. Exercise the surface. Save \`lane-${index + 1}.png\`. Pass when the result is correct.`
  ).join("\n");
  return `## ${title}

**Depends on.** ${depends}

**Files.**

- [ ] Edit the implementation.

**Build.**

- [ ] Build the named symbol.

**You see.**

- [ ] Observe the expected result.

**Verify, unit.** ${RULE}

- [ ] Run the focused unit test.

**Verify, live.** ${RULE} ${"Ten lanes on `grok-4.6` at the PR head"}

${lanes}

**Verify, perf.** ${RULE}

- [ ] Metric. Record the value.
- [ ] Probe. Run the probe.
- [ ] Baseline. Record trunk first.
- [ ] Rule. Compare the result.

**Review gate.** None.

**Merge.**

- [ ] Land the verified change.
`;
}

function plan(sections) {
  return `# Recursive plan

## How to read this

One box is one unit of work. Every box names the evidence that checks it. Check a box only when its evidence exists. The playbooks/ path explains execution. ${RULE}

## Program checklist

### Arm the program

- [ ] persist the plan path
- [ ] read \`git show origin/main:\` before each tick
- [ ] arm the 30-minute audit with \`scheduler_create\`
- [ ] send a status message

### Spawn owners

- [ ] Spawn the owners.

### PR mechanics

- [ ] Resolve the forge.

### Verdict and merge

- [ ] Verify the verdict.

### Boot recipe

- [ ] Boot the surface.

${sections.join("\n")}
## Close the program

- [ ] Close with evidence.

## Appendix A. Prototype evidence

- [ ] Fixture evidence.
`;
}

async function runChecker(content) {
  const directory = await mkdtemp(join(tmpdir(), "check-plan-"));
  const file = join(directory, "plan.md");
  await writeFile(file, content);
  try {
    const result = Bun.spawnSync([process.execPath, SCRIPT, file]);
    return {
      code: result.exitCode,
      stdout: result.stdout.toString(),
      stderr: result.stderr.toString(),
    };
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

describe("recursive dependency graph", () => {
  it("reports depth for an acyclic nested graph", async () => {
    const result = await runChecker(
      plan([
        section("Run smoke (smoke)", "checker"),
        section("Harden checker (checker)", "#sync"),
        section("Sync upstream (#sync)", "None."),
      ])
    );
    expect(result.code).toBe(0);
    expect(result.stdout).toContain("sync");
    expect(result.stdout).toContain("depth=2");
  });

  it("rejects a malformed None dependency", async () => {
    const result = await runChecker(
      plan([section("Malformed root (root)", "None")])
    );
    expect(result.code).toBe(1);
    expect(result.stderr).toContain("None");
  });

  it("rejects an unknown dependency", async () => {
    const result = await runChecker(
      plan([section("Watch errors (watcher)", "missing")])
    );
    expect(result.code).toBe(1);
    expect(result.stderr).toContain("watcher");
    expect(result.stderr).toContain("missing");
  });

  it("rejects duplicate identifiers", async () => {
    const result = await runChecker(
      plan([
        section("First unit (same)", "None."),
        section("Second unit (same)", "None."),
      ])
    );
    expect(result.code).toBe(1);
    expect(result.stderr).toContain("duplicate identifier same");
  });

  it("rejects dependency cycles", async () => {
    const result = await runChecker(
      plan([
        section("First unit (a)", "b"),
        section("Second unit (b)", "a"),
      ])
    );
    expect(result.code).toBe(1);
    expect(result.stderr).toContain("cycle");
    expect(result.stderr).toContain("a -> b -> a");
  });

  it("accepts identifiers ending with a period", async () => {
    const result = await runChecker(
      plan([
        section("Root (root.)", "None."),
        section("Leaf (leaf)", "root."),
      ])
    );
    expect(result.code).toBe(0);
    expect(result.stdout).toContain("depth=1");
  });

  it("rejects whitespace inside identifiers", async () => {
    const result = await runChecker(
      plan([section("Malformed ( foo )", "None.")])
    );
    expect(result.code).toBe(1);
    expect(result.stderr).toContain("invalid identifier");
  });

  it("rejects empty dependency entries", async () => {
    const result = await runChecker(
      plan([
        section("Root (root)", "None."),
        section("Malformed (bad)", "root,"),
      ])
    );
    expect(result.code).toBe(1);
    expect(result.stderr).toContain("invalid dependency identifier");
  });

  it("handles a deep acyclic dependency chain", async () => {
    const count = 20000;
    const result = await runChecker(
      plan(
        Array.from({ length: count }, (_, index) =>
          section(
            `Task ${index} (${index})`,
            index === 0 ? "None." : String(index - 1)
          )
        )
      )
    );
    expect(result.code).toBe(0);
    expect(result.stdout).toContain(`depth=${count - 1}`);
  });

});
