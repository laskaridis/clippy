"""Reusable fake-agent helpers for deterministic Ralph tests.

The helpers stay test-only and mirror the shared Agent contract closely enough
to exercise orchestration flows without invoking the real Codex adapter.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TypeAlias

from ralph.agents.base import AgentResult

FakeAgentStep: TypeAlias = AgentResult | BaseException


@dataclass(frozen=True, slots=True)
class FakeAgentCall:
    """Record one fake-agent invocation."""

    prompt_text: str
    model: str


@dataclass(slots=True)
class FakeAgent:
    """Deterministic Agent implementation for tests.

    The fake consumes a scripted sequence of AgentResult values or exceptions,
    records each invocation, and fails loudly when a test asks for more steps
    than were scripted.
    """

    responses: Sequence[FakeAgentStep] = field(default_factory=tuple)
    calls: list[FakeAgentCall] = field(default_factory=list, init=False)
    _cursor: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.responses = tuple(self.responses)

    def invoke(self, prompt_text: str, *, model: str) -> AgentResult:
        self.calls.append(FakeAgentCall(prompt_text=prompt_text, model=model))
        if self._cursor >= len(self.responses):
            raise AssertionError(
                f"FakeAgent ran out of scripted responses after {self._cursor} invocation(s)."
            )

        response = self.responses[self._cursor]
        self._cursor += 1
        if isinstance(response, BaseException):
            raise response
        return response

    @property
    def invocation_count(self) -> int:
        """Return the number of scripted invocations consumed so far."""

        return self._cursor


def scripted_agent(*responses: FakeAgentStep) -> FakeAgent:
    """Build a fake agent from a scripted response sequence."""

    return FakeAgent(responses=responses)


def agent_result(
    stdout: str,
    *,
    exit_code: int = 0,
    metadata: dict[str, object] | None = None,
) -> AgentResult:
    """Convenience constructor for deterministic fake responses."""

    return AgentResult(stdout=stdout, exit_code=exit_code, metadata={} if metadata is None else dict(metadata))


def agent_error(message: str) -> RuntimeError:
    """Build a predictable exception for controlled fake-agent failures."""

    return RuntimeError(message)


__all__ = [
    "FakeAgent",
    "FakeAgentCall",
    "FakeAgentStep",
    "agent_error",
    "agent_result",
    "scripted_agent",
]
