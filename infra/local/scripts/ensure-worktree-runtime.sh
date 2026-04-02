#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Ensure backend runtime metadata and database availability for the active worktree.
# Preconditions: backend bootsrap.sh must be executable and capable of producing runtime JSON.
# Invariants: Treats runtime JSON as source of truth and fails fast on missing prerequisites.
# Outcomes: Prints concise readiness summary after DB/runtime checks complete.
# Artifacts:
# - Delegated `backend/.local/worktree-env-<worktree-id>.env` generation via `bootsrap.sh --ensure-runtime-json` (runtime env contract).
# - Delegated `backend/.local/worktree-runtime-<worktree-id>.json` generation via `bootsrap.sh --ensure-runtime-json` (runtime metadata for tooling).
# - Delegated Docker Compose postgres runtime state when bootstrap resolves to managed worktree Postgres.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
BACKEND_BOOTSTRAP_SCRIPT="${ROOT_DIR}/backend/scripts/bootsrap.sh"

help() {
  cat <<'EOF'
Ensure local infrastructure for this worktree is ready.

This command resolves worktree runtime settings and guarantees the configured
database is reachable. When DATABASE_URL is not set, it starts the local
dockerized PostgreSQL service defined in infra/docker/docker-compose.yml.

Usage:
  infra/local/scripts/ensure-worktree-runtime.sh
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  help
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "[infra-local] error: unexpected arguments: $*" >&2
  help >&2
  exit 1
fi

if [[ ! -x "${BACKEND_BOOTSTRAP_SCRIPT}" ]]; then
  echo "[infra-local] error: missing executable ${BACKEND_BOOTSTRAP_SCRIPT}" >&2
  exit 1
fi

echo "[infra-local] ensuring worktree runtime and database availability"
runtime_json="$("${BACKEND_BOOTSTRAP_SCRIPT}" --ensure-runtime-json)"

runtime_summary="$(
  RUNTIME_JSON="${runtime_json}" python - <<'PY'
import json
import os

payload = json.loads(os.environ["RUNTIME_JSON"])
print(
    f"[infra-local] ready: mode={payload.get('databaseMode')}, "
    f"db={payload.get('databaseName')}, port={payload.get('databasePort')}, "
    f"env={payload.get('envFile')}"
)
PY
)"
echo "${runtime_summary}"
