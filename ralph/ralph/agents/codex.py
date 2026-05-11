"""Codex-backed Ralph agent implementation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from ralph.agents.base import Agent, AgentResult
from ralph.errors import AgentExecutionError

CODEX_BINARY = "codex"
CODEX_OUTPUT_PREFIX = "ralph-codex-"
CODEX_OUTPUT_SUFFIX = ".txt"


@dataclass(frozen=True, slots=True)
class CodexAgent(Agent):
    """Concrete v1 Ralph agent that shells out to the Codex CLI."""

    binary: str = CODEX_BINARY

    def invoke(self, prompt_text: str, *, model: str) -> AgentResult:
        output_path = self._create_output_path()
        command = self._build_command(model=model, output_path=output_path)

        try:
            completed = subprocess.run(
                command,
                input=prompt_text,
                text=True,
                capture_output=True,
                check=False,
            )
            payload = self._read_payload(output_path)
            return AgentResult(
                stdout=payload,
                exit_code=completed.returncode,
                metadata=self._build_metadata(
                    command=command,
                    completed=completed,
                    output_path=output_path,
                ),
            )
        except FileNotFoundError as exc:
            raise AgentExecutionError(
                f"Codex binary not found: {self.binary}"
            ) from exc
        except OSError as exc:
            raise AgentExecutionError(
                f"Codex invocation failed before completion: {exc}"
            ) from exc
        finally:
            self._cleanup_output_path(output_path)

    def _build_command(self, *, model: str, output_path: Path) -> list[str]:
        return [
            self.binary,
            "--model",
            model,
            "--ask-for-approval",
            "never",
            "-c",
            "shell_environment_policy.inherit=all",
            "exec",
            "--ephemeral",
            "--sandbox",
            "danger-full-access",
            "-o",
            str(output_path),
            "-",
        ]

    def _create_output_path(self) -> Path:
        fd, raw_path = tempfile.mkstemp(prefix=CODEX_OUTPUT_PREFIX, suffix=CODEX_OUTPUT_SUFFIX)
        os.close(fd)
        return Path(raw_path)

    @staticmethod
    def _read_payload(output_path: Path) -> str:
        if not output_path.exists():
            return ""
        return output_path.read_text(encoding="utf-8", errors="replace")

    @staticmethod
    def _build_metadata(*, command: list[str], completed: subprocess.CompletedProcess[str], output_path: Path) -> dict[str, Any]:
        return {
            "agent": CODEX_BINARY,
            "command": command,
            "output_path": str(output_path),
            "process_stdout": completed.stdout,
            "process_stderr": completed.stderr,
            "returncode": completed.returncode,
        }

    @staticmethod
    def _cleanup_output_path(output_path: Path) -> None:
        output_path.unlink(missing_ok=True)


__all__ = ["CODEX_BINARY", "CodexAgent"]
