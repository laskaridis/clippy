#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Run backend browser E2E tests (Playwright) in a worktree-aware runtime context.
# Preconditions: Local infra/runtime scripts exist and Playwright package is installed in backend env.
# Invariants: Ensures runtime env is loaded before browser tests and installs Chromium for deterministic runs.
# Outcomes: Executes Django E2E tests that interact with the real backend-rendered web UI.
# Artifacts:
# - Uses backend/scripts/env.sh exports to scope runtime config for browser-driven Django tests.
# - Installs/uses Playwright Chromium browser binary for the current execution environment.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
BACKEND_PYTHON="${BACKEND_DIR}/.venv/bin/python"
INFRA_ENSURE_SCRIPT="${ROOT_DIR}/infra/local/scripts/ensure-worktree-runtime.sh"
ENV_SCRIPT="${BACKEND_DIR}/scripts/env.sh"

help() {
  cat <<'EOF'
Run backend Playwright E2E tests in a worktree-aware environment.

Flow:
  1) Ensure local infra is ready (starts dockerized PostgreSQL if needed)
  2) Load current worktree runtime variables via backend/scripts/env.sh
  3) Install Playwright Chromium browser binary if missing
  4) Execute python manage.py test with passthrough args (defaults to backend quick-search E2E module)

Usage:
  backend/scripts/test-e2e.sh [manage.py test args...]
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  help
  exit 0
fi

if [[ ! -x "${INFRA_ENSURE_SCRIPT}" ]]; then
  echo "[backend-e2e] error: missing executable ${INFRA_ENSURE_SCRIPT}" >&2
  exit 1
fi

if [[ ! -x "${ENV_SCRIPT}" ]]; then
  echo "[backend-e2e] error: missing executable ${ENV_SCRIPT}" >&2
  exit 1
fi

if [[ ! -x "${BACKEND_PYTHON}" ]]; then
  echo "[backend-e2e] error: missing Python interpreter ${BACKEND_PYTHON}" >&2
  echo "[backend-e2e] hint: run 'make backend-init' first." >&2
  exit 1
fi

echo "[backend-e2e] ensuring local infrastructure"
"${INFRA_ENSURE_SCRIPT}"

echo "[backend-e2e] loading worktree environment"
ENV_EXPORTS="$("${ENV_SCRIPT}" --print)"
set -a
# shellcheck disable=SC1091
source /dev/stdin <<<"${ENV_EXPORTS}"
set +a

if [[ "${BACKEND_E2E_SKIP_BROWSER_INSTALL:-0}" != "1" ]]; then
  echo "[backend-e2e] ensuring Playwright Chromium browser (best effort)"
  if ! (
    cd "${BACKEND_DIR}"
    "${BACKEND_PYTHON}" -m playwright install chromium
  ); then
    echo "[backend-e2e] warning: failed to install Playwright Chromium; continuing with system browser channel if available." >&2
  fi
fi

if [[ $# -gt 0 ]]; then
  TEST_ARGS=("$@")
else
  TEST_ARGS=("apps.clips.tests.e2e.test_quick_search_e2e")
fi

echo "[backend-e2e] running: python manage.py test --tag=e2e ${TEST_ARGS[*]}"
(
  cd "${BACKEND_DIR}"
  "${BACKEND_PYTHON}" manage.py test --tag=e2e "${TEST_ARGS[@]}"
)
