#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  pickup_gh_issue.sh <issue-number>

Actions:
  1) Fetch and print issue summary
  2) Move issue to project status "In progress"
USAGE
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
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

require_cmd gh
require_cmd python3

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

echo "[pickup] loading issue #$ISSUE_NUMBER"
gh issue view "$ISSUE_NUMBER" --json number,title,url,body

python3 .codex/skills/resolve-github-issue/scripts/set_project_status.py \
  --issue "$ISSUE_NUMBER" \
  --status "In progress"

echo "[pickup] issue #$ISSUE_NUMBER is in progress"
