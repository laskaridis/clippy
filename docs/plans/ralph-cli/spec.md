# Python Ralph CLI Harness

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This document must be maintained in accordance with [docs/PLANS.md](docs/PLANS.md).

## Purpose / Big Picture

`ralph/ralph.sh` is currently a thin Bash loop that validates a feature folder, renders two prompt files, repeatedly shells out to `codex exec`, and stops when the first line of the model output reports `RALPH_STATUS=CONTINUE`, `RALPH_STATUS=COMPLETE`, or `RALPH_STATUS=BLOCKED`. That is enough for a prototype, but it is brittle: execution state is mostly implicit, malformed output is not modeled cleanly, resume and inspection are missing, and the code is hard to extend without turning the shell script into a larger pile of string handling.

After this change, Ralph becomes a real Python command-line harness that still performs the same v1 workflow a user sees today: it requires a prepared feature folder with `spec.md` and `tasks.json`, runs one implementation iteration at a time through a configurable agent interface that defaults to the `codex` CLI in v1, and runs a retrospective pass when implementation completes. The visible improvement is that operators gain structured feature-local run sessions, deterministic error reporting, resume support, explicit lifecycle boundaries, and a compatibility-preserving migration path where `./ralph/ralph.sh` still works.

## Progress

- [x] (2026-05-08 15:40Z) Audited `ralph/ralph.sh`, `ralph/prompts/code.md`, `ralph/prompts/retro.md`, and `ralph/README.md` to capture the current harness contract.
- [x] (2026-05-08 15:52Z) Confirmed the repository planning format in `docs/PLANS.md` and the existing `docs/plans/*/spec.md` conventions.
- [x] (2026-05-08 16:05Z) Locked the product decisions for the rewrite: Python platform CLI, `codex` CLI adapter backend, file-based prompts, feature-local structured state, single active run per feature, strict typed failures, and a compatibility shim for `ralph.sh`.
- [ ] Create the standalone Python package and package metadata under `ralph/`.
- [ ] Implement the Python CLI subcommands `run`, `resume`, and `retro`.
- [ ] Add lifecycle, agent, and session-persistence modules, then replace `ralph/ralph.sh` with a thin delegating wrapper.
- [ ] Add deterministic unit and integration tests with a fake agent plus an optional real-`codex` smoke path.
- [ ] Add Makefile targets and documentation for the new harness workflow.

## Surprises & Discoveries

- Observation: the current Ralph surface is intentionally tiny. The entire implementation is one shell script plus two Markdown prompt templates and a README.
  Evidence: `find ralph -maxdepth 2 -type f` currently returns only `ralph/README.md`, `ralph/prompts/code.md`, `ralph/prompts/retro.md`, and `ralph/ralph.sh`.

- Observation: the Bash harness already has an implicit architecture, even though it is not modeled as such: argument parsing, feature-folder validation, prompt rendering, `codex` invocation, status parsing, and lifecycle orchestration are separate concerns interleaved in one file.
  Evidence: `ralph/ralph.sh` contains `usage`, `validate_positive_integer`, `run_codex_prompt`, inline feature-path validation, inline prompt rendering, and a loop that switches on the first output line.

- Observation: the repository does not already expose a stable top-level Python-tooling surface for Ralph through the root `Makefile`.
  Evidence: `make help` lists backend, extension, and cross-project targets, but nothing for `ralph`.

## Decision Log

- Decision: implement Ralph as a standalone Python CLI under `ralph/` rather than as a backend utility.
  Rationale: Ralph orchestrates repository work but is not part of the Django application. Keeping it separate avoids coupling harness lifecycle decisions to backend packaging.
  Date/Author: 2026-05-08 / Codex

- Decision: preserve the current workflow boundary in v1: Ralph owns implementation iterations and retrospective execution only.
  Rationale: the current feature-folder contract is already clear. Pulling planning or publishing into the same rewrite would expand scope before the execution harness itself is reliable.
  Date/Author: 2026-05-08 / Codex

- Decision: continue using the `codex` CLI as the only concrete agent in v1, but hide it behind a Python agent interface.
  Rationale: the rewrite should improve orchestration first, not re-implement model transport, auth, or session semantics. An agent abstraction keeps room for later backends such as Claude Code without delaying the migration.
  Date/Author: 2026-05-08 / Codex

