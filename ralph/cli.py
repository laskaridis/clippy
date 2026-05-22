from __future__ import annotations

import argparse
from contextlib import ExitStack
from pathlib import Path
from collections.abc import Sequence
import sys

from .logging import CompositeEventSink, EventSink, JsonlEventSink, TerminalEventSink
from .orchestrator import (
    RunBlocked,
    RunCompleted,
    RunContext,
    RunFailed,
    RunOutcome,
    RunSetupError,
    RunUsageError,
    run as run_harness,
)


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_SETUP_ERROR = 2
EXIT_BLOCKED = 3


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:  # pragma: no cover - argparse validates this path
        raise argparse.ArgumentTypeError("must be a positive integer") from exc

    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ralph",
        description="Run the Ralph feature-delivery harness.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    run_parser = subcommands.add_parser(
        "run",
        help="Run the Ralph workflow against a feature directory.",
    )
    run_parser.add_argument(
        "feature_dir",
        help="Path to the feature directory that contains the Ralph workflow inputs.",
    )
    run_parser.add_argument(
        "--agent",
        default="codex",
        help="Built-in agent name to use for the run (default: codex).",
    )
    run_parser.add_argument(
        "--model",
        default="gpt-5.4",
        help="Model name to pass through to the selected agent (default: gpt-5.4).",
    )
    run_parser.add_argument(
        "--max-iterations",
        type=_positive_int,
        default=50,
        help="Maximum number of code-step iterations to run (default: 50).",
    )
    run_parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help="Optional JSONL event-log path.",
    )
    return parser


def _run_command(args: argparse.Namespace) -> int:
    run_context = RunContext(
        feature_dir=Path(args.feature_dir),
        agent_name=args.agent,
        model=args.model,
        max_iterations=args.max_iterations,
        log_path=args.log,
    )
    terminal_sink = TerminalEventSink()
    with ExitStack() as stack:
        sinks: list[EventSink] = [terminal_sink]
        if args.log is not None:
            try:
                jsonl_sink = stack.enter_context(JsonlEventSink(args.log))
            except OSError as exc:
                print(f"Unable to open JSONL log path {args.log}: {exc}", file=sys.stderr)
                return EXIT_SETUP_ERROR
            sinks.append(jsonl_sink)

        event_sink = (
            terminal_sink
            if len(sinks) == 1
            else CompositeEventSink(tuple(sinks))
        )
        outcome = run_harness(run_context, event_sink=event_sink)
    return _exit_code_for_outcome(outcome)


def _exit_code_for_outcome(outcome: RunOutcome) -> int:
    if isinstance(outcome, RunCompleted):
        return EXIT_SUCCESS

    if isinstance(outcome, RunBlocked):
        return EXIT_BLOCKED

    if isinstance(outcome, RunFailed):
        return EXIT_FAILURE

    if isinstance(outcome, RunSetupError):
        return EXIT_SETUP_ERROR

    if isinstance(outcome, RunUsageError):
        return EXIT_SETUP_ERROR

    raise TypeError(f"Unhandled run outcome type: {type(outcome)!r}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_command(args)

    parser.error(f"Unknown command: {args.command}")
    return 2
