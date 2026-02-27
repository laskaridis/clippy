#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  gh_create_pr.sh <issue-number> --body-file <path> [--title <title>]

Requirements:
  - Tests must have been run with scripts/run_required_tests.sh
  - Current branch must not be master
USAGE
}

ISSUE_NUMBER=""
BODY_FILE=""
TITLE=""

if [[ $# -eq 0 ]]; then
  usage >&2
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --body-file)
      BODY_FILE="${2:-}"
      shift 2
      ;;
    --title)
      TITLE="${2:-}"
      shift 2
      ;;
    *)
      if [[ -z "$ISSUE_NUMBER" ]]; then
        ISSUE_NUMBER="$1"
        shift
      else
        echo "Unexpected argument: $1" >&2
        usage >&2
        exit 1
      fi
      ;;
  esac
done

if [[ -z "$ISSUE_NUMBER" || ! "$ISSUE_NUMBER" =~ ^[0-9]+$ ]]; then
  echo "Issue number is required and must be numeric" >&2
  usage >&2
  exit 1
fi

if [[ -z "$BODY_FILE" || ! -f "$BODY_FILE" ]]; then
  echo "--body-file is required and must exist" >&2
  usage >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

CURRENT_BRANCH="$(git branch --show-current)"
if [[ -z "$CURRENT_BRANCH" || "$CURRENT_BRANCH" == "master" ]]; then
  echo "Run from a non-master branch/worktree" >&2
  exit 1
fi

if [[ ! -f .local/resolve-gh-issue-tests.ok ]]; then
  echo "Missing .local/resolve-gh-issue-tests.ok. Run run_required_tests.sh first." >&2
  exit 1
fi

LAST_TESTED_SHA="$(cat .local/resolve-gh-issue-tests.ok)"
CURRENT_SHA="$(git rev-parse HEAD)"
if [[ "$LAST_TESTED_SHA" != "$CURRENT_SHA" ]]; then
  echo "Tests were not run on current HEAD ($CURRENT_SHA). Last tested: $LAST_TESTED_SHA" >&2
  echo "Run run_required_tests.sh again before creating PR." >&2
  exit 1
fi

if [[ -z "$TITLE" ]]; then
  ISSUE_TITLE="$(gh issue view "$ISSUE_NUMBER" --json title --jq '.title')"
  TITLE="Fixes #$ISSUE_NUMBER: $ISSUE_TITLE"
fi

if [[ "$TITLE" != *"Fixes #$ISSUE_NUMBER"* ]]; then
  TITLE="$TITLE (Fixes #$ISSUE_NUMBER)"
fi

git push -u origin "$CURRENT_BRANCH"

PR_URL="$(gh pr create --base master --head "$CURRENT_BRANCH" --title "$TITLE" --body-file "$BODY_FILE")"

echo "Created PR: $PR_URL"

python3 .agents/skills/resolve-github-issue/scripts/gh_update_issue.py \
  --issue "$ISSUE_NUMBER" \
  --status "In review" \
  --skip-assign

echo "[delivery] issue #$ISSUE_NUMBER moved to In review"
