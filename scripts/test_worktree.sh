#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
EXTENSION_DIR="${ROOT_DIR}/extension"
BACKEND_SCRIPT="${BACKEND_DIR}/scripts/bootsrap.sh"

if [[ ! -x "${BACKEND_SCRIPT}" ]]; then
  echo "[test-worktree] error: missing executable ${BACKEND_SCRIPT}" >&2
  exit 1
fi

echo "[test-worktree] bootstrapping backend runtime"
"${BACKEND_SCRIPT}" --bootstrap-only

ENV_FILE="$("${BACKEND_SCRIPT}" --print-env-path)"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[test-worktree] error: expected env file not found at ${ENV_FILE}" >&2
  exit 1
fi

echo "[test-worktree] running backend tests"
(
  cd "${BACKEND_DIR}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
  python manage.py test
)

echo "[test-worktree] running extension unit tests"
(
  cd "${EXTENSION_DIR}"
  pnpm test
)

echo "[test-worktree] running extension e2e tests"
(
  cd "${EXTENSION_DIR}"
  pnpm run test:e2e
)

echo "[test-worktree] complete"
