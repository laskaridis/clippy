#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREE_ROOT="$(cd "${BACKEND_DIR}/.." && git rev-parse --show-toplevel)"
WORKTREE_BASENAME="$(basename "${WORKTREE_ROOT}")"
PRINT_JSON=0

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage:
  backend/scripts/runserver_worktree.sh [PORT]
  backend/scripts/runserver_worktree.sh --print-json
  backend/scripts/runserver_worktree.sh --help

Description:
  Starts Django for the current git worktree with deterministic defaults:
  - per-worktree SQLite DB path
  - per-worktree development port
  - per-worktree host/base URL

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
  exit 0
fi

if [[ "${1:-}" == "--print-json" ]]; then
  PRINT_JSON=1
  shift
fi

# Prefer GNU sha1sum but fall back to the macOS-default shasum implementation.
if command -v sha1sum >/dev/null 2>&1; then
  WORKTREE_HASH="$(printf '%s' "${WORKTREE_ROOT}" | sha1sum | cut -c1-6)"
elif command -v shasum >/dev/null 2>&1; then
  WORKTREE_HASH="$(printf '%s' "${WORKTREE_ROOT}" | shasum -a 1 | cut -c1-6)"
else
  echo "[clippy] error: neither sha1sum nor shasum is available" >&2
  exit 1
fi
WORKTREE_ID="${WORKTREE_BASENAME}-${WORKTREE_HASH}"

# Keep each worktree's default sqlite DB isolated from sibling worktrees.
export DJANGO_SQLITE_PATH="${DJANGO_SQLITE_PATH:-${BACKEND_DIR}/.local/db-${WORKTREE_ID}.sqlite3}"
mkdir -p "$(dirname "${DJANGO_SQLITE_PATH}")"

# Pick a deterministic port per worktree, while still allowing overrides.
DEFAULT_PORT="$((8000 + (0x${WORKTREE_HASH} % 200)))"
PORT="${DJANGO_DEV_PORT:-${PORT:-${1:-${DEFAULT_PORT}}}}"
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

if [[ "${PRINT_JSON}" == "1" ]]; then
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
  exit 0
fi

echo "[clippy] worktree=${WORKTREE_ROOT}"
echo "[clippy] host=${HOST}"
echo "[clippy] sqlite=${DJANGO_SQLITE_PATH}"
echo "[clippy] port=${PORT}"
echo "[clippy] base_url=${BASE_URL}"

cd "${BACKEND_DIR}"
python manage.py migrate
python manage.py shell -c "from apps.accounts.bootstrap import ensure_admin_user_from_env; print(ensure_admin_user_from_env())"
python manage.py runserver "0.0.0.0:${PORT}"
