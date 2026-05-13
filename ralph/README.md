# Meet Ralph

Ralph is a repo-local Python CLI that runs one feature-folder implementation loop at a time through the `codex` CLI, persists run state in `.ralph/sessions.sqlite3`, and recovers interrupted work by starting a fresh run.

## What Ralph Expects

Run Ralph from the repository root and point it at a feature folder using a relative path.

The feature folder must contain:

- `spec.md`
- `tasks.json`

The coding agent is expected to maintain:

- `ralph.txt`
- `ralph.retro.md`

Ralph creates `ralph.txt` on the first coding iteration if it does not exist already. Retrospective-only runs require `ralph.txt` to already exist.

## Prerequisites

Install the package in editable mode from the repository root:

```bash
python -m pip install -e ralph
```

That exposes the `ralph` console script.

Ralph currently resolves only one agent backend: `codex`. The `codex` binary must be installed and usable in your shell environment.

## Commands

Start a fresh run:

```bash
ralph run --feature-dir docs/plans/ralph-cli
```

Run the retrospective only:

```bash
ralph retro --feature-dir docs/plans/ralph-cli
```

Common options:

- `--feature-dir` is required and must be relative to your current working directory.
- `--max-iterations` defaults to `50`.
- `--coding-model` defaults to `gpt-5.4-mini`.
- `--retro-model` defaults to `gpt-5.4-medium`.

Example with explicit models:

```bash
ralph run \
  --feature-dir docs/plans/ralph-cli \
  --max-iterations 10 \
  --coding-model gpt-5.4-mini \
  --retro-model gpt-5.4-medium
```

## How A Run Works

`ralph run`:

1. Validates that the feature folder exists and contains `spec.md` and `tasks.json`.
2. Creates a fresh session whenever startup is allowed. Older incomplete sessions remain historical state and do not block a new run.
3. Rejects startup when `.ralph/sessions.sqlite3` records a live lock. A dead same-host lock may be reclaimed automatically before the new session starts.
4. Renders the coding prompt and invokes `codex`.
5. Requires the coding response to start with exactly one of:
   - `RALPH_STATUS=CONTINUE`
   - `RALPH_STATUS=COMPLETE`
   - `RALPH_STATUS=BLOCKED`
6. Validates bookkeeping after each coding pass:
   - `tasks.json` must still be valid JSON with a top-level `tasks` list.
   - `RALPH_STATUS=COMPLETE` is accepted only when every task is marked `completed`.
   - `RALPH_STATUS=CONTINUE` is accepted only when at least one task is still not completed.
   - `RALPH_STATUS=BLOCKED` must include a human-readable blocker line immediately after the status line.
7. Repeats until the run completes, blocks, fails, or hits the iteration cap.
8. Automatically runs the retrospective after coding completes.

## Outcomes And Exit Codes

`ralph run` prints one terminal outcome:

- `completed`
- `blocked`
- `failed`
- `max_iterations`
- `degraded`

Current exit behavior is strict:

- `completed` exits `0`
- every other run outcome exits `1`

`ralph retro` prints:

- `completed` and exits `0`
- `failed` and exits `1`

`degraded` means the coding loop completed, but the retrospective phase failed.

## Session Store

Ralph stores feature-local control-plane state in `.ralph/sessions.sqlite3`.

The database is the sole source of truth for session history and the active lock. It contains the current run state, older historical sessions, and the active lock row used to gate new runs.

Legacy file-backed artifacts such as `.ralph/sessions/*.json`, `.ralph/sessions/current.json`, and `.ralph/lock` are ignored by this version of Ralph. They do not need to be migrated and do not affect startup.

If a run is interrupted, start another `ralph run`. The new run can reclaim only a dead same-host lock; otherwise it respects the live lock state recorded in the database and begins a fresh session once startup is allowed.

## Retrospective Behavior

The retrospective phase reads the same feature folder and requires `ralph.txt`. It succeeds only when:

- the agent exits with code `0`
- `ralph.retro.md` exists after the run

You can rerun it later:

```bash
ralph retro --feature-dir docs/plans/ralph-cli
```

That is the supported way to regenerate the retrospective output.

## Legacy Shell Entry Point

`./ralph/ralph.sh` remains a compatibility shim.

Legacy usage:

```bash
./ralph/ralph.sh --feature-dir docs/plans/ralph-cli
./ralph/ralph.sh --feature-dir docs/plans/ralph-cli --retro-only
```

The shim behavior is:

- normal runs map to `ralph run`
- `--retro-only` maps to `ralph retro`
- `--retro-only` rejects `--max-iterations`
- `--retro-only` rejects `--coding-model`
- `PYTHON_BIN` can override the Python executable used by the shim

The Python CLI is the primary interface. The shell entry point exists to preserve the older workflow.
