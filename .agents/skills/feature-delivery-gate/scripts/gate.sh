#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Execute feature delivery gate checks before handoff to review.
# Preconditions: Requires workflow preflight script and gh CLI connectivity.
# Invariants: Runs required preflight/tests and enforces existence of open PR for current branch.
# Outcomes: Confirms gate pass.
#

usage() {
  cat <<'USAGE'
Usage: gate.sh [--full-tests]
USAGE
}

FULL_TESTS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --full-tests) FULL_TESTS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 1 ;;
  esac
done

if [[ ! -x ./scripts/agent-preflight.sh ]]; then
  echo "[feature-delivery-gate] missing ./scripts/agent-preflight.sh" >&2
  exit 1
fi

./scripts/agent-preflight.sh

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

echo "[feature-delivery-gate] passed for branch ${BRANCH}"
