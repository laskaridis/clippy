import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

/**
 * Prepare a worktree-scoped unpacked extension directory.
 *
 * Inputs:
 * - Built extension assets in extension/chrome/dist
 * - Backend worktree runtime metadata from:
 *     backend/scripts/runserver_worktree.sh --print-json
 *
 * Outputs:
 * - extension/.local/worktree-runtime.json
 * - extension/.local/worktrees/<worktree-id>/chrome/
 *   - generated manifest.json (host_permissions scoped to worktree backend)
 *   - generated runtime-config.js (WEBCLIPPINGS_RUNTIME_CONFIG.apiBaseUrl)
 *   - copied src/ and dist/ runtime assets
 *
 * This script is intended to run via:
 * - npm run prepare:worktree
 * - npm run build:worktree
 */
const extensionDir = path.resolve(import.meta.dirname, "..");
const repoRoot = path.resolve(extensionDir, "..");
const backendScript = path.join(repoRoot, "backend", "scripts", "runserver_worktree.sh");
const sourceChromeDir = path.join(extensionDir, "chrome");
const sourceDistDir = path.join(sourceChromeDir, "dist");

if (!fs.existsSync(sourceDistDir)) {
  console.error(
    "[extension] Missing chrome/dist. Run `npm run build` in extension/ before prepare-worktree-extension."
  );
  process.exit(1);
}

const runtimeResult = spawnSync(backendScript, ["--print-json"], {
  cwd: repoRoot,
  encoding: "utf8",
});

if (runtimeResult.status !== 0) {
  console.error(runtimeResult.stdout);
  console.error(runtimeResult.stderr);
  throw new Error("Failed to read backend worktree runtime from runserver_worktree.sh --print-json");
}

let backendRuntime;
try {
  backendRuntime = JSON.parse(runtimeResult.stdout);
} catch (error) {
  console.error(runtimeResult.stdout);
  throw new Error(`Failed to parse backend runtime JSON: ${String(error)}`);
}

const runtimeRoot = path.join(extensionDir, ".local");
const worktreeOutputDir = path.join(runtimeRoot, "worktrees", backendRuntime.worktreeId, "chrome");
fs.mkdirSync(worktreeOutputDir, { recursive: true });

fs.cpSync(path.join(sourceChromeDir, "src"), path.join(worktreeOutputDir, "src"), {
  recursive: true,
  force: true,
});
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
  "utf8"
);

const runtimeConfigContent = `globalThis.WEBCLIPPINGS_RUNTIME_CONFIG = {
  apiBaseUrl: ${JSON.stringify(backendRuntime.backendBaseUrl)}
};
`;
fs.writeFileSync(path.join(worktreeOutputDir, "runtime-config.js"), runtimeConfigContent, "utf8");

const extensionRuntime = {
  ...backendRuntime,
  extensionDir: worktreeOutputDir,
};
fs.mkdirSync(runtimeRoot, { recursive: true });
fs.writeFileSync(
  path.join(runtimeRoot, "worktree-runtime.json"),
  JSON.stringify(extensionRuntime, null, 2) + "\n",
  "utf8"
);

console.log(`[extension] worktree=${backendRuntime.worktreeId}`);
console.log(`[extension] backend=${backendRuntime.backendBaseUrl}`);
console.log(`[extension] extension_dir=${worktreeOutputDir}`);
