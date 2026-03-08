#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="${ROOT_DIR}/.githooks"

if [[ ! -d "${HOOKS_DIR}" ]]; then
  echo "[setup-git-hooks] error: missing hooks directory at ${HOOKS_DIR}" >&2
  exit 1
fi

git -C "${ROOT_DIR}" config core.hooksPath .githooks
chmod +x "${HOOKS_DIR}/"*
if [[ -f "${ROOT_DIR}/scripts/agent-preflight.sh" ]]; then
  chmod +x "${ROOT_DIR}/scripts/agent-preflight.sh"
fi
if [[ -f "${ROOT_DIR}/scripts/start-task.sh" ]]; then
  chmod +x "${ROOT_DIR}/scripts/start-task.sh"
fi

echo "[setup-git-hooks] configured core.hooksPath=.githooks"
echo "[setup-git-hooks] installed hooks:"
ls -1 "${HOOKS_DIR}"
echo "[setup-git-hooks] workflow helpers:"
echo "  - scripts/agent-preflight.sh"
echo "  - scripts/start-task.sh"
