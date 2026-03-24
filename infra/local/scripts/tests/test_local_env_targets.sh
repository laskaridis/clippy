#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Verify local-env Make targets and compose manager CLI contract.
# Preconditions: Run from repository root.
# Invariants: Tests are non-destructive and do not invoke Docker lifecycle commands.
# Outcomes: Fails fast when target wiring/help output regress.
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SCRIPT_PATH="${ROOT_DIR}/infra/local/scripts/manage-worktree-compose.sh"
MAKEFILE_PATH="${ROOT_DIR}/Makefile"

fail() {
  echo "[test-local-env-targets] error: $*" >&2
  exit 1
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local context="$3"
  if [[ "${haystack}" != *"${needle}"* ]]; then
    fail "${context}: expected to find '${needle}'"
  fi
}

if [[ ! -x "${SCRIPT_PATH}" ]]; then
  fail "expected executable script at ${SCRIPT_PATH}"
fi

if [[ ! -f "${MAKEFILE_PATH}" ]]; then
  fail "missing Makefile at ${MAKEFILE_PATH}"
fi

script_help="$("${SCRIPT_PATH}" --help)"
assert_contains "${script_help}" "Commands:" "script help output"
assert_contains "${script_help}" "start" "script help output"
assert_contains "${script_help}" "stop" "script help output"
assert_contains "${script_help}" "status" "script help output"
assert_contains "${script_help}" "teardown" "script help output"

set +e
invalid_output="$("${SCRIPT_PATH}" invalid 2>&1)"
invalid_exit=$?
set -e
if [[ ${invalid_exit} -eq 0 ]]; then
  fail "invalid command should fail"
fi
assert_contains "${invalid_output}" "unsupported command 'invalid'" "invalid command output"

make_help_output="$(cd "${ROOT_DIR}" && make help)"
assert_contains "${make_help_output}" "make local-env-start" "make help output"
assert_contains "${make_help_output}" "make local-env-stop" "make help output"
assert_contains "${make_help_output}" "make local-env-status" "make help output"
assert_contains "${make_help_output}" "make local-env-teardown" "make help output"

makefile_contents="$(cat "${MAKEFILE_PATH}")"
assert_contains "${makefile_contents}" "./infra/local/scripts/manage-worktree-compose.sh start" "Makefile wiring"
assert_contains "${makefile_contents}" "./infra/local/scripts/manage-worktree-compose.sh stop" "Makefile wiring"
assert_contains "${makefile_contents}" "./infra/local/scripts/manage-worktree-compose.sh status" "Makefile wiring"
assert_contains "${makefile_contents}" "./infra/local/scripts/manage-worktree-compose.sh teardown" "Makefile wiring"

echo "[test-local-env-targets] ok"
