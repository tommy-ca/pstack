---
name: principle-test-behavior-not-implementation
description: "Apply when you write, change, or keep a test. Assert what the code's users can observe, so that the test fails when that behavior breaks and keeps passing when only the internals change."
disable-model-invocation: true
---

# Test Behavior, Not Implementation

A test is a claim about what users of the code can observe through its interface: return values, errors, state they can read back, and effects on outside systems. Private helpers, internal call order, and intermediate data are implementation.

Judge each test against two imagined edits:

- **Break the behavior** (a wrong value, a skipped or doubled effect). If the test still passes, it proves nothing. The usual causes are a loose assertion, an expected value computed by the code under test, and an assertion on data the test built itself.
- **Change the internals** and keep every observable result. If the test fails, it is pinned to the implementation.

Keep a test that catches the first edit and survives the second. Rewrite or delete the rest. Drive the code through its public interface with a concrete input, and derive the expected value from the requirement. What an external service receives is behavior. A call to an internal helper is not. Pair "this never happens" with a case where it does happen. Assert the error type that callers branch on, not the message.

<!-- canonical-exception: cursor/plugins #474 tracks the upstream matcher error where non-vacuous assertions were grouped into the undefined check. -->
**Weak assertions that fail on `undefined` but miss real behavioral defects:**
- **Non-discriminating checks.** Asserting only `toBeDefined()`, `toBeTruthy()`, `toBeInstanceOf(Object)`, or `toBeGreaterThan(0)` when a concrete expected result should be verified. While these fail if the function returns `undefined`, they pass on almost any dummy value (such as `{}` or `true`) and hide bugs.

