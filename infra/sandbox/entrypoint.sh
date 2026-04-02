#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Bootstrap an idempotent sandbox runtime with SSH, PostgreSQL, shell
# environment persistence, GitHub CLI auth, and a first-boot repository clone.
# Preconditions: The sandbox image already provides the required system tools,
# the `agent` and `postgres` users, and writable persistent volumes.
# Invariants: Re-running this entrypoint must preserve existing home/workspace/
# database state and only create missing resources.
# Outcomes: The container exposes a ready SSH surface for the `agent` user and a
# local PostgreSQL-backed workspace clone at `${SANDBOX_WORKSPACE}`.
#

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  COLOR_INFO=$'\033[0;32m'
  COLOR_WARN=$'\033[0;33m'
  COLOR_ERROR=$'\033[0;31m'
  COLOR_RESET=$'\033[0m'
else
  COLOR_INFO=""
  COLOR_WARN=""
  COLOR_ERROR=""
  COLOR_RESET=""
fi

info() {
  printf '%b\n' "${COLOR_INFO}[sandbox] ${*}${COLOR_RESET}"
}

warn() {
  printf '%b\n' "${COLOR_WARN}[sandbox] warning: ${*}${COLOR_RESET}"
}

error() {
  printf '%b\n' "${COLOR_ERROR}[sandbox] error: ${*}${COLOR_RESET}" >&2
}

require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    error "required command not found: ${command_name}"
    exit 1
  fi
}

shell_quote() {
  printf '%q' "${1}"
}

