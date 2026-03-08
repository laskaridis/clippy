#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/agent-preflight.sh [--issue <number>] [--require-issue] [--set-in-progress]

Checks:
  - current branch is feature/<slug>
  - current directory is inside .worktrees/<name>
  - optional issue existence/assignment via GitHub CLI
EOF
}

ISSUE_NUMBER="${WORKFLOW_ISSUE_ID:-}"
REQUIRE_ISSUE="${WORKFLOW_REQUIRE_ISSUE:-0}"
SET_IN_PROGRESS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue)
      ISSUE_NUMBER="${2:-}"
      shift 2
      ;;
    --require-issue)
      REQUIRE_ISSUE=1
      shift
      ;;
    --set-in-progress)
      SET_IN_PROGRESS=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[agent-preflight] error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

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

if [[ "${REQUIRE_ISSUE}" == "1" && -z "${ISSUE_NUMBER}" ]]; then
  echo "[agent-preflight] error: --require-issue set but no issue provided" >&2
  exit 1
fi

if [[ -n "${ISSUE_NUMBER}" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "[agent-preflight] error: gh CLI is required when using --issue" >&2
    exit 1
  fi

  if ! gh issue view "${ISSUE_NUMBER}" --json number >/dev/null; then
    echo "[agent-preflight] error: issue #${ISSUE_NUMBER} not accessible" >&2
    exit 1
  fi

  if [[ "${SET_IN_PROGRESS}" == "1" ]]; then
    gh issue edit "${ISSUE_NUMBER}" --add-assignee @me --add-label "in progress" >/dev/null
  fi
fi

echo "[agent-preflight] ok branch=${BRANCH_NAME} dir=${CURRENT_DIR}"
if [[ -n "${ISSUE_NUMBER}" ]]; then
  echo "[agent-preflight] ok issue=#${ISSUE_NUMBER}"
fi
