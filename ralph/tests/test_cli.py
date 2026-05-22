from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

from ralph import cli
from ralph.logging import CompositeEventSink, TerminalEventSink
from ralph.orchestrator import RunCompleted, RunContext


class CliTests(TestCase):
    def test_build_parser_exposes_run_flags_and_defaults(self) -> None:
        parser = cli.build_parser()
        help_buffer = StringIO()

        with self.assertRaises(SystemExit) as exc_info, redirect_stdout(help_buffer):
            parser.parse_args(["run", "-h"])

        self.assertEqual(exc_info.exception.code, 0)

        help_text = help_buffer.getvalue()
        for flag in ("ralph run", "--agent", "--model", "--max-iterations", "--log"):
            self.assertIn(flag, help_text)

        args = parser.parse_args(["run", "/tmp/feature-dir"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.feature_dir, "/tmp/feature-dir")
        self.assertEqual(args.agent, "codex")
        self.assertEqual(args.model, "gpt-5.4")
        self.assertEqual(args.max_iterations, 50)
        self.assertIsNone(args.log)

    def test_main_run_passes_default_context_to_orchestrator(self) -> None:
        with patch("ralph.cli.run_harness", return_value=RunCompleted()) as run_harness:
            exit_code = cli.main(["run", "/tmp/feature-dir"])

        self.assertEqual(exit_code, cli.EXIT_SUCCESS)
        run_context = run_harness.call_args.args[0]
        self.assertIsInstance(run_context, RunContext)
        self.assertEqual(run_context.feature_dir, Path("/tmp/feature-dir"))
        self.assertEqual(run_context.agent_name, "codex")
        self.assertEqual(run_context.model, "gpt-5.4")
        self.assertEqual(run_context.max_iterations, 50)
        self.assertIsNone(run_context.log_path)
        self.assertIsInstance(run_harness.call_args.kwargs["event_sink"], TerminalEventSink)

    def test_main_run_attaches_jsonl_sink_when_log_path_is_provided(self) -> None:
        with TemporaryDirectory() as temp_dir:
            feature_dir = Path(temp_dir) / "feature"
            feature_dir.mkdir()
            log_path = Path(temp_dir) / "events.jsonl"

            with patch("ralph.cli.run_harness", return_value=RunCompleted()) as run_harness:
                exit_code = cli.main(
                    [
                        "run",
                        str(feature_dir),
                        "--agent",
                        "codex",
                        "--model",
                        "gpt-5.4",
                        "--max-iterations",
                        "7",
                        "--log",
                        str(log_path),
                    ]
                )

        self.assertEqual(exit_code, cli.EXIT_SUCCESS)
        run_context = run_harness.call_args.args[0]
        self.assertEqual(run_context.feature_dir, feature_dir)
        self.assertEqual(run_context.agent_name, "codex")
        self.assertEqual(run_context.model, "gpt-5.4")
        self.assertEqual(run_context.max_iterations, 7)
        self.assertEqual(run_context.log_path, log_path)

        event_sink = run_harness.call_args.kwargs["event_sink"]
        self.assertIsInstance(event_sink, CompositeEventSink)
        self.assertIsInstance(event_sink.sinks[0], TerminalEventSink)
        self.assertEqual(len(event_sink.sinks), 2)

    def test_positive_iteration_limit_rejects_zero(self) -> None:
        parser = cli.build_parser()

        with self.assertRaises(SystemExit) as exc_info, redirect_stderr(StringIO()):
            parser.parse_args(["run", "/tmp/feature-dir", "--max-iterations", "0"])

        self.assertEqual(exc_info.exception.code, 2)
