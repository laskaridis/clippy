#!/usr/bin/env bash

set -euo pipefail

quote_env_value() {
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
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

sandbox_repo_url="$(git remote get-url origin 2>/dev/null || true)"
if [[ -z "${sandbox_repo_url}" ]]; then
  printf 'Refusing to generate .devcontainer/.env because the host checkout has no usable origin remote.\n' >&2
  exit 1
fi

cp .devcontainer/.env.example .devcontainer/.env
{
  printf '\nSANDBOX_REPO_URL=%s\n' "$(quote_env_value "${sandbox_repo_url}")"
  printf 'GIT_AUTH_TOKEN=%s\n' "$(quote_env_value "${GIT_AUTH_TOKEN}")"
  printf 'SANDBOX_ID=%s\n' "$(quote_env_value "${SANDBOX_ID}")"
  printf 'COMPOSE_PROJECT_NAME=%s\n' "$(quote_env_value "${SANDBOX_ID}")"
} >> .devcontainer/.env
