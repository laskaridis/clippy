#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

help() {
  cat <<'EOF'
Run backend Playwright E2E tests in the prepared devcontainer environment.

Flow:
  1) Change to backend/
  2) Install Playwright Chromium browser binary if requested and missing
  3) Execute python manage.py test --tag=e2e with passthrough args (defaults to backend quick-search E2E module)

Usage:
  backend/scripts/test-e2e.sh [manage.py test args...]
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  help
  exit 0
fi

if [[ "${BACKEND_E2E_SKIP_BROWSER_INSTALL:-0}" != "1" ]]; then
  echo "[backend-e2e] ensuring Playwright Chromium browser (best effort)"
  if ! (
    cd "${BACKEND_DIR}"
    python -m playwright install chromium
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
  python manage.py test --tag=e2e "${TEST_ARGS[@]}"
)
