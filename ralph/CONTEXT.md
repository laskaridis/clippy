# Ralph

Ralph is an opinionated reusable harness for running a feature-delivery lifecycle over a structured feature directory.

## Language

**Ralph harness CLI**:
A reusable, opinionated Python command-line application that owns and executes the Ralph workflow and is exposed through `ralph run <path>`, `python -m ralph`, and the `ralph` console script.
_Avoid_: script, bash harness, repo-only tool

**Ralph lifecycle orchestrator**:
The Ralph harness CLI component that owns step sequencing and determines the next step from prior step outputs.
_Avoid_: step-local loop controller, agent implementation

**Step**:
A bounded unit of Ralph lifecycle work with a stable execution contract and structured result.
_Avoid_: script phase, ad hoc command

**Code step**:
A **Step** that performs one coding iteration by invoking the selected coding agent once.
_Avoid_: whole loop, generic task runner, user-defined plugin step

**Step result**:
The structured output of a Ralph workflow step that reports its outcome and any typed execution facts needed by the orchestrator.
_Avoid_: free-form agent output, workflow hint

**Task selection**:
The act of choosing the next eligible implementation task from `tasks.json` for the current coding iteration.
_Avoid_: orchestrator scheduling, external planning

**Agent**:
The Ralph collaborator responsible for executing a step prompt with a specific coding system and returning its raw result.
_Avoid_: adapter, workflow engine, step implementation

**AFK execution**:
Ralph execution mode where built-in agents run without interactive approval and only stop for terminal blocked or failed outcomes.
_Avoid_: interactive approval loop, attended execution

**Step id**:
A stable identifier for a Ralph **Step** used by the orchestrator, tests, and observability.
_Avoid_: language-specific type check, implicit class name

**Lifecycle module**:
The Ralph module that defines lifecycle concepts and contracts such as **Step** and **Step result**.
_Avoid_: agent execution, CLI wiring

**Workflow module**:
The Ralph module that contains built-in workflow step implementations such as the **Code step**.
_Avoid_: generic lifecycle contracts, agent registry

**Orchestrator module**:
The Ralph module that owns the **Ralph lifecycle orchestrator** and the **Run context**.
_Avoid_: step-local parsing, agent-specific command details

**Agents module**:
The Ralph module that defines **Agent** implementations and agent execution results.
_Avoid_: workflow transitions, step contracts

**Logging module**:
The Ralph module that defines run events, terminal presentation, and JSONL event sinks.
_Avoid_: workflow transitions, agent subprocess logic

**Run event**:
A structured event record emitted by the **Logging module** for terminal output or JSONL logging.
_Avoid_: ad hoc debug print, free-form log line

**Run context**:
The structured immutable execution context for one Ralph run that exposes shared run inputs to the orchestrator and steps.
_Avoid_: global state, unbounded service bag

**Feature directory**:
The directory passed to Ralph for a run that contains the workflow artifacts required by the active Ralph workflow.
_Avoid_: arbitrary working directory, hidden internal state

## Relationships

- The **Ralph harness CLI** contains the **Ralph lifecycle orchestrator**
- The **Orchestrator module** contains the **Ralph lifecycle orchestrator** and the **Run context**
- The **Ralph lifecycle orchestrator** executes one **Step** at a time during a run
- Every **Step** execution returns one **Step result**
- The **Lifecycle module** defines **Step** and **Step result**
- The **Code step** is a kind of **Step**
- The **Code step** has the **Step id** `code`
- The **Workflow module** contains the **Code step**
- The **Code step** owns **Task selection**
- The **Code step** invokes one **Agent**
- The **Agents module** contains **Agent** implementations and agent execution results
- The **Logging module** contains run-event presenters and JSONL sinks
- Every **Step** reads shared run data through the **Run context**
- The **Run context** includes one **Feature directory**
- The **Run context** includes one stable run identifier
- **Agent** execution in Ralph uses **AFK execution**
- Every **Run event** includes a timestamp and run identifier

## Example dialogue

> **Dev:** "Does the **Code step** own the whole Ralph loop?"
> **Domain expert:** "No — the **Ralph lifecycle orchestrator** owns the loop, and the **Code step** performs one iteration."

## Flagged ambiguities

- "workflow profile" was used to mean a project-owned workflow definition — resolved: Ralph owns the workflow; projects only supply inputs and selected runtime choices such as agent selection.
- "Code step" was used to mean the whole coding loop — resolved: the loop belongs to the **Ralph lifecycle orchestrator**; the **Code step** performs one coding iteration.
- "next_hint" was proposed as a step output — resolved: steps stay agnostic of the wider workflow, so transition choice belongs only to the **Ralph lifecycle orchestrator**.
- "task selection" could have been placed in the orchestrator — resolved: **Task selection** belongs to the **Code step** and is implemented through the code-step prompt.
- "AgentAdapter" was proposed as the extension point name — resolved: use **Agent** as the technology-agnostic term.
- "step input" risked mixing step-local data with orchestration concerns — resolved: shared run inputs are exposed through a bounded **Run context**, while loop control stays in the **Ralph lifecycle orchestrator**.
- The orchestrator could have inspected `tasks.json` directly to decide lifecycle transitions — resolved: the **Ralph lifecycle orchestrator** relies only on **Step result** outcomes.
- "blocked" could have implied resumable run state — resolved: both `blocked` and `fail` are terminal run outcomes in the MVP; `blocked` differs by carrying a human unblock contract.
- Agent discovery could have been user-extensible at runtime — resolved: **Agent** implementations are built into Ralph and selected from a static built-in registry.
- Workflow artifact content does not belong to the harness — resolved: the **Ralph lifecycle orchestrator** validates required artifact existence in the **Feature directory**, while step implementations own artifact semantics and usage.
- Agent approval policy could have been user-configurable — resolved: Ralph uses **AFK execution** in the MVP, so built-in agents run without interactive approval.
- Workflow progression could have been user-configurable or data-driven — resolved: the **Ralph lifecycle orchestrator** hard-codes transitions based on **Step id** and **Step result** outcome.
- Module boundaries could have been grouped more generically — resolved: **Workflow module** holds built-in steps, **Lifecycle module** holds step contracts, **Agents module** holds agents and agent results, and **Orchestrator module** holds run orchestration and run context.
- The public CLI is Python-first — resolved: `ralph run <path>` and `python -m ralph` are canonical, while `ralph/ralph.sh` is only a compatibility wrapper.
- Run metadata was previously narrowed too far — resolved: the immutable **Run context** includes a stable run identifier for shared observability correlation.
