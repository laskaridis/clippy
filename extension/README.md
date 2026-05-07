# WebClippings Chrome Extension

This module includes browser extensions (currently only for Chrome) that clip
texts and save them using the API published by the backend.

## Contents
`chrome`  # source code for Chrome browser extension
`scripts` # helper scripts used to assist development workflow

## Prerequisites

- Docker
- Google Chrome

For local work, start the sandbox from the repository root with
`.sandbox/bin/start`, open a shell with `.sandbox/bin/bash`, and run
`make extension-init` or `make all-init` inside `/workspace` before using the
extension commands below.

## Install dependencies

```bash
make extension-init
```

## Build

Compile TypeScript source from `chrome/src` to runtime JavaScript in `chrome/dist`:

```bash
make extension-build
```

## Unit tests

Run the extension test suite (build + Node test runner):

```bash
make extension-test-unit
```

## E2E tests (Playwright)

Run popup integration tests against a real Chromium extension runtime and backend:

```bash
make extension-test-e2e
```

If the backend is not already reachable, the Playwright helper starts it with `make backend-run` from the repository root.

This validates the signed-out popup experience end-to-end (status message, login button, and hidden save/label controls).
It also validates signed-in state by logging in through `/accounts/login/` and confirming
the save controls are shown while login controls are hidden.

Before running the extension in a browser outside Playwright, generate the checked-in runtime config in place:

```bash
cd extension
pnpm run prepare:runtime-config
```

During local development, the canonical automated path is to build and test the
extension from inside `dev-sandbox`, where the live repository clone exists at
`/workspace/extension/chrome`.

## Accessibility audits (WCAG 2.1 AA)

Run automated accessibility audits for both:
- Django frontend pages (`/accounts/*`, `/clips/*`)
- Extension popup (signed-out + signed-in)

```bash
cd extension
pnpm run test:a11y
```

This command reports all findings and fails when `serious` or `critical` issues are detected.

## Load in Chrome (unpacked)

1. Build the extension first (`pnpm run build`).
2. Generate the runtime config in place (`pnpm run prepare:runtime-config`).
3. Open Chrome and go to `chrome://extensions`.
4. Enable **Developer mode** (top-right).
5. Click **Load unpacked**.
6. Select the `extension/chrome` directory from the filesystem copy you built
   and prepared for manual browser testing.

Chrome reads the checked-in `manifest.json` and `runtime-config.js` from `extension/chrome`.

## Iterate during development

After changing `.ts` files:

1. Run `pnpm run build` again.
2. In `chrome://extensions`, click the **Reload** button on the WebClippings extension.
