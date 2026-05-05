#!/usr/bin/env bash

set -euo pipefail

quote_env_value() {
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

normalize_repo_url() {
  local repo_url="$1"

  case "${repo_url}" in
    git@*:* )
      local host="${repo_url#git@}"
      host="${host%%:*}"
      local path="${repo_url#*:}"
      printf 'https://%s/%s\n' "${host}" "${path}"
      ;;
    ssh://git@*/* )
      local without_scheme="${repo_url#ssh://git@}"
      local host="${without_scheme%%/*}"
      local path="${without_scheme#*/}"
      printf 'https://%s/%s\n' "${host}" "${path}"
      ;;
    * )
      printf '%s\n' "${repo_url}"
      ;;
  esac
}

resolve_sandbox_repo_url() {
  local configured_repo_url="${SANDBOX_REPO_URL:-}"
  if [[ -n "${configured_repo_url}" ]]; then
    normalize_repo_url "${configured_repo_url}"
    return
  fi

  configured_repo_url="$(git remote get-url origin 2>/dev/null || true)"
  if [[ -z "${configured_repo_url}" ]]; then
    printf 'Refusing to generate .devcontainer/.env because the host checkout has no usable origin remote and SANDBOX_REPO_URL is not set.\n' >&2
    exit 1
  fi

  normalize_repo_url "${configured_repo_url}"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"
cd "${repo_root}"

if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  printf 'Refusing to generate .devcontainer/.env because the host tree is not clean.\n' >&2
  exit 1
fi

missing_vars=()
for var_name in GIT_AUTH_TOKEN SANDBOX_ID; do
  if [[ -z "${!var_name:-}" ]]; then
    missing_vars+=("${var_name}")
  fi
done

if (( ${#missing_vars[@]} > 0 )); then
  printf 'Missing required sandbox input(s): %s\n' "${missing_vars[*]}" >&2
  exit 1
fi

sandbox_repo_url="$(resolve_sandbox_repo_url)"

cp .devcontainer/.env.example .devcontainer/.env
{
  printf '\nSANDBOX_REPO_URL=%s\n' "$(quote_env_value "${sandbox_repo_url}")"
  printf 'GIT_AUTH_TOKEN=%s\n' "$(quote_env_value "${GIT_AUTH_TOKEN}")"
  printf 'SANDBOX_ID=%s\n' "$(quote_env_value "${SANDBOX_ID}")"
  printf 'COMPOSE_PROJECT_NAME=%s\n' "$(quote_env_value "${SANDBOX_ID}")"
} >> .devcontainer/.env
