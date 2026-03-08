#!/usr/bin/env bash
set -euo pipefail

ISSUE=""
STRICT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue) ISSUE="${2:-}"; shift 2 ;;
    --strict) STRICT=1; shift ;;
    -h|--help)
      echo "Usage: audit.sh [--issue <number>] [--strict]"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

fail_count=0
warn_count=0

note_fail() { echo "[workflow-audit] FAIL: $1"; fail_count=$((fail_count+1)); }
note_warn() { echo "[workflow-audit] WARN: $1"; warn_count=$((warn_count+1)); }
note_ok() { echo "[workflow-audit] OK: $1"; }

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$ROOT" ]]; then
  note_fail "not in git repo"
else
  if [[ "$ROOT" == *"/.worktrees/"* ]]; then
    note_ok "running in dedicated worktree"
  else
    note_fail "not running in .worktrees checkout"
  fi

  BRANCH="$(git branch --show-current)"
  if [[ "$BRANCH" =~ ^feature/[a-z0-9-]+$ ]]; then
    note_ok "feature branch naming is valid ($BRANCH)"
  else
    note_fail "branch must match feature/<slug>; current=${BRANCH:-detached}"
  fi

  if [[ -n "$(git status --porcelain)" ]]; then
    note_warn "worktree has local changes"
  else
    note_ok "worktree is clean"
  fi
fi

if [[ -n "$ISSUE" ]]; then
  if gh issue view "$ISSUE" --json number,state,assignees,labels >/tmp/workflow-audit-issue.json 2>/dev/null; then
    note_ok "issue #$ISSUE is accessible"
  else
    note_fail "issue #$ISSUE is not accessible via gh"
  fi
fi

BRANCH="$(git branch --show-current 2>/dev/null || true)"
if [[ -n "$BRANCH" ]]; then
  if gh pr list --head "$BRANCH" --state open --json number,url | grep -q '"number"'; then
    note_ok "open PR exists for branch $BRANCH"
  else
    note_warn "no open PR found for branch $BRANCH"
  fi
fi

if [[ "$fail_count" -gt 0 ]]; then
  exit 1
fi

if [[ "$STRICT" -eq 1 && "$warn_count" -gt 0 ]]; then
  exit 2
fi

echo "[workflow-audit] complete: fail=$fail_count warn=$warn_count"
