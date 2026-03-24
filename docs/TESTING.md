# Testing Guidelines

Run relevant tests after changes. Minimum commands:

```bash
make all-test
```

Equivalent manual commands:

```bash
make backend-test-unit
make backend-test-e2e
make extension-test-unit
make extension-test-e2e
make extension-test-a11y
```

Equivalent script-level commands:

```bash
cd backend
./scripts/test.sh
./scripts/test-e2e.sh
cd ../extension
pnpm test
pnpm run test:e2e
pnpm run test:a11y
```

## Expectations

- Add or update tests for every behavioral change.
- Add regression tests for bug fixes.
- Test both happy paths and authorization/ownership boundaries.
- Preserve modular boundaries: when cross-module behavior changes, add integration tests for the boundary contract.
- For API changes, align tests with `specs/001-web-clipping-app/contracts/openapi.yaml` and update the contract when behavior changes.
- Prefer targeted runs during iteration, then run broader suites before finishing.
- For frontend accessibility work, run `pnpm run test:a11y` in `extension/`; the suite reports all findings and fails on serious/critical WCAG 2.1 A/AA violations.
