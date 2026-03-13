#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Record auditable emergency bypass usage details for policy exceptions.
# Preconditions: Requires both reason and ticket reference arguments.
# Invariants: Always appends immutable log entries to .local/emergency-bypass.log before suggesting commands.
# Outcomes: Creates an audit trail and prints required follow-up remediation guidance.
# Artifacts:
# - `.local/emergency-bypass.log` append-only entries (`timestamp`, `branch`, `ticket`, `reason`) — auditable bypass ledger.
#

REASON=""
TICKET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reason) REASON="${2:-}"; shift 2 ;;
    --ticket) TICKET="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: bypass.sh --reason <text> --ticket <incident-or-task-ref>"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$REASON" || -z "$TICKET" ]]; then
  echo "Both --reason and --ticket are required" >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel)"
BRANCH="$(git branch --show-current 2>/dev/null || echo detached)"
NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
LOG_DIR="${ROOT}/.local"
LOG_FILE="${LOG_DIR}/emergency-bypass.log"
mkdir -p "$LOG_DIR"

{
  echo "timestamp=${NOW}"
  echo "branch=${BRANCH}"
  echo "ticket=${TICKET}"
  echo "reason=${REASON}"
  echo "---"
} >> "$LOG_FILE"

echo "[safe-emergency-bypass] logged bypass request to ${LOG_FILE}"
echo "[safe-emergency-bypass] next command (narrow bypass):"
echo "  SKIP_FEATURE_BRANCH_CHECK=1 git commit -m \"Emergency fix (${TICKET}): <summary>\""
echo "[safe-emergency-bypass] fallback (last resort):"
echo "  git commit --no-verify -m \"Emergency fix (${TICKET}): <summary>\""
echo "[safe-emergency-bypass] required follow-up: open remediation task/PR to restore full compliance."
