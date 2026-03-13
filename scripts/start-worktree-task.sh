#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Create a compliant feature branch worktree without GitHub issue integration.
# Preconditions: Run inside a git repository; task slug follows [a-z0-9-]+.
# Invariants: Branch naming and worktree location follow workflow policy.
# Outcomes: Creates `.worktrees/<slug>` and branch `feature/<slug>` from the chosen base branch.
#

usage() {
  cat <<'EOF'
Usage: scripts/start-worktree-task.sh <task-slug> [base-branch]

Example:
  scripts/start-worktree-task.sh orchestrated-agent-workflow master
EOF
}

if [[ $# -eq 1 && ( "$1" == "--help" || "$1" == "-h" ) ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage >&2
  exit 1
fi

TASK_SLUG="$1"
BASE_BRANCH="${2:-master}"

if [[ ! "${TASK_SLUG}" =~ ^[a-z0-9-]+$ ]]; then
  echo "[start-worktree-task] error: task slug must match [a-z0-9-]+" >&2
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "[start-worktree-task] error: run this command from a git repository" >&2
  exit 1
fi

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "${ROOT_DIR}"

WORKTREE_DIR="${ROOT_DIR}/.worktrees/${TASK_SLUG}"
BRANCH_NAME="feature/${TASK_SLUG}"

git fetch --quiet origin "${BASE_BRANCH}"

if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "[start-worktree-task] error: branch ${BRANCH_NAME} already exists locally" >&2
  exit 1
fi

if [[ -e "${WORKTREE_DIR}" ]]; then
  echo "[start-worktree-task] error: worktree path exists: ${WORKTREE_DIR}" >&2
  exit 1
fi

git worktree add "${WORKTREE_DIR}" -b "${BRANCH_NAME}" "origin/${BASE_BRANCH}"

cat <<EOF
[start-worktree-task] created worktree: ${WORKTREE_DIR}
[start-worktree-task] branch: ${BRANCH_NAME}

Next:
  cd ${WORKTREE_DIR}
  scripts/agent-preflight.sh
EOF

