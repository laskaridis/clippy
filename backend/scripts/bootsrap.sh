#!/usr/bin/env bash
set -euo pipefail

PRINT_JSON=0
BOOTSTRAP_ONLY=0
PRINT_ENV_PATH=0
NO_RELOAD=0

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
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
  printf '%b\n' "${COLOR_INFO}[clippy] ${*}${COLOR_RESET}"
}

warn() {
  printf '%b\n' "${COLOR_WARN}[clippy] warning: ${*}${COLOR_RESET}"
}

error() {
  printf '%b\n' "${COLOR_ERROR}[clippy] error: ${*}${COLOR_RESET}" >&2
}

help() {
  cat <<'EOF'
Starts the app for the current git worktree with deterministic defaults:
  - per-worktree PostgreSQL (via docker compose) when DATABASE_URL is not set
  - per-worktree development port (with automatic fallback if busy)
  - per-worktree host/base URL

Usage:
  backend/scripts/bootsrap.sh [PORT]

Options:
  PORT              Optional positional override for the runserver port.
  --print-json      Print resolved worktree runtime values as JSON and exit.
  --print-env-path  Print per-worktree env file path and exit.
  --bootstrap-only  Prepare runtime (db/migrate/admin/runtime metadata) and exit.
  --no-reload       Pass --noreload to Django runserver (useful for automation).
  -h, --help        Show this help text and exit.

Environment overrides:
  DJANGO_DEV_PORT / PORT   Override default runserver port.
  DJANGO_DEV_HOST          Override default worktree host.
  DJANGO_DEV_BASE_URL      Override default backend base URL.
  DJANGO_DEV_DB_PORT / POSTGRES_PORT  Override worktree postgres host port.
  DJANGO_DEV_DB_NAME / POSTGRES_DB    Override worktree postgres database name.
  DJANGO_DEV_DB_USER / POSTGRES_USER  Override worktree postgres database user.
  DJANGO_DEV_DB_PASSWORD / POSTGRES_PASSWORD  Override worktree postgres password.
  DJANGO_DOCKER_COMPOSE_PROJECT       Override compose project name.
  ALLOWED_HOSTS            Override allowed hosts (defaults include worktree host + localhost).
EOF
}

POSITIONAL_PORT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      help
      exit 0
      ;;
    --print-json)
      PRINT_JSON=1
      shift
      ;;
    --bootstrap-only)
      BOOTSTRAP_ONLY=1
      shift
      ;;
    --print-env-path)
      PRINT_ENV_PATH=1
      shift
      ;;
    --no-reload)
      NO_RELOAD=1
      shift
      ;;
    *)
      if [[ -n "${POSITIONAL_PORT}" ]]; then
        error "unexpected argument: $1"
        exit 1
      fi
      POSITIONAL_PORT="$1"
      shift
      ;;
  esac
done

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREE_ROOT="$(cd "${BACKEND_DIR}/.." && git rev-parse --show-toplevel)"
WORKTREE_BASENAME="$(basename "${WORKTREE_ROOT}")"

# Prefer GNU sha1sum but fall back to the macOS-default shasum implementation.
if command -v sha1sum >/dev/null 2>&1; then
  WORKTREE_HASH="$(printf '%s' "${WORKTREE_ROOT}" | sha1sum | cut -c1-6)"
elif command -v shasum >/dev/null 2>&1; then
  WORKTREE_HASH="$(printf '%s' "${WORKTREE_ROOT}" | shasum -a 1 | cut -c1-6)"
else
  error "neither sha1sum nor shasum is available"
  exit 1
fi
WORKTREE_ID="${WORKTREE_BASENAME}-${WORKTREE_HASH}"
RUNTIME_STATE_PATH="${BACKEND_DIR}/.local/worktree-runtime-${WORKTREE_ID}.json"
RUNTIME_ENV_PATH="${BACKEND_DIR}/.local/worktree-env-${WORKTREE_ID}.env"
mkdir -p "${BACKEND_DIR}/.local"
COMPOSE_FILE="${WORKTREE_ROOT}/infra/docker/docker-compose.yml"
COMPOSE_PROJECT_INPUT="${DJANGO_DOCKER_COMPOSE_PROJECT:-webclippings-${WORKTREE_ID}}"

