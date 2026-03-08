import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";

/**
 * Prepare a worktree-scoped unpacked extension directory.
 *
 * Inputs:
 * - Built extension assets in extension/chrome/dist
 * - Backend worktree runtime metadata, resolved in this order:
 *   1) backend/.local/worktree-runtime-<worktree-id>.json (only when it matches this
 *      worktree and its backendPort is actively listening)
 *   2) backend/scripts/bootsrap.sh --print-json (fallback)
 *
 * Outputs:
 * - extension/.local/worktree-runtime-<worktree-id>.json
 * - extension/.local/worktrees/<worktree-id>/chrome/
 *   - generated manifest.json (host_permissions scoped to worktree backend)
 *   - generated runtime-config.js (WEBCLIPPINGS_RUNTIME_CONFIG.apiBaseUrl)
 *   - copied src/ and dist/ runtime assets
 *
 * This script is intended to run via:
 * - pnpm run prepare:worktree
 * - pnpm run build:worktree
 */
const extensionDir = path.resolve(import.meta.dirname, "..");
const repoRoot = path.resolve(extensionDir, "..");
const backendScript = path.join(repoRoot, "backend", "scripts", "bootsrap.sh");
const worktreeHash = crypto
  .createHash("sha1")
  .update(repoRoot)
  .digest("hex")
  .slice(0, 6);
const worktreeId = `${path.basename(repoRoot)}-${worktreeHash}`;
const backendRuntimeStatePath = path.join(
  repoRoot,
  "backend",
  ".local",
  `worktree-runtime-${worktreeId}.json`,
);
const sourceChromeDir = path.join(extensionDir, "chrome");
const sourceDistDir = path.join(sourceChromeDir, "dist");

if (!fs.existsSync(sourceDistDir)) {
  console.error(
    "[extension] Missing chrome/dist. Run `pnpm run build` in extension/ before prepare-worktree-extension.",
  );
  process.exit(1);
}

function readBackendRuntimeFromScript() {
  const runtimeResult = spawnSync(backendScript, ["--print-json"], {
    cwd: repoRoot,
    encoding: "utf8",
  });

  if (runtimeResult.status !== 0) {
    console.error(runtimeResult.stdout);
    console.error(runtimeResult.stderr);
    throw new Error(
      "Failed to read backend worktree runtime from bootsrap.sh --print-json",
    );
  }

  try {
    return JSON.parse(runtimeResult.stdout);
  } catch (error) {
    console.error(runtimeResult.stdout);
    throw new Error(`Failed to parse backend runtime JSON: ${String(error)}`);
  }
}

function isBackendRuntimeShape(value) {
  return (
    value &&
    typeof value === "object" &&
    typeof value.worktreeRoot === "string" &&
    typeof value.worktreeId === "string" &&
    typeof value.worktreeHash === "string" &&
    Number.isInteger(value.backendPort) &&
    typeof value.backendHost === "string" &&
    typeof value.backendBaseUrl === "string" &&
    typeof value.databaseUrl === "string" &&
    typeof value.envFile === "string"
  );
}

function isPortListening(port) {
  const check = spawnSync("lsof", ["-nP", `-iTCP:${port}`, "-sTCP:LISTEN"], {
    encoding: "utf8",
  });
  return check.status === 0;
}

function readRunningBackendRuntime() {
  if (!fs.existsSync(backendRuntimeStatePath)) {
    return null;
  }

  try {
    const parsed = JSON.parse(fs.readFileSync(backendRuntimeStatePath, "utf8"));
    if (!isBackendRuntimeShape(parsed)) {
      return null;
    }
    if (path.resolve(parsed.worktreeRoot) !== repoRoot) {
      return null;
    }
    if (!isPortListening(parsed.backendPort)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

const backendRuntime =
  readRunningBackendRuntime() ?? readBackendRuntimeFromScript();

const runtimeRoot = path.join(extensionDir, ".local");
const worktreeOutputDir = path.join(
  runtimeRoot,
  "worktrees",
  backendRuntime.worktreeId,
  "chrome",
);
fs.mkdirSync(worktreeOutputDir, { recursive: true });

fs.cpSync(
  path.join(sourceChromeDir, "src"),
  path.join(worktreeOutputDir, "src"),
  {
    recursive: true,
    force: true,
  },
);
fs.cpSync(sourceDistDir, path.join(worktreeOutputDir, "dist"), {
  recursive: true,
  force: true,
});

const manifestPath = path.join(sourceChromeDir, "manifest.json");
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
manifest.host_permissions = [`${backendRuntime.backendBaseUrl}/*`];
fs.writeFileSync(
  path.join(worktreeOutputDir, "manifest.json"),
  JSON.stringify(manifest, null, 2) + "\n",
  "utf8",
);

const runtimeConfigContent = `globalThis.WEBCLIPPINGS_RUNTIME_CONFIG = {
  apiBaseUrl: ${JSON.stringify(backendRuntime.backendBaseUrl)}
};
`;
fs.writeFileSync(
  path.join(worktreeOutputDir, "runtime-config.js"),
  runtimeConfigContent,
  "utf8",
);

const extensionRuntime = {
  ...backendRuntime,
  extensionDir: worktreeOutputDir,
};
fs.mkdirSync(runtimeRoot, { recursive: true });
fs.writeFileSync(
  path.join(runtimeRoot, `worktree-runtime-${backendRuntime.worktreeId}.json`),
  JSON.stringify(extensionRuntime, null, 2) + "\n",
  "utf8",
);

console.log(`[extension] worktree=${backendRuntime.worktreeId}`);
console.log(`[extension] backend=${backendRuntime.backendBaseUrl}`);
console.log(`[extension] extension_dir=${worktreeOutputDir}`);
