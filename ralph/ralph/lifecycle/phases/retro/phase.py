"""Single-shot retrospective phase execution for Ralph."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from ralph.agents.base import Agent
from ralph.config import RunConfig
from ralph.lifecycle.phases.base import Phase, PhaseOutcome, PhaseResult
from ralph.lifecycle.phases.retro.prompt import render_retro_prompt
from ralph.lifecycle.phases.retro.validation import validate_retro_prerequisites

RETRO_PHASE_NAME = "retro"


@dataclass(frozen=True, slots=True)
class RetroPhase(Phase):
    """Run exactly one retrospective pass for a resolved Ralph feature folder."""

    config: RunConfig
    agent: Agent
    prompt_text: str | None = None

    def run(self) -> PhaseResult:
        ralph_txt_path = validate_retro_prerequisites(self.config)
        rendered_prompt = render_retro_prompt(
            self.config.feature_dir,
            prompt_text=self.prompt_text,
        )
        agent_result = self.agent.invoke(rendered_prompt, model=self.config.retro_model)
        retro_output_present = _retro_output_present(self.config)
        outcome = (
            PhaseOutcome.COMPLETED
            if agent_result.exit_code == 0 and retro_output_present
            else PhaseOutcome.FAILED
        )
        return PhaseResult(
            outcome=outcome,
            metadata=_build_phase_metadata(
                config=self.config,
                agent_result_metadata=agent_result.metadata,
                agent_exit_code=agent_result.exit_code,
                ralph_txt_path=ralph_txt_path,
                prompt_chars=len(rendered_prompt),
                retro_output_present=retro_output_present,
                response_chars=len(agent_result.stdout),
            ),
        )


def run_retro_phase(
    config: RunConfig,
    agent: Agent,
    *,
    prompt_text: str | None = None,
) -> PhaseResult:
    """Convenience wrapper for one retrospective-phase invocation."""

    return RetroPhase(config=config, agent=agent, prompt_text=prompt_text).run()


def _retro_output_present(config: RunConfig) -> bool:
    return config.retro_path.exists() and config.retro_path.is_file()


def _build_phase_metadata(
    *,
    config: RunConfig,
    agent_result_metadata: Mapping[str, Any],
    agent_exit_code: int,
    ralph_txt_path: Path,
    prompt_chars: int,
    retro_output_present: bool,
    response_chars: int,
) -> dict[str, Any]:
    return {
        "phase": RETRO_PHASE_NAME,
        "feature_dir": str(config.feature_dir),
        "retro_model": config.retro_model,
        "agent_exit_code": agent_exit_code,
        "agent_metadata": dict(agent_result_metadata),
        "ralph_txt_path": str(ralph_txt_path),
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "retro_output_path": str(config.retro_path),
        "retro_output_present": retro_output_present,
    }


__all__ = [
    "RETRO_PHASE_NAME",
    "RetroPhase",
    "run_retro_phase",
]
