#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
find_worktree_runserver() {
  ps -axo pid=,command= | awk '/manage.py runserver/ { pid=$1; $1=""; sub(/^ /, ""); print pid "|" $0 }' | while IFS='|' read -r pid command; do
    local cwd
    cwd="$(lsof -a -p "${pid}" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"
    if [[ "${cwd}" == "${BACKEND_DIR}" ]]; then
      printf '%s|%s\n' "${pid}" "${command}"
    fi
  done
}

running="$(find_worktree_runserver)"
if [[ -z "${running}" ]]; then
  echo "[backend-check] no backend server is running for this worktree."
  exit 1
fi

first_line="$(printf '%s\n' "${running}" | head -n 1)"
pid="${first_line%%|*}"
command="${first_line#*|}"
port="$(printf '%s\n' "${command}" | sed -n 's/.*runserver [^:]*:\([0-9][0-9]*\).*/\1/p')"

if [[ -z "${port}" ]]; then
  echo "[backend-check] error: could not determine listening port for pid ${pid}." >&2
  exit 1
fi

echo "[backend-check] backend server is already listening at http://127.0.0.1:${port}/clips/"