# Pick a deterministic port window per worktree and resolve to a free port.
PORT_RANGE_START=8000
PORT_RANGE_SIZE=1000
DEFAULT_PORT="$((PORT_RANGE_START + (0x${WORKTREE_HASH} % PORT_RANGE_SIZE)))"
PORT_OVERRIDE="${DJANGO_DEV_PORT:-${PORT:-${POSITIONAL_PORT:-}}}"
PORT="${PORT_OVERRIDE:-${DEFAULT_PORT}}"

port_is_free() {
  local candidate_port="$1"
  if command -v lsof >/dev/null 2>&1; then
    if lsof -nP -iTCP:"${candidate_port}" -sTCP:LISTEN >/dev/null 2>&1; then
      return 1
    fi
    return 0
  fi

  # Fallback for environments without lsof.
  CANDIDATE_PORT="${candidate_port}" python -c 'import os, socket, sys
port = int(os.environ["CANDIDATE_PORT"])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    # Match Django runserver bind target (0.0.0.0) to avoid false "free" ports.
    s.bind(("0.0.0.0", port))
except OSError:
    sys.exit(1)
finally:
    s.close()'
}

resolve_default_port() {
  local candidate="$1"
  local range_start="$2"
  local range_size="$3"
  local attempts=0

  while (( attempts < range_size )); do
    if port_is_free "${candidate}"; then
      printf '%s\n' "${candidate}"
      return 0
    fi
    candidate="$((range_start + ((candidate - range_start + 1) % range_size)))"
    attempts=$((attempts + 1))
  done

  error "no free ports available in range ${range_start}-$((range_start + range_size - 1))"
  return 1
}

read_previous_runtime_database_port() {
  RUNTIME_STATE_PATH="${RUNTIME_STATE_PATH}" python -c 'import json, os, pathlib, sys
path = pathlib.Path(os.environ["RUNTIME_STATE_PATH"])
if not path.exists():
    sys.exit(1)
try:
    payload = json.loads(path.read_text())
except Exception:
    sys.exit(1)
port = payload.get("databasePort")
if isinstance(port, int):
    print(port)
    sys.exit(0)
sys.exit(1)'
}

if [[ -z "${PORT_OVERRIDE}" ]]; then
  requested_port="${PORT}"
  PORT="$(resolve_default_port "${PORT}" "${PORT_RANGE_START}" "${PORT_RANGE_SIZE}")"
  if [[ "${PORT}" != "${requested_port}" && "${PRINT_JSON}" != "1" ]]; then
    warn "default port ${requested_port} is busy; using ${PORT} instead"
  fi
fi
DEFAULT_HOST="clippy-${WORKTREE_HASH}.localhost"

if [[ -n "${DJANGO_DEV_HOST:-}" ]]; then
  HOST="${DJANGO_DEV_HOST}"
elif [[ -n "${DJANGO_DEV_BASE_URL:-}" ]]; then
  HOST="$(DJANGO_DEV_BASE_URL="${DJANGO_DEV_BASE_URL}" python -c 'import os
from urllib.parse import urlsplit

host = urlsplit(os.environ["DJANGO_DEV_BASE_URL"]).hostname
if not host:
    raise SystemExit("[clippy] error: DJANGO_DEV_BASE_URL must include a hostname")
print(host)')"
else
  HOST="${DEFAULT_HOST}"
fi

BASE_URL="${DJANGO_DEV_BASE_URL:-http://${HOST}:${PORT}}"
export DJANGO_DEV_PORT="${PORT}"
export DJANGO_DEV_HOST="${HOST}"
export DJANGO_DEV_BASE_URL="${BASE_URL}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-${HOST},localhost,127.0.0.1,[::1]}"