detect_pg_bin_dir() {
  local candidate
  for candidate in /usr/lib/postgresql/*/bin; do
    if [[ -x "${candidate}/initdb" && -x "${candidate}/pg_ctl" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

resolve_repo_clone_url() {
  if [[ -z "${GH_TOKEN:-}" ]]; then
    printf '%s\n' "${SANDBOX_REPO_URL}"
    return 0
  fi

  if [[ "${SANDBOX_REPO_URL}" =~ ^https://github\.com/(.+)$ ]]; then
    printf 'https://x-access-token:%s@github.com/%s\n' "${GH_TOKEN}" "${BASH_REMATCH[1]}"
    return 0
  fi

  printf '%s\n' "${SANDBOX_REPO_URL}"
}

configure_local_repo_access() {
  local repo_path=""

  if [[ "${SANDBOX_REPO_URL}" =~ ^file://(.+)$ ]]; then
    repo_path="${BASH_REMATCH[1]}"
  elif [[ "${SANDBOX_REPO_URL}" = /* ]]; then
    repo_path="${SANDBOX_REPO_URL}"
  fi

  if [[ -z "${repo_path}" ]]; then
    return 0
  fi

  sudo -H -u agent env HOME="${SANDBOX_HOME}" git config --global --add safe.directory "${repo_path}"
}

require_command ssh-keygen
require_command psql
require_command pg_isready
require_command git
require_command sudo

SANDBOX_HOME="${SANDBOX_HOME:-/home/agent}"
SANDBOX_WORKSPACE="${SANDBOX_WORKSPACE:-/workspace/webclippings}"
SANDBOX_REPO_URL="${SANDBOX_REPO_URL:-https://github.com/laskaridis/clippy.git}"
SANDBOX_REPO_BRANCH="${SANDBOX_REPO_BRANCH:-}"
SANDBOX_EXPORT_DIR="${SANDBOX_EXPORT_DIR:-/exports/extension}"
SANDBOX_SSH_PORT="${SANDBOX_SSH_PORT:-22}"
SANDBOX_WEB_PORT="${SANDBOX_WEB_PORT:-8000}"
SANDBOX_POSTGRES_DATA="${SANDBOX_POSTGRES_DATA:-/var/lib/postgresql/data}"
SANDBOX_POSTGRES_LOG="${SANDBOX_POSTGRES_LOG:-/var/log/postgresql/sandbox.log}"
SANDBOX_POSTGRES_PORT="${SANDBOX_POSTGRES_PORT:-5432}"
SANDBOX_DB_NAME="${SANDBOX_DB_NAME:-webclippings}"
SANDBOX_DB_USER="${SANDBOX_DB_USER:-agent}"
SANDBOX_DB_PASSWORD="${SANDBOX_DB_PASSWORD:-agent}"
SANDBOX_DB_HOST="${SANDBOX_DB_HOST:-127.0.0.1}"
SANDBOX_DB_SSLMODE="${SANDBOX_DB_SSLMODE:-disable}"
SANDBOX_RUNTIME_ENV_PATH="${SANDBOX_RUNTIME_ENV_PATH:-/etc/profile.d/10-sandbox-env.sh}"
SANDBOX_SSH_ENV_PATH="${SANDBOX_SSH_ENV_PATH:-${SANDBOX_HOME}/.ssh/environment}"
SANDBOX_AUTHORIZED_KEYS_PATH="${SANDBOX_AUTHORIZED_KEYS_PATH:-${SANDBOX_HOME}/.ssh/authorized_keys}"
SANDBOX_START_SSHD="${SANDBOX_START_SSHD:-1}"
SANDBOX_START_POSTGRES="${SANDBOX_START_POSTGRES:-1}"
SANDBOX_KEEPALIVE_CMD="${SANDBOX_KEEPALIVE_CMD:-}"
SANDBOX_POSTGRES_SUPERUSER="${SANDBOX_POSTGRES_SUPERUSER:-postgres}"
SANDBOX_SSH_PUBLIC_KEY="${SANDBOX_SSH_PUBLIC_KEY:-${SSH_PUBLIC_KEY:-}}"
SANDBOX_PUBLIC_WEB_HOST="${SANDBOX_PUBLIC_WEB_HOST:-localhost}"
SANDBOX_PUBLIC_BASE_URL="${SANDBOX_PUBLIC_BASE_URL:-http://${SANDBOX_PUBLIC_WEB_HOST}:${SANDBOX_WEB_PORT}}"

PG_BIN_DIR="$(detect_pg_bin_dir)" || {
  error "could not locate PostgreSQL binaries under /usr/lib/postgresql"
  exit 1
}

DATABASE_URL="postgresql://${SANDBOX_DB_USER}:${SANDBOX_DB_PASSWORD}@${SANDBOX_DB_HOST}:${SANDBOX_POSTGRES_PORT}/${SANDBOX_DB_NAME}?sslmode=${SANDBOX_DB_SSLMODE}"
export DATABASE_URL

WORKSPACE_ROOT="$(dirname "${SANDBOX_WORKSPACE}")"
WORKTREE_BASENAME="$(basename "${SANDBOX_WORKSPACE}")"
if command -v sha1sum >/dev/null 2>&1; then
  WORKTREE_HASH="$(printf '%s' "${SANDBOX_WORKSPACE}" | sha1sum | cut -c1-6)"
elif command -v shasum >/dev/null 2>&1; then
  WORKTREE_HASH="$(printf '%s' "${SANDBOX_WORKSPACE}" | shasum -a 1 | cut -c1-6)"
else
  error "neither sha1sum nor shasum is available"
  exit 1
fi
SANDBOX_WORKTREE_ID="${WORKTREE_BASENAME}-${WORKTREE_HASH}"
SANDBOX_EXTENSION_RUNTIME_DIR="${SANDBOX_WORKSPACE}/extension/.local/worktrees/${SANDBOX_WORKTREE_ID}/chrome"

mkdir -p /var/log/postgresql "${SANDBOX_HOME}/.ssh" "${WORKSPACE_ROOT}" "${SANDBOX_EXPORT_DIR}"
touch "${SANDBOX_POSTGRES_LOG}"
chown -R agent:agent "${SANDBOX_HOME}" "${WORKSPACE_ROOT}"
if ! chown -R agent:agent "${SANDBOX_EXPORT_DIR}" 2>/dev/null; then
  warn "could not change ownership for ${SANDBOX_EXPORT_DIR}; continuing with existing host mount permissions"
fi
chown postgres:postgres /var/log/postgresql "${SANDBOX_POSTGRES_LOG}"
chmod 0700 "${SANDBOX_HOME}/.ssh"

ensure_authorized_keys() {
  touch "${SANDBOX_AUTHORIZED_KEYS_PATH}"
  chown agent:agent "${SANDBOX_AUTHORIZED_KEYS_PATH}"
  chmod 0600 "${SANDBOX_AUTHORIZED_KEYS_PATH}"

  if [[ -z "${SANDBOX_SSH_PUBLIC_KEY}" ]]; then
    warn "SANDBOX_SSH_PUBLIC_KEY is unset; SSH access will require keys to be provisioned later"
    return 0
  fi

  if grep -Fqx "${SANDBOX_SSH_PUBLIC_KEY}" "${SANDBOX_AUTHORIZED_KEYS_PATH}"; then
    info "SSH public key already present for agent"
    return 0
  fi

  printf '%s\n' "${SANDBOX_SSH_PUBLIC_KEY}" >>"${SANDBOX_AUTHORIZED_KEYS_PATH}"
  info "installed SSH public key for agent"
}

persist_runtime_env() {
  local tmp_profile
  local tmp_ssh

  tmp_profile="$(mktemp)"
  tmp_ssh="$(mktemp)"

  cat >"${tmp_profile}" <<EOF
#!/usr/bin/env bash
export DATABASE_URL=$(shell_quote "${DATABASE_URL}")
export SANDBOX_HOME=$(shell_quote "${SANDBOX_HOME}")
export SANDBOX_WORKSPACE=$(shell_quote "${SANDBOX_WORKSPACE}")
export SANDBOX_EXPORT_DIR=$(shell_quote "${SANDBOX_EXPORT_DIR}")
export SANDBOX_WORKTREE_ID=$(shell_quote "${SANDBOX_WORKTREE_ID}")
export SANDBOX_EXTENSION_RUNTIME_DIR=$(shell_quote "${SANDBOX_EXTENSION_RUNTIME_DIR}")
export DJANGO_DEV_PORT=$(shell_quote "${SANDBOX_WEB_PORT}")
export PORT=$(shell_quote "${SANDBOX_WEB_PORT}")
export DJANGO_DEV_HOST=$(shell_quote "${SANDBOX_PUBLIC_WEB_HOST}")
export DJANGO_DEV_BASE_URL=$(shell_quote "${SANDBOX_PUBLIC_BASE_URL}")
export ALLOWED_HOSTS=$(shell_quote "${SANDBOX_PUBLIC_WEB_HOST},localhost,127.0.0.1,[::1]")
EOF

  cat >"${tmp_ssh}" <<EOF
DATABASE_URL=${DATABASE_URL}
SANDBOX_HOME=${SANDBOX_HOME}
SANDBOX_WORKSPACE=${SANDBOX_WORKSPACE}
SANDBOX_EXPORT_DIR=${SANDBOX_EXPORT_DIR}
SANDBOX_WORKTREE_ID=${SANDBOX_WORKTREE_ID}
SANDBOX_EXTENSION_RUNTIME_DIR=${SANDBOX_EXTENSION_RUNTIME_DIR}
DJANGO_DEV_PORT=${SANDBOX_WEB_PORT}
PORT=${SANDBOX_WEB_PORT}
DJANGO_DEV_HOST=${SANDBOX_PUBLIC_WEB_HOST}
DJANGO_DEV_BASE_URL=${SANDBOX_PUBLIC_BASE_URL}
ALLOWED_HOSTS=${SANDBOX_PUBLIC_WEB_HOST},localhost,127.0.0.1,[::1]
EOF

  local env_name
  for env_name in OPENAI_API_KEY OPENAI_BASE_URL OPENAI_ORG_ID OPENAI_PROJECT_ID; do
    if [[ -n "${!env_name:-}" ]]; then
      printf 'export %s=%s\n' "${env_name}" "$(shell_quote "${!env_name}")" >>"${tmp_profile}"
      printf '%s=%s\n' "${env_name}" "${!env_name}" >>"${tmp_ssh}"
    fi
  done

  install -m 0644 "${tmp_profile}" "${SANDBOX_RUNTIME_ENV_PATH}"
  install -m 0600 "${tmp_ssh}" "${SANDBOX_SSH_ENV_PATH}"
  chown agent:agent "${SANDBOX_SSH_ENV_PATH}"
  rm -f "${tmp_profile}" "${tmp_ssh}"
  info "persisted sandbox runtime environment"
}

ensure_postgres_initialized() {
  mkdir -p "${SANDBOX_POSTGRES_DATA}"
  chown -R postgres:postgres "${SANDBOX_POSTGRES_DATA}"
  chmod 0700 "${SANDBOX_POSTGRES_DATA}"

  if [[ -f "${SANDBOX_POSTGRES_DATA}/PG_VERSION" ]]; then
    info "reusing existing PostgreSQL data directory"
    return 0
  fi

  info "initializing PostgreSQL data directory"
  sudo -u postgres "${PG_BIN_DIR}/initdb" \
    --pgdata="${SANDBOX_POSTGRES_DATA}" \
    --username="${SANDBOX_POSTGRES_SUPERUSER}" \
    --auth-local=trust \
    --auth-host=scram-sha-256 >/dev/null
}

postgres_ready() {
  pg_isready -h "${SANDBOX_DB_HOST}" -p "${SANDBOX_POSTGRES_PORT}" -U "${SANDBOX_POSTGRES_SUPERUSER}" >/dev/null 2>&1
}

start_postgres() {
  if [[ "${SANDBOX_START_POSTGRES}" != "1" ]]; then
    warn "SANDBOX_START_POSTGRES=${SANDBOX_START_POSTGRES}; skipping PostgreSQL startup"
    return 0
  fi

  ensure_postgres_initialized

  if postgres_ready; then
    info "PostgreSQL already accepting connections on ${SANDBOX_DB_HOST}:${SANDBOX_POSTGRES_PORT}"
    return 0
  fi

  if sudo -u postgres "${PG_BIN_DIR}/pg_ctl" -D "${SANDBOX_POSTGRES_DATA}" status >/dev/null 2>&1; then
    info "PostgreSQL process already running; waiting for readiness"
  else
    info "starting PostgreSQL on ${SANDBOX_DB_HOST}:${SANDBOX_POSTGRES_PORT}"
    sudo -u postgres "${PG_BIN_DIR}/pg_ctl" \
      -D "${SANDBOX_POSTGRES_DATA}" \
      -l "${SANDBOX_POSTGRES_LOG}" \
      -o "-c listen_addresses=${SANDBOX_DB_HOST} -c port=${SANDBOX_POSTGRES_PORT}" \
      start >/dev/null
  fi

  local attempt
  for attempt in $(seq 1 30); do
    if postgres_ready; then
      info "PostgreSQL is ready"
      return 0
    fi
    sleep 1
  done

  error "PostgreSQL failed to become ready; see ${SANDBOX_POSTGRES_LOG}"
  tail -n 100 "${SANDBOX_POSTGRES_LOG}" >&2 || true
  exit 1
}

configure_database() {
  if [[ "${SANDBOX_START_POSTGRES}" != "1" ]]; then
    return 0
  fi

  info "ensuring PostgreSQL role ${SANDBOX_DB_USER} exists"
  sudo -u postgres psql \
    --dbname=postgres \
    --set=ON_ERROR_STOP=1 \
    --set=app_user="${SANDBOX_DB_USER}" \
    --set=app_password="${SANDBOX_DB_PASSWORD}" \
    <<'SQL' >/dev/null
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'app_user', :'app_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = :'app_user')
\gexec
SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'app_user', :'app_password')
\gexec
SQL

  if [[ "$(sudo -u postgres psql --dbname=postgres --tuples-only --no-align --set=ON_ERROR_STOP=1 --command="SELECT 1 FROM pg_database WHERE datname = '${SANDBOX_DB_NAME}'")" != "1" ]]; then
    info "creating PostgreSQL database ${SANDBOX_DB_NAME}"
    sudo -u postgres createdb \
      --owner="${SANDBOX_DB_USER}" \
      "${SANDBOX_DB_NAME}"
  else
    info "reusing existing PostgreSQL database ${SANDBOX_DB_NAME}"
  fi
}

sync_extension_export_once() {
  if [[ ! -d "${SANDBOX_EXTENSION_RUNTIME_DIR}" ]]; then
    return 0
  fi

  mkdir -p "${SANDBOX_EXPORT_DIR}"
  find "${SANDBOX_EXPORT_DIR}" -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
  cp -a "${SANDBOX_EXTENSION_RUNTIME_DIR}/." "${SANDBOX_EXPORT_DIR}/"
}

start_extension_export_sync() {
  info "watching ${SANDBOX_EXTENSION_RUNTIME_DIR} for host extension export sync"
  (
    while true; do
      if ! sync_extension_export_once; then
        warn "extension export sync failed; retrying"
      fi
      sleep 2
    done
  ) &
  EXTENSION_SYNC_PID=$!
}

configure_gh_auth() {
  if [[ -z "${GH_TOKEN:-}" ]]; then
    warn "GH_TOKEN is unset; skipping gh authentication"
    return 0
  fi

  if sudo -H -u agent env HOME="${SANDBOX_HOME}" gh auth status >/dev/null 2>&1; then
    info "gh auth already configured for agent"
    return 0
  fi

  info "configuring gh auth for agent"
  printf '%s' "${GH_TOKEN}" | sudo -H -u agent env HOME="${SANDBOX_HOME}" gh auth login --hostname github.com --with-token >/dev/null
  sudo -H -u agent env HOME="${SANDBOX_HOME}" gh auth setup-git >/dev/null
}

ensure_workspace_clone() {
  if [[ -d "${SANDBOX_WORKSPACE}/.git" ]]; then
    info "reusing existing workspace clone at ${SANDBOX_WORKSPACE}"
    return 0
  fi

  if [[ -e "${SANDBOX_WORKSPACE}" && -n "$(find "${SANDBOX_WORKSPACE}" -mindepth 1 -maxdepth 1 2>/dev/null)" ]]; then
    error "workspace path ${SANDBOX_WORKSPACE} exists but is not a git clone"
    exit 1
  fi

  rm -rf "${SANDBOX_WORKSPACE}"

  local clone_url
  clone_url="$(resolve_repo_clone_url)"
  configure_local_repo_access
  info "cloning repository into ${SANDBOX_WORKSPACE}"
  sudo -H -u agent env HOME="${SANDBOX_HOME}" git clone "${clone_url}" "${SANDBOX_WORKSPACE}" >/dev/null

  if [[ -n "${SANDBOX_REPO_BRANCH}" ]]; then
    info "checking out ${SANDBOX_REPO_BRANCH} in sandbox workspace"
    sudo -H -u agent env HOME="${SANDBOX_HOME}" git -C "${SANDBOX_WORKSPACE}" checkout "${SANDBOX_REPO_BRANCH}" >/dev/null
  fi
}

start_sshd() {
  if [[ "${SANDBOX_START_SSHD}" != "1" ]]; then
    warn "SANDBOX_START_SSHD=${SANDBOX_START_SSHD}; skipping sshd startup"
    return 0
  fi

  ssh-keygen -A >/dev/null
  info "starting sshd on port ${SANDBOX_SSH_PORT}"
  /usr/sbin/sshd -D -e -p "${SANDBOX_SSH_PORT}" &
  SSHD_PID=$!
}

stop_postgres() {
  if [[ "${SANDBOX_START_POSTGRES}" != "1" ]]; then
    return 0
  fi

  if sudo -u postgres "${PG_BIN_DIR}/pg_ctl" -D "${SANDBOX_POSTGRES_DATA}" status >/dev/null 2>&1; then
    info "stopping PostgreSQL"
    sudo -u postgres "${PG_BIN_DIR}/pg_ctl" -D "${SANDBOX_POSTGRES_DATA}" stop -m fast >/dev/null || warn "PostgreSQL shutdown reported an error"
  fi
}

cleanup() {
  local exit_code=$?

  if [[ -n "${EXTENSION_SYNC_PID:-}" ]] && kill -0 "${EXTENSION_SYNC_PID}" >/dev/null 2>&1; then
    kill "${EXTENSION_SYNC_PID}" >/dev/null 2>&1 || true
    wait "${EXTENSION_SYNC_PID}" || true
  fi

  if [[ -n "${SSHD_PID:-}" ]] && kill -0 "${SSHD_PID}" >/dev/null 2>&1; then
    kill "${SSHD_PID}" >/dev/null 2>&1 || true
    wait "${SSHD_PID}" || true
  fi

  stop_postgres
  exit "${exit_code}"
}

trap cleanup EXIT INT TERM

ensure_authorized_keys
persist_runtime_env
start_postgres
configure_database
configure_gh_auth
ensure_workspace_clone
start_extension_export_sync
start_sshd

if [[ -n "${SANDBOX_KEEPALIVE_CMD}" ]]; then
  info "running keepalive command"
  bash -lc "${SANDBOX_KEEPALIVE_CMD}" &
  KEEPALIVE_PID=$!
  wait "${KEEPALIVE_PID}"
else
  if [[ -n "${SSHD_PID:-}" ]]; then
    wait "${SSHD_PID}"
  else
    info "sandbox bootstrap complete; keeping container alive"
    tail -f /dev/null &
    KEEPALIVE_PID=$!
    wait "${KEEPALIVE_PID}"
  fi
fi
