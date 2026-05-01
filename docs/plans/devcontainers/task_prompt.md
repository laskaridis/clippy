Read docs/plans/devcontainers/spec.md. Create tasks for that plan in docs/plans/devcontainers/tasks.json. Tasks are going to be implemented by small
    model with low reasoning capabilities such as gpt-5.4-mini so make sure that each tasks:
    - has a single purpose/objective to avoid having the model interpret
    - is locally verifiable and avoids subjective judgement
    - is fully specified with explicit constraints and clear input/output formats
    - has a narrow scope (a few files) preventing context explosion

Use a json format to document the tasks, with the following schema:
```json
{
    "id": "[task's unique idientifier, i.e. task-01]",
    "goal": "what to do",
    "files": ["file1.py", "file2.py"],
    "constraints": [ ... ],
    "acceptance_criteria": [ ... ],
    "dependencies: [ "task-00", ... ],
    "status": "pending|completed",
    "implementation_notes": [ ... ]
}
```