# Meet Ralph

Ralph is a lightweight autonomous implementation loop for coding.

Use the Python CLI entrypoint `ralph run <path>` against a feature directory that contains:

- `spec.md`
- `tasks.json`

The progress log `ralph.txt` is still the traceability file used during runs, and should live in the same feature folder.

The legacy `ralph/ralph.sh` script remains only as a compatibility wrapper. It translates supported legacy run flags into the Python CLI and rejects retired retrospective flags.

## What Ralph does

For each run, Ralph:

1. Reads the spec and task list to understand the feature context.
2. Picks the next eligible task and implements one coding iteration at a time.
3. Reports clear progress in the terminal.
4. Optionally writes a machine-readable JSONL event log.
5. Stops when the workflow completes, becomes blocked, fails, or reaches the max-iterations limit.

Ralph does not run a retrospective in the MVP Python CLI.

## CLI usage

Primary entrypoint:

```bash
ralph run path/to/feature
```

The same execution path is also available through:

```bash
python -m ralph run path/to/feature
```

Supported `run` flags:

- `--agent codex` - built-in agent name, default `codex`
- `--model gpt-5.4` - model name passed through to the selected agent, default `gpt-5.4`
- `--max-iterations 50` - maximum number of code-step iterations to run, default `50`
- `--log path/to/events.jsonl` - optional JSONL event log path

Notes:

- `feature_dir` is a positional argument and must point to the feature directory for the run.
- The CLI validates that the feature directory exists and contains `spec.md` and `tasks.json` before any agent execution starts.
- If `--log` is provided and the file cannot be opened, Ralph exits with a setup error.
- The shell wrapper accepts `--feature-dir`, `--max-iterations`, and `--coding-model` for migration purposes only. Retired retrospective flags such as `--retro-only` and `--retro-model` fail fast with explicit migration errors.

## Terminal output

Ralph always prints human-readable progress in the terminal.

The terminal output covers:

- run start
- step start
- agent invocation
- step finish
- final run outcome

Blocked runs print the blocker text exactly as returned by the workflow. Failed runs print the failure summary. Setup and usage errors are reported as distinct terminal errors.

## JSONL logging

When `--log <path>` is set, Ralph appends one JSON object per line to the requested file.

The JSONL schema is stable and every record includes:

- `event`
- `timestamp`
- `run_id`

Required event types:

- `run_started`
- `step_started`
- `agent_invoked`
- `step_finished`
- `run_finished`

Event-specific fields are added as needed:

- `run_started` includes `feature_dir`, `agent_name`, `model`, and `max_iterations`
- `step_started` includes `iteration` and `step_id`
- `agent_invoked` includes `iteration`, `step_id`, `agent_name`, and `model`
- `step_finished` includes `iteration`, `step_id`, `outcome`, and optional `blocker_text`, `failure_summary`, or `raw_response`
- `run_finished` includes `outcome`, `iterations`, and optional `message`, `blocker_text`, `failure_summary`, `raw_response`, or `missing_artifacts`

If a step fails because the agent response cannot be parsed or validated, the raw agent response is preserved in the log record.

## Exit behavior

Ralph uses deterministic exit codes:

- `0` - successful completion
- `1` - failed termination
- `2` - invalid usage or setup error
- `3` - blocked termination

Setup errors include missing feature directories, missing required workflow artifacts, and JSONL log-path open failures.
