#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

( cd backend && python manage.py test )
( cd extension && pnpm test && pnpm test:e2e )

mkdir -p .local
printf '%s\n' "$(git rev-parse HEAD)" > .local/resolve-gh-issue-tests.ok

echo "Tests passed for commit $(cat .local/resolve-gh-issue-tests.ok)"
