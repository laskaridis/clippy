# Code Quality
This document describes how to write correct, clean, highly maintainable code that fulfills the quality standards for this project.

## Core principles 
- Prioritise writing clean, easily maintainable code.
- Keep it simple; always prefer the simplest possible implementation that solves the problem and is easiest to understand and reason about.
- YAGNI; refrain from adding features or code for hypothetical future needs.
- Bias heavily towards high cohesion and low coupling.
- Refrain from introducing new dependencies without clear and strong justification.
- Make small, focused, incremental changes.
- Design your code so it is idempotent, wherever practical.
- Keep user-facing error messages actionable.
- Refrain from keeping around unused code or other artifacts.

## Code clarity
- Use intention revealing names for variables, functions, classes, etc.
- Document scripts, public classes, modules, and non-trivial functions:
  - Focus your documentation on intent, key assumptions pre-conditions, invariants and side-effects.
  - Avoid commenting obvious implementation details.
- As a litmus test, **ALWAYS** ask: if this code breaks at 1am in production, would somebody looking at it for the first time be able to quickly understand it to fix it? If the answer is no - refactor.
- Prefer functional programming idiom where practical to promote clarity:
  - Prefer pure functions and stateless logic where practical.
  - Avoid hidden state and side effects.
  - Keep data transformations explicit.

## Write good git commits
- Limit the subject line to 72 characters.
- Separate the subject from the body with a blank line.
- **Keep commits logically scoped**:
  - One logical change per commit
  - Avoid mixing unrelated changes
- **Provide the necessary context in the body**: 
  - Emphasize explaining the intent (i.e. the why) behind your changes.
  - Mention important design decisions and key assumptions.
  - Note any side effects, migrations, or compatibility impacts
- **Reference relevant artifacts when applicable**:
  - Spec IDs
  - Issue numbers
  - ADRs
  - Related PRs

## Testing
- Write tests for **all** new behavior.
- Update tests when modifying behavior.
- Do not remove failing tests without replacing them with correct ones.
- When fixing bugs first make sure you have an automated test replicating the problem.

## Code safety
- Prefer immutability where practical.
- Use optionals when possible instead of NULL values.
- For non-statically typed languages (e.g. Python) **ALWAYS** use type hints and type checks to avoid embarrassing bugs.

## Scripting
- Always use color coding for messages (green=ok, yellow=warn, red=error)
- Always include documentation to explain purpose, independent usage, and expected outcomes.
- Modularise script files to improve clarity and maintainability (i.e. avoid monolithic scripts)
