"""Agent-resolution boundary for Ralph backends."""

from __future__ import annotations

from ralph.agents.base import Agent
from ralph.agents.codex import CODEX_BINARY, CodexAgent
from ralph.errors import AgentExecutionError


def resolve_agent(agent_name: str) -> Agent:
    """Return the concrete agent backend for a resolved agent identifier."""

    normalized_name = agent_name.strip().lower()
    if normalized_name == CODEX_BINARY:
        return CodexAgent()
    raise AgentExecutionError(f"Unknown Ralph agent identifier: {agent_name!r}")


__all__ = ["resolve_agent"]
