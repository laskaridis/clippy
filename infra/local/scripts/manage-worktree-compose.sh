#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Manage worktree-scoped Docker Compose services for local development.
# Preconditions: backend bootstrap script and infra/docker compose file must exist.
# Invariants: Runtime metadata from backend bootstrap is the source of truth for compose project/db settings.
# Outcomes: Runs deterministic compose lifecycle actions (start/stop/status/teardown) for the active worktree.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
BOOTSTRAP_SCRIPT="${ROOT_DIR}/backend/scripts/bootsrap.sh"
COMPOSE_FILE="${ROOT_DIR}/infra/docker/docker-compose.yml"

COLOR_RESET=$'\033[0m'
COLOR_GREEN=$'\033[0;32m'
COLOR_YELLOW=$'\033[1;33m'
COLOR_RED=$'\033[0;31m'

ok() {
  echo "${COLOR_GREEN}[local-env] $*${COLOR_RESET}"
}

warn() {
  echo "${COLOR_YELLOW}[local-env] $*${COLOR_RESET}" >&2
}

error() {
  echo "${COLOR_RED}[local-env] error: $*${COLOR_RESET}" >&2
}

help() {
  cat <<'EOF'
Manage worktree-scoped Docker Compose services.

Usage:
  infra/local/scripts/manage-worktree-compose.sh <command>

Commands:
  start      Ensure runtime metadata and start postgres service
  stop       Stop worktree-scoped compose services (retain volumes)
  status     Show compose service status and postgres container health
  teardown   Remove worktree-scoped compose services, network, and volumes
EOF
}

require_cmd() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    error "required command '${cmd}' is not installed"
    exit 1
  fi
}

require_prereqs() {
  if [[ ! -x "${BOOTSTRAP_SCRIPT}" ]]; then
    error "missing executable backend bootstrap script: ${BOOTSTRAP_SCRIPT}"
    exit 1
  fi

  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    error "missing compose file: ${COMPOSE_FILE}"
    exit 1
  fi

  require_cmd docker

  if ! docker info >/dev/null 2>&1; then
    error "docker daemon is not running; start Docker and retry"
    exit 1
  fi
}

load_runtime() {
  local runtime_json
  runtime_json="$("${BOOTSTRAP_SCRIPT}" --print-json)"
  local runtime_env
  runtime_env="$(
    RUNTIME_JSON="${runtime_json}" python - <<'PY'
import json
import os
import shlex

payload = json.loads(os.environ["RUNTIME_JSON"])
pairs = {
    "COMPOSE_PROJECT": payload.get("composeProject", ""),
    "DB_PORT": str(payload.get("databasePort", "")),
    "DB_NAME": payload.get("databaseName", ""),
    "DB_USER": payload.get("databaseUser", ""),
    "DB_MODE": payload.get("databaseMode", ""),
}

for key, value in pairs.items():
    print(f"{key}={shlex.quote(value)}")
PY
  )"

  # shellcheck disable=SC1091
  source /dev/stdin <<<"${runtime_env}"

  if [[ -z "${COMPOSE_PROJECT}" ]]; then
    error "failed to resolve compose project from bootstrap runtime metadata"
    exit 1
  fi
}

compose() {
  docker compose -f "${COMPOSE_FILE}" --project-name "${COMPOSE_PROJECT}" "$@"
}

start() {
  if [[ "${DB_MODE}" != "worktree_postgres" ]]; then
    warn "databaseMode='${DB_MODE}'; skipping compose start because DATABASE_URL is externally managed"
    ok "runtime metadata ready (compose project ${COMPOSE_PROJECT})"
    return 0
  fi

  ok "starting postgres (project=${COMPOSE_PROJECT}, port=${DB_PORT}, db=${DB_NAME})"
  POSTGRES_PORT="${DB_PORT}" \
  POSTGRES_DB="${DB_NAME}" \
  POSTGRES_USER="${DB_USER}" \
  compose up -d postgres

  ok "started local environment"
}

stop() {
  ok "stopping compose services for project ${COMPOSE_PROJECT}"
  compose stop
  ok "stopped local environment (volumes retained)"
}

status() {
  ok "compose services for project ${COMPOSE_PROJECT}"
  compose ps

  if [[ "${DB_MODE}" == "worktree_postgres" ]]; then
    local container_id
    container_id="$(compose ps -q postgres)"
    if [[ -z "${container_id}" ]]; then
      warn "postgres container is not created/running for project ${COMPOSE_PROJECT}"
      return 1
    fi

    local health
    health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}")"
    ok "postgres health=${health} (container=${container_id})"
  else
    warn "databaseMode='${DB_MODE}'; postgres container health check skipped"
  fi
}

teardown() {
  ok "tearing down compose services and volumes for project ${COMPOSE_PROJECT}"
  compose down -v
  ok "teardown complete"
}

main() {
  local command="${1:-}"
  if [[ -z "${command}" || "${command}" == "-h" || "${command}" == "--help" ]]; then
    help
    exit 0
  fi

  case "${command}" in
    start|stop|status|teardown)
      ;;
    *)
      error "unsupported command '${command}'"
      help >&2
      exit 1
      ;;
  esac

  if [[ $# -gt 1 ]]; then
    error "unexpected arguments: ${*:2}"
    help >&2
    exit 1
  fi

  require_prereqs
  load_runtime

  case "${command}" in
    start)
      start
      ;;
    stop)
      stop
      ;;
    status)
      status
      ;;
    teardown)
      teardown
      ;;
  esac
}

main "$@"
