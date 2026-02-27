#!/usr/bin/env bash
set -euo pipefail

PRINT_JSON=0

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
Starts Django for the current git worktree with deterministic defaults:
  - per-worktree SQLite DB path
  - per-worktree development port (with automatic fallback if busy)
  - per-worktree host/base URL

Usage:
  backend/scripts/runserver_worktree.sh [PORT]

Options:
  PORT          Optional positional override for the runserver port.
  --print-json  Print resolved worktree runtime values as JSON and exit.
  -h, --help    Show this help text and exit.

Environment overrides:
  DJANGO_DEV_PORT / PORT   Override default runserver port.
  DJANGO_DEV_HOST          Override default worktree host.
  DJANGO_DEV_BASE_URL      Override default backend base URL.
  DJANGO_SQLITE_PATH       Override default per-worktree sqlite path.
  ALLOWED_HOSTS            Override allowed hosts (defaults include worktree host + localhost).
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  help
  exit 0
fi

if [[ "${1:-}" == "--print-json" ]]; then
  PRINT_JSON=1
  shift
fi

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

# Keep each worktree's default sqlite DB isolated from sibling worktrees.
export DJANGO_SQLITE_PATH="${DJANGO_SQLITE_PATH:-${BACKEND_DIR}/.local/db-${WORKTREE_ID}.sqlite3}"
mkdir -p "$(dirname "${DJANGO_SQLITE_PATH}")"

# Pick a deterministic port window per worktree and resolve to a free port.
PORT_RANGE_START=8000
PORT_RANGE_SIZE=1000
DEFAULT_PORT="$((PORT_RANGE_START + (0x${WORKTREE_HASH} % PORT_RANGE_SIZE)))"
PORT_OVERRIDE="${DJANGO_DEV_PORT:-${PORT:-${1:-}}}"
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

emit_runtime_json() {
  WORKTREE_ROOT="${WORKTREE_ROOT}" \
  WORKTREE_ID="${WORKTREE_ID}" \
  WORKTREE_HASH="${WORKTREE_HASH}" \
  DJANGO_SQLITE_PATH="${DJANGO_SQLITE_PATH}" \
  PORT="${PORT}" \
  HOST="${HOST}" \
  BASE_URL="${BASE_URL}" \
  python -c 'import json, os; print(json.dumps({
"worktreeRoot": os.environ["WORKTREE_ROOT"],
"worktreeId": os.environ["WORKTREE_ID"],
"worktreeHash": os.environ["WORKTREE_HASH"],
"djangoSqlitePath": os.environ["DJANGO_SQLITE_PATH"],
"backendPort": int(os.environ["PORT"]),
"backendHost": os.environ["HOST"],
"backendBaseUrl": os.environ["BASE_URL"],
}))'
}

if [[ "${PRINT_JSON}" == "1" ]]; then
  emit_runtime_json
  exit 0
fi

emit_runtime_json > "${RUNTIME_STATE_PATH}"

info "worktree=${WORKTREE_ROOT}"
info "host=${HOST}"
info "sqlite=${DJANGO_SQLITE_PATH}"
info "port=${PORT}"
info "base_url=${BASE_URL}"

cd "${BACKEND_DIR}"
python manage.py migrate
python manage.py shell -c "from apps.accounts.bootstrap import ensure_admin_user_from_env; print(ensure_admin_user_from_env())"
python manage.py runserver "0.0.0.0:${PORT}"
