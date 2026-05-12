---
name: spec-to-tasks
description: Convert the specified specification document into a list of tasks that can be executed by a coding agent. Use this skill when you have a specification document and want to break it down into actionable tasks for a coding agent to implement.
---

## Purpose

Convert a specification file into a strict JSON implementation task plan to be implemented by low-reasoning coding agents.

The output must contain small, tightly bounded, implementation-ready tasks with clear instructions, explicit scope, dependencies, and verifiable acceptance criteria.

## Constraints

This skill is meant to be use for planning only. It must not modify any repository files other than the requested output task list.

## Inputs

Required:

- a specification file

## Operating Rules

- Read the specification file completely before you start generating tasks.
- Before drafting tasks, extract every explicit requirement from the specification into an internal checklist.
- Classify each extracted requirement as one of: functional, non-functional, compatibility, interface, persistence, validation, documentation, or prohibition.
- Do not draft tasks until this checklist is complete.
- Inspect the repository only as needed to identify likely affected files, modules, tests, APIs, and conventions.
- Preserve exact specification semantics for named interfaces, exact enum values, exact file paths, lifecycle rules, ownership rules, compatibility requirements, and prohibitions.
- If the specification names a type, file, flag, state, artifact behavior, or allowed terminal outcome explicitly, at least one task must restate it explicitly.
- Refrain from inventing requirements.
- Do not add cleanup work, deletion work, new CLI flags, stricter validation rules, or new user-facing behavior unless the specification explicitly requires them or they are strictly necessary to satisfy another explicit requirement.
- Moving ownership of a file or responsibility does not imply deleting the prior file unless the specification explicitly requires removal.
- If you identify ambiguity in the specs which materially affects architecture, behavior, or task decomposition, stop and ask the user for clarification before proceeding. Otherwise, make conservative assumptions and explicitly document them in implementation_notes.”
- Prefer many small tasks over broad tasks.
- Each task must have one clear, specific and unabmiguous objective defined to avoid allowing the model to second guess.
- Design for narrowly scoped tasks that modify the minimum necessary files. Avoid broad cross-cutting tasks unless required by the specification.
- Split a task if it combines more than one major concern.
- Split a task if it modifies more than 5 files, unless the files are trivial siblings in one narrow module.
- Split a task if a low-reasoning agent would need to make more than one architectural or policy decision while implementing it.
- Each task must include clear, unabmiguous and locally verifiable acceptance criteria which verify observable behaviour.
- Acceptance criteria must be locally observable from files, return values, CLI behavior, persisted artifacts, or deterministic tests.
- Avoid subjective acceptance criteria such as “keeps the design clear”, “reflects the rewrite properly”, or “is suitable for later use”.
- Prefer acceptance criteria that mention exact files, commands, states, outputs, or failure behaviors.
- Each task must include clear implementation guidelines to steer the model's implementation and don't allow it to drift.
- Treat non-functional requirements and prohibitions as first-class requirements.
- Explicit dependency constraints, standard-library-only constraints, non-goals, forbidden behaviors, and idempotence rules must each map to at least one task.
- Assumptions must be implementation-local, conservative, and non-user-facing.
- Assumptions may fill implementation gaps, but they must not add new product behavior or policy.
- If an assumption would change CLI behavior, lifecycle semantics, persistence semantics, artifact ownership, or compatibility behavior, stop and ask the user instead of assuming.
- Tasks must be safe for low-reasoning implementation agents.
- If any explicit requirement is uncovered, revise the tasks instead of returning a partial plan.
- If a task cannot be traced back to an explicit requirement or necessary implementation support, remove it or narrow it.

## Task Quality Examples

Bad task:

- `Implement the coding phase and orchestration.`

Why it is bad:

- It combines multiple concerns.
- It leaves file ownership unclear.
- It gives a low-reasoning agent too much room to invent structure.

Better split:

- `Implement coding phase status parsing in ralph/ralph/lifecycle/phases/code/status.py.`
- `Implement coding-phase bookkeeping validation in ralph/ralph/lifecycle/phases/code/validation.py.`
- `Implement orchestrator run/resume transition handling in ralph/ralph/lifecycle/orchestrator.py.`

Bad acceptance criterion:

- `The module is ready for later lifecycle use.`

Better acceptance criterion:

- ``run` refuses to continue an incomplete session and returns the documented typed failure when `.ralph/lock` is active.``

## Output schema - MUST MATCH EXACTLY

Return only valid JSON. No markdown, no prose, no comments.

Schema:
{
  "spec_path": "<path to the specification file relative from repo_root>",
  "repo_root": "<path to the repository root>",
  "tasks": [
    {
      "id": "TASK-001",
      "title": "<less or equal to 80 characters, imperative>",
      "objective": "<1 to 3 sentence description of what needs to be accomplished>",
      "type": "<implementation|validation|refactor|documentation|cleanup>",
      "files": [
        "<path/to/file1 relative from repo_root>"
      ],
      "constraints": [
        "<deescription of anything critical that must constraint this implementation>"
      ],
      "implementation_notes": [
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

## Final Validation

Before returning, verify that:
- Output is valid JSON.
- You completed an internal requirement-to-task coverage pass before returning.
- Every task has one clear, specific and unambiguous outcome that aligns with the specification.
- Every task has a small, clear and tightly bunded file scope.
- Every task has clean, unambiguous and verifiable acceptance criteria.
- No task requires second guessing how it will be implemented.
- Dependencies reference valid task IDs and there are no circular dependencies between tasks.
- Every task depends on all earlier tasks that produce files, modules, interfaces, fixtures, or artifacts it directly relies on.
- Validation tasks depend on every implementation task whose output they verify.
- Test tasks depend on the implementation tasks for every module they test.
- No dependency may exist only because it is convenient ordering; dependencies must reflect actual producer-consumer relationships.
- No implementation work was performed
- Every functional and non-functional requirement from the specification must map to at least one task.
- Every explicit compatibility requirement, non-goal, prohibition, idempotence rule, and dependency/tooling constraint maps to at least one task.
- For each task, verify that a low-reasoning coding agent could implement it without guessing hidden policy, hidden dependencies, or unstated acceptance checks.
