import { chromium, test } from "@playwright/test";
import fs from "node:fs";
import { assertNoSeriousOrCriticalFindings, collectWcag21AALevelFindings } from "./support/a11y";
import {
  BACKEND_BASE_URL,
  ensureAccessibilityFixture,
  ensureActiveE2EUser,
  ensureBackendRunning,
  launchExtensionContext,
  loginThroughBackend,
  openPopupPage,
  stopBackendProcess,
} from "./support/runtime";

let clipId = "";

test.beforeAll(async () => {
  await ensureBackendRunning();
  ensureActiveE2EUser();
  clipId = ensureAccessibilityFixture().clipId;
});

test.afterAll(async () => {
  stopBackendProcess();
});

test("[@a11y] login page meets WCAG 2.1 AA serious/critical gate", async () => {
  const browser = await chromium.launch({ channel: "chromium", headless: true });
  const context = await browser.newContext();
  try {
    const page = await context.newPage();
    await page.goto(`${BACKEND_BASE_URL}/accounts/login/`, {
      waitUntil: "domcontentloaded",
    });
    const findings = await collectWcag21AALevelFindings(page);
    assertNoSeriousOrCriticalFindings(findings, "web login page");
  } finally {
    await context.close();
    await browser.close();
  }
});

test("[@a11y] register page meets WCAG 2.1 AA serious/critical gate", async () => {
  const browser = await chromium.launch({ channel: "chromium", headless: true });
  const context = await browser.newContext();
  try {
    const page = await context.newPage();
    await page.goto(`${BACKEND_BASE_URL}/accounts/register/`, {
      waitUntil: "domcontentloaded",
    });
    const findings = await collectWcag21AALevelFindings(page);
    assertNoSeriousOrCriticalFindings(findings, "web register page");
  } finally {
    await context.close();
    await browser.close();
  }
});

test("[@a11y] authenticated clips pages meet WCAG 2.1 AA serious/critical gate", async () => {
  const browser = await chromium.launch({ channel: "chromium", headless: true });
  const context = await browser.newContext();
  try {
    await loginThroughBackend(context);

    const clipsPage = await context.newPage();
    await clipsPage.goto(`${BACKEND_BASE_URL}/clips/`, { waitUntil: "domcontentloaded" });
    const clipsFindings = await collectWcag21AALevelFindings(clipsPage);
    assertNoSeriousOrCriticalFindings(clipsFindings, "web clips list page");

    const labelsPage = await context.newPage();
    await labelsPage.goto(`${BACKEND_BASE_URL}/clips/labels/`, { waitUntil: "domcontentloaded" });
    const labelsFindings = await collectWcag21AALevelFindings(labelsPage);
    assertNoSeriousOrCriticalFindings(labelsFindings, "web labels page");

    const detailPage = await context.newPage();
    await detailPage.goto(`${BACKEND_BASE_URL}/clips/${clipId}/`, { waitUntil: "domcontentloaded" });
    const detailFindings = await collectWcag21AALevelFindings(detailPage);
    assertNoSeriousOrCriticalFindings(detailFindings, "web clip detail page");
  } finally {
    await context.close();
    await browser.close();
  }
});

test("[@a11y] extension popup signed-out meets WCAG 2.1 AA serious/critical gate", async () => {
  const { context, extensionId, userDataDir } = await launchExtensionContext();
  try {
    const popup = await openPopupPage(context, extensionId);
    const findings = await collectWcag21AALevelFindings(popup);
    assertNoSeriousOrCriticalFindings(findings, "extension popup signed-out");
  } finally {
    await context.close();
    fs.rmSync(userDataDir, { recursive: true, force: true });
  }
});

test("[@a11y] extension popup signed-in meets WCAG 2.1 AA serious/critical gate", async () => {
  const { context, extensionId, userDataDir } = await launchExtensionContext();
  try {
    await loginThroughBackend(context);
    const popup = await openPopupPage(context, extensionId);
    const findings = await collectWcag21AALevelFindings(popup);
    assertNoSeriousOrCriticalFindings(findings, "extension popup signed-in");
  } finally {
    await context.close();
    fs.rmSync(userDataDir, { recursive: true, force: true });
  }
});
