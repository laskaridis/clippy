#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Bootstrap and validate backend+extension runtime assets for one worktree.
# Preconditions: Requires backend bootstrap script, python3, pnpm, and generated extension tooling.
# Invariants: Resolves runtime JSON, rebuilds extension artifacts, and verifies metadata/manifest alignment.
# Outcomes: Outputs deterministic runtime summary usable by agents and local tooling.
# Artifacts:
# - `/tmp/worktree-bootstrap-backend.log` and `/tmp/worktree-bootstrap-build.log` — transient diagnostics for bootstrap/build failures.
# - Delegated generated artifacts from backend/extension scripts (worktree env/runtime json and extension `.local/worktrees/<id>/chrome`).
#

# Bootstrap and verify worktree-scoped runtime artifacts for backend + extension.
# This script:
# 1) resolves backend runtime values from bootsrap.sh --print-json
# 2) builds extension worktree artifacts
# 3) validates runtime metadata and generated extension config alignment
# 4) prints a deterministic summary for agent/user consumption

help() {
  cat <<'EOF'
Usage:
  bootstrap_worktree_runtime.sh

Bootstraps and verifies local worktree runtime for this repository.

Checks performed:
  - backend bootstrap via backend/scripts/bootsrap.sh --bootstrap-only
  - backend runtime resolution via backend/scripts/bootsrap.sh --print-json
  - extension build via pnpm run build:worktree
  - generated extension directory exists:
      extension/.local/worktrees/<worktree-id>/chrome
  - runtime metadata exists:
      extension/.local/worktree-runtime-<worktree-id>.json
  - generated manifest/runtime-config point to the resolved backend base URL
  - optional listening-port health check (lsof)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  help
  exit 0
fi

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  C_INFO=$'\033[0;32m'
  C_WARN=$'\033[0;33m'
  C_ERR=$'\033[0;31m'
  C_OFF=$'\033[0m'
else
  C_INFO=""
  C_WARN=""
  C_ERR=""
  C_OFF=""
fi

info() { printf '%b\n' "${C_INFO}[worktree-bootstrap] $*${C_OFF}"; }
warn() { printf '%b\n' "${C_WARN}[worktree-bootstrap] warning: $*${C_OFF}"; }
err() { printf '%b\n' "${C_ERR}[worktree-bootstrap] error: $*${C_OFF}" >&2; }

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "${SKILL_DIR}/../../.." && pwd)"
BACKEND_SCRIPT="${REPO_ROOT}/backend/scripts/bootsrap.sh"
EXTENSION_DIR="${REPO_ROOT}/extension"

if [[ ! -x "${BACKEND_SCRIPT}" ]]; then
  err "missing executable backend bootstrap script: ${BACKEND_SCRIPT}"
  exit 1
fi

if ! command -v pnpm >/dev/null 2>&1; then
  err "pnpm is required but not found"
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  err "python3 is required but not found"
  exit 1
fi

info "bootstrapping backend runtime via bootsrap.sh --bootstrap-only"
"${BACKEND_SCRIPT}" --bootstrap-only >/tmp/worktree-bootstrap-backend.log 2>&1 || {
  cat /tmp/worktree-bootstrap-backend.log >&2
  err "backend bootstrap failed"
  exit 1
}

info "resolving backend runtime via bootsrap.sh --print-json"
RUNTIME_JSON="$("${BACKEND_SCRIPT}" --print-json)"

# Extract a single key from the backend runtime JSON payload.
read_field() {
  local key="$1"
  RUNTIME_JSON="${RUNTIME_JSON}" KEY_NAME="${key}" python3 - <<'PY'
import json
import os

obj = json.loads(os.environ["RUNTIME_JSON"])
value = obj[os.environ["KEY_NAME"]]
print(value)
PY
}

WORKTREE_ID="$(read_field worktreeId)"
BACKEND_HOST="$(read_field backendHost)"
BACKEND_PORT="$(read_field backendPort)"
BACKEND_BASE_URL="$(read_field backendBaseUrl)"
DATABASE_URL="$(read_field databaseUrl)"
ENV_FILE="$(read_field envFile)"

info "building extension runtime (pnpm run build:worktree)"
(
  cd "${EXTENSION_DIR}"
  pnpm run build:worktree >/tmp/worktree-bootstrap-build.log 2>&1 || {
    cat /tmp/worktree-bootstrap-build.log >&2
    err "extension build:worktree failed"
    exit 1
  }
)

WORKTREE_EXTENSION_DIR="${EXTENSION_DIR}/.local/worktrees/${WORKTREE_ID}/chrome"
CANONICAL_RUNTIME="${EXTENSION_DIR}/.local/worktree-runtime-${WORKTREE_ID}.json"

[[ -d "${WORKTREE_EXTENSION_DIR}" ]] || {
  err "missing generated extension directory: ${WORKTREE_EXTENSION_DIR}"
  exit 1
}

[[ -f "${CANONICAL_RUNTIME}" ]] || {
  err "missing canonical runtime metadata: ${CANONICAL_RUNTIME}"
  exit 1
}

if [[ -f "${WORKTREE_EXTENSION_DIR}/manifest.json" ]]; then
  # Ensure extension host permissions match the resolved backend origin.
  if ! grep -q "${BACKEND_BASE_URL}/\\*" "${WORKTREE_EXTENSION_DIR}/manifest.json"; then
    err "manifest host_permissions do not include ${BACKEND_BASE_URL}/*"
    exit 1
  fi
else
  err "missing generated manifest: ${WORKTREE_EXTENSION_DIR}/manifest.json"
  exit 1
fi

if [[ -f "${WORKTREE_EXTENSION_DIR}/runtime-config.js" ]]; then
  # Ensure runtime config points to the same backend origin used for permissions.
  if ! grep -q "${BACKEND_BASE_URL}" "${WORKTREE_EXTENSION_DIR}/runtime-config.js"; then
    err "runtime-config.js does not include backend base URL ${BACKEND_BASE_URL}"
    exit 1
  fi
else
  err "missing generated runtime-config.js: ${WORKTREE_EXTENSION_DIR}/runtime-config.js"
  exit 1
fi

if command -v lsof >/dev/null 2>&1; then
  if lsof -nP -iTCP:"${BACKEND_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    info "backend health check: listening on port ${BACKEND_PORT}"
  else
    warn "backend health check: no process listening on ${BACKEND_PORT}; run backend/scripts/bootsrap.sh to start Django"
  fi
else
  warn "lsof not found; skipped backend listening-port health check"
fi

printf '\n'
info "runtime bootstrap complete"
echo "worktree_id=${WORKTREE_ID}"
echo "backend_host=${BACKEND_HOST}"
echo "backend_port=${BACKEND_PORT}"
echo "backend_base_url=${BACKEND_BASE_URL}"
echo "database_url=${DATABASE_URL}"
echo "env_file=${ENV_FILE}"
echo "extension_dir=${WORKTREE_EXTENSION_DIR}"
echo "runtime_metadata_canonical=${CANONICAL_RUNTIME}"
