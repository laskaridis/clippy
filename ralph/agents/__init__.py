from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from .base import Agent, AgentRequest, AgentResult
from .codex import CodexAgent


class UnknownAgentError(ValueError):
    """Raised when a caller asks for a built-in agent that does not exist."""


_BUILTIN_AGENTS: Mapping[str, Agent] = MappingProxyType(
    {
        "codex": CodexAgent(),
    }
)


def available_agents() -> tuple[str, ...]:
    """Return the statically registered built-in agent names."""

    return tuple(_BUILTIN_AGENTS)


def get_agent(name: str) -> Agent:
    """Resolve a built-in agent by name."""

    try:
        return _BUILTIN_AGENTS[name]
    except KeyError as exc:  # pragma: no cover - defensive branch
        raise UnknownAgentError(f"Unknown built-in agent: {name}") from exc


__all__ = [
    "Agent",
    "AgentRequest",
    "AgentResult",
    "CodexAgent",
    "UnknownAgentError",
    "available_agents",
    "get_agent",
]
