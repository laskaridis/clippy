from __future__ import annotations

import argparse
from collections.abc import Sequence


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2
