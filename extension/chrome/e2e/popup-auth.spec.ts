import { expect, test, chromium, BrowserContext, Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn, spawnSync, ChildProcess } from "node:child_process";

/**
 * Popup authentication E2E tests.
 *
 * This suite runs against a real Chromium extension runtime and Django backend.
 *
 * Worktree/runtime assumptions:
 * - `npm run build:worktree` has prepared `extension/.local/worktree-runtime.json`.
 * - The runtime file provides:
 *   - backendBaseUrl (browser-facing host/origin used for auth/cookies)
 *   - backendPort (local port used for health checks and backend startup)
 *   - djangoSqlitePath (worktree-scoped test database path)
 *   - extensionDir (generated unpacked extension directory to load in Chromium)
 *
 * Coverage:
 * - Signed-out popup shows login controls and hides save controls.
 * - Signed-in popup shows save controls and hides login controls.
 */
const REPO_ROOT = path.resolve(process.cwd(), "..");
const BACKEND_DIR = path.join(REPO_ROOT, "backend");
const WORKTREE_RUNTIME_FILE = path.resolve(process.cwd(), ".local", "worktree-runtime.json");
const E2E_EMAIL = "extension-e2e-user@example.com";
const E2E_PASSWORD = "Password123!";

type WorktreeRuntime = {
  backendBaseUrl: string;
  backendHost: string;
  backendPort: number;
  djangoSqlitePath: string;
  extensionDir: string;
};

function loadWorktreeRuntime(): WorktreeRuntime {
  if (!fs.existsSync(WORKTREE_RUNTIME_FILE)) {
    throw new Error(
      "Missing extension/.local/worktree-runtime.json. Run `npm run prepare:worktree` in extension/ first."
    );
  }
  const raw = fs.readFileSync(WORKTREE_RUNTIME_FILE, "utf8");
  return JSON.parse(raw) as WorktreeRuntime;
}

const RUNTIME = loadWorktreeRuntime();
const EXTENSION_DIR = RUNTIME.extensionDir;
const BACKEND_BASE_URL = RUNTIME.backendBaseUrl;
const LOGIN_URL = `${BACKEND_BASE_URL}/accounts/login/`;
const BACKEND_HEALTHCHECK_URL = `http://127.0.0.1:${RUNTIME.backendPort}/accounts/login/`;

let backendProcess: ChildProcess | null = null;

function runBackendCommand(args: string[]): void {
  const result = spawnSync("python", ["manage.py", ...args], {
    cwd: BACKEND_DIR,
    encoding: "utf8",
    env: {
      ...process.env,
      DJANGO_SQLITE_PATH: RUNTIME.djangoSqlitePath,
      ALLOWED_HOSTS: `${RUNTIME.backendHost},localhost,127.0.0.1,[::1]`,
    },
  });

  if (result.status !== 0) {
    throw new Error(
      `Command failed: python manage.py ${args.join(" ")}\n${result.stdout}\n${result.stderr}`
    );
  }
}

async function isBackendReachable(): Promise<boolean> {
  try {
    const response = await fetch(BACKEND_HEALTHCHECK_URL, { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}

async function waitForBackend(timeoutMs = 20_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    if (await isBackendReachable()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }

  throw new Error(`Timed out waiting for backend at ${BACKEND_BASE_URL}.`);
}

async function ensureBackendRunning(): Promise<void> {
  if (await isBackendReachable()) {
    return;
  }

  backendProcess = spawn(
    "python",
    ["manage.py", "runserver", `0.0.0.0:${RUNTIME.backendPort}`, "--noreload"],
    {
      cwd: BACKEND_DIR,
      stdio: "pipe",
      env: {
        ...process.env,
        DJANGO_SQLITE_PATH: RUNTIME.djangoSqlitePath,
        ALLOWED_HOSTS: `${RUNTIME.backendHost},localhost,127.0.0.1,[::1]`,
      },
    },
  );

  backendProcess.on("error", (error) => {
    // Surface startup errors if readiness check fails.
    // eslint-disable-next-line no-console
    console.error("Failed to start backend:", error);
  });

  await waitForBackend();
}

function ensureActiveE2EUser(): void {
  const script = `
from django.contrib.auth import get_user_model
User = get_user_model()
email = "${E2E_EMAIL}"
password = "${E2E_PASSWORD}"
user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
user.email = email
user.is_active = True
user.set_password(password)
user.save()
print("ok")
  `.trim();

  runBackendCommand(["shell", "-c", script]);
}

async function launchExtensionContext(): Promise<{
  context: BrowserContext;
  extensionId: string;
  userDataDir: string;
}> {
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "webclippings-ext-"));
  const headless = process.env.PW_EXTENSION_HEADLESS !== "false";

  const context = await chromium.launchPersistentContext(userDataDir, {
    channel: "chromium",
    headless,
    ignoreDefaultArgs: ["--disable-extensions"],
    args: [
      `--disable-extensions-except=${EXTENSION_DIR}`,
      `--load-extension=${EXTENSION_DIR}`,
      "--disable-crash-reporter",
    ],
  });

  let serviceWorker = context.serviceWorkers()[0];
  if (!serviceWorker) {
    serviceWorker = await context.waitForEvent("serviceworker", { timeout: 20_000 });
  }

  const extensionId = new URL(serviceWorker.url()).host;
  return { context, extensionId, userDataDir };
}

async function openPopupPage(context: BrowserContext, extensionId: string): Promise<Page> {
  const popupUrl = `chrome-extension://${extensionId}/src/popup/popup.html`;
  const page = await context.newPage();
  await page.goto(popupUrl, { waitUntil: "domcontentloaded", timeout: 20_000 });
  return page;
}

async function loginThroughBackend(context: BrowserContext): Promise<void> {
  const page = await context.newPage();
  await page.goto(LOGIN_URL, { waitUntil: "domcontentloaded", timeout: 20_000 });
  await page.fill("#id_username", E2E_EMAIL);
  await page.fill("#id_password", E2E_PASSWORD);

  await Promise.all([
    page.waitForURL(/\/clips\/$/, { timeout: 20_000 }),
    page.click('button[type="submit"]'),
  ]);

  await page.close();
}

test.beforeAll(async () => {
  runBackendCommand(["migrate", "--noinput"]);
  ensureActiveE2EUser();
  await ensureBackendRunning();
});

test.afterAll(async () => {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill("SIGTERM");
  }
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
