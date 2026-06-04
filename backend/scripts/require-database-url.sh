#!/usr/bin/env bash
set -euo pipefail

COMMAND_NAME="${1:-backend command}"

if [[ -n "${DATABASE_URL:-}" ]]; then
  exit 0
fi

cat >&2 <<EOF
[backend-preflight] ${COMMAND_NAME} requires DATABASE_URL.

This repository expects backend commands to run inside the prepared dev-sandbox:
  1. cp .sandbox/.env.example .sandbox/.env
  2. Fill in the required sandbox values in .sandbox/.env
  3. .sandbox/bin/start
  4. .sandbox/bin/bash
  5. make all-init    # first use per fresh sandbox

Then rerun: make ${COMMAND_NAME}

If you intentionally run from the host shell, export DATABASE_URL to a reachable
PostgreSQL instance first.
EOF

exit 1