- Decision: keep prompt assets as Markdown files on disk, but colocate each prompt under the phase package that owns it.
  Rationale: the prompts are part of the product surface and should remain easy to inspect, diff, and iterate without editing Python source, while phase-local ownership keeps each phase self-contained.
  Date/Author: 2026-05-08 / Codex

- Decision: add feature-local machine-readable run sessions under `<feature-dir>/.ralph/` while preserving `ralph.txt` and `ralph.retro.md` as human-readable artifacts.
  Rationale: structured session state is necessary for resume, recovery, error categorization, and auditability, but the existing log files remain useful operator-facing evidence.
  Date/Author: 2026-05-08 / Codex

- Decision: keep bookkeeping ownership with the coding agent for `tasks.json`, `ralph.txt`, and `ralph.retro.md`, and make the harness validate those artifacts after each iteration.
  Rationale: this preserves the current prompt contract and keeps the rewrite focused on harness control flow instead of inventing a richer agent response schema in the same milestone.
  Date/Author: 2026-05-08 / Codex

- Decision: preserve existing `ralph.sh` flags and behavior through a shell compatibility shim that delegates into Python.
  Rationale: a clean migration should not break existing docs or operator habits while the new Python CLI is introduced.
  Date/Author: 2026-05-08 / Codex

- Decision: name the top-level Python package `ralph`.
  Rationale: the harness already lives under `ralph/`, and a matching import path keeps the module surface simple and avoids redundant `ralph_cli` naming.
  Date/Author: 2026-05-09 / Codex

- Decision: model the harness lifecycle as a static sequence of explicit phases, with the orchestrator coordinating across them.
  Rationale: Ralph’s loop should stay responsible for iteration counting, phase transitions, and overall run outcome, while individual phases encapsulate their own implementation details and remain replaceable as new lifecycle phases such as review or ship are added later.
  Date/Author: 2026-05-09 / Codex

- Decision: make lifecycle a top-level package that owns orchestration and phase execution.
  Rationale: the harness should express lifecycle as a first-class concept instead of scattering its control plane across unrelated root modules. Grouping the orchestrator and phases under `ralph.lifecycle` makes the execution model explicit and keeps lifecycle-specific logic cohesive.
  Date/Author: 2026-05-09 / Codex

- Decision: make each phase invocation single-shot and workflow-agnostic.
  Rationale: a phase should perform one unit of work such as one coding pass or one retrospective pass, then return a local outcome. This keeps phase modules focused and leaves loop control and next-phase selection entirely with the orchestrator.
  Date/Author: 2026-05-09 / Codex

- Decision: make agent integration a separate top-level package.
  Rationale: Ralph core should not be structurally synonymous with Codex. A dedicated `ralph.agents` package isolates agent-specific invocation details, prompt transport, and diagnostics so future agents can be introduced without reshaping lifecycle code.
  Date/Author: 2026-05-09 / Codex

- Decision: keep run-session persistence in a top-level `ralph.session` module rather than under lifecycle.
  Rationale: session state is operational control-plane persistence shared by the CLI and lifecycle orchestration. Keeping it top-level avoids making persistence look like a subtype of lifecycle behavior.
  Date/Author: 2026-05-09 / Codex

- Decision: expose Python subcommands `run`, `resume`, and `retro` in v1, and defer a public `inspect` command.
  Rationale: the current shell script only supports “run the full lifecycle” and “retrospective only.” `run`, `resume`, and `retro` cover the required operator workflows, while deferred inspection can be served by the persisted session artifacts until a dedicated read-only command is justified.
  Date/Author: 2026-05-09 / Codex

- Decision: make the installed `ralph` console script the public Python CLI surface in v1.
  Rationale: the package lives under `ralph/` as a standalone tool. Requiring an editable install keeps the operator entrypoint simple and avoids ambiguous repo-root `python -m ...` behavior.
  Date/Author: 2026-05-09 / Codex

- Decision: make the orchestrator own all new-session versus resume-session decisions.
  Rationale: session lifecycle is control-plane behavior, not a CLI parsing concern. Keeping those rules in the orchestrator makes `run` and `resume` deterministic and testable.
  Date/Author: 2026-05-09 / Codex

