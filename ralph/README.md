# Meet Ralph

Ralph is a repo-local Python command-line harness for feature-folder implementation loops.

## Install

Install the package in editable mode from the repository root:

```bash
python -m pip install -e ralph
```

That exposes the `ralph` console script.

## CLI

Public subcommands:

- `ralph run --feature-dir <relative-path>` starts a fresh implementation run.
- `ralph resume --feature-dir <relative-path>` continues the incomplete run recorded in the feature-local session files.
- `ralph retro --feature-dir <relative-path>` runs the retrospective pass only.

Common options:

- `--feature-dir` is required and must be relative to the current working directory.
- `--max-iterations` limits coding iterations for `run` and `resume`.
- `--coding-model` selects the model used for coding iterations.
- `--retro-model` selects the model used for the retrospective pass.

`run` and `resume` print the terminal run outcome: `completed`, `blocked`, `failed`, `max_iterations`, or `degraded`.
`retro` prints `completed` when the retrospective succeeds and `failed` otherwise.

## Feature Folder Contract

Ralph expects a prepared feature folder with at least:

- `spec.md`
- `tasks.json`

The retrospective pass also requires:

- `ralph.txt`

During execution Ralph writes feature-local control-plane state under `.ralph/`:

- `.ralph/sessions/<session-id>.json` for each run session
- `.ralph/sessions/current.json` as the current incomplete-session pointer, or the latest terminal session
- `.ralph/lock` for active-run ownership

`run` fails fast if an incomplete session or active lock already exists. `resume` is the recovery path for interrupted runs, including stale-lock reclamation when the recorded process is gone and the heartbeat is old enough.

If the session state becomes corrupted beyond automated recovery, inspect the human-readable artifacts in the feature folder, delete `.ralph/` intentionally, and start a new `run`.

## Retrospectives

When implementation completes successfully, Ralph runs the retrospective automatically. If the retrospective fails after implementation succeeds, the run is marked `degraded` rather than `failed`.

You can rerun `retro` against a completed feature folder to regenerate only the retrospective state and output it owns.

## Legacy Shell Entry Point

`./ralph/ralph.sh` remains a compatibility shim for the old interface. It still accepts `--feature-dir`, `--max-iterations`, `--coding-model`, `--retro-model`, and `--retro-only`, then translates them into the Python CLI.

- `--retro-only` maps to `ralph retro`
- all other legacy runs map to `ralph run`
- when `--retro-only` is present, the shim rejects `--max-iterations` and `--coding-model`

The shim keeps the old operator workflow working while the Python CLI is the primary entry point.
