#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREE_ROOT="$(cd "${BACKEND_DIR}/.." && git rev-parse --show-toplevel)"
WORKTREE_BASENAME="$(basename "${WORKTREE_ROOT}")"
WORKTREE_HASH="$(printf '%s' "${WORKTREE_ROOT}" | sha1sum | cut -c1-6)"
WORKTREE_ID="${WORKTREE_BASENAME}-${WORKTREE_HASH}"

# Keep each worktree's default sqlite DB isolated from sibling worktrees.
export DJANGO_SQLITE_PATH="${DJANGO_SQLITE_PATH:-${BACKEND_DIR}/.local/db-${WORKTREE_ID}.sqlite3}"
mkdir -p "$(dirname "${DJANGO_SQLITE_PATH}")"

# Pick a deterministic port per worktree, while still allowing overrides.
DEFAULT_PORT="$((8000 + (0x${WORKTREE_HASH} % 200)))"
PORT="${DJANGO_DEV_PORT:-${PORT:-${1:-${DEFAULT_PORT}}}}"

echo "[clippy] worktree=${WORKTREE_ROOT}"
echo "[clippy] sqlite=${DJANGO_SQLITE_PATH}"
echo "[clippy] port=${PORT}"

cd "${BACKEND_DIR}"
python manage.py migrate
python manage.py shell -c "from apps.accounts.bootstrap import ensure_admin_user_from_env; print(ensure_admin_user_from_env())"
python manage.py runserver "0.0.0.0:${PORT}"
