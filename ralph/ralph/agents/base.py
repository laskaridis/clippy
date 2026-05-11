"""Shared agent protocol for Ralph backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, runtime_checkable


AgentMetadata = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class AgentResult:
    """Structured result for one agent invocation."""

    stdout: str
    exit_code: int
    metadata: AgentMetadata = field(default_factory=dict)


@runtime_checkable
class Agent(Protocol):
    """Execution protocol for agent backends."""

    def invoke(self, prompt_text: str, *, model: str) -> AgentResult:
        """Run one prompt against the backend and return a structured result."""

