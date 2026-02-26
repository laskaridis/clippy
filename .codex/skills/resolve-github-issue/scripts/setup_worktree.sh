#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  setup_worktree.sh <issue-number> [branch-name] [worktree-dir]

Defaults:
  branch-name: issue-<issue-number>
  worktree-dir: issue-<issue-number>

Actions:
  1) git fetch origin
  2) create or reuse .worktrees/<worktree-dir>
  3) print absolute worktree path
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

ISSUE_NUMBER="${1:-}"
if [[ -z "$ISSUE_NUMBER" || ! "$ISSUE_NUMBER" =~ ^[0-9]+$ ]]; then
  usage >&2
  exit 1
fi

BRANCH_NAME="${2:-issue-$ISSUE_NUMBER}"
WORKTREE_DIR="${3:-issue-$ISSUE_NUMBER}"

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

mkdir -p .worktrees

git fetch origin

if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
  EXISTING_PATH="$(git worktree list --porcelain | awk -v b="refs/heads/$BRANCH_NAME" '
    $1 == "worktree" { path=$2 }
    $1 == "branch" && $2 == b { print path; exit }
  ')"

  if [[ -n "$EXISTING_PATH" ]]; then
    echo "$EXISTING_PATH"
    exit 0
  fi

  git worktree add ".worktrees/$WORKTREE_DIR" "$BRANCH_NAME"
  realpath ".worktrees/$WORKTREE_DIR"
  exit 0
fi

git worktree add ".worktrees/$WORKTREE_DIR" -b "$BRANCH_NAME" origin/master
realpath ".worktrees/$WORKTREE_DIR"
