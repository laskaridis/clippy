# Testing Guidelines

Run tests inside the prepared devcontainer environment. Start `make backend-run` first if a test or browser flow needs a live Django server.

Minimum commands:

```bash
make all-test
```

Equivalent manual commands:

```bash
make backend-test-unit
make backend-test-e2e
make extension-test-unit
make extension-test-e2e
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

If your change affects extension accessibility or UI semantics, also run the accessibility suite:

```bash
make extension-test-a11y
```

For full releasability gates before handoff, run:

```bash
make all-verify
```

## Expectations

- Add or update tests for every behavioral change.
- Add regression tests for bug fixes.
- Test both happy paths and authorization/ownership boundaries.
- Preserve modular boundaries: when cross-module behavior changes, add integration tests for the boundary contract.
- For API changes, align tests with the active OpenAPI contract under `specs/*/contracts/openapi.yaml` and update that contract when behavior changes.
- Prefer targeted runs during iteration, then run broader suites before finishing.
- For frontend accessibility work, run `pnpm run test:a11y` in `extension/`; the suite reports all findings and fails on serious/critical WCAG 2.1 A/AA violations.
- Browser-driven checks should use the host `localhost:<DJANGO_DEV_PORT>` origin that the active worktree exposes.
