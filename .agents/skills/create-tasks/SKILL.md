---
name: create-tasks
description: Convert a specification document into a list of tasks that can be executed by a coding agent. Use this skill when you have a specification document and want to break it down into actionable tasks for a coding agent to implement.
argument-hint: Where is the specification document located that you want to convert into tasks?
---

## Purpose

Your goal is to convert a specification file into a strict implementation task plan to be implemented by low-reasoning coding agents without the mediation of a human developer.

The output must contain small, tightly bounded, implementation-ready tasks with clear instructions, explicit scope, dependencies, and verifiable acceptance criteria.

## Inputs

The user is requried to provide a specification file. If none has been provided then stop and ask the user to provide one.

## Constraints

You are running in **RESTRICTED WRITE MODE**. This means that you are not allowed to add or modify any repository files other than the requested output task list.

## Task generation guidelines

1. Create tasks with clear goals:

- Each task must have one clear, specific and unabmiguous objective.
- Avoid unclear, vague and ambiguous task goals that would allow the model to second guess.
- It is crucial by reading the task a low-reasoning coding agent avoids guessing what it needs to implement or how to implement it.

2. Create small tasks:

- Design for narrowly scoped tasks that modify the minimum necessary files. Avoid broad cross-cutting tasks unless required by the specification.
- Prefer many small tasks over broad tasks.

3. Split tasks with too broad scope:

- Split a task if it combines more than one major concern.
- Split a task if a low-reasoning agent would need to make more than one architectural or policy decision while implementing it.

4. Create verifiable tasks:

- Each task must include clear, unabmiguous and locally verifiable acceptance criteria which verify observable behaviour.
- Acceptance criteria must be locally observable from files, return values, CLI behavior, persisted artifacts, or deterministic tests.
- Avoid subjective acceptance criteria such as “keeps the design clear”, “reflects the rewrite properly”, or “is suitable for later use”.

5. Provide clear implementation guidelines for each task:

- Provide clear and unambiguous implementation guidelines as if you are explaining to a junior developer how to implement the task.
- Avoid vague instructions such as “refactor for clarity”, “optimize the implementation”, or “implement in a clean way”.

4. Link tasks to an explicity user story or requirement:

- If a task cannot be directly traced back to a specific user story or requirement, either remove it or narrow it.

5. Ask the user for clarifications as needed:

- If you identify ambiguity in the specs which materially affects architecture, behavior, or task decomposition, stop and ask the user for clarification.
- If you identify a gap in the specifications that would make it impossible to implement or verify a task, stop and ask the user for clarification.
- Otherwise, make conservative assumptions and explicitly document them in implementation_notes.

## Workflow 

1. First read the entire specification file before you start generating tasks.

2. Inspect the repository as needed to get context on existing structure and likely affected files.

3. Generate a prioritized list of tasks following the task generation guidelines.

4. Review all tasks using the final validation checklist below.

## Output

Write a `tasks.json` file in the same directory as the specification. Include only a valid JSON - no markdown, no prose, no comments.

Use the following schema EXACTLY:
```
{
  "spec_path": "<path to the specification file relative from repo_root>",
  "tasks": [
    {
      "id": "TASK-001",
      "title": "<less or equal to 80 characters, imperative>",
      "objective": "<1 sentence description of what needs to be accomplished>",
      "status": "<pending|completed>",
      "story_addressed": "<the id of the user story or requirement this task traces back to>",
      "requirements_addressed": [
        "<the id of the functional or non-fucnctional requirement this task traces back to>"
      ]
      "files": [
        "<path/to/file1 relative from repo_root>"
      ],
      "out_of_scope": [
        "<description of anything that is explicitly out of scope for this task>"
      ],
      "existing_context": [
        "<description of any relevant existing code, architecture, or design that should be taken into account when implementing this task>"
      ],
      "constraints": [
        "<description of anything critical that must constraint this implementation>"
      ],
      "implementation_guidelines": [
        "<any specific instructions or guidelines for the implementation of this task>"
      ],
      "acceptance_criteria": [
        "<clear and locally verifiable conditions that must be satisfied for this task to be considered complete>"
      ],
      "assumptions": [
        "<any assumptions you are making about the implementation, the codebase, or the specifications that should be documented for future reference>"
      ],
      "dependencies": ["TASK-000"]
    }
  ]
}
```

### GOOD example of a task following the guidelines:
```
{
  "id": "TASK-001",
  "title": "Prevent duplicate products in wishlist",
  "objective": "Ensure that adding the same product to a wishlist more than once does not create duplicate wishlist entries.",
  "status": "pending",
  "story_addressed": "US-001",
  "requirements_addressed": [
    "FR-002"
  ],
  "files": [
    "src/main/kotlin/com/example/wishlist/WishlistService.kt",
    "src/test/kotlin/com/example/wishlist/WishlistServiceTest.kt"
  ],
  "out_of_scope": [
    "Do not change the wishlist API contract.",
    "Do not change the database schema.",
    "Do not modify product catalog lookup behavior.",
    "Do not refactor unrelated wishlist methods."
  ],
  "existing_context": [
    "WishlistService.addProduct(userId, productId) is the existing entry point for adding products to a wishlist.",
    "WishlistRepository.findByUserId(userId) returns the current wishlist for a user.",
    "WishlistServiceTest already contains tests for adding a product to a wishlist."
  ],
  "constraints": [
    "Use the existing WishlistRepository methods if they are sufficient.",
    "Do not introduce a new duplicate-checking abstraction unless required by the existing code structure.",
    "Preserve existing public method signatures."
  ],
  "implementation_guidelines": [
    "Load the current wishlist before adding the requested product.",
    "Check whether the wishlist already contains an item with the same productId.",
    "If the product already exists, return the wishlist unchanged.",
    "If the product does not exist, add it using the existing persistence flow.",
    "Add or update tests in WishlistServiceTest to cover the duplicate-product case."
  ],
  "acceptance_criteria": [
    "When a product is added to an empty wishlist, the wishlist contains exactly one item for that product.",
    "When the same product is added twice, the wishlist still contains exactly one item for that product.",
    "No existing WishlistServiceTest test fails.",
    "No public API signature is changed."
  ],
  "assumptions": [
    "Product identity is determined by productId.",
    "Returning the unchanged wishlist is the expected behavior when a duplicate product is added."
  ],
  "dependencies": ["TASK-000"]
}
```

## Final verificaiton checklist

Before returning, verify that all of the following conditions are satisfied:

[ ] Output is valid JSON file placed under the same directory as the specification file with the name `tasks.json`.
[ ] You completed an internal requirement-to-task coverage pass before returning.
[ ] Every task has one clear, specific and unambiguous outcome that aligns with the specification.
[ ] Every task has a small, clear and tightly bunded file scope.
[ ] Every task has clear, unambiguous and verifiable acceptance criteria.
[ ] No task requires second guessing how it will be implemented or how it will be verified.
[ ] Task dependencies reference valid IDs and there are no circular dependencies between tasks.
[ ] All the user stories and requirements mentioned in the specification are covered by at least one task.
[ ] Each task can be traced back directly to a user story or a functional/non-functional requirement explicitly mentioned in the task.
