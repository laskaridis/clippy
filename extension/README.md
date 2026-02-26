# WebClippings Chrome Extension

Quick guide to build, test, and load the extension locally.

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

## Build for git worktree development

Prepare a worktree-scoped unpacked extension directory (manifest + runtime backend URL):

```bash
cd extension
pnpm run build:worktree
```

This writes:
- `extension/.local/worktree-runtime.json` (resolved backend/runtime metadata)
- `extension/.local/worktrees/<worktree-id>/chrome` (load this in Chrome)

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

This validates the signed-out popup experience end-to-end (status message, login button, and hidden save/label controls).
It also validates signed-in state by logging in through `/accounts/login/` and confirming
the save controls are shown while login controls are hidden.

## Load in Chrome (unpacked)

1. Build the extension for this worktree first (`pnpm run build:worktree`).
2. Open Chrome and go to `chrome://extensions`.
3. Enable **Developer mode** (top-right).
4. Click **Load unpacked**.
5. Select the folder: `extension/.local/worktrees/<worktree-id>/chrome`.

Chrome reads the generated `manifest.json`, which is scoped to this worktree backend origin.

## Iterate during development

After changing `.ts` files:

1. Run `pnpm run build:worktree` again.
2. In `chrome://extensions`, click the **Reload** button on the WebClippings extension.
