#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Report whether a backend server is running for the current worktree.
# Preconditions: Requires process inspection tools (ps/lsof) and access to backend .local metadata.
# Invariants: Uses worktree lock + PID validation first, then process scan fallback before reading listen port.
# Outcomes: Prints canonical server URL when running, otherwise exits non-zero with clear status.
# Artifacts:
# - Consumes/cleans `backend/.local/backend-<worktree-id>.pid` (fallback `backend.pid`) — validates or removes stale PID metadata.
# - Uses `backend/.local/backend-<worktree-id>.lock` (fallback `.lock.d`) — ensures consistent reads during concurrent lifecycle actions.
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
      echo "[backend-check] error: timed out waiting for server lock ${lock_file}" >&2
      return 1
    fi
    LOCK_HELD=1
    return 0
  fi

  while ! mkdir "${lock_file}.d" 2>/dev/null; do
    if (( elapsed >= LOCK_TIMEOUT_SECONDS * 10 )); then
      echo "[backend-check] error: timed out waiting for server lock ${lock_file}.d" >&2
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

resolve_listen_port_for_pid() {
  local pid="$1"
  lsof -a -nP -p "${pid}" -iTCP -sTCP:LISTEN 2>/dev/null \
    | awk 'NR>1 {print $9; exit}' \
    | sed -n 's/.*:\([0-9][0-9]*\)$/\1/p' \
    | head -n 1
}
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
PID_FILE="$(resolve_pid_file)"
LOCK_FILE="$(resolve_lock_file "${PID_FILE}")"

cleanup() {
  release_worktree_lock "${LOCK_FILE}"
}
trap cleanup EXIT
acquire_worktree_lock "${LOCK_FILE}"

if [[ -f "${PID_FILE}" ]]; then
  recorded_pid="$(tr -d '[:space:]' < "${PID_FILE}")"
  if [[ -n "${recorded_pid}" ]] && kill -0 "${recorded_pid}" 2>/dev/null && is_expected_backend_pid "${recorded_pid}"; then
    if ! printf '%s\n' "${running}" | grep -q "^${recorded_pid}|"; then
      recorded_command="$(ps -p "${recorded_pid}" -o command= 2>/dev/null || true)"
      running="$(printf '%s\n%s|%s\n' "${running}" "${recorded_pid}" "${recorded_command}" | awk 'NF && !seen[$0]++')"
    fi
  else
    rm -f "${PID_FILE}"
  fi
fi

if [[ -z "${running}" ]]; then
  echo "[backend-check] no backend server is running for this worktree."
  exit 1
fi

pid=""
port=""
while IFS='|' read -r candidate_pid _; do
  if [[ -z "${candidate_pid}" ]]; then
    continue
  fi
  candidate_port="$(resolve_listen_port_for_pid "${candidate_pid}")"
  if [[ -n "${candidate_port}" ]]; then
    pid="${candidate_pid}"
    port="${candidate_port}"
    break
  fi
done < <(printf '%s\n' "${running}")

if [[ -z "${port}" ]]; then
  echo "[backend-check] error: could not determine listening port for backend runserver process." >&2
  exit 1
fi

echo "[backend-check] backend server is already listening at http://127.0.0.1:${port}/clips/"
trap - EXIT
release_worktree_lock "${LOCK_FILE}"
