#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BOOTSTRAP_SCRIPT="${SCRIPT_DIR}/bootsrap.sh"

list_worktree_runserver_pids() {
  ps -axo pid=,command= | grep -E 'manage.py runserver|scripts/bootsrap.sh --no-reload' | grep -v grep | while read -r pid rest; do
    local cwd
    cwd="$(lsof -a -p "${pid}" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"
    if [[ "${cwd}" == "${BACKEND_DIR}" && "${pid}" != "$$" ]]; then
      printf '%s\n' "${pid}"
    fi
  done
}

if [[ ! -x "${BOOTSTRAP_SCRIPT}" ]]; then
  echo "[backend-start] error: missing executable ${BOOTSTRAP_SCRIPT}" >&2
  exit 1
fi

existing_pids="$(list_worktree_runserver_pids)"
if [[ -n "${existing_pids}" ]]; then
  echo "[backend-start] error: backend server is already running for this worktree (pid(s): ${existing_pids//$'\n'/, })" >&2
  echo "[backend-start] hint: use ./scripts/stop-server.sh before starting again." >&2
  exit 1
fi

cd "${BACKEND_DIR}"
exec "${BOOTSTRAP_SCRIPT}" --no-reload "$@"
