#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Build extension runtime artifacts and start the backend server for this worktree.
# Preconditions: Requires extension dependencies and a devcontainer-local backend start command.
# Invariants: Ensures extension build step runs unless skipped and delegates backend lifecycle to `make backend-run`.
# Outcomes: Starts a worktree-scoped local stack with deterministic runtime metadata.
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
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

if [[ ${#PASSTHROUGH_ARGS[@]} -gt 0 ]]; then
  echo "[run-worktree-stack] error: passthrough args are no longer supported; run make backend-run directly" >&2
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
(
  cd "${BACKEND_DIR}"
  exec make backend-run
)
