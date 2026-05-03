Read docs/plans/devcontainers/spec.md and then create tasks for that plan in docs/plans/devcontainers/tasks.json. 

Assume that each task will be implemented by a low reasoning model such as gpt-5.4-mini. As such, ensure that each task:
  - Has a very specific and clear goal defined to not allow the model to second guess.
  - Has a narrowly bounded scope touching few (2-3) files at most to constraint the model for scope explosion.
  - Has clear and locally verifiable exit conditions which must be satisfiable by editing only the listed files.
  - If a task would require touching unlisted files, split it into prerequisite tasks instead of broadening the current task.
  - Includes clear implementation guidelines to steer the model's implementation and don't allow it to drift.
  - For infra, bootstrap, or other foundation changes, generate an early smoke-test task immediately after the foundational edit task.

  Use the following schema for each task:
  ```json
  {
      "id": "[task's unique idientifier, i.e. task-01]",
      "task_type": "implementation|cleanup|validation|documentation"
      "goal": "describe what needs to be done",
      "files": ["file1.py", "file2.py"],
      "constraints": [ ... ],
      "acceptance_criteria": [ ... ],
      "dependencies: [ "task-00", ... ],
      "status": "pending|completed",
      "implementation_notes": [ ... ],
  }
  ```
