#!/usr/bin/env bash
set -euo pipefail

#
# Intent: Verify the Makefile help surface no longer advertises local-env targets.
# Preconditions: Run from repository root.
# Invariants: Tests are non-destructive and do not invoke Docker lifecycle commands.
# Outcomes: Fails fast when the help output regresses.
#

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
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

if [[ ! -f "${MAKEFILE_PATH}" ]]; then
  fail "missing Makefile at ${MAKEFILE_PATH}"
fi

make_help_output="$(cd "${ROOT_DIR}" && make help)"
assert_contains "${make_help_output}" "make backend-run" "make help output"
if [[ "${make_help_output}" == *"local-env-"* ]]; then
  fail "make help output should not advertise local-env targets"
fi

makefile_contents="$(cat "${MAKEFILE_PATH}")"
assert_contains "${makefile_contents}" "backend-run" "Makefile wiring"

echo "[test-local-env-targets] ok"
