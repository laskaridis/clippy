#!/usr/bin/env bash

set -euo pipefail

usage() {
	cat <<'EOF'
Usage: ./ralph.sh --feature-dir <path> [--max-iterations <number>] [--coding-model <name>]

Compatibility wrapper for the Python CLI:
  python -m ralph run <path> [--max-iterations <number>] [--model <name>]

Options:
  --help                     Show this help message.
  --feature-dir <path>       Feature directory to pass to `ralph run` (required).
  --max-iterations <number>   Forwarded unchanged to `ralph run`.
  --coding-model <name>       Legacy name for `--model`; forwarded to `ralph run --model`.
  --retro-model <name>        Retired legacy flag. The Python MVP no longer supports retro-only mode.
  --retro-only                Retired legacy flag. The Python MVP no longer supports retro-only mode.
EOF
}

error() {
	printf '%s\n' "$*" >&2
}

is_known_flag() {
	case "$1" in
	--help|-h|--feature-dir|--max-iterations|--coding-model|--retro-model|--retro-only|--)
		return 0
		;;
	*)
		return 1
		;;
	esac
}

python_cmd() {
	if command -v python3 >/dev/null 2>&1; then
		printf '%s\n' python3
		return
	fi

	printf '%s\n' python
}

feature_dir=""
max_iterations=""
coding_model=""

while [[ $# -gt 0 ]]; do
	case "$1" in
	--help|-h)
		usage
		exit 0
		;;
	--feature-dir)
		shift
		if [[ $# -eq 0 || -z "${1:-}" ]]; then
			error "Missing value for --feature-dir."
			usage
			exit 2
		fi
		if is_known_flag "$1"; then
			error "Missing value for --feature-dir."
			usage
			exit 2
		fi
		feature_dir="$1"
		;;
	--max-iterations)
		shift
		if [[ $# -eq 0 || -z "${1:-}" ]]; then
			error "Missing value for --max-iterations."
			usage
			exit 2
		fi
		if is_known_flag "$1"; then
			error "Missing value for --max-iterations."
			usage
			exit 2
		fi
		max_iterations="$1"
		;;
	--coding-model)
		shift
		if [[ $# -eq 0 || -z "${1:-}" ]]; then
			error "Missing value for --coding-model."
			usage
			exit 2
		fi
		if is_known_flag "$1"; then
			error "Missing value for --coding-model."
			usage
			exit 2
		fi
		coding_model="$1"
		;;
	--retro-model)
		error "Migration error: --retro-model is retired. Use: python -m ralph run <path>"
		exit 2
		;;
	--retro-only)
		error "Migration error: --retro-only is retired. Use: python -m ralph run <path>"
		exit 2
		;;
	--)
		shift
		if [[ $# -gt 0 ]]; then
			error "Unexpected positional argument: $1"
		else
			error "Missing required --feature-dir argument."
		fi
		usage
		exit 2
		;;
	--*)
		error "Unknown argument: $1"
		usage
		exit 2
		;;
	*)
		error "Unexpected positional argument: $1"
		usage
		exit 2
		;;
	esac
	shift
done

if [[ -z "$feature_dir" ]]; then
	error "Missing required --feature-dir argument."
	usage
	exit 2
fi

python_executable="$(python_cmd)"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_command=("$python_executable" -m ralph run "$feature_dir")

if [[ -n "$max_iterations" ]]; then
	python_command+=(--max-iterations "$max_iterations")
fi

if [[ -n "$coding_model" ]]; then
	python_command+=(--model "$coding_model")
fi

PYTHONPATH="${repo_root}${PYTHONPATH:+:${PYTHONPATH}}" exec "${python_command[@]}"
