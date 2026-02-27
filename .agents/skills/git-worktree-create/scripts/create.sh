#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  create.sh --branch <branch-name> [--dry-run]

Create or reuse a git worktree for an existing branch under:
  <project-root>/.worktrees/<derived-name>

Options:
  --branch <name>  Existing branch to use (required)
  --dry-run        Print planned actions without creating anything
  -h, --help       Show this help
USAGE
}

BRANCH=""
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch)
      BRANCH="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unexpected argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${BRANCH}" ]]; then
  echo "--branch is required" >&2
  usage >&2
  exit 1
fi

if [[ "${BRANCH}" == "master" ]]; then
  echo "Refusing to create a worktree for 'master'" >&2
  exit 1
fi

COMMON_DIR="$(git rev-parse --git-common-dir)"
PROJECT_ROOT="$(cd "${COMMON_DIR}/.." && pwd -P)"
WORKTREES_DIR="${PROJECT_ROOT}/.worktrees"

# Create the .worktrees directory if it doesn't exist (except in dry-run mode)
if [[ ! -d "${WORKTREES_DIR}" && "${DRY_RUN}" -eq 0 ]]; then
  mkdir -p "${WORKTREES_DIR}"
fi

# Convert a user-supplied branch name into a stable directory segment for
# <project-root>/.worktrees/<derived-name>:
# - lowercase everything
# - replace any non [a-z0-9._-] run with "-"
# - collapse repeated "-" and trim leading/trailing "-" or "."
# Return "invalid" when normalization would produce an empty name.
# Example: "Feature/Issue-123 Fix Auth" -> "feature-issue-123-fix-auth"
derive_worktree_name() {
  local raw="$1"
  local normalized
  normalized="$(printf '%s' "${raw}" | tr '[:upper:]' '[:lower:]' | sed -E 's#[^a-z0-9._-]+#-#g; s#-+#-#g; s#(^[-.]+|[-.]+$)##g')"
  if [[ -z "${normalized}" ]]; then
    echo "invalid"
  else
    echo "${normalized}"
  fi
}

# Create the worktree name and path based on the branch:
WORKTREE_NAME="$(derive_worktree_name "${BRANCH}")"
if [[ "${WORKTREE_NAME}" == "invalid" ]]; then
  echo "Unable to derive a valid worktree directory name from branch: ${BRANCH}" >&2
  exit 1
fi
TARGET_WORKTREE_PATH="${WORKTREES_DIR}/${WORKTREE_NAME}"

if [[ "${DRY_RUN}" -eq 0 ]]; then
  git fetch origin
fi

# Determine if the branch exists locally or only on origin.
# This affects the git worktree add command later:
# We check for the local ref first to preserve local branch
# intent (e.g. including unpushed commits):
determine_branch_source() {
  local local_ref="refs/heads/$1"
  local remote_ref="refs/remotes/origin/$1"
  if git show-ref --verify --quiet "${local_ref}"; then
    echo "local"
  elif git show-ref --verify --quiet "${remote_ref}"; then
    echo "remote"
  fi
}
SOURCE_KIND="$(determine_branch_source "${BRANCH}")"
if [[ -z "${SOURCE_KIND}" ]]; then
  echo "Branch does not exist locally or on origin: ${BRANCH}" >&2
  exit 1
fi

# Check if target path exists and is already a worktree for the same branch:
if [[ -d "${TARGET_WORKTREE_PATH}" ]]; then
  if [[ -d "${TARGET_WORKTREE_PATH}/.git" || -f "${TARGET_WORKTREE_PATH}/.git" ]]; then
    existing_common_dir="$(git -C "${TARGET_WORKTREE_PATH}" rev-parse --git-common-dir 2>/dev/null || true)"
    if [[ -z "${existing_common_dir}" ]]; then
      echo "Target path exists but is not a valid git worktree: ${TARGET_WORKTREE_PATH}" >&2
      exit 1
    fi
    if [[ "${existing_common_dir}" != "${COMMON_DIR}" ]]; then
      echo "Target path points to a different repository: ${TARGET_WORKTREE_PATH}" >&2
      exit 1
    fi
    existing_branch="$(git -C "${TARGET_WORKTREE_PATH}" branch --show-current 2>/dev/null || true)"
    if [[ "${existing_branch}" == "${BRANCH}" ]]; then
      echo "status=reused"
      echo "project_root=${PROJECT_ROOT}"
      echo "worktree_path=${TARGET_WORKTREE_PATH}"
      echo "branch=${BRANCH}"
      echo "source_kind=${SOURCE_KIND}"
      exit 0
    fi
    echo "Target path exists with a different branch (${existing_branch}): ${TARGET_WORKTREE_PATH}" >&2
    exit 1
  fi
  echo "Target path exists and is not a git worktree: ${TARGET_WORKTREE_PATH}" >&2
  exit 1
fi

if [[ "${SOURCE_KIND}" == "local" ]]; then
  ADD_CMD=(git worktree add "${TARGET_WORKTREE_PATH}" "${BRANCH}")
else
  # Branch is not available locally so we need to track it
  ADD_CMD=(git worktree add --track -b "${BRANCH}" "${TARGET_WORKTREE_PATH}" "origin/${BRANCH}")
fi

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "status=dry-run"
  echo "project_root=${PROJECT_ROOT}"
  echo "worktree_path=${TARGET_WORKTREE_PATH}"
  echo "branch=${BRANCH}"
  echo "source_kind=${SOURCE_KIND}"
  printf 'command='
  printf '%q ' "${ADD_CMD[@]}"
  printf '\n'
  exit 0
fi

"${ADD_CMD[@]}"

echo "status=created"
echo "project_root=${PROJECT_ROOT}"
echo "worktree_path=${TARGET_WORKTREE_PATH}"
echo "branch=${BRANCH}"
echo "source_kind=${SOURCE_KIND}"
