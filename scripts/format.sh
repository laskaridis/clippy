#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Format backend and extension source trees in one command.
# Preconditions: Run from repo checkout with python and pnpm dependencies already installed.
# Invariants: Backend is formatted with black and extension with prettier; command fails on tool errors.
# Outcomes: Leaves codebase consistently formatted and prints phase progress.
# Artifacts:
# - Reformatted source files in `backend/` and `extension/` when formatting changes are needed.
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[format] backend (black)"
(
  cd "${ROOT_DIR}/backend"
  python -m black .
)

echo "[format] extension (prettier)"
(
  cd "${ROOT_DIR}/extension"
  pnpm run format
)

echo "[format] complete"