- Decision: make session locking explicit and reclaim stale locks only through `resume`.
  Rationale: Ralph needs single-active-run protection, but it also needs an auditable recovery path after crashes. Encoding lock ownership in machine-readable data keeps recovery deterministic.
  Date/Author: 2026-05-09 / Codex

- Decision: keep coding-status validation minimal, explicit, and based only on `tasks.json` parseability plus task `status` values.
  Rationale: Ralph should reject malformed control signals and obvious bookkeeping contradictions without turning the harness into a second planner or reviewer.
  Date/Author: 2026-05-09 / Codex

- Decision: treat malformed status output, subprocess failures, missing artifacts, and contract violations as explicit typed failures.
  Rationale: orchestration code must fail deterministically. Warning and continuing on ambiguous control-plane failures makes runs hard to trust.
  Date/Author: 2026-05-08 / Codex

- Decision: if implementation succeeds and retrospective fails, mark the run as degraded rather than failed.
  Rationale: retrospective output is valuable but not release-critical. Losing it should be visible, but it should not erase a successful implementation run.
  Date/Author: 2026-05-08 / Codex

## Outcomes & Retrospective

Work has not started yet. The current outcome of this document is a decision-complete implementation plan for replacing the Bash prototype with a structured Python CLI without changing Ralph’s v1 feature-folder workflow.

The main risk to watch during implementation is accidental scope growth. The rewrite should improve control, observability, and testability, not turn Ralph into a planner, scheduler, or hosted service.

## Context and Orientation

Ralph lives today in the repository root under `ralph/`. The current entrypoint is `ralph/ralph.sh`. It requires `--feature-dir`, assumes the directory contains `spec.md` and `tasks.json`, and optionally accepts `--max-iterations`, `--coding-model`, `--retro-model`, and `--retro-only`. It reads `ralph/prompts/code.md` for implementation iterations and `ralph/prompts/retro.md` for the final retrospective. It writes no structured state of its own. Instead, it relies on the coding model to update `tasks.json`, append to `ralph.txt`, and later write `ralph.retro.md`.

The first line of each coding response is Ralph’s control signal. The shell script strips the first line and expects one of three exact values: `RALPH_STATUS=CONTINUE`, `RALPH_STATUS=COMPLETE`, or `RALPH_STATUS=BLOCKED`. Anything else is merely warned about today. The Python rewrite must formalize that contract. In this plan, “agent” means the module that launches an external coding tool such as `codex` and captures its output, “run session” means machine-readable metadata persisted under the feature directory for one Ralph execution, and “degraded” means a finished implementation run whose retrospective failed.

This repository already has a stable task surface in the root `Makefile`, and Ralph should join that surface rather than inventing an ad hoc testing story. There is currently no top-level Make target for Ralph. The implementation must add one. The rewrite must remain repo-local and must not depend on the Django backend package. That means Ralph should ship its own package metadata and test layout under `ralph/`.

The resulting file layout should be:

- `ralph/pyproject.toml` for Ralph’s standalone package metadata and development tool configuration.
- `ralph/ralph/` as the Python package.
- `ralph/ralph/cli.py` for argument parsing and command dispatch.
- `ralph/ralph/config.py` for CLI options, feature-folder validation, default resolution, and resolved agent selection.
- `ralph/ralph/agents/base.py` for the shared agent protocol and structured execution result.
- `ralph/ralph/agents/factory.py` for resolving configured agent identifiers to concrete implementations.
- `ralph/ralph/agents/codex.py` for the concrete `codex` implementation used in v1.
- `ralph/ralph/session.py` for persisted feature-local run sessions, the current-session pointer, and active-run locking.
- `ralph/ralph/lifecycle/orchestrator.py` for the outer Ralph loop, phase sequencing, overall run outcome, and resume logic.
- `ralph/ralph/lifecycle/phases/base.py` for the shared phase protocol and `PhaseResult` / `PhaseOutcome` contract.
- `ralph/ralph/lifecycle/phases/code/` as a phase package that owns the coding phase implementation, prompt asset, status parsing, and code-phase validation.
- `ralph/ralph/lifecycle/phases/retro/` as a phase package that owns the retrospective phase implementation, prompt asset, and retro-phase validation.
- `ralph/tests/` for deterministic unit and integration tests using a fake agent.

