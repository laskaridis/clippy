# Meet Ralph

Ralph is a lightweight autonomous implementation loop for coding.

To use it, all you need to do is point him to a folder that contains two files:
- A feature description file: `spec.md`
- A task list file: `tasks.json`

For retrospective-only runs, the same feature folder must also contain `ralph.txt`.

## What Ralph does

For each iteration, Ralph:

1. Reads the spec and tasks to understand the context
2. Picks the next task and implements it.
4. Continues looping until completion, blockage, or the max iteration limit.
6. After finishing, ralph will reflect on its work and identify points for improvement.

Througought the process, ralph tracks progress by leaving notes to himself in a file (`ralph.txt`) which can be used to audit his actions.

At any point that ralph gets stuck, it will escalate to a human to sort things out.

## Current lifecycle

Ralph currently has a simple three-phase lifecycle:

1. Setup
   Ralph validates CLI arguments, resolves the feature directory, and ensures the required prompt and feature files exist for the selected mode.
2. Implementation loop
   Ralph repeatedly runs Codex for one task at a time until the agent reports `CONTINUE`, `COMPLETE`, or `BLOCKED`.
3. Retrospective
   When the agent reports `COMPLETE`, Ralph runs a second Codex pass using `prompts/retro.md`, which writes a `ralph.retro.md` review for the finished feature.

Ralph also supports a retrospective-only entrypoint that skips the implementation loop and runs the retrospective directly against an existing feature folder.

## Current status and boundaries

Ralph is currently a prompt-driven implementation harness, not a standalone service or framework. It does not manage task planning itself; it assumes a feature folder has already been prepared with a usable `spec.md` and `tasks.json`.

Its current control model is intentionally narrow:

- one task per iteration
- status-driven loop control via the first response line
- success only when the agent explicitly reports completion
- retrospective after successful completion, or directly via `--retro-only`

If the agent reports `BLOCKED`, if Codex execution fails, or if the iteration cap is reached without completion, Ralph exits without performing the retrospective.

## CLI usage

Full lifecycle run:

```bash
./ralph/ralph.sh --feature-dir specs/my-feature
```

Retrospective only:

```bash
./ralph/ralph.sh --feature-dir specs/my-feature --retro-only
```

Notes:

- `--feature-dir` is always required and must be relative to the current working directory.
- `--retro-only` requires `spec.md`, `tasks.json`, `ralph.txt`, and `prompts/retro.md`.
- `--retro-only` cannot be combined with `--max-iterations` or `--coding-model`.
