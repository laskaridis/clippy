#!/usr/bin/env bash

# Ralph script entrypoint.
# Usage: ./ralph.sh --feature-dir <relative-path> [--max-iterations <number>]
#
# Options:
#   --help                     Show this help message.
#   --feature-dir <path>       Specify a feature folder to use (relative to current working directory).
#   --max-iterations <number>  Set the maximum number of iterations (default 50).

set -euo pipefail

# Color codes for logging:
COLOR_RESET='\033[0m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_RED='\033[0;31m'

# Logs an informational message to stdout
log_info() {
	printf "%b[INFO]%b %s\n" "$COLOR_YELLOW" "$COLOR_RESET" "$*"
}

# Logs a success message to stdout
log_ok() {
	printf "%b[OK]%b %s\n" "$COLOR_GREEN" "$COLOR_RESET" "$*"
}

# Logs a warning message to stderr
log_warn() {
	printf "%b[WARN]%b %s\n" "$COLOR_YELLOW" "$COLOR_RESET" "$*"
}

# Logs an error messsage to stderr
log_error() {
	printf "%b[ERROR]%b %s\n" "$COLOR_RED" "$COLOR_RESET" "$*" >&2
}

usage() {
	cat <<'EOF'
Usage: ./ralph.sh --feature-dir <relative-path> [--max-iterations <number>]

Options:
  --help                     Show this help message.
  --feature-dir <path>       Specify a feature folder to use (required, relative to current working directory).
  --max-iterations <number>  Set the maximum number of iterations (default: 50).
EOF
}

validate_positive_integer() {
	local value="$1"
	[[ "$value" =~ ^[1-9][0-9]*$ ]]
}

FEATURE_DIR=""
MAX_ITERATIONS=50

while [[ $# -gt 0 ]]; do
	case "$1" in
	--help|-h)
		usage
		exit 0
		;;
	--feature-dir)
		shift
		if [[ $# -eq 0 || -z "${1:-}" ]]; then
			log_error "Missing value for --feature-dir."
			usage
			exit 1
		fi
		FEATURE_DIR="$1"
		;;
	--max-iterations)
		shift
		if [[ $# -eq 0 || -z "${1:-}" ]]; then
			log_error "Missing value for --max-iterations."
			usage
			exit 1
		fi
		MAX_ITERATIONS="$1"
		;;
	*)
		log_error "Unknown argument: $1"
		usage
		exit 1
		;;
	esac
	shift
done

if [[ -z "$FEATURE_DIR" ]]; then
	log_error "--feature-dir is required."
	usage
	exit 1
fi

if [[ "$FEATURE_DIR" = /* ]]; then
	log_error "--feature-dir must be a relative path from CWD: $FEATURE_DIR"
	exit 1
fi

FEATURE_DIR_PATH="${PWD}/${FEATURE_DIR}"

if [[ ! -d "$FEATURE_DIR_PATH" ]]; then
	log_error "Feature directory does not exist under CWD: $FEATURE_DIR_PATH"
	exit 1
fi

SPEC_FILE="${FEATURE_DIR_PATH}/spec.md"
TASKS_FILE="${FEATURE_DIR_PATH}/tasks.md"

if [[ ! -f "$SPEC_FILE" ]]; then
	log_error "Missing required file: $SPEC_FILE"
	exit 1
fi

if [[ ! -f "$TASKS_FILE" ]]; then
	log_error "Missing required file: $TASKS_FILE"
	exit 1
fi

if ! validate_positive_integer "$MAX_ITERATIONS"; then
	log_error "--max-iterations must be a positive integer. Received: $MAX_ITERATIONS"
	exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROMPT_FILE="$SCRIPT_DIR/prompt.md"

if [[ ! -f "$PROMPT_FILE" ]]; then
	log_error "Prompt file not found: $PROMPT_FILE"
	exit 1
fi

PROMPT_TEMPLATE="$(cat "$PROMPT_FILE")"
PROMPT_PAYLOAD="${PROMPT_TEMPLATE//\$ARGUMENTS/$FEATURE_DIR_PATH}"

for ((iteration = 1; iteration <= MAX_ITERATIONS; iteration++)); do
	log_info "Iteration ${iteration}/${MAX_ITERATIONS}: running Codex."

	last_message_file="$(mktemp)"
	if ! codex --ask-for-approval never -c shell_environment_policy.inherit=all exec --ephemeral --sandbox danger-full-access -o "$last_message_file" - <<<"$PROMPT_PAYLOAD"; then
		log_error "Codex execution failed on iteration $iteration."
		rm -f "$last_message_file"
		exit 1
	fi

	codex_result="$(cat "$last_message_file")"
	rm -f "$last_message_file"
	status_line="$(printf "%s\n" "$codex_result" | head -n 1 | tr -d '\r')"

	log_info "Codex result (iteration ${iteration}):"
	printf "%s\n" "$codex_result"

	case "$status_line" in
		"RALPH_STATUS=COMPLETE")
			log_ok "Completion detected on iteration ${iteration}. Ralph loop finalized."
			exit 0
			;;
		"RALPH_STATUS=CONTINUE")
			;;
        "RALPH_STATUS=BLOCKED")
            log_error "Ralph is blocked on iteration ${iteration}. Exiting with failure."
            exit 1
		*)
			log_warn "Invalid Ralph status line on iteration ${iteration}: '$status_line'"
			;;
	esac

	if (( iteration < MAX_ITERATIONS )); then
		log_info "Ralph not complete yet. Continuing to next iteration."
	fi
done

log_info "Reached max iterations (${MAX_ITERATIONS}) without completion status."
