"""Single-shot coding phase execution for Ralph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ralph.agents.base import Agent
from ralph.config import RunConfig
from ralph.lifecycle.phases.base import Phase, PhaseResult
from ralph.lifecycle.phases.code.prompt import render_code_prompt
from ralph.lifecycle.phases.code.status import CodeStatusResult, parse_code_status
from ralph.lifecycle.phases.code.validation import CodeBookkeepingResult, validate_code_bookkeeping

CODE_PHASE_NAME = "code"


@dataclass(frozen=True, slots=True)
class CodePhase(Phase):
    """Run exactly one coding pass for a resolved Ralph feature folder."""

    config: RunConfig
    agent: Agent
    prompt_text: str | None = None

    def run(self) -> PhaseResult:
        rendered_prompt = render_code_prompt(
            self.config.feature_dir,
            prompt_text=self.prompt_text,
        )
        agent_result = self.agent.invoke(rendered_prompt, model=self.config.coding_model)
        status_result = parse_code_status(agent_result.stdout)
        bookkeeping_result = validate_code_bookkeeping(self.config, status_result)
        return PhaseResult(
            outcome=status_result.phase_outcome,
            metadata=_build_phase_metadata(
                config=self.config,
                agent_result_metadata=agent_result.metadata,
                agent_exit_code=agent_result.exit_code,
                status_result=status_result,
                bookkeeping_result=bookkeeping_result,
            ),
        )


def run_code_phase(
    config: RunConfig,
    agent: Agent,
    *,
    prompt_text: str | None = None,
) -> PhaseResult:
    """Convenience wrapper for one coding-phase invocation."""

    return CodePhase(config=config, agent=agent, prompt_text=prompt_text).run()


def _build_phase_metadata(
    *,
    config: RunConfig,
    agent_result_metadata: Mapping[str, Any],
    agent_exit_code: int,
    status_result: CodeStatusResult,
    bookkeeping_result: CodeBookkeepingResult,
) -> dict[str, Any]:
    return {
        "phase": CODE_PHASE_NAME,
        "feature_dir": str(config.feature_dir),
        "coding_model": config.coding_model,
        "agent_exit_code": agent_exit_code,
        "agent_metadata": dict(agent_result_metadata),
        "status": status_result.status.value,
        "blocker_line": status_result.blocker_line,
        "bookkeeping": {
            "tasks_path": str(bookkeeping_result.tasks_path),
            "ralph_txt_path": str(bookkeeping_result.ralph_txt_path),
            "task_count": bookkeeping_result.task_count,
            "completed_task_count": bookkeeping_result.completed_task_count,
            "pending_task_count": bookkeeping_result.pending_task_count,
            "ralph_txt_created": bookkeeping_result.ralph_txt_created,
            "all_tasks_completed": bookkeeping_result.all_tasks_completed,
        },
    }


__all__ = [
    "CODE_PHASE_NAME",
    "CodePhase",
    "run_code_phase",
]