default_db_name() {
  WORKTREE_ID="${WORKTREE_ID}" python -c 'import os, re
raw = "webclippings_" + os.environ["WORKTREE_ID"].lower()
sanitized = re.sub(r"[^a-z0-9_]", "_", raw)
print(sanitized[:63])'
}

sanitize_compose_project() {
  RAW_VALUE="$1" python -c 'import os, re
value = os.environ["RAW_VALUE"].lower()
value = re.sub(r"[^a-z0-9_-]", "-", value)
value = re.sub(r"-{2,}", "-", value).strip("-_")
if not value:
    value = "webclippings"
if not re.match(r"^[a-z0-9]", value):
    value = "webclippings-" + value
print(value[:63])'
}

url_encode_component() {
  RAW_VALUE="$1" python -c 'import os
from urllib.parse import quote

print(quote(os.environ["RAW_VALUE"], safe=""))'
}

shell_quote() {
  RAW_VALUE="$1" python -c 'import os, shlex
print(shlex.quote(os.environ["RAW_VALUE"]))'
}

DB_PORT_RANGE_START=15432
DB_PORT_RANGE_SIZE=1000
DEFAULT_DB_PORT="$((DB_PORT_RANGE_START + (0x${WORKTREE_HASH} % DB_PORT_RANGE_SIZE)))"
DB_PORT_OVERRIDE="${DJANGO_DEV_DB_PORT:-${POSTGRES_PORT:-}}"
DB_PORT="${DB_PORT_OVERRIDE:-${DEFAULT_DB_PORT}}"
if [[ -z "${DB_PORT_OVERRIDE}" ]]; then
  if PREVIOUS_DB_PORT="$(read_previous_runtime_database_port)"; then
    DB_PORT="${PREVIOUS_DB_PORT}"
  else
    DB_PORT="$(resolve_default_port "${DB_PORT}" "${DB_PORT_RANGE_START}" "${DB_PORT_RANGE_SIZE}")"
  fi
fi
DB_NAME="${DJANGO_DEV_DB_NAME:-${POSTGRES_DB:-$(default_db_name)}}"
DB_USER="${DJANGO_DEV_DB_USER:-${POSTGRES_USER:-webclippings}}"
DB_PASSWORD="${DJANGO_DEV_DB_PASSWORD:-${POSTGRES_PASSWORD:-password}}"
COMPOSE_PROJECT="$(sanitize_compose_project "${COMPOSE_PROJECT_INPUT}")"
if [[ "${COMPOSE_PROJECT}" != "${COMPOSE_PROJECT_INPUT}" && "${PRINT_JSON}" != "1" ]]; then
  warn "compose project name sanitized to ${COMPOSE_PROJECT} (from ${COMPOSE_PROJECT_INPUT})"
fi

if [[ -n "${DATABASE_URL:-}" ]]; then
  DB_MODE="external"
elif [[ -f "${COMPOSE_FILE}" ]]; then
  DB_MODE="worktree_postgres"
  ENCODED_DB_USER="$(url_encode_component "${DB_USER}")"
  ENCODED_DB_PASSWORD="$(url_encode_component "${DB_PASSWORD}")"
  export DATABASE_URL="postgres://${ENCODED_DB_USER}:${ENCODED_DB_PASSWORD}@127.0.0.1:${DB_PORT}/${DB_NAME}"
else
  error "DATABASE_URL is not set and compose file is missing (${COMPOSE_FILE})"
  exit 1
fi

