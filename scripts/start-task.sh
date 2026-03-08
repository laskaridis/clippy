#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/start-task.sh <issue-number> <task-slug> [base-branch]

Example:
  scripts/start-task.sh 123 quick-search-milestone3 master
EOF
}

if [[ $# -eq 1 && ( "$1" == "--help" || "$1" == "-h" ) ]]; then
  usage
  exit 0
fi

if [[ $# -lt 2 || $# -gt 3 ]]; then
  usage >&2
  exit 1
fi

ISSUE_NUMBER="$1"
TASK_SLUG="$2"
BASE_BRANCH="${3:-master}"

if [[ ! "${ISSUE_NUMBER}" =~ ^[0-9]+$ ]]; then
  echo "[start-task] error: issue number must be numeric" >&2
  exit 1
fi

if [[ ! "${TASK_SLUG}" =~ ^[a-z0-9-]+$ ]]; then
  echo "[start-task] error: task slug must match [a-z0-9-]+" >&2
  exit 1
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "[start-task] error: run this command from a git repository" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "[start-task] error: gh CLI is required" >&2
  exit 1
fi

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "${ROOT_DIR}"

WORKTREE_DIR="${ROOT_DIR}/.worktrees/${TASK_SLUG}"
BRANCH_NAME="feature/${TASK_SLUG}"

git fetch --quiet origin "${BASE_BRANCH}"

if git show-ref --verify --quiet "refs/heads/${BRANCH_NAME}"; then
  echo "[start-task] error: branch ${BRANCH_NAME} already exists locally" >&2
  exit 1
fi

if [[ -e "${WORKTREE_DIR}" ]]; then
  echo "[start-task] error: worktree path exists: ${WORKTREE_DIR}" >&2
  exit 1
fi

git worktree add "${WORKTREE_DIR}" -b "${BRANCH_NAME}" "origin/${BASE_BRANCH}"

if ! gh label list --limit 200 | awk '{print $1}' | grep -Fxq "in progress"; then
  gh label create "in progress" --color "FBCA04" --description "Work actively in progress" >/dev/null
fi

gh issue edit "${ISSUE_NUMBER}" --add-assignee @me --add-label "in progress" >/dev/null

cat <<EOF
[start-task] created worktree: ${WORKTREE_DIR}
[start-task] branch: ${BRANCH_NAME}
[start-task] issue: #${ISSUE_NUMBER} assigned and moved to in progress

Next:
  cd ${WORKTREE_DIR}
  scripts/agent-preflight.sh --issue ${ISSUE_NUMBER} --require-issue
EOF