`ralph/README.md` remains in place. The Python rewrite should move prompt ownership into the corresponding phase packages rather than keeping a centralized `ralph/prompts/` area.

## Plan of Work

Begin by establishing Ralph as its own Python package. Add `ralph/pyproject.toml` with a lightweight build configuration and a console script entry such as `ralph = "ralph.cli:main"`. Treat that installed console script as the public Python CLI surface in v1. Keep tool configuration local to Ralph where practical so the harness can be tested independently of `backend/pyproject.toml`. Add a `ralph/tests/__init__.py` file if needed so `unittest` discovery is stable. Documentation and verification commands should assume a one-time editable install such as `python -m pip install -e ralph` before invoking `ralph ...` directly.

Next, split the current shell responsibilities into Python modules. In `ralph/ralph/config.py`, define typed configuration objects for the common runtime options: feature directory, max iterations, coding model, retro model, retro-only mode, the selected agent identifier, and the derived paths to `spec.md`, `tasks.json`, `ralph.txt`, `ralph.retro.md`, and `.ralph/`. Make feature-folder validation explicit and raise typed exceptions when required files are missing or the feature path is absolute. The v1 default agent is `codex`, but lifecycle code must consume only the resolved agent interface rather than importing Codex-specific logic directly.

In `ralph/ralph/agents/base.py`, define a small agent protocol that accepts prompt text plus model configuration and returns a structured result containing stdout content, exit status, and any agent metadata needed for diagnostics. In `ralph/ralph/agents/codex.py`, implement that protocol by executing the same underlying `codex` command used today: `codex --model <model> --ask-for-approval never -c shell_environment_policy.inherit=all exec --ephemeral --sandbox danger-full-access -o <tempfile> -`. The implementation must capture the result payload from the temp file, preserve stderr or subprocess failure details for debugging, and remove the temp file reliably. In `ralph/ralph/agents/factory.py`, keep the v1 mapping from the configured agent identifier to the concrete agent implementation. The package structure should make it straightforward to add peers such as `claude_code.py` later without touching lifecycle modules.

In `ralph/ralph/lifecycle/phases/base.py`, define the shared phase contract. Each phase invocation is single-shot and returns only a local outcome such as `next_iteration`, `completed`, `blocked`, or `failed`, plus any phase metadata needed by the orchestrator. The phase contract must not expose any knowledge of which phase comes next.

In `ralph/ralph/lifecycle/phases/code/`, implement the coding phase as a self-contained package. The phase package owns the code prompt asset, prompt rendering, code-phase prerequisites, first-line status parsing, and post-run bookkeeping validation for a single coding pass. It must replace the `$ARGUMENTS` placeholder with the resolved feature directory path, parse the first output line, and return a local phase outcome without deciding whether to repeat the code phase or advance to retrospective. The phase must talk to the abstract agent interface rather than a Codex-specific module.

In `ralph/ralph/lifecycle/phases/retro/`, implement the retrospective phase as a self-contained package. The phase package owns the retro prompt asset, prompt rendering, retro prerequisites, and retrospective output validation for a single retrospective pass. It must validate that retrospective-only execution still requires `ralph.txt`. The retro phase must also depend only on the abstract agent interface.

Do not introduce a centralized `ralph.lifecycle.prompts` module. Prompt ownership and prompt-related helper logic stay with the corresponding phase packages.

Keep phase-dependent validation logic with the phase that owns it. For the coding phase, the first-line response parser must inspect the first output line and map it to a typed status enum. Any missing first line, malformed status, or blocked response lacking the required human-readable blocker line becomes a contract violation. The shell script’s current “warn and continue” behavior is intentionally removed here.

Do not introduce a centralized `ralph.lifecycle.validation` module for phase-dependent checks. If a validation rule depends on a specific phase contract, keep it inside that phase package. Only genuinely cross-phase validation should live outside the phase packages, and feature-folder validation remains in `ralph.config`.

