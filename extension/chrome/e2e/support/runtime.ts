import { chromium, BrowserContext, Page } from "@playwright/test";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createHash } from "node:crypto";
import { spawn, spawnSync, ChildProcess } from "node:child_process";

const E2E_EMAIL = "extension-e2e-user@example.com";
const E2E_PASSWORD = "Password123!";

const REPO_ROOT = path.resolve(process.cwd(), "..");
const BACKEND_DIR = path.join(REPO_ROOT, "backend");
const BACKEND_WORKTREE_SCRIPT = path.join(BACKEND_DIR, "scripts", "bootsrap.sh");
const BACKEND_LOG_LINE_LIMIT = 80;

let backendProcess: ChildProcess | null = null;
let backendStartupError: Error | null = null;
const backendStdoutBuffer: string[] = [];
const backendStderrBuffer: string[] = [];

function calculateWorktreeId(worktreeRoot: string): string {
  return createHash("sha1").update(worktreeRoot).digest("hex").slice(0, 6);
}

const WORKTREE_RUNTIME_FILE = path.resolve(
  process.cwd(),
  ".local",
  `worktree-runtime-${path.basename(REPO_ROOT)}-${calculateWorktreeId(REPO_ROOT)}.json`
);

type WorktreeRuntime = {
  backendBaseUrl: string;
  backendHost: string;
  backendPort: number;
  databaseUrl: string;
  envFile: string;
  extensionDir: string;
};

function loadWorktreeRuntime(): WorktreeRuntime {
  if (!fs.existsSync(WORKTREE_RUNTIME_FILE)) {
    throw new Error(
      "Missing extension/.local/worktree-runtime-<worktree-id>.json. Run `pnpm run prepare:worktree` in extension/ first."
    );
  }
  const raw = fs.readFileSync(WORKTREE_RUNTIME_FILE, "utf8");
  return JSON.parse(raw) as WorktreeRuntime;
}

export const RUNTIME = loadWorktreeRuntime();
export const BACKEND_BASE_URL = RUNTIME.backendBaseUrl;
const BACKEND_HEALTHCHECK_URL = `http://127.0.0.1:${RUNTIME.backendPort}/accounts/login/`;

function appendLogLines(buffer: string[], chunk: string): void {
  const lines = chunk
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0);

  if (lines.length === 0) {
    return;
  }

  buffer.push(...lines);
  if (buffer.length > BACKEND_LOG_LINE_LIMIT) {
    buffer.splice(0, buffer.length - BACKEND_LOG_LINE_LIMIT);
  }
}

function formatRecentBackendLogs(): string {
  const sections: string[] = [];

  if (backendStdoutBuffer.length > 0) {
    sections.push(`stdout:\n${backendStdoutBuffer.join("\n")}`);
  }

  if (backendStderrBuffer.length > 0) {
    sections.push(`stderr:\n${backendStderrBuffer.join("\n")}`);
  }

  return sections.length > 0 ? sections.join("\n\n") : "(no backend output captured)";
}

function resetBackendStartupLogs(): void {
  backendStartupError = null;
  backendStdoutBuffer.length = 0;
  backendStderrBuffer.length = 0;
}

function collectBackendStartupLogs(process: ChildProcess): void {
  process.stdout?.on("data", (chunk: Buffer | string) => {
    appendLogLines(backendStdoutBuffer, String(chunk));
  });

  process.stderr?.on("data", (chunk: Buffer | string) => {
    appendLogLines(backendStderrBuffer, String(chunk));
  });
}

function loadBackendEnv(): NodeJS.ProcessEnv {
  const command = `set -a; source "${RUNTIME.envFile}"; set +a; env -0`;
  const result = spawnSync("bash", ["-lc", command], {
    encoding: "utf8",
    cwd: BACKEND_DIR,
    env: process.env,
    maxBuffer: 1024 * 1024 * 8,
  });
  if (result.status !== 0) {
    throw new Error(
      `Failed to load backend env file ${RUNTIME.envFile}\n${result.stdout}\n${result.stderr}`
    );
  }

  const merged: NodeJS.ProcessEnv = { ...process.env };
  for (const entry of result.stdout.split("\0")) {
    if (!entry) {
      continue;
    }
    const separator = entry.indexOf("=");
    if (separator <= 0) {
      continue;
    }
    const key = entry.slice(0, separator);
    const value = entry.slice(separator + 1);
    merged[key] = value;
  }
  return merged;
}

