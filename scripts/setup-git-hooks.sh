#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Configure repository git hooks and workflow helper executability.
# Preconditions: Run inside repository root with writable git config and hooks files.
# Invariants: Sets core.hooksPath to .githooks and enforces executable hook/helper scripts.
# Outcomes: Leaves local clone ready to enforce workflow preflight checks on commit.
# Artifacts:
# - `git config core.hooksPath=.githooks` — persists repository-local hook path so git executes project hooks.
# - Executable bit updates on `.githooks/*`, `scripts/agent-preflight.sh`, `scripts/start-task.sh` — ensures hook/helper scripts can run.
#

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
