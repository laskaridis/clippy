---
name: tdd
description: Guide coding agents through test-driven development for code changes. Use when the user asks to implement, fix, refactor, or extend behavior using TDD, red-green-refactor, test-first development, characterization tests, regression tests, or when a change should be driven by failing tests before production code is edited.
---

# TDD

Use this skill to make tests the executable description of the desired behavior before changing production code.

## Core Rule

Do not edit production code for a behavior change until you have written or identified a failing test that describes the intended behavior.

Exceptions:

- You may inspect production code to understand seams, existing behavior, and test placement.
- You may make test-only setup changes needed to express the failing behavior.
- You may skip the red step only when the user explicitly asks for it, the change is purely mechanical, or the project cannot run tests locally. State the reason clearly.

## Workflow

1. Clarify the behavior:

- Identify the smallest observable behavior change.
- If expected behavior is ambiguous, ask before writing tests.
- Prefer testing public behavior through stable interfaces over private implementation details.

2. Find the existing test pattern:

- Locate nearby tests for the same module, feature, command, route, component, or integration.
- Reuse the project's existing test framework, fixtures, naming style, assertions, factories, and helper conventions.
- If no relevant tests exist, add the smallest new test file in the conventional location.

3. Write the red test:

- Add one failing test for the next smallest behavior slice.
- Make the test fail for the right reason, not because of syntax errors, missing imports, bad fixtures, or an incorrect assumption.
- Run the narrowest relevant test command and capture the failure.

4. Make it green:

- Implement the minimum production code needed to pass the failing test.
- Avoid broad rewrites, speculative abstractions, unrelated cleanup, or extra behavior not covered by the test.
- Run the same narrow test until it passes.

5. Refactor safely:

- Improve names, structure, duplication, and seams only while tests are green.
- Keep each refactor behavior-preserving and small.
- Run the relevant tests after refactoring.

6. Repeat:

- Add the next failing test only after the prior slice is green.
- Expand from narrow unit tests to integration or end-to-end tests when behavior crosses boundaries.
- Finish by running the broader relevant suite for the changed area.

## Test Selection

- Use characterization tests first when modifying legacy or poorly understood behavior. Lock current behavior before changing it.
- Use regression tests for bug fixes. Reproduce the bug with a failing test before fixing it.
- Use unit tests for isolated business rules, parsing, validation, calculations, and branch-heavy logic.
- Use integration tests for persistence, API boundaries, framework wiring, auth, serialization, queues, or cross-module behavior.
- Use end-to-end tests only for critical user flows or when lower-level tests cannot observe the behavior reliably.

## Implementation Discipline

- Keep tests deterministic: avoid real time, network, randomness, or shared global state unless the project already has controlled helpers.
- Prefer one behavioral assertion per test scenario, with enough assertions to prove the behavior.
- Name tests after the behavior they specify, not the method internals.
- Add the minimum fixture data needed to explain the scenario.
- Do not weaken or delete existing tests to make the suite pass unless the user explicitly confirms the behavior changed.
- Treat flaky failures, broad snapshot updates, and "test only passes alone" as design feedback to fix, not as noise to ignore.

## Reporting

When summarizing TDD work, include:

- The failing test added and the behavior it captured.
- The narrow command used to observe red and green.
- The production change made to satisfy the test.
- Any broader verification run, or why broader verification was not possible.
