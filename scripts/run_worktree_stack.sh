#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_SCRIPT="${ROOT_DIR}/backend/scripts/bootsrap.sh"
EXTENSION_DIR="${ROOT_DIR}/extension"

SKIP_EXTENSION_BUILD=0
PASSTHROUGH_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-extension-build)
      SKIP_EXTENSION_BUILD=1
      shift
      ;;
    *)
      PASSTHROUGH_ARGS+=("$1")
      shift
      ;;
  esac
done

if [[ ! -x "${BACKEND_SCRIPT}" ]]; then
  echo "[run-worktree-stack] error: missing executable ${BACKEND_SCRIPT}" >&2
  exit 1
fi

if [[ "${SKIP_EXTENSION_BUILD}" == "0" ]]; then
  echo "[run-worktree-stack] preparing extension worktree build"
  (
    cd "${EXTENSION_DIR}"
    pnpm run build:worktree
  )
fi

echo "[run-worktree-stack] starting backend"
exec "${BACKEND_SCRIPT}" "${PASSTHROUGH_ARGS[@]}"
