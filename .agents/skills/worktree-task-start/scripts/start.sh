#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Start task work by creating compliant branch/worktree without issue integration.
# Preconditions: Requires slug; optional base branch.
# Invariants: Delegates canonical setup to scripts/start-worktree-task.sh.
# Outcomes: Creates feature branch worktree under .worktrees.
#

usage() {
  cat <<'USAGE'
Usage: start.sh --slug <task-slug> [--base <branch>]
USAGE
}

SLUG=""
BASE="master"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --slug) SLUG="${2:-}"; shift 2 ;;
    --base) BASE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ -z "$SLUG" ]]; then
  usage >&2
  exit 1
fi

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/../../.." && pwd)"

"${REPO_ROOT}/scripts/start-worktree-task.sh" "$SLUG" "$BASE"