start_worktree_postgres() {
  if [[ "${DB_MODE}" != "worktree_postgres" ]]; then
    return 0
  fi

  if ! command -v docker >/dev/null 2>&1; then
    error "docker is required for worktree postgres bootstrap; either install Docker or set DATABASE_URL explicitly"
    return 1
  fi

  if ! docker info >/dev/null 2>&1; then
    error "docker daemon is not running; start Docker or set DATABASE_URL explicitly"
    return 1
  fi

  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    error "missing compose file: ${COMPOSE_FILE}"
    return 1
  fi

  info "starting worktree postgres via docker compose (project=${COMPOSE_PROJECT}, port=${DB_PORT}, db=${DB_NAME})"
  POSTGRES_PORT="${DB_PORT}" \
  POSTGRES_DB="${DB_NAME}" \
  POSTGRES_USER="${DB_USER}" \
  POSTGRES_PASSWORD="${DB_PASSWORD}" \
  docker compose -f "${COMPOSE_FILE}" --project-name "${COMPOSE_PROJECT}" up -d postgres

  local attempts=0
  until (( attempts >= 30 )); do
    if command -v pg_isready >/dev/null 2>&1; then
      if PGPASSWORD="${DB_PASSWORD}" pg_isready -h 127.0.0.1 -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; then
        return 0
      fi
    else
      if CANDIDATE_PORT="${DB_PORT}" python -c 'import os, socket, sys
port = int(os.environ["CANDIDATE_PORT"])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1.0)
try:
    s.connect(("127.0.0.1", port))
except OSError:
    sys.exit(1)
finally:
    s.close()'; then
        return 0
      fi
    fi
    attempts=$((attempts + 1))
    sleep 1
  done

  error "postgres did not become ready on 127.0.0.1:${DB_PORT}"
  return 1
}

wait_for_external_database() {
  if [[ "${DB_MODE}" != "external" ]]; then
    return 0
  fi

  read -r DB_WAIT_HOST DB_WAIT_PORT <<EOF
$(DATABASE_URL="${DATABASE_URL}" python -c 'import os
from urllib.parse import urlparse
parsed = urlparse(os.environ["DATABASE_URL"])
host = parsed.hostname or "127.0.0.1"
port = parsed.port or (5432 if parsed.scheme in {"postgres", "postgresql"} else 0)
print(host, port)')
EOF

  if [[ -z "${DB_WAIT_HOST}" || -z "${DB_WAIT_PORT}" || "${DB_WAIT_PORT}" == "0" ]]; then
    error "could not determine host/port from DATABASE_URL for external database readiness check"
    return 1
  fi

  local attempts=0
  until (( attempts >= 30 )); do
    if DB_WAIT_HOST="${DB_WAIT_HOST}" DB_WAIT_PORT="${DB_WAIT_PORT}" python -c 'import os, socket, sys
host = os.environ["DB_WAIT_HOST"]
port = int(os.environ["DB_WAIT_PORT"])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1.0)
try:
    s.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    s.close()'; then
      return 0
    fi
    attempts=$((attempts + 1))
    sleep 1
  done

  error "external database did not become reachable at ${DB_WAIT_HOST}:${DB_WAIT_PORT}"
  return 1
}

write_runtime_env() {
  local quoted_worktree_id quoted_database_url quoted_allowed_hosts quoted_host quoted_base_url quoted_db_name quoted_db_user quoted_db_password quoted_compose_project
  quoted_worktree_id="$(shell_quote "${WORKTREE_ID}")"
  quoted_database_url="$(shell_quote "${DATABASE_URL}")"
  quoted_allowed_hosts="$(shell_quote "${ALLOWED_HOSTS}")"
  quoted_host="$(shell_quote "${HOST}")"
  quoted_base_url="$(shell_quote "${BASE_URL}")"
  quoted_db_name="$(shell_quote "${DB_NAME}")"
  quoted_db_user="$(shell_quote "${DB_USER}")"
  quoted_db_password="$(shell_quote "${DB_PASSWORD}")"
  quoted_compose_project="$(shell_quote "${COMPOSE_PROJECT}")"

  cat > "${RUNTIME_ENV_PATH}" <<EOF
# Generated by backend/scripts/bootsrap.sh for ${WORKTREE_ID}
# shellcheck disable=SC2034
WORKTREE_ID=${quoted_worktree_id}
WORKTREE_HASH=${WORKTREE_HASH}
DJANGO_DEV_PORT=${PORT}
DJANGO_DEV_HOST=${quoted_host}
DJANGO_DEV_BASE_URL=${quoted_base_url}
ALLOWED_HOSTS=${quoted_allowed_hosts}
DATABASE_URL=${quoted_database_url}
POSTGRES_PORT=${DB_PORT}
POSTGRES_DB=${quoted_db_name}
POSTGRES_USER=${quoted_db_user}
POSTGRES_PASSWORD=${quoted_db_password}
DJANGO_DOCKER_COMPOSE_PROJECT=${quoted_compose_project}
EOF
}

