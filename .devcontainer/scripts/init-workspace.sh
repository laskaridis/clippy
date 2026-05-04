#!/usr/bin/env bash

set -euo pipefail

workspace_dir=/workspace
workspace_git_dir="${workspace_dir}/.git"
metadata_file="${workspace_git_dir}/devcontainer-sandbox.env"
askpass_script=/usr/local/bin/devcontainer-git-askpass.sh

require_input() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    printf 'Missing required sandbox input: %s\n' "${name}" >&2
    exit 1
  fi
}

require_input SANDBOX_REPO_URL
require_input GIT_AUTH_TOKEN
require_input SANDBOX_ID

git_with_auth() {
  GIT_TERMINAL_PROMPT=0 GIT_ASKPASS="${askpass_script}" git "$@"
}

write_metadata() {
  mkdir -p "${workspace_git_dir}"
  {
    printf 'SANDBOX_ID=%s\n' "${SANDBOX_ID}"
    printf 'SANDBOX_REPO_URL=%s\n' "${SANDBOX_REPO_URL}"
  } > "${metadata_file}"
}

read_metadata_value() {
  local key="$1"
  local value=""
  if [[ -f "${metadata_file}" ]]; then
    value="$(sed -n "s/^${key}=//p" "${metadata_file}" | tail -n 1)"
  fi
  printf '%s' "${value}"
}

ensure_metadata_matches() {
  if [[ ! -f "${metadata_file}" ]]; then
    write_metadata
    return
  fi

  local recorded_id recorded_repo recorded_origin
  recorded_id="$(read_metadata_value SANDBOX_ID)"
  recorded_repo="$(read_metadata_value SANDBOX_REPO_URL)"
  recorded_origin="$(git -C "${workspace_dir}" remote get-url origin)"

  if [[ "${recorded_id}" != "${SANDBOX_ID}" || "${recorded_repo}" != "${SANDBOX_REPO_URL}" || "${recorded_origin}" != "${SANDBOX_REPO_URL}" ]]; then
    printf 'Workspace metadata does not match the requested sandbox.\n' >&2
    printf 'Recorded SANDBOX_ID=%s, SANDBOX_REPO_URL=%s, origin=%s\n' "${recorded_id}" "${recorded_repo}" "${recorded_origin}" >&2
    printf 'Requested SANDBOX_ID=%s, SANDBOX_REPO_URL=%s\n' "${SANDBOX_ID}" "${SANDBOX_REPO_URL}" >&2
    exit 1
  fi
}

if [[ ! -d "${workspace_git_dir}" ]]; then
  mkdir -p "${workspace_dir}"
  git_with_auth clone "${SANDBOX_REPO_URL}" "${workspace_dir}"
  git -C "${workspace_dir}" checkout -B master origin/master
  git -C "${workspace_dir}" branch --set-upstream-to=origin/master master
  write_metadata
else
  ensure_metadata_matches
fi
