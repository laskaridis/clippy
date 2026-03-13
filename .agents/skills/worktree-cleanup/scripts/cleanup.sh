#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Safely remove completed git worktrees after strict safety checks.
# Preconditions: Must run from worktree root with clean tree and pushed upstream-tracking branch.
# Invariants: Refuses main worktree removal, validates cleanliness and ahead/behind state before deletion.
# Outcomes: Either reports check-only success or removes linked worktree safely.
# Artifacts:
# - Removes linked git worktree directory via `git worktree remove` (unless `--check-only`).
#

usage() {
  cat <<'USAGE'
Usage:
  cleanup_worktree.sh [--check-only]

Actions:
  1) verify current directory is a linked worktree
  2) fail if working tree is dirty
  3) fetch origin and fail if local branch is ahead of upstream
  4) cd to project root and remove the linked worktree

Options:
  --check-only   run all safety checks without removing the worktree
USAGE
}

CHECK_ONLY=0
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi
if [[ "${1:-}" == "--check-only" ]]; then
  CHECK_ONLY=1
elif [[ $# -gt 0 ]]; then
  echo "Unexpected argument: $1" >&2
  usage >&2
  exit 1
fi

WORKTREE_PATH="$(pwd -P)"
WORKTREE_TOPLEVEL="$(git rev-parse --show-toplevel)"
if [[ "$WORKTREE_TOPLEVEL" != "$WORKTREE_PATH" ]]; then
  echo "Run from the worktree root. Current: $WORKTREE_PATH, worktree root: $WORKTREE_TOPLEVEL" >&2
  exit 1
fi

COMMON_DIR="$(git rev-parse --git-common-dir)"
PROJECT_ROOT="$(cd "$COMMON_DIR/.." && pwd -P)"
if [[ "$WORKTREE_PATH" == "$PROJECT_ROOT" ]]; then
  echo "Refusing to remove the main working tree: $WORKTREE_PATH" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Worktree has local changes. Commit/stash/clean before cleanup." >&2
  git status --short >&2
  exit 1
fi

BRANCH="$(git branch --show-current)"
if [[ -z "$BRANCH" ]]; then
  echo "Detached HEAD is not supported for cleanup." >&2
  exit 1
fi

UPSTREAM_REF="$(git for-each-ref --format='%(upstream:short)' "refs/heads/$BRANCH")"
if [[ -z "$UPSTREAM_REF" ]]; then
  echo "Branch '$BRANCH' has no upstream tracking branch. Push first." >&2
  exit 1
fi
if [[ "$UPSTREAM_REF" != origin/* ]]; then
  echo "Branch '$BRANCH' must track origin/* for cleanup. Current upstream: '$UPSTREAM_REF'." >&2
  exit 1
fi

git fetch origin

AHEAD_BEHIND="$(git rev-list --left-right --count "$UPSTREAM_REF...HEAD")"
AHEAD_COUNT="${AHEAD_BEHIND##* }"
if [[ "$AHEAD_COUNT" -ne 0 ]]; then
  echo "Branch '$BRANCH' is ahead of '$UPSTREAM_REF' by $AHEAD_COUNT commit(s). Push first." >&2
  exit 1
fi

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  echo "Checks passed for $WORKTREE_PATH"
  exit 0
fi

cd "$PROJECT_ROOT"
git worktree remove "$WORKTREE_PATH"
echo "Removed worktree: $WORKTREE_PATH"