emit_runtime_json() {
  WORKTREE_ROOT="${WORKTREE_ROOT}" \
  WORKTREE_ID="${WORKTREE_ID}" \
  WORKTREE_HASH="${WORKTREE_HASH}" \
  PORT="${PORT}" \
  HOST="${HOST}" \
  BASE_URL="${BASE_URL}" \
  DB_MODE="${DB_MODE}" \
  DB_PORT="${DB_PORT}" \
  DB_NAME="${DB_NAME}" \
  DB_USER="${DB_USER}" \
  DATABASE_URL="${DATABASE_URL}" \
  COMPOSE_PROJECT="${COMPOSE_PROJECT}" \
  RUNTIME_ENV_PATH="${RUNTIME_ENV_PATH}" \
  python -c 'import json, os; print(json.dumps({
"worktreeRoot": os.environ["WORKTREE_ROOT"],
"worktreeId": os.environ["WORKTREE_ID"],
"worktreeHash": os.environ["WORKTREE_HASH"],
"backendPort": int(os.environ["PORT"]),
"backendHost": os.environ["HOST"],
"backendBaseUrl": os.environ["BASE_URL"],
"databaseMode": os.environ["DB_MODE"],
"databaseUrl": os.environ["DATABASE_URL"],
"databasePort": int(os.environ["DB_PORT"]),
"databaseName": os.environ["DB_NAME"],
"databaseUser": os.environ["DB_USER"],
"composeProject": os.environ["COMPOSE_PROJECT"],
"envFile": os.environ["RUNTIME_ENV_PATH"],
}))'
}

if [[ "${PRINT_ENV_PATH}" == "1" ]]; then
  write_runtime_env
  printf '%s\n' "${RUNTIME_ENV_PATH}"
  exit 0
fi

if [[ "${PRINT_JSON}" == "1" ]]; then
  # Keep stdout machine-parseable for tooling that consumes this command.
  start_worktree_postgres 1>&2
  wait_for_external_database 1>&2
  write_runtime_env
  emit_runtime_json
  exit 0
fi

write_runtime_env
emit_runtime_json > "${RUNTIME_STATE_PATH}"

info "worktree=${WORKTREE_ROOT}"
info "host=${HOST}"
info "port=${PORT}"
info "base_url=${BASE_URL}"
if [[ "${DB_MODE}" == "worktree_postgres" ]]; then
  info "database=postgres://${DB_USER}@127.0.0.1:${DB_PORT}/${DB_NAME} (compose project ${COMPOSE_PROJECT})"
else
  info "database=external DATABASE_URL"
fi

cd "${BACKEND_DIR}"
start_worktree_postgres
wait_for_external_database
python manage.py migrate
python manage.py shell -c "from apps.accounts.bootstrap import ensure_admin_user_from_env; print(ensure_admin_user_from_env())"
if [[ "${BOOTSTRAP_ONLY}" == "1" ]]; then
  info "bootstrap-only complete"
  exit 0
fi
RUNSERVER_ARGS=("0.0.0.0:${PORT}")
if [[ "${NO_RELOAD}" == "1" ]]; then
  RUNSERVER_ARGS+=("--noreload")
fi
python manage.py runserver "${RUNSERVER_ARGS[@]}"