In `ralph/ralph/session.py`, create the feature-local `.ralph/` directory on first run and persist machine-readable session artifacts under `.ralph/sessions/`. Use `.ralph/sessions/<session-id>.json` for each run session, `.ralph/sessions/current.json` as the pointer to the current incomplete session when one exists or otherwise the latest terminal session, and `.ralph/lock` for active-run ownership. The lock file must record at least session id, pid, hostname, started-at timestamp, and last-heartbeat timestamp. Refresh the heartbeat at phase boundaries. A lock may be treated as stale only when the recorded process is no longer running on the recorded host and the last heartbeat is older than a conservative stale threshold of 10 minutes. Only `resume` may reclaim a stale lock automatically; `run` must fail instead. Session files should store only operational control-plane data such as resolved config, current phase, iteration count, last phase outcome, timestamps, agent result metadata, and overall run outcome. Valid terminal run outcomes in v1 are `completed`, `blocked`, `failed`, `max_iterations`, and `degraded`. Do not duplicate `ralph.txt` narrative or persist full prompt and response bodies.

In `ralph/ralph/lifecycle/orchestrator.py`, implement the outer lifecycle rules. The orchestrator owns all session-lifecycle decisions. `run` validates configuration, creates a new session through `ralph.session`, acquires the lock, performs the iteration loop, invokes the current phase once per iteration, and decides whether to repeat the current phase, advance to the next phase, stop blocked, stop at max iterations, or fail. `run` must not continue an existing incomplete session; if `.ralph/sessions/current.json` points to an incomplete session or `.ralph/lock` is active, `run` fails fast and tells the operator to use `resume`. `resume` loads exactly one existing incomplete session, validates or reclaims the lock under the stale-lock rules above, and continues that session without creating a new one. Terminal sessions (`completed`, `blocked`, `failed`, `max_iterations`, and `degraded`) are closed and may not be resumed. The orchestrator owns the static v1 phase pipeline, phase transitions, iteration counting, and overall run outcome. The CLI resolves the configured agent through `ralph.agents.factory` before calling into the lifecycle entrypoints. When the code phase reports completion, the orchestrator runs the retrospective phase automatically. When a later non-critical phase fails after successful implementation, the orchestrator records a degraded run outcome rather than a full failure.

Bookkeeping validation must remain narrow and objective. After each successful coding iteration, validate only the explicit v1 bookkeeping contract: `tasks.json` still exists and is parseable, `ralph.txt` exists or was created, `RALPH_STATUS=BLOCKED` includes the required blocker line, `RALPH_STATUS=COMPLETE` is accepted only when every task entry in `tasks.json` has `status: "completed"`, and `RALPH_STATUS=CONTINUE` is accepted only when at least one task entry remains not `completed`. Do not make the harness rewrite `tasks.json` or `ralph.txt`. Do not infer implementation correctness from `spec.md`, git state, or ad hoc dependency reasoning in v1. The harness only enforces that the required artifacts exist, are internally coherent, and can support future commands through the persisted session artifacts.

Then replace the shell entrypoint. Rewrite `ralph/ralph.sh` so it becomes a compatibility shim that delegates to the Python package. It must preserve the existing operator contract: the legacy full-lifecycle flags map to `run`, and `--retro-only` maps to `retro`. The shim must not reimplement validation logic beyond minimal argument pass-through.

Finally, add repository task surfaces and documentation. Add root `Makefile` targets for at least `ralph-test` and `ralph-verify`. `ralph-test` should run the deterministic Ralph test suite. `ralph-verify` should run Ralph’s tests plus any lint and typecheck commands established for the new package. Update `ralph/README.md` so it documents both the new subcommand-oriented Python CLI and the compatibility behavior of `ralph/ralph.sh`.

## Concrete Steps

Perform the work from the repository root.

1. Confirm the current Ralph contract before editing anything.

       sed -n '1,260p' ralph/ralph.sh
       sed -n '1,220p' ralph/prompts/code.md
       sed -n '1,220p' ralph/prompts/retro.md
       sed -n '1,220p' ralph/README.md

   Expected result: the shell script shows the current flag set and the status-line loop, and the prompts show the current feature-folder and bookkeeping contract.

2. Create the standalone Python package and package metadata under `ralph/`.

       mkdir -p ralph/ralph/lifecycle/phases/code ralph/ralph/lifecycle/phases/retro ralph/ralph/agents ralph/tests

   Then add `ralph/pyproject.toml`, package modules, and test files as described in this plan.

