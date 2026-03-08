#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: start.sh --issue <number> --slug <task-slug> [--base <branch>] [--bootstrap]
USAGE
}

ISSUE=""
SLUG=""
BASE="master"
BOOTSTRAP=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue) ISSUE="${2:-}"; shift 2 ;;
    --slug) SLUG="${2:-}"; shift 2 ;;
    --base) BASE="${2:-}"; shift 2 ;;
    --bootstrap) BOOTSTRAP=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ -z "$ISSUE" || -z "$SLUG" ]]; then
  usage >&2
  exit 1
fi

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/../../.." && pwd)"

"${REPO_ROOT}/scripts/start-task.sh" "$ISSUE" "$SLUG" "$BASE"

if [[ "$BOOTSTRAP" -eq 1 ]]; then
  WORKTREE_PATH="${REPO_ROOT}/.worktrees/${SLUG}"
  (
    cd "${WORKTREE_PATH}/.agents/skills/worktree-bootstrap"
    ./scripts/bootstrap.sh
  )
fi