const BACKEND_ENV = loadBackendEnv();

export function runBackendCommand(args: string[]): string {
  const result = spawnSync("python", ["manage.py", ...args], {
    cwd: BACKEND_DIR,
    encoding: "utf8",
    env: BACKEND_ENV,
  });

  if (result.status !== 0) {
    throw new Error(
      `Command failed: python manage.py ${args.join(" ")}\n${result.stdout}\n${result.stderr}`
    );
  }

  return result.stdout;
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
    if (backendStartupError) {
      throw new Error(
        `Backend process failed to start: ${backendStartupError.message}\nRecent backend logs:\n${formatRecentBackendLogs()}`
      );
    }

    if (await isBackendReachable()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }

  throw new Error(
    `Timed out waiting for backend at ${BACKEND_BASE_URL}.\nRecent backend logs:\n${formatRecentBackendLogs()}`
  );
}

export async function ensureBackendRunning(): Promise<void> {
  if (await isBackendReachable()) {
    return;
  }

  resetBackendStartupLogs();
  backendProcess = spawn(BACKEND_WORKTREE_SCRIPT, [String(RUNTIME.backendPort), "--no-reload"], {
    cwd: BACKEND_DIR,
    stdio: "pipe",
    env: BACKEND_ENV,
  });

  collectBackendStartupLogs(backendProcess);

  backendProcess.on("error", (error) => {
    backendStartupError = error;
  });

  await waitForBackend();
}

export function stopBackendProcess(): void {
  if (backendProcess && !backendProcess.killed) {
    backendProcess.kill("SIGTERM");
  }
}

export function ensureActiveE2EUser(): void {
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

export async function launchExtensionContext(): Promise<{
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
      `--disable-extensions-except=${RUNTIME.extensionDir}`,
      `--load-extension=${RUNTIME.extensionDir}`,
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

export async function openPopupPage(context: BrowserContext, extensionId: string): Promise<Page> {
  const popupUrl = `chrome-extension://${extensionId}/src/popup/popup.html`;
  const page = await context.newPage();
  await page.goto(popupUrl, { waitUntil: "domcontentloaded", timeout: 20_000 });
  return page;
}

export async function loginThroughBackend(context: BrowserContext): Promise<void> {
  const page = await context.newPage();
  await page.goto(`${BACKEND_BASE_URL}/accounts/login/`, {
    waitUntil: "domcontentloaded",
    timeout: 20_000,
  });
  await page.fill("#id_username", E2E_EMAIL);
  await page.fill("#id_password", E2E_PASSWORD);

  await Promise.all([
    page.waitForURL(/\/clips\/$/, { timeout: 20_000 }),
    page.click('button[type="submit"]'),
  ]);

  await page.close();
}

export function ensureAccessibilityFixture(): { clipId: string } {
  const script = `
import json
from django.contrib.auth import get_user_model
from apps.clips.models import Clip, Label

User = get_user_model()
email = "${E2E_EMAIL}"
password = "${E2E_PASSWORD}"
user, _ = User.objects.get_or_create(username=email, defaults={"email": email})
user.email = email
user.is_active = True
user.set_password(password)
user.save()

label, _ = Label.objects.get_or_create(user=user, name="a11y-fixture", defaults={"color": "#6366F1"})
clip, _ = Clip.objects.get_or_create(
    user=user,
    url="https://example.com/a11y-fixture",
    defaults={
        "title": "Accessibility fixture clip",
        "domain": "example.com",
        "raw_content": "Accessibility fixture content used by Playwright audits.",
        "normalized_text": "accessibility fixture content used by playwright audits",
    },
)
clip.labels.add(label)

print(json.dumps({"clipId": str(clip.id)}))
  `.trim();

  const output = runBackendCommand(["shell", "-c", script])
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("{"))
    .at(-1);

  if (!output) {
    throw new Error("Failed to parse accessibility fixture output.");
  }

  return JSON.parse(output) as { clipId: string };
}