3. Add root Makefile targets for Ralph verification.

   The expected commands at the end of this step are:

       make ralph-test
       make ralph-verify

   `make ralph-test` must run the deterministic test suite for `ralph/tests/`. `make ralph-verify` must include at least tests and any local lint or typecheck commands introduced for Ralph.

4. Install the Ralph package in editable mode for local CLI verification, then verify the deterministic test path.

       python -m pip install -e ralph
       python -m unittest discover -s ralph/tests

   Expected result: the editable install succeeds in the prepared development environment, and the deterministic suite passes without requiring a live `codex` binary or network access.

5. Verify the compatibility shim still exposes the old interface.

       ./ralph/ralph.sh --help

   Expected result: the help output still shows `--feature-dir`, `--max-iterations`, `--coding-model`, `--retro-model`, and `--retro-only`, even though the implementation now delegates into Python.

6. Optionally run a real smoke path against a prepared feature directory when `codex` is installed and the operator wants end-to-end proof.

       ralph run --feature-dir docs/plans/devcontainers

   Expected result: the tool starts a real Ralph iteration flow, persists `.ralph/sessions/current.json` plus the current session record inside the target feature folder, and reports typed run status instead of raw shell-script logging.

## Validation and Acceptance

Acceptance is behavioral, not structural. The rewrite is complete only when a user can still point Ralph at a feature folder and get the same high-level workflow as today, but with stronger operator controls.

For CLI acceptance, Ralph must expose `run`, `resume`, and `retro` through the installed `ralph` console script, and `./ralph/ralph.sh` must still accept the existing legacy flags. `--retro-only` through the shell shim must resolve to the Python retrospective workflow without requiring any operator-visible migration.

For execution acceptance, `run` must keep the current loop semantics: one coding iteration at a time, one active run per feature, stop on `COMPLETE`, `BLOCKED`, hard failure, or iteration cap, and run retrospective automatically after implementation completion.

For state acceptance, each feature run must create and maintain a `.ralph/` directory containing machine-readable session metadata sufficient for `resume`. Interrupting a run after a completed iteration must allow `resume` to continue from persisted state rather than starting over. Each run must produce a per-session record under `.ralph/sessions/`, update `.ralph/sessions/current.json`, and enforce single active ownership through `.ralph/lock`. `run` must fail when an incomplete session already exists, and `resume` must be the only command that can continue or reclaim that session.

For failure-model acceptance, the harness must classify at least these failure categories explicitly: agent execution failure, prompt-loading failure, feature-folder validation failure, malformed status contract, bookkeeping validation failure, and retrospective failure. Retrospective failure after successful implementation must surface as degraded success, not as a full run failure.

For testing acceptance, deterministic tests in `ralph/tests/` must cover:

- successful multi-iteration completion
- blocked run
- malformed first-line status
- missing `ralph.txt` in retrospective mode
- resume after an interrupted run
- run fails when an incomplete session already exists
- stale-lock recovery through `resume`
- bookkeeping validation failure
- degraded success when retrospective fails after implementation completes

For repo-surface acceptance, `make ralph-test` and `make ralph-verify` must exist and succeed in the development environment prepared for this repository.

## Idempotence and Recovery

The Python CLI must be safe to rerun against the same feature folder. Re-running `retro` against a completed feature folder should overwrite or regenerate only the retrospective state and output it owns. Re-running `run` against a feature with an active lock or an incomplete current session must fail fast with a clear message rather than creating a second concurrent run.

If a run is interrupted, the operator recovery path is `resume`, not manual editing of `.ralph/sessions/*.json`, `.ralph/sessions/current.json`, or `.ralph/lock`. The session files should be treated as internal control-plane data. `resume` may reclaim a stale lock automatically under the stale-lock rules above. If state becomes corrupted beyond automated recovery, the fallback is to inspect the human-readable artifacts in the feature folder, delete `.ralph/` intentionally, and start a fresh run. The harness must document that fallback explicitly.

The shell compatibility shim must remain idempotent because it performs only argument translation and delegation. All authoritative validation and mutation must live in Python.

## Artifacts and Notes

