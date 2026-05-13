#!/usr/bin/env bash

# Compatibility shim for the legacy Ralph shell entrypoint.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

usage() {
	cat <<'EOF'
Usage: ./ralph.sh --feature-dir <relative-path> [--max-iterations <number>] [--coding-model <name>] [--retro-model <name>] [--retro-only]

Options:
  --help                     Show this help message.
  --feature-dir <path>       Specify a feature folder to use (required, relative to current working directory).
  --max-iterations <number>  Set the maximum number of iterations (default: 50).
  --coding-model <name>      Set the Codex model used for implementation iterations (default: gpt-5.4-mini).
  --retro-model <name>       Set the Codex model used for the final retrospective (default: gpt-5.4-medium).
  --retro-only               Run only the retrospective phase. Requires ralph.txt and rejects --max-iterations/--coding-model.
EOF
}

error() {
	printf 'ralph: %s\n' "$*" >&2
}

feature_dir=""
max_iterations=""
coding_model=""
retro_model=""
retro_only=0

while [[ $# -gt 0 ]]; do
	case "$1" in
		--help|-h)
			usage
			exit 0
			;;
		--feature-dir)
			shift
			if [[ $# -eq 0 || -z "${1:-}" ]]; then
				error "missing value for --feature-dir"
				usage
				exit 1
			fi
			feature_dir="$1"
			;;
		--max-iterations)
			shift
			if [[ $# -eq 0 || -z "${1:-}" ]]; then
				error "missing value for --max-iterations"
				usage
				exit 1
			fi
			max_iterations="$1"
			;;
		--coding-model)
			shift
			if [[ $# -eq 0 || -z "${1:-}" ]]; then
				error "missing value for --coding-model"
				usage
				exit 1
			fi
			coding_model="$1"
			;;
		--retro-model)
			shift
			if [[ $# -eq 0 || -z "${1:-}" ]]; then
				error "missing value for --retro-model"
				usage
				exit 1
			fi
			retro_model="$1"
			;;
		--retro-only)
			retro_only=1
			;;
		*)
			error "unknown argument: $1"
			usage
			exit 1
			;;
	esac
	shift
done

if [[ -z "$feature_dir" ]]; then
	error "--feature-dir is required"
	usage
	exit 1
fi

if [[ "$feature_dir" = /* ]]; then
	error "--feature-dir must be a relative path from CWD: $feature_dir"
	exit 1
fi

python_args=()
if (( retro_only )); then
	if [[ -n "$max_iterations" ]]; then
		error "--max-iterations cannot be used with --retro-only"
		usage
		exit 1
	fi
	if [[ -n "$coding_model" ]]; then
		error "--coding-model cannot be used with --retro-only"
		usage
		exit 1
	fi

	python_args+=(retro --feature-dir "$feature_dir")
	if [[ -n "$retro_model" ]]; then
		python_args+=(--retro-model "$retro_model")
	fi
else
	python_args+=(run --feature-dir "$feature_dir")
	if [[ -n "$max_iterations" ]]; then
		python_args+=(--max-iterations "$max_iterations")
	fi
	if [[ -n "$coding_model" ]]; then
		python_args+=(--coding-model "$coding_model")
	fi
	if [[ -n "$retro_model" ]]; then
		python_args+=(--retro-model "$retro_model")
	fi
fi

PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" exec "$PYTHON_BIN" -m ralph.cli "${python_args[@]}"
