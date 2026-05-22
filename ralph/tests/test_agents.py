from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from ralph.agents import CodexAgent, UnknownAgentError, available_agents, get_agent
from ralph.agents.base import AgentRequest, AgentResult


class AgentsTests(TestCase):
    def test_registry_resolves_codex_and_rejects_unknown_agents(self) -> None:
        self.assertEqual(available_agents(), ("codex",))
        self.assertIsInstance(get_agent("codex"), CodexAgent)

        with self.assertRaises(UnknownAgentError):
            get_agent("missing")

    def test_codex_agent_preserves_successful_raw_response(self) -> None:
        agent = CodexAgent()

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "response.txt"

            def fake_run(command, input, text, capture_output, check):
                self.assertEqual(input, "prompt body")
                self.assertTrue(text)
                self.assertTrue(capture_output)
                self.assertFalse(check)

                output_index = command.index("-o") + 1
                Path(command[output_index]).write_text(
                    '{"outcome":"complete"}', encoding="utf-8"
                )
                return SimpleNamespace(returncode=0, stdout="stdout", stderr="")

            with patch.object(CodexAgent, "_make_output_path", return_value=output_path), patch(
                "ralph.agents.codex.subprocess.run", side_effect=fake_run
            ) as run_mock:
                result = agent.invoke(
                    AgentRequest(
                        prompt="prompt body",
                        model="gpt-5.4",
                        feature_dir=Path(temp_dir) / "feature",
                        run_id="run-123",
                    )
                )

        self.assertTrue(result.success)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "stdout")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.raw_response, '{"outcome":"complete"}')
        self.assertEqual(run_mock.call_count, 1)
        self.assertEqual(
            result.command,
            (
                "codex",
                "--model",
                "gpt-5.4",
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
            ),
        )

    def test_codex_agent_surfaces_subprocess_failures_with_raw_response(self) -> None:
        agent = CodexAgent()

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "response.txt"

            def fake_run(command, input, text, capture_output, check):
                Path(command[command.index("-o") + 1]).write_text(
                    '{"outcome":"fail","failure_summary":"raw failure"}',
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=19, stdout="", stderr="codex error")

            with patch.object(CodexAgent, "_make_output_path", return_value=output_path), patch(
                "ralph.agents.codex.subprocess.run", side_effect=fake_run
            ):
                result = agent.invoke(
                    AgentRequest(
                        prompt="prompt body",
                        model="gpt-5.4",
                        feature_dir=Path(temp_dir) / "feature",
                        run_id="run-123",
                    )
                )

        self.assertFalse(result.success)
        self.assertEqual(result.returncode, 19)
        self.assertEqual(result.stderr, "codex error")
        self.assertEqual(result.error_message, "codex error")
        self.assertEqual(
            result.raw_response,
            '{"outcome":"fail","failure_summary":"raw failure"}',
        )

    def test_codex_agent_surfaces_oserror_as_structured_failure(self) -> None:
        agent = CodexAgent()

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "response.txt"

            with patch.object(CodexAgent, "_make_output_path", return_value=output_path), patch(
                "ralph.agents.codex.subprocess.run",
                side_effect=OSError("codex not installed"),
            ):
                result = agent.invoke(
                    AgentRequest(
                        prompt="prompt body",
                        model="gpt-5.4",
                        feature_dir=Path(temp_dir) / "feature",
                        run_id="run-123",
                    )
                )

        self.assertFalse(result.success)
        self.assertIsNone(result.returncode)
        self.assertEqual(result.stderr, "codex not installed")
        self.assertEqual(result.error_message, "codex not installed")
        self.assertIsNone(result.raw_response)
