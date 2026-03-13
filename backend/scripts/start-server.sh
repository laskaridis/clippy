#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Start exactly one backend server instance for the current worktree.
# Preconditions: bootsrap.sh, process tools, and writable backend/.local directory are required.
# Invariants: Serializes starts with a worktree lock, validates existing PID/process state, and writes PID atomically.
# Outcomes: Launches Django runserver through bootsrap.sh with worktree-scoped lifecycle metadata.
# Artifacts:
# - `backend/.local/backend-<worktree-id>.pid` (fallback `backend.pid`) — PID artifact for worktree server ownership.
# - `backend/.local/backend-<worktree-id>.lock` (fallback `.lock.d`) — startup coordination lock to serialize lifecycle mutations.
# - `<pid>.tmp.$$` transient file — atomic PID write staging file that is moved into place.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BOOTSTRAP_SCRIPT="${SCRIPT_DIR}/bootsrap.sh"
PID_DIR="${BACKEND_DIR}/.local"
LOCK_TIMEOUT_SECONDS="${BACKEND_SERVER_LOCK_TIMEOUT_SECONDS:-30}"
LOCK_HELD=0

resolve_pid_file() {
  local env_path env_name worktree_id
  mkdir -p "${PID_DIR}"

  if [[ -x "${BOOTSTRAP_SCRIPT}" ]] && env_path="$("${BOOTSTRAP_SCRIPT}" --print-env-path 2>/dev/null)"; then
    env_name="$(basename "${env_path}")"
    if [[ "${env_name}" == worktree-env-*.env ]]; then
      worktree_id="${env_name#worktree-env-}"
      worktree_id="${worktree_id%.env}"
      printf '%s/backend-%s.pid\n' "${PID_DIR}" "${worktree_id}"
      return 0
    fi
  fi

  printf '%s/backend.pid\n' "${PID_DIR}"
}

resolve_lock_file() {
  local pid_file="$1"
  printf '%s\n' "${pid_file%.pid}.lock"
}

acquire_worktree_lock() {
  local lock_file="$1"
  local elapsed=0

  if command -v flock >/dev/null 2>&1; then
    exec 9>"${lock_file}"
    if ! flock -w "${LOCK_TIMEOUT_SECONDS}" 9; then
      echo "[backend-start] error: timed out waiting for server lock ${lock_file}" >&2
      return 1
    fi
    LOCK_HELD=1
    return 0
  fi

  while ! mkdir "${lock_file}.d" 2>/dev/null; do
    if (( elapsed >= LOCK_TIMEOUT_SECONDS * 10 )); then
      echo "[backend-start] error: timed out waiting for server lock ${lock_file}.d" >&2
      return 1
    fi
    elapsed=$((elapsed + 1))
    sleep 0.1
  done
  LOCK_HELD=2
}

release_worktree_lock() {
  local lock_file="$1"
  if [[ "${LOCK_HELD}" == "1" ]]; then
    flock -u 9 || true
    exec 9>&- || true
  elif [[ "${LOCK_HELD}" == "2" ]]; then
    rmdir "${lock_file}.d" 2>/dev/null || true
  fi
  LOCK_HELD=0
}

is_expected_backend_pid() {
  local pid="$1"
  local command cwd
  command="$(ps -p "${pid}" -o command= 2>/dev/null || true)"
  cwd="$(lsof -a -p "${pid}" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p' || true)"

  [[ -n "${command}" ]] \
    && [[ "${cwd}" == "${BACKEND_DIR}" ]] \
    && [[ "${command}" =~ manage\.py[[:space:]]+runserver|scripts/bootsrap\.sh[[:space:]]+--no-reload ]]
}

list_worktree_runserver_pids() {
  ps -axo pid=,command= | awk '/manage.py runserver|scripts\/bootsrap.sh --no-reload/ { print $1 }' | while read -r pid; do
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

PID_FILE="$(resolve_pid_file)"
LOCK_FILE="$(resolve_lock_file "${PID_FILE}")"

tmp_pid_file=""
cleanup() {
  if [[ -n "${tmp_pid_file}" ]]; then
    rm -f "${tmp_pid_file}"
  fi
  release_worktree_lock "${LOCK_FILE}"
}
trap cleanup EXIT

acquire_worktree_lock "${LOCK_FILE}"

if [[ -f "${PID_FILE}" ]]; then
  recorded_pid="$(tr -d '[:space:]' < "${PID_FILE}")"
  if [[ -n "${recorded_pid}" ]] && kill -0 "${recorded_pid}" 2>/dev/null && is_expected_backend_pid "${recorded_pid}"; then
    echo "[backend-start] error: backend server is already running for this worktree (pid: ${recorded_pid})" >&2
    echo "[backend-start] hint: use ./scripts/stop-server.sh before starting again." >&2
    exit 1
  fi
  rm -f "${PID_FILE}"
fi

existing_pids="$(list_worktree_runserver_pids)"
if [[ -n "${existing_pids}" ]]; then
  echo "[backend-start] error: backend server is already running for this worktree (pid(s): ${existing_pids//$'\n'/, })" >&2
  echo "[backend-start] hint: use ./scripts/stop-server.sh before starting again." >&2
  exit 1
fi

tmp_pid_file="${PID_FILE}.tmp.$$"
printf '%s\n' "$$" > "${tmp_pid_file}"
mv "${tmp_pid_file}" "${PID_FILE}"
tmp_pid_file=""
release_worktree_lock "${LOCK_FILE}"
trap - EXIT
cd "${BACKEND_DIR}"
exec "${BOOTSTRAP_SCRIPT}" --no-reload "$@"
