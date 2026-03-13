import { expect, test } from "@playwright/test";
import fs from "node:fs";
import {
  ensureActiveE2EUser,
  ensureBackendRunning,
  launchExtensionContext,
  loginThroughBackend,
  openPopupPage,
  stopBackendProcess,
} from "./support/runtime";

/**
 * Popup authentication E2E tests.
 *
 * This suite runs against a real Chromium extension runtime and Django backend.
 *
 * Worktree/runtime assumptions:
 * - `pnpm run build:worktree` has prepared
 *   `extension/.local/worktree-runtime-<worktree-id>.json`.
 * - The runtime file provides:
 *   - backendBaseUrl (browser-facing host/origin used for auth/cookies)
 *   - backendPort (local port used for health checks and backend startup)
 *   - envFile (worktree-scoped backend env file consumed by test helpers)
 *   - extensionDir (generated unpacked extension directory to load in Chromium)
 *
 * Coverage:
 * - Signed-out popup shows login controls and hides save controls.
 * - Signed-in popup shows save controls and hides login controls.
 */

test.beforeAll(async () => {
  await ensureBackendRunning();
  ensureActiveE2EUser();
});

test.afterAll(async () => {
  stopBackendProcess();
});

test("signed-out popup shows login prompt and hides save controls", async () => {
  test.setTimeout(90_000);

  const { context, extensionId, userDataDir } = await launchExtensionContext();
  try {
    const popup = await openPopupPage(context, extensionId);
    await expect(popup.locator("#status")).toHaveText("Sign in to WebClippings to save this clip.");
    await expect(popup.locator("#open-login")).toHaveText("Log in");
    await expect(popup.locator("#open-login")).toBeVisible();
    await expect(popup.locator("#save-clip")).toBeHidden();
    await expect(popup.locator("#labels-input")).toBeHidden();
  } finally {
    await context.close();
    fs.rmSync(userDataDir, { recursive: true, force: true });
  }
});

test("signed-in popup shows save controls and hides login button", async () => {
  test.setTimeout(90_000);

  const { context, extensionId, userDataDir } = await launchExtensionContext();
  try {
    await loginThroughBackend(context);

    const popup = await openPopupPage(context, extensionId);
    await expect(popup.locator("#save-clip")).toBeVisible();
    await expect(popup.locator("#labels-input")).toBeVisible();
    await expect(popup.locator("#open-login")).toBeHidden();
  } finally {
    await context.close();
    fs.rmSync(userDataDir, { recursive: true, force: true });
  }
});
