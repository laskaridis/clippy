from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import cast

from ralph.agents import AgentRequest, AgentResult, UnknownAgentError, get_agent

from ..lifecycle import (
    BlockedStepResult,
    CompleteStepResult,
    FailedStepResult,
    RepeatStepResult,
    StepResult,
)
from ..orchestrator import RunContext


_PROMPT_RESOURCE = "prompts/code.md"


@dataclass(frozen=True, slots=True)
class CodeStep:
    """Built-in single-iteration coding step for the Ralph MVP."""

    step_id: str = "code"

    def execute(self, run_context: RunContext) -> StepResult:
        prompt = self._render_prompt(run_context.feature_dir)

        try:
            agent = get_agent(run_context.agent_name)
        except UnknownAgentError as exc:
            return FailedStepResult(failure_summary=str(exc))

        result = agent.invoke(
            AgentRequest(
                prompt=prompt,
                model=run_context.model,
                feature_dir=run_context.feature_dir,
                run_id=run_context.run_id,
            )
        )

        if not result.success:
            return FailedStepResult(
                failure_summary=result.error_message or self._agent_failure_summary(result),
                raw_response=self._captured_response(result),
            )

        raw_response = self._captured_response(result)
        if raw_response is None or not raw_response.strip():
            return FailedStepResult(
                failure_summary="Agent returned no response body.",
                raw_response=raw_response,
            )

        return self._parse_step_response(raw_response)

    def _render_prompt(self, feature_dir: Path) -> str:
        template = resources.files("ralph").joinpath(_PROMPT_RESOURCE).read_text(encoding="utf-8")
        return template.replace("$ARGUMENTS", str(feature_dir.resolve()))

    def _parse_step_response(self, raw_response: str) -> StepResult:
        try:
            payload = json.loads(raw_response.strip())
        except json.JSONDecodeError as exc:
            return FailedStepResult(
                failure_summary=f"Code step response was not valid JSON: {exc.msg}.",
                raw_response=raw_response,
            )

        if not isinstance(payload, dict):
            return FailedStepResult(
                failure_summary="Code step response must be a JSON object.",
                raw_response=raw_response,
            )

        outcome = payload.get("outcome")
        if not isinstance(outcome, str):
            return FailedStepResult(
                failure_summary="Code step response must include a string outcome field.",
                raw_response=raw_response,
            )

        if outcome == "repeat":
            return self._parse_repeat_response(payload, raw_response)
        if outcome == "complete":
            return self._parse_complete_response(payload, raw_response)
        if outcome == "blocked":
            return self._parse_blocked_response(payload, raw_response)
        if outcome == "fail":
            return self._parse_failed_response(payload, raw_response)

        return FailedStepResult(
            failure_summary=f"Code step response used an unknown outcome: {outcome}.",
            raw_response=raw_response,
        )

    def _parse_repeat_response(self, payload: dict[str, object], raw_response: str) -> StepResult:
        if set(payload) != {"outcome"}:
            return FailedStepResult(
                failure_summary="Code step repeat response must contain only the outcome field.",
                raw_response=raw_response,
            )
        return RepeatStepResult()

    def _parse_complete_response(self, payload: dict[str, object], raw_response: str) -> StepResult:
        if set(payload) != {"outcome"}:
            return FailedStepResult(
                failure_summary="Code step complete response must contain only the outcome field.",
                raw_response=raw_response,
            )
        return CompleteStepResult()

    def _parse_blocked_response(self, payload: dict[str, object], raw_response: str) -> StepResult:
        if set(payload) != {"outcome", "blocker_text"}:
            return FailedStepResult(
                failure_summary="Code step blocked response must contain outcome and blocker_text fields only.",
                raw_response=raw_response,
            )

        blocker_text = payload.get("blocker_text")
        if not self._is_nonempty_text(blocker_text):
            return FailedStepResult(
                failure_summary="Code step blocked response must include a non-empty blocker_text string.",
                raw_response=raw_response,
            )

        return BlockedStepResult(blocker_text=cast(str, blocker_text))

    def _parse_failed_response(self, payload: dict[str, object], raw_response: str) -> StepResult:
        if set(payload) != {"outcome", "failure_summary"}:
            return FailedStepResult(
                failure_summary="Code step fail response must contain outcome and failure_summary fields only.",
                raw_response=raw_response,
            )

        failure_summary = payload.get("failure_summary")
        if not self._is_nonempty_text(failure_summary):
            return FailedStepResult(
                failure_summary="Code step fail response must include a non-empty failure_summary string.",
                raw_response=raw_response,
            )

        return FailedStepResult(
            failure_summary=cast(str, failure_summary),
            raw_response=raw_response,
        )

    @staticmethod
    def _captured_response(result: AgentResult) -> str | None:
        if result.raw_response is not None:
            return result.raw_response
        if result.stdout:
            return result.stdout
        return None

    @staticmethod
    def _agent_failure_summary(result: AgentResult) -> str:
        return result.stderr.strip() or "Agent execution failed without a diagnostic message."

    @staticmethod
    def _is_nonempty_text(value: object) -> bool:
        return isinstance(value, str) and value.strip() != ""
