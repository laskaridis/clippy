#!/usr/bin/env bash
set -euo pipefail

# Resolves and loads environment values for the current worktree.
# Important shell behavior:
# - Executed mode (`./scripts/env.sh`) cannot modify the parent shell env.
# - Source mode (`source ./scripts/env.sh --setup`) can set env vars directly.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNSERVER_SCRIPT="${SCRIPT_DIR}/bootsrap.sh"

IS_SOURCED=0
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  IS_SOURCED=1
fi

if [[ -t 2 && -z "${NO_COLOR:-}" ]]; then
  COLOR_INFO=$'\033[0;32m'
  COLOR_WARN=$'\033[0;33m'
  COLOR_ERROR=$'\033[0;31m'
  COLOR_RESET=$'\033[0m'
else
  COLOR_INFO=""
  COLOR_WARN=""
  COLOR_ERROR=""
  COLOR_RESET=""
fi

info() {
  printf '%b\n' "${COLOR_INFO}[clippy] ${*}${COLOR_RESET}" >&2
}

warn() {
  printf '%b\n' "${COLOR_WARN}[clippy] warning: ${*}${COLOR_RESET}" >&2
}

error() {
  printf '%b\n' "${COLOR_ERROR}[clippy] error: ${*}${COLOR_RESET}" >&2
}

help() {
  cat <<'EOF_HELP'
Usage: env.sh [OPTIONS]

Options:
  --help      Show this help message and exit
  --setup     When sourced, export vars in current shell:
              source ./scripts/env.sh --setup
              When executed, exits with an error.
  --print     Print raw environment file for the current worktree
EOF_HELP
}

finish() {
  local code="${1:-0}"
  if [[ "${IS_SOURCED}" == "1" ]]; then
    return "${code}"
  fi
  exit "${code}"
}

resolve_env_file() {
  local env_file

  if [[ ! -x "${RUNSERVER_SCRIPT}" ]]; then
    error "missing executable: ${RUNSERVER_SCRIPT}"
    return 1
  fi

  if ! env_file="$("${RUNSERVER_SCRIPT}" --print-env-path)"; then
    error "failed to resolve env path from bootsrap.sh"
    return 1
  fi

  if [[ -z "${env_file}" ]]; then
    error "bootsrap.sh returned an empty env path"
    return 1
  fi

  if [[ ! -f "${env_file}" ]]; then
    error "no env file found at ${env_file}"
    return 1
  fi

  printf '%s\n' "${env_file}"
}

load_env_in_current_shell() {
  local env_file="$1"
  export ENV_FILE="${env_file}"
  # Export all env file keys in the current shell.
  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
}

setup() {
  local env_file
  if [[ "${IS_SOURCED}" != "1" ]]; then
    error "--setup must be sourced to modify your current shell"
    error "run: source ./scripts/env.sh --setup"
    return 1
  fi

  env_file="$(resolve_env_file)"
  info "resolved environment file: ${env_file}"
  load_env_in_current_shell "${env_file}"
  info "loaded environment in current shell from ${env_file}"
}

print_env() {
  local env_file
  env_file="$(resolve_env_file)"
  cat "${env_file}"
}

if [[ $# -eq 0 ]]; then
  warn "no option provided"
  help
  finish 1
fi

if [[ $# -gt 1 ]]; then
  error "expected a single option"
  help
  finish 1
fi

case "$1" in
  --help)
    help
    finish 0
    ;;
  --setup)
    setup
    finish 0
    ;;
  --print)
    print_env
    finish 0
    ;;
  *)
    error "unknown option: $1"
    help
    finish 1
    ;;
esac
