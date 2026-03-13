#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Run backend and extension lint checks in a single workflow.
# Preconditions: Run from repository with lint dependencies installed in backend and extension.
# Invariants: Backend uses ruff and extension uses eslint; any lint failure stops the script.
# Outcomes: Produces pass/fail lint gate across both projects.
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[lint] backend (ruff)"
(
  cd "${ROOT_DIR}/backend"
  python -m ruff check .
)

echo "[lint] extension (eslint)"
(
  cd "${ROOT_DIR}/extension"
  pnpm run lint
)

echo "[lint] complete"
