#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Execute the full worktree test stack across backend, extension unit, and extension e2e.
# Preconditions: Backend bootstrap script and extension test dependencies must be available.
# Invariants: Bootstraps runtime first, loads worktree env, then runs tests with non-interactive backend execution.
# Outcomes: Confirms cross-project behavior for the current worktree when all suites pass.
# Artifacts:
# - Uses `backend/.local/worktree-env-<worktree-id>.env` (resolved via `bootsrap.sh --print-env-path`) — runtime env artifact sourced for backend tests.
#

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

echo "[test-worktree] running backend unit/integration tests"
(
  cd "${BACKEND_DIR}"
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
  python manage.py test --exclude-tag=e2e --noinput
)

echo "[test-worktree] running backend browser e2e tests"
(
  cd "${BACKEND_DIR}"
  ./scripts/test-e2e.sh
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
