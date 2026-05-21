# Feature Specification: Ralph Harness CLI MVP

## Purpose / Big Picture

Ralph currently works as a Bash script that can drive a coding loop, but it is hard to evolve, hard to test, and too tightly tied to one implementation style. This feature turns Ralph into an opinionated Python command-line tool that keeps the current development-loop value while making the harness easier to extend, observe, and reuse across projects.

After this change, a user can run `ralph run <path>` against a feature directory and rely on a stable harness that owns the Ralph lifecycle, executes one coding iteration at a time through a built-in agent, reports clear progress in the terminal, and optionally writes a machine-readable run log for automation and debugging.

## User stories

### UC-001: Run an opinionated Ralph coding workflow from a stable CLI

For the Ralph harness CLI, we need to replace the current shell entrypoint with a stable Python command-line workflow, so that users can run the Ralph coding loop through a reusable and installable tool.

#### Constraints

- The MVP only covers the `run` mode.
- The public CLI must use `ralph run <path>` as the primary entrypoint.
- The `<path>` argument represents the feature directory for the current built-in workflow.
- The workflow remains opinionated and built into Ralph rather than user-configurable.
- Ralph must validate that the required workflow artifacts exist before step execution begins.
- Ralph must keep `ralph/ralph.sh` as a temporary compatibility wrapper until the new CLI is proven.

#### Acceptance criteria

- **AC-001:** Given a feature directory that contains the required workflow artifacts, When a user runs `ralph run <path>`, Then Ralph starts the built-in coding workflow through the Python CLI.
- **AC-002:** Given a feature directory path is missing or invalid, When a user runs `ralph run <path>`, Then Ralph exits with a setup error before invoking any agent.
- **AC-003:** Given a user still invokes `ralph/ralph.sh` during migration, When they pass the legacy arguments, Then the wrapper delegates to the new Python CLI behavior instead of reimplementing the workflow itself.

### UC-002: Observe Ralph runs clearly in terminal output and optional machine-readable logs

For the Ralph harness CLI, we need to provide actionable run feedback, so that users and automation can understand what Ralph is doing and why a run succeeded, blocked, or failed.

#### Constraints

- Console progress output is always enabled.
- Machine-readable logging is optional and only enabled when the user passes `--log <path>`.
- The machine-readable log format must be JSONL.
- The JSONL event schema is a stable public contract.
- The machine-readable log must capture step and agent activity without changing the workflow artifacts managed by the model.

#### Acceptance criteria

- **AC-001:** Given a user runs `ralph run <path>`, When Ralph executes the workflow, Then the terminal output shows step progress, agent usage, and the final run outcome in a clear human-readable form.
- **AC-002:** Given a user runs `ralph run <path> --log <file>`, When Ralph executes the workflow, Then Ralph writes JSONL events to the requested path using the documented event schema.
- **AC-003:** Given a run fails because a step result cannot be parsed or validated, When `--log <file>` is enabled, Then the machine-readable log preserves the raw failed agent response for debugging.

### UC-003: Run one coding iteration at a time through a built-in agent and step contract

For the Ralph harness CLI, we need each coding iteration to be encapsulated behind a stable step contract, so that Ralph can control the lifecycle cleanly and add future steps later without rewriting the whole harness.

#### Constraints

- The MVP includes only one built-in workflow step: the Code step.
- The Code step performs exactly one coding iteration per execution.
- The Ralph lifecycle orchestrator decides whether to repeat the step, complete the run, block, or fail based only on the returned Step result.
- Task selection remains inside the Code step and is driven through the code-step prompt.
- Built-in agents are statically registered in Ralph and selected by name.
- The default agent is `codex` and the default model is `gpt-5.4`.
- Agent execution is AFK-only in the MVP, with no interactive approval flow.
- The model must return only a JSON string and nothing else.

#### Acceptance criteria

