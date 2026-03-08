#!/usr/bin/env bash
set -euo pipefail

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
