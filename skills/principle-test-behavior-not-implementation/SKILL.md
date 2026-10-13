---
name: principle-test-behavior-not-implementation
description: "Apply when you write, change, or keep a test. Call the code as its users do and assert the exact result they see. Rewrite or delete a test that would pass if every imported function returned undefined."
disable-model-invocation: true
---

# Test Behavior, Not Implementation

A test calls the code as its users do and asserts the exact result they see. Rewrite or delete any test that would still pass if the subject did nothing or returned `undefined` or a wrong value.

<!-- canonical-exception: cursor/plugins #474 tracks the upstream matcher error where non-vacuous assertions were grouped into the undefined check. -->
**Shapes that pass when the subject does nothing or returns `undefined` (vacuous assertions):**

- **No assertion or execution only.** Calling the subject with no `expect`, or only `expect(() => f()).not.toThrow()`.
- **Negative or absence check alone.** Only `toBeUndefined()`, `toBeFalsy()`, or `expect(mock).not.toHaveBeenCalled()`, without asserting presence on contrasting inputs.
- **Self-referential.** The expected value comes from the code under test: `expect(f(a)).toBe(f(a))`.
- **Constant pin.** The assertion restates a hand-maintained constant, config default, table row, or prompt string.
- **Fixture asserts fixture.** The assertion reads data the test built, with no call to the subject.

**Weak assertions that fail on `undefined` but miss real behavioral defects:**

- **Non-discriminating checks.** Asserting only `toBeDefined()`, `toBeTruthy()`, `toBeInstanceOf(Object)`, or `toBeGreaterThan(0)` where a concrete expected result should be verified. They fail if the function returns `undefined`, but pass on almost any dummy value such as `{}` or `true`, and hide bugs.

**The fix:** call the subject in the test body with one concrete input and assert the literal output or effect, `expect(slugify("Hello, World!")).toBe("hello-world")`. For a mock, assert the payload it received. For an absence, also assert the presence on another input. For a constant, test the mechanism that reads it with one input instead of restating the value. When no such assertion exists, delete the test.

**Keep** relation checks across table rows (a key in two tables, a parent that exists) and `*.test-d.ts` type checks.
