#!/usr/bin/env bash
set -euo pipefail

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
