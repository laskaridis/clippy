#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: gate.sh --issue <number> [--full-tests] [--to-review]
USAGE
}

ISSUE=""
FULL_TESTS=0
TO_REVIEW=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue) ISSUE="${2:-}"; shift 2 ;;
    --full-tests) FULL_TESTS=1; shift ;;
    --to-review) TO_REVIEW=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ -z "$ISSUE" ]]; then
  usage >&2
  exit 1
fi

if [[ ! -x ./scripts/agent-preflight.sh ]]; then
  echo "[feature-delivery-gate] missing ./scripts/agent-preflight.sh" >&2
  exit 1
fi

./scripts/agent-preflight.sh --issue "$ISSUE" --require-issue

if [[ "$FULL_TESTS" -eq 1 ]]; then
  ./scripts/test_worktree.sh
else
  (
    cd backend
    ENV_FILE="$(ls -1 .local/worktree-env-*.env 2>/dev/null | head -n 1 || true)"
    if [[ -n "$ENV_FILE" ]]; then
      set -a && source "$ENV_FILE" && set +a
    fi
    python manage.py test --noinput
  )
fi

BRANCH="$(git branch --show-current)"
if [[ -z "$BRANCH" ]]; then
  echo "[feature-delivery-gate] detached HEAD" >&2
  exit 1
fi

if ! gh pr list --head "$BRANCH" --state open --json number,url | grep -q '"number"'; then
  echo "[feature-delivery-gate] no open PR found for branch $BRANCH" >&2
  exit 1
fi

if [[ "$TO_REVIEW" -eq 1 ]]; then
  if ! gh label list --limit 200 | awk '{print $1}' | grep -Fxq "in review"; then
    gh label create "in review" --color "0E8A16" --description "Work is in review" >/dev/null
  fi
  gh issue edit "$ISSUE" --remove-label "in progress" --add-label "in review" >/dev/null
fi

echo "[feature-delivery-gate] passed for issue #$ISSUE"
