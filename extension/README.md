# WebClippings Chrome Extension

This module includes browser extensions (currently only for Chrome) that clip
texts and save them using the API published by the backend.

## Contents
`chrome`  # source code for Chrome browser extension
`scripts` # helper scripts used to assist development workflow

## Prerequisites

- Node.js 18+
- pnpm
- Google Chrome

## Install dependencies

```bash
cd extension
pnpm install
```

## Build

Compile TypeScript source from `chrome/src` to runtime JavaScript in `chrome/dist`:

```bash
cd extension
pnpm run build
```

## Unit tests

Run the extension test suite (build + Node test runner):

```bash
cd extension
pnpm test
```

## E2E tests (Playwright)

Run popup integration tests against a real Chromium extension runtime and backend:

```bash
cd extension
pnpm install
pnpm exec playwright install chromium
pnpm run test:e2e
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

During local development, use the unpacked extension from the active sandbox
clone's `extension/chrome` directory. The host checkout only launches Dev
Containers; the live extension code runs from `/workspace/extension/chrome`
inside `dev-sandbox`.

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
6. Select the folder: `extension/chrome` from the active sandbox clone.

Chrome reads the checked-in `manifest.json` and `runtime-config.js` from `extension/chrome`.

## Iterate during development

After changing `.ts` files:

1. Run `pnpm run build` again.
2. In `chrome://extensions`, click the **Reload** button on the WebClippings extension.
