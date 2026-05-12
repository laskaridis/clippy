"""Public command-line interface for Ralph."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from ralph.agents.factory import resolve_agent
from ralph.config import DEFAULT_CODING_MODEL, DEFAULT_RETRO_MODEL, RunConfig, resolve_run_config
from ralph.errors import RalphError
from ralph.lifecycle.orchestrator import run as run_run
from ralph.lifecycle.phases.retro.phase import run_retro_phase

COMMAND_RUN = "run"
COMMAND_RETRO = "retro"


def build_parser() -> argparse.ArgumentParser:
    """Build the public Ralph CLI parser."""

    parser = argparse.ArgumentParser(
        prog="ralph",
        description="Ralph CLI for feature-folder runs and retrospective passes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    shared = argparse.ArgumentParser(add_help=False)
    _add_common_options(shared)

    subparsers.add_parser(
        COMMAND_RUN,
        parents=[shared],
        help="Start a fresh Ralph run; interrupted work is recovered by running again.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    ).set_defaults(handler=_handle_run)

    subparsers.add_parser(
        COMMAND_RETRO,
        parents=[shared],
        help="Run the retrospective pass only.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    ).set_defaults(handler=_handle_retro)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the installed `ralph` console script."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except RalphError as exc:
        print(f"ralph: {exc}", file=sys.stderr)
        return 1


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--feature-dir",
        required=True,
        help="Relative path to the feature folder that contains spec.md and tasks.json.",
    )
    parser.add_argument(
        "--max-iterations",
        type=_positive_int,
        default=50,
        help="Maximum number of coding iterations before the run stops.",
    )
    parser.add_argument(
        "--coding-model",
        default=None,
        help="Model name used for coding iterations.",
    )
    parser.add_argument(
        "--retro-model",
        default=None,
        help="Model name used for the retrospective pass.",
    )


def _handle_run(args: argparse.Namespace) -> int:
    config = _resolve_config(args, retro_only=False)
    agent = resolve_agent(config.agent_identifier)
    outcome = run_run(config, agent)
    print(outcome.value)
    return _exit_code_for_run_outcome(outcome.value)


def _handle_retro(args: argparse.Namespace) -> int:
    config = _resolve_config(args, retro_only=True)
    agent = resolve_agent(config.agent_identifier)
    result = run_retro_phase(config, agent)
    print(result.outcome.value)
    return 0 if result.outcome.value == "completed" else 1


def _resolve_config(args: argparse.Namespace, *, retro_only: bool) -> RunConfig:
    return resolve_run_config(
        args.feature_dir,
        max_iterations=args.max_iterations,
        coding_model=args.coding_model or DEFAULT_CODING_MODEL,
        retro_model=args.retro_model or DEFAULT_RETRO_MODEL,
        retro_only=retro_only,
    )


def _exit_code_for_run_outcome(outcome: str) -> int:
    return 0 if outcome == "completed" else 1


def _positive_int(raw_value: str) -> int:
    try:
        parsed = int(raw_value, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {raw_value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {raw_value!r}")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
