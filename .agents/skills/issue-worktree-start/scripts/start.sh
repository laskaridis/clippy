#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Start issue work by creating compliant worktree/branch via shared workflow script.
# Preconditions: Requires issue id and slug; optional bootstrap requires worktree-bootstrap skill script.
# Invariants: Delegates canonical setup to scripts/start-task.sh to preserve workflow invariants.
# Outcomes: Creates worktree context and optionally bootstraps runtime artifacts.
# Artifacts:
# - Delegated artifacts from `scripts/start-task.sh` (worktree path, feature branch, issue state updates).
# - Optional delegated runtime artifacts from worktree-bootstrap (env/json/build outputs) when `--bootstrap` is passed.
#

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
