#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKTREE_ROOT="$(cd "${BACKEND_DIR}/.." && git rev-parse --show-toplevel)"
WORKTREE_BASENAME="$(basename "${WORKTREE_ROOT}")"
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

VENV_DIR="${BACKEND_DIR}/.venv"
REQUIREMENTS_FILE="${BACKEND_DIR}/requirements.txt"
REQUIREMENTS_STAMP="${VENV_DIR}/.requirements.sha256"

compute_requirements_hash() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${REQUIREMENTS_FILE}" | cut -d ' ' -f1
    return
  fi

  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${REQUIREMENTS_FILE}" | cut -d ' ' -f1
    return
  fi

  echo "[clippy] error: neither sha256sum nor shasum is available" >&2
  exit 1
}

ensure_virtualenv_and_requirements() {
  if [ ! -d "${VENV_DIR}" ]; then
    echo "[clippy] creating virtualenv at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
  fi

  # shellcheck disable=SC1090
  source "${VENV_DIR}/bin/activate"

  if ! python -m pip --version >/dev/null 2>&1; then
    echo "[clippy] error: pip is unavailable in ${VENV_DIR}" >&2
    exit 1
  fi

  local current_hash
  current_hash="$(compute_requirements_hash)"
  local installed_hash=""
  if [ -f "${REQUIREMENTS_STAMP}" ]; then
    installed_hash="$(cat "${REQUIREMENTS_STAMP}")"
  fi

  if [ "${current_hash}" != "${installed_hash}" ]; then
    echo "[clippy] installing backend requirements"
    python -m pip install -r "${REQUIREMENTS_FILE}"
    printf '%s' "${current_hash}" > "${REQUIREMENTS_STAMP}"
  else
    echo "[clippy] backend requirements already up to date"
  fi
}

echo "[clippy] worktree=${WORKTREE_ROOT}"
echo "[clippy] sqlite=${DJANGO_SQLITE_PATH}"
echo "[clippy] port=${PORT}"

cd "${BACKEND_DIR}"
ensure_virtualenv_and_requirements
python manage.py migrate
python manage.py shell -c "from apps.accounts.bootstrap import ensure_admin_user_from_env; print(ensure_admin_user_from_env())"

if [ "${CLIPPY_SKIP_RUNSERVER:-0}" = "1" ]; then
  echo "[clippy] skipping runserver because CLIPPY_SKIP_RUNSERVER=1"
  exit 0
fi

python manage.py runserver "0.0.0.0:${PORT}"