- **AC-001:** Given the Code step finishes an iteration and returns `repeat`, When the orchestrator receives the Step result, Then Ralph reruns the Code step until another terminal or advancement outcome is returned or the iteration cap is reached.
- **AC-002:** Given the Code step returns `complete` and the orchestrator resolves no follow-up step, When Ralph processes the Step result, Then Ralph ends the run successfully.
- **AC-003:** Given the Code step returns `blocked`, When Ralph ends the run, Then Ralph prints the blocker text exactly as returned by the agent and exits with the blocked exit code.
- **AC-004:** Given the Code step returns `fail`, When Ralph ends the run, Then Ralph outputs the failure summary and exits with the failure exit code.

## Requirements

All requirements **must** be expressed strictly using [EARS](./ears-syntax.md) syntax.

### Functional requirements

- **FR-001**: When a user runs `ralph run <path>`, the Ralph harness CLI shall execute the built-in Ralph workflow against the provided feature directory.
- **FR-002**: When the user provides `--agent <agent>`, the Ralph harness CLI shall select that built-in agent by name or fail fast if the name is unknown.
- **FR-003**: When the user omits `--agent`, the Ralph harness CLI shall use `codex` as the default agent.
- **FR-004**: When the user provides `--model <model>`, the Ralph harness CLI shall pass that model selection to the selected agent for the run.
- **FR-005**: When the user omits `--model`, the Ralph harness CLI shall use `gpt-5.4` as the default model.
- **FR-006**: When the user provides `--max-iterations <n>`, the Ralph lifecycle orchestrator shall enforce that run limit.
- **FR-007**: While starting a run, the Ralph lifecycle orchestrator shall validate that the required workflow artifacts exist in the feature directory before invoking any workflow step.
- **FR-008**: When the Ralph lifecycle orchestrator executes the Code step, the Code step shall perform exactly one coding iteration and return one structured Step result.
- **FR-009**: When the Code step invokes an Agent, the Agent shall execute exactly one prompt invocation and return one Agent result.
- **FR-010**: While interpreting the Agent result, the Code step shall parse only a JSON-string response and shall reject any surrounding prose or malformed content.
- **FR-011**: When the Code step receives a valid JSON response, the Code step shall convert that response into one Step result with one of these outcomes only: `repeat`, `complete`, `blocked`, or `fail`.
- **FR-012**: When a Step result outcome is `repeat`, the Ralph lifecycle orchestrator shall rerun the last executed step.
- **FR-013**: When a Step result outcome is `complete`, the Ralph lifecycle orchestrator shall resolve the next step in hard-coded workflow logic and shall complete the run successfully if no follow-up step exists.
- **FR-014**: When a Step result outcome is `blocked`, the Ralph lifecycle orchestrator shall stop the run, print the blocker text exactly as returned by the step result, and exit with the blocked outcome.
- **FR-015**: When a Step result outcome is `fail`, the Ralph lifecycle orchestrator shall stop the run, print the failure summary, and exit with the failure outcome.
- **FR-016**: When the user provides `--log <path>`, the Ralph harness CLI shall write machine-readable JSONL events to that path.
- **FR-017**: While a run is being logged, the Ralph harness CLI shall emit at least `run_started`, `step_started`, `agent_invoked`, `step_finished`, and `run_finished` events.
- **FR-018**: While writing JSONL events, the Ralph harness CLI shall include a stable `run_id` in every event record.
- **FR-019**: When the user invokes the legacy shell entrypoint during migration, the compatibility wrapper shall delegate to the Python CLI instead of running an independent lifecycle implementation.
- **FR-020**: While executing a built-in agent in the MVP, Ralph shall run in AFK mode without interactive approval prompts.

### Non-functional requirements

- **NFR-001**: The Ralph harness CLI shall be modular so that lifecycle orchestration, workflow step logic, and agent execution can be tested independently.
- **NFR-002**: The Ralph harness CLI shall preserve a stable public CLI contract for `ralph run <path>` throughout the MVP.
- **NFR-003**: The Ralph harness CLI shall preserve a stable public JSONL log schema throughout the MVP.
- **NFR-004**: The Ralph harness CLI shall keep the workflow opinionated and built-in for the MVP so that changing the lifecycle requires a Ralph code change and release rather than runtime configuration.
- **NFR-005**: The Ralph harness CLI shall keep `Run context` immutable during a run.
- **NFR-006**: The Ralph harness CLI shall keep human-readable workflow artifacts such as `ralph.txt` model-managed rather than harness-managed.
- **NFR-007**: The Ralph harness CLI shall provide deterministic exit codes that distinguish successful completion, blocked termination, failed termination, and invalid usage or setup errors.

