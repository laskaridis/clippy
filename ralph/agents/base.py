from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AgentRequest:
    """Typed input for one agent invocation."""

    prompt: str
    model: str
    feature_dir: Path
    run_id: str = ""


@dataclass(frozen=True, slots=True)
class AgentResult:
    """Structured outcome of one agent invocation."""

    success: bool
    command: tuple[str, ...]
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    raw_response: str | None = None
    error_message: str | None = None


class Agent(Protocol):
    """A built-in Ralph agent implementation."""

    name: str

    def invoke(self, request: AgentRequest) -> AgentResult:
        """Run the agent once and return a structured result."""

