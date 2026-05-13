## What went well

- The rewrite did produce a coherent repo-local harness surface instead of a larger shell-script tangle. `TASK-007`, `TASK-016`, `TASK-018`, and `TASK-020` landed reusable boundaries in `ralph/ralph/session.py`, `ralph/ralph/lifecycle/orchestrator.py`, `ralph/ralph/cli.py`, and `ralph/tests/fakes.py`.

- The stateful paths were validated with real deterministic evidence, not just marked done. Re-running `python -m unittest discover -s ralph/tests` and `make ralph-verify` passed with 19 tests plus lint/typecheck, and `ralph/tests/test_orchestrator_run.py` and `ralph/tests/test_orchestrator_resume.py` cover the main lifecycle cases from `TASK-022` including multi-iteration completion, blocked runs, incomplete-session refusal, stale-lock recovery, and degraded retro outcomes.

## Recurring struggles

- The public CLI contract was weaker than the internal run model. The feature spec defines retrospective failure after successful implementation as "degraded success" (`docs/plans/ralph-cli/spec.md`), but `ralph/ralph/cli.py` maps `degraded` to exit code `1` via `_exit_code_for_run_outcome()`. A direct check returned `completed 0` and `degraded 1`, and there is no CLI-focused test in `ralph/tests/` to catch that gap. This points to `TASK-018` being structurally complete without fully validating operator-visible semantics.

- Retro success is currently an existence check, not proof that the current retro pass produced fresh output. `ralph/ralph/lifecycle/phases/retro/phase.py` marks the phase successful when the agent exits `0` and `ralph.retro.md` merely exists. `ralph/tests/test_retro_phase.py` pre-seeds that file, and a direct validation run returned `completed` while leaving the file content as `stale retro`. That is a real acceptance gap under `TASK-015`.

- Validation skewed toward helper functions and repo-local checks rather than the installed entrypoint. `ralph.txt` for `TASK-025` records `python -m pip install -e ralph`, `python -m unittest discover -s ralph/tests`, `make ralph-verify`, and `./ralph/ralph.sh --help`, but not `ralph --help` or any smoke of the installed console script. In this environment, `python -m pip install -e ralph` succeeded while bare `ralph --help` still returned `/bin/bash: ralph: command not found`; the script only worked when invoked directly from `sysconfig.get_path("scripts")`.

## Scope/control issues

- There was no major product-scope drift, but reusable guidance updates were scattered across implementation tasks instead of being handled as one deliberate workflow artifact. `ralph.txt` records `AGENTS.md` updates as scope deviations in `TASK-005`, `TASK-006`, `TASK-020`, and `TASK-023`. The changes were useful, but the pattern shows the plan had no clean lane for cross-cutting guidance capture.

## Prompt/task design issues

- `TASK-022` explicitly allowed "CLI-level behavior" to be "verified indirectly through orchestrator entrypoints." That shortcut reduced work, but it also removed the feedback loop that would have caught the `degraded` exit-code mismatch in `ralph/ralph/cli.py`.

- `TASK-014` and `TASK-015` constrained retro mutations to `ralph.retro.md`, but their acceptance criteria never required evidence that the file was regenerated or refreshed during the current pass. That left room for the existence-only success check now in `ralph/ralph/lifecycle/phases/retro/phase.py`.

## Follow-up tasks

- Add CLI-level contract tests for `run`, `resume`, and `retro`, including exit-code assertions for `completed`, `degraded`, `blocked`, and typed failure paths.  
  `Scope:` `ralph/tests/`, `Makefile`, and the Ralph verification workflow behind `make ralph-verify`.  
  `Expected outcome:` future harness changes will prove the public CLI contract directly instead of inferring it from orchestrator and helper coverage.  
  `Problem it solves:` the current workflow let `degraded` drift into a non-zero CLI exit even though the spec treats it as a successful implementation outcome.

- Tighten retrospective completion checks so a retro pass succeeds only when it creates or refreshes `ralph.retro.md` during that invocation, and add a regression test for stale pre-existing output.  
  `Scope:` `ralph/ralph/lifecycle/phases/retro/phase.py`, `ralph/tests/test_retro_phase.py`, and any shared Ralph retro validation guidance.  
  `Expected outcome:` future retrospective passes will validate real output production instead of passing on leftover artifacts.  
  `Problem it solves:` the current `TASK-015` implementation can return `completed` while leaving stale retrospective content untouched.

- Add a reusable console-script smoke check and environment note for editable installs, especially shim-managed Python setups.  
  `Scope:` `ralph/README.md`, `Makefile`, and shared developer guidance such as `AGENTS.md` or workflow docs.  
  `Expected outcome:` future verification will catch “installed but not invokable” states, and operators will know whether a PATH or reshim step is required.  
  `Problem it solves:` `TASK-025` proved editable installation but not actual shell invocation of `ralph`, which overstated operator readiness in this environment.
