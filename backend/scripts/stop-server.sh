#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

list_worktree_runserver_pids() {
  ps -axo pid=,command= | grep -E 'manage.py runserver|scripts/bootsrap.sh --no-reload' | grep -v grep | while read -r pid rest; do
    local cwd
    cwd="$(lsof -a -p "${pid}" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"
    if [[ "${cwd}" == "${BACKEND_DIR}" && "${pid}" != "$$" ]]; then
      printf '%s\n' "${pid}"
    fi
  done
}

pids="$(list_worktree_runserver_pids)"
if [[ -z "${pids}" ]]; then
  echo "[backend-stop] error: no backend server is running for this worktree." >&2
  exit 1
fi

for pid in ${pids}; do
  kill "${pid}"
done

sleep 1
remaining_pids="$(list_worktree_runserver_pids)"
if [[ -n "${remaining_pids}" ]]; then
  echo "[backend-stop] error: failed to stop backend server pid(s): ${remaining_pids//$'\n'/, }" >&2
  exit 1
fi

echo "[backend-stop] backend server stopped for this worktree."
