#!/usr/bin/env bash
set -euo pipefail

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
