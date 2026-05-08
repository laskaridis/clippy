#!/usr/bin/env bash

# Ralph script entrypoint.
# Usage: ./ralph.sh --feature-dir <relative-path> [--max-iterations <number>] [--coding-model <name>] [--retro-model <name>] [--retro-only]
#
# Options:
#   --help                     Show this help message.
#   --feature-dir <path>       Specify a feature folder to use (relative to current working directory).
#   --max-iterations <number>  Set the maximum number of iterations (default 50).
#   --coding-model <name>      Set the Codex model used for implementation iterations (default gpt-5.4-mini).
#   --retro-model <name>       Set the Codex model used for the final retrospective (default gpt-5.4-medium).
#   --retro-only               Run only the retrospective phase (requires ralph.txt and disallows coding-only flags).

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

validate_positive_integer() {
	local value="$1"
	[[ "$value" =~ ^[1-9][0-9]*$ ]]
}

run_codex_prompt() {
	local prompt_payload="$1"
	local model="$2"
	local label="$3"
	local exit_code=0
	local last_message_file

	last_message_file="$(mktemp)"

	if codex --model "$model" --ask-for-approval never -c shell_environment_policy.inherit=all exec --ephemeral --sandbox danger-full-access -o "$last_message_file" - <<<"$prompt_payload"; then
		exit_code=0
	else
		exit_code=$?
	fi

	if [[ -f "$last_message_file" ]]; then
		CODEX_RESULT="$(cat "$last_message_file")"
		rm -f "$last_message_file"
	else
		CODEX_RESULT=""
	fi

	log_info "Codex result (${label}):"
	printf "%s\n" "$CODEX_RESULT"

	return "$exit_code"
}

FEATURE_DIR=""
MAX_ITERATIONS=50
CODING_MODEL="gpt-5.4-mini"
RETRO_MODEL="gpt-5.4-medium"
RETRO_ONLY=0
CODEX_RESULT=""
MAX_ITERATIONS_SET=0
CODING_MODEL_SET=0

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
		MAX_ITERATIONS_SET=1
		;;
	--coding-model)
		shift
		if [[ $# -eq 0 || -z "${1:-}" ]]; then
			log_error "Missing value for --coding-model."
			usage
			exit 1
		fi
		CODING_MODEL="$1"
		CODING_MODEL_SET=1
		;;
	--retro-model)
		shift
		if [[ $# -eq 0 || -z "${1:-}" ]]; then
			log_error "Missing value for --retro-model."
			usage
			exit 1
		fi
		RETRO_MODEL="$1"
		;;
	--retro-only)
		RETRO_ONLY=1
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
TASKS_FILE="${FEATURE_DIR_PATH}/tasks.json"

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

if (( RETRO_ONLY )); then
	if (( MAX_ITERATIONS_SET )); then
		log_error "--max-iterations cannot be used with --retro-only."
		usage
		exit 1
	fi

	if (( CODING_MODEL_SET )); then
		log_error "--coding-model cannot be used with --retro-only."
		usage
		exit 1
	fi
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODE_PROMPT_FILE="$SCRIPT_DIR/prompts/code.md"
RETRO_PROMPT_FILE="$SCRIPT_DIR/prompts/retro.md"
RALPH_LOG_FILE="${FEATURE_DIR_PATH}/ralph.txt"

if [[ ! -f "$RETRO_PROMPT_FILE" ]]; then
	log_error "Prompt file not found: $RETRO_PROMPT_FILE"
	exit 1
fi

RETRO_PROMPT_TEMPLATE="$(cat "$RETRO_PROMPT_FILE")"
RETRO_PROMPT_PAYLOAD="${RETRO_PROMPT_TEMPLATE//\$ARGUMENTS/$FEATURE_DIR_PATH}"

if (( RETRO_ONLY )); then
	if [[ ! -f "$RALPH_LOG_FILE" ]]; then
		log_error "Missing required file for --retro-only: $RALPH_LOG_FILE"
		exit 1
	fi

	log_info "Running retrospective only with model ${RETRO_MODEL}."
	if run_codex_prompt "$RETRO_PROMPT_PAYLOAD" "$RETRO_MODEL" "retrospective"; then
		log_ok "Retrospective completed successfully."
		exit 0
	fi

	log_error "Retrospective execution failed in --retro-only mode."
	exit 1
fi

if [[ ! -f "$CODE_PROMPT_FILE" ]]; then
	log_error "Prompt file not found: $CODE_PROMPT_FILE"
	exit 1
fi

CODE_PROMPT_TEMPLATE="$(cat "$CODE_PROMPT_FILE")"
CODE_PROMPT_PAYLOAD="${CODE_PROMPT_TEMPLATE//\$ARGUMENTS/$FEATURE_DIR_PATH}"

for ((iteration = 1; iteration <= MAX_ITERATIONS; iteration++)); do
	log_info "Iteration ${iteration}/${MAX_ITERATIONS}: running Codex with coding model ${CODING_MODEL}."

	if ! run_codex_prompt "$CODE_PROMPT_PAYLOAD" "$CODING_MODEL" "iteration ${iteration}"; then
		log_error "Codex execution failed on iteration $iteration."
		exit 1
	fi

	status_line="$(printf "%s\n" "$CODEX_RESULT" | head -n 1 | tr -d '\r')"

	case "$status_line" in
		"RALPH_STATUS=COMPLETE")
			log_ok "Completion detected on iteration ${iteration}. Ralph loop finalized."

			log_info "Running retrospective with model ${RETRO_MODEL}."
			if run_codex_prompt "$RETRO_PROMPT_PAYLOAD" "$RETRO_MODEL" "retrospective"; then
				log_ok "Retrospective completed successfully."
			else
				log_warn "Retrospective execution failed after completion. Continuing without blocking Ralph success."
			fi

			exit 0
			;;
		"RALPH_STATUS=CONTINUE")
			;;
		"RALPH_STATUS=BLOCKED")
			log_error "Ralph is blocked on iteration ${iteration}. Exiting with failure."
			exit 1
			;;
		*)
			log_warn "Invalid Ralph status line on iteration ${iteration}: '$status_line'"
			;;
	esac

	if (( iteration < MAX_ITERATIONS )); then
		log_info "Ralph not complete yet. Continuing to next iteration."
	fi
done

log_info "Reached max iterations (${MAX_ITERATIONS}) without completion status."
