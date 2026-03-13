#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Enforce hard workflow preflight gates before development or commit operations.
# Preconditions: Run in a git worktree.
# Invariants: Validates feature branch naming and .worktrees location.
# Outcomes: Exits non-zero on any policy violation and prints actionable error context.
#

usage() {
  cat <<'EOF'
Usage: scripts/agent-preflight.sh

Checks:
  - current branch is feature/<slug>
  - current directory is inside .worktrees/<name>
EOF
}

if [[ $# -gt 0 ]]; then
  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
  fi
  echo "[agent-preflight] error: unknown argument: $1" >&2
  usage >&2
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "[agent-preflight] error: not inside a git repository" >&2
  exit 1
fi

ROOT_DIR="$(git rev-parse --show-toplevel)"
CURRENT_DIR="$(pwd -P)"

if ! BRANCH_NAME="$(git symbolic-ref --quiet --short HEAD 2>/dev/null)"; then
  echo "[agent-preflight] error: detached HEAD is not allowed for task work" >&2
  exit 1
fi

if [[ ! "${BRANCH_NAME}" =~ ^feature/[a-z0-9-]+$ ]]; then
  echo "[agent-preflight] error: branch '${BRANCH_NAME}' must match feature/<slug>" >&2
  exit 1
fi

if [[ "${ROOT_DIR}" != *"/.worktrees/"* ]]; then
  echo "[agent-preflight] error: repository root must be a dedicated .worktrees checkout" >&2
  exit 1
fi

if [[ "${CURRENT_DIR}" != "${ROOT_DIR}"* ]]; then
  echo "[agent-preflight] error: command must run from within the worktree root" >&2
  exit 1
fi

echo "[agent-preflight] ok branch=${BRANCH_NAME} dir=${CURRENT_DIR}"