## Solution

Ralph will be rebuilt as a Python CLI package rooted under `ralph/` while preserving the existing shell entrypoint as a temporary delegating wrapper. The new CLI will own a fixed built-in lifecycle with a single MVP step, the Code step, and will run one coding iteration at a time until the lifecycle finishes, blocks, fails, or reaches the iteration cap.

### Key architectural decisions

- Ralph is an opinionated product, not a generic workflow framework.
- The workflow lifecycle and step transitions are built into Ralph and change only through code changes.
- The MVP exposes one public command shape: `ralph run <path>`.
- The MVP supports built-in agents only, starting with `codex`.
- The MVP uses AFK execution only.
- The MVP treats machine-readable JSONL logging as an optional but stable public contract.

### Modules

- `cli`: owns command parsing, defaults, and exit-code mapping.
- `orchestrator`: owns the Ralph lifecycle orchestrator, the immutable Run context, required-artifact validation, and hard-coded workflow transitions.
- `lifecycle`: owns shared lifecycle contracts such as Step and Step result.
- `workflow`: owns built-in workflow step implementations such as the Code step.
- `agents`: owns Agent contracts, Agent results, and built-in agent implementations.

### Interfaces & Schemas

- `Run context` carries the shared run inputs needed across the lifecycle, including the feature directory, selected agent and model options, and a stable run identifier.
- `Step result` uses a strict structured contract with the outcomes `repeat`, `complete`, `blocked`, and `fail`.
- The Code step requires the model to return only JSON and nothing else.
- The blocked outcome includes a plain blocker string that is shown to the user exactly as returned.
- The JSONL event log is a stable schema that includes event type, timestamp, run identifier, and step or agent context where relevant.

### Important technical considerations

- Ralph validates that required workflow artifacts exist before step execution, but it does not own their contents.
- The Code step owns prompt construction, task selection, single-iteration execution, and interpretation of the model response.
- The harness does not manage `ralph.txt`; that file remains model-managed.
- The temporary shell wrapper must not preserve its own logic beyond argument translation and delegation.

## Assumptions

- Users run Ralph against a prepared feature directory that follows the current built-in Ralph workflow contract.
- The required workflow artifacts for the MVP remain `spec.md` and `tasks.json`.
- The existing Codex-based coding flow remains the behavioral baseline for the first built-in agent.
- Future steps such as review, test, or retrospective are out of scope for this MVP but are expected later.
- The environment where Ralph runs can execute the selected built-in agent non-interactively.

## Edge cases

- The user provides a feature directory path that does not exist.
- The feature directory exists but one or more required workflow artifacts are missing.
- The user requests an unknown built-in agent.
- The user passes `--log` without a path.
- The selected agent returns non-JSON output.
- The selected agent returns JSON that does not satisfy the Code step contract.
- The Code step returns `complete` and the orchestrator resolves no follow-up step.
- The Code step returns `blocked` with a blocker message that must be surfaced exactly as received.
- The run reaches the max-iterations limit before the Code step returns a terminal or advancement outcome.

## Out of Scope

- User-defined workflows or runtime workflow composition.
- User-defined or dynamically discovered agents.
- Interactive approval flows or configurable sandbox controls.
- Retrospective support in the MVP.
- Additional built-in steps beyond the Code step.
- Automatic creation of missing workflow artifacts.
- Harness ownership of `ralph.txt` or other model-managed workflow files.
- Deep interpretation or validation of `spec.md`, `tasks.json`, or other workflow artifact contents by the harness.

## Clarifications needed

- None at this stage.
