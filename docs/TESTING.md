# Testing Guidelines

Run relevant tests after changes. Minimum commands:

```bash
./scripts/test_worktree.sh
```

Equivalent manual commands:

```bash
cd backend
./scripts/bootsrap.sh --bootstrap-only
ENV_FILE="$(./scripts/bootsrap.sh --print-env-path)"
set -a && source "${ENV_FILE}" && set +a
python manage.py test
cd ../extension
pnpm test
pnpm run test:e2e
```

## Expectations

- Add or update tests for every behavioral change.
- Add regression tests for bug fixes.
- Test both happy paths and authorization/ownership boundaries.
- Preserve modular boundaries: when cross-module behavior changes, add integration tests for the boundary contract.
- For API changes, align tests with `specs/001-web-clipping-app/contracts/openapi.yaml` and update the contract when behavior changes.
- Prefer targeted runs during iteration, then run broader suites before finishing.
