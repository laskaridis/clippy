#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"

help() {
  cat <<'EOF'
Run backend non-E2E tests.

Flow:
  1) Change to backend/
  2) Execute python manage.py test excluding E2E-tagged tests

Usage:
  backend/scripts/test.sh [manage.py test args...]
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  help
  exit 0
fi

echo "[backend-test] running: python manage.py test --exclude-tag=e2e $*"
(
  cd "${BACKEND_DIR}"
  python manage.py test --exclude-tag=e2e "$@"
)