The current `codex` invocation in the shell prototype is the behavioral baseline the v1 `CodexAgent` must preserve:

    codex --model "$model" --ask-for-approval never \
      -c shell_environment_policy.inherit=all \
      exec --ephemeral --sandbox danger-full-access \
      -o "$last_message_file" - <<<"$prompt_payload"

The first-line control contract is also non-negotiable because the prompt files and the existing workflow already depend on it:

    RALPH_STATUS=CONTINUE
    RALPH_STATUS=COMPLETE
    RALPH_STATUS=BLOCKED

The Python rewrite may add richer diagnostics and structured state, but it must not silently change that control protocol in v1.

## Interfaces and Dependencies

The Python CLI must support both a modern subcommand surface and the legacy wrapper surface. Agent selection is internal in v1 and resolves to `codex`, but the module boundaries below must make future public agent configurability a non-breaking extension. Session persistence is a separate top-level concern consumed by lifecycle, not part of the lifecycle package itself.

The modern interface is:

- `ralph run --feature-dir <relative-path> [--max-iterations <n>] [--coding-model <name>] [--retro-model <name>]`
- `ralph resume --feature-dir <relative-path>`
- `ralph retro --feature-dir <relative-path> [--retro-model <name>]`

The legacy wrapper surface is:

- `./ralph/ralph.sh --feature-dir <relative-path> [--max-iterations <n>] [--coding-model <name>] [--retro-model <name>]`
- `./ralph/ralph.sh --feature-dir <relative-path> --retro-only [--retro-model <name>]`

The package must define at least these Python interfaces by the end of implementation:

- `ralph.config.RunConfig` representing all resolved run options and important paths.
- `ralph.agents.base.Agent` as the protocol for execution backends.
- `ralph.agents.base.AgentResult` as the structured result of a single agent invocation.
- `ralph.agents.factory.resolve_agent(agent_name: str) -> Agent`.
- `ralph.agents.codex.CodexAgent` implementing `Agent`.
- `ralph.session.RunSessionStore` for `.ralph/` session persistence, current-session pointer updates, and locking.
- `ralph.session.RunLock` as the structured lock record persisted in `.ralph/lock`.
- `ralph.lifecycle.phases.base.Phase` as the shared lifecycle phase contract.
- `ralph.lifecycle.phases.base.PhaseOutcome` with values `next_iteration`, `completed`, `blocked`, and `failed`.
- `ralph.lifecycle.phases.base.PhaseResult` as the structured result of a single phase invocation.
- `ralph.lifecycle.phases.code` owning the coding-phase status parsing and code-phase validation contract.
- `ralph.lifecycle.orchestrator.run(config: RunConfig, agent: Agent) -> RunOutcome`.
- `ralph.lifecycle.orchestrator.resume(config: RunConfig, agent: Agent) -> RunOutcome`.
- `ralph.lifecycle.orchestrator.run_retro(config: RunConfig, agent: Agent) -> RunOutcome`.

Use only the Python standard library in v1 unless a non-stdlib dependency is necessary to achieve deterministic behavior that the standard library cannot provide cleanly. The current requirements do not justify adding external CLI frameworks. `argparse`, `dataclasses`, `json`, `pathlib`, `subprocess`, `tempfile`, `time`, and `typing` are sufficient.

Revision note: 2026-05-08. Created the initial ExecPlan for migrating Ralph from `ralph/ralph.sh` to a standalone Python CLI harness after locking the product and implementation decisions interactively.
Revision note: 2026-05-09. Updated the plan to use the `ralph` package name, explicit lifecycle phases, feature-local session history under `.ralph/sessions/`, and an orchestrator that sequences single-shot phase invocations.
Revision note: 2026-05-09. Refined the package boundaries so `ralph.lifecycle` owns orchestration and phases, and `ralph.agents` isolates concrete agent integrations such as Codex for future configurability.
Revision note: 2026-05-09. Moved prompt ownership and phase-dependent validation into per-phase packages, and lifted session persistence to top-level `ralph.session`.
Revision note: 2026-05-09. Locked the public Python CLI to the installed `ralph` console script, made `run` versus `resume` orchestrator-owned and mutually exclusive for incomplete sessions, specified stale-lock recovery semantics, and replaced vague status validation with explicit `tasks.json`-based checks.
