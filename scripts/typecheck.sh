#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Run backend and extension type checks as a combined gate.
# Preconditions: Dependencies and typecheck tools must already be installed in each subproject.
# Invariants: Uses mypy for backend and TypeScript no-emit check for extension; exits on first failure.
# Outcomes: Returns success only when both projects pass type checks.
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[typecheck] backend (mypy)"
(
  cd "${ROOT_DIR}/backend"
  python -m mypy .
)

echo "[typecheck] extension (tsc --noEmit)"
(
  cd "${ROOT_DIR}/extension"
  pnpm run typecheck
)

echo "[typecheck] complete"
