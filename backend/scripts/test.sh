#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Run backend Django tests in a worktree-aware runtime context.
# Preconditions: Infra ensure script and env helper script must be present and executable.
# Invariants: Always ensures runtime readiness before loading env exports and invoking manage.py test.
# Outcomes: Returns backend test results using the active worktree configuration.
# Artifacts:
# - Sources exported env payload from `backend/scripts/env.sh --print` into test process scope — establishes worktree runtime variables for test execution.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
INFRA_ENSURE_SCRIPT="${ROOT_DIR}/infra/local/scripts/ensure-worktree-runtime.sh"
ENV_SCRIPT="${BACKEND_DIR}/scripts/env.sh"

help() {
  cat <<'EOF'
Run backend tests in a worktree-aware environment.

Flow:
  1) Ensure local infra is ready (starts dockerized PostgreSQL if needed)
  2) Load current worktree runtime variables via backend/scripts/env.sh
  3) Execute python manage.py test with passthrough arguments

Usage:
  backend/scripts/test.sh [manage.py test args...]
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  help
  exit 0
fi

if [[ ! -x "${INFRA_ENSURE_SCRIPT}" ]]; then
  echo "[backend-test] error: missing executable ${INFRA_ENSURE_SCRIPT}" >&2
  exit 1
fi

if [[ ! -x "${ENV_SCRIPT}" ]]; then
  echo "[backend-test] error: missing executable ${ENV_SCRIPT}" >&2
  exit 1
fi

echo "[backend-test] ensuring local infrastructure"
"${INFRA_ENSURE_SCRIPT}"

echo "[backend-test] loading worktree environment"
ENV_EXPORTS="$("${ENV_SCRIPT}" --print)"
set -a
# shellcheck disable=SC1091
source /dev/stdin <<<"${ENV_EXPORTS}"
set +a

echo "[backend-test] running: python manage.py test $*"
(
  cd "${BACKEND_DIR}"
  python manage.py test "$@"
)
