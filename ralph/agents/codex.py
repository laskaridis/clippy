from __future__ import annotations

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .base import AgentRequest, AgentResult


@dataclass(frozen=True, slots=True)
class CodexAgent:
    """AFK Codex runner used by the Ralph MVP."""

    name: str = "codex"
    executable: str = "codex"

    def invoke(self, request: AgentRequest) -> AgentResult:
        output_path = self._make_output_path()
        raw_response: str | None = None
        command = (
            self.executable,
            "--model",
            request.model,
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
        )

        try:
            completed = subprocess.run(
                command,
                input=request.prompt,
                text=True,
                capture_output=True,
                check=False,
            )
            raw_response = self._read_output_path(output_path)
        except OSError as exc:
            raw_response = self._read_output_path(output_path)
            return AgentResult(
                success=False,
                command=command,
                stderr=str(exc),
                raw_response=raw_response,
                error_message=str(exc),
            )
        finally:
            output_path.unlink(missing_ok=True)

        error_message = None
        if completed.returncode != 0:
            error_message = completed.stderr.strip() or (
                f"{self.name} exited with status {completed.returncode}."
            )

        return AgentResult(
            success=completed.returncode == 0,
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            raw_response=raw_response,
            error_message=error_message,
        )

    def _make_output_path(self) -> Path:
        handle = tempfile.NamedTemporaryFile(prefix="ralph-codex-", suffix=".txt", delete=False)
        try:
            return Path(handle.name)
        finally:
            handle.close()

    @staticmethod
    def _read_output_path(output_path: Path) -> str | None:
        if not output_path.exists():
            return None
        return output_path.read_text(encoding="utf-8")
