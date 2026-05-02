import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const extensionDir = path.resolve(scriptDir, "..");
const runtimeConfigPath = path.join(
  extensionDir,
  "chrome",
  "runtime-config.js",
);

function normalizeApiBaseUrl(input) {
  return new URL(input).origin;
}

function resolveApiBaseUrl() {
  const explicitApiBaseUrl = process.env.WEBCLIPPINGS_API_BASE_URL;
  if (explicitApiBaseUrl) {
    return normalizeApiBaseUrl(explicitApiBaseUrl);
  }

  const djangoDevPort = process.env.DJANGO_DEV_PORT || "8000";
  return normalizeApiBaseUrl(`http://localhost:${djangoDevPort}`);
}

let apiBaseUrl;
try {
  apiBaseUrl = resolveApiBaseUrl();
} catch (error) {
  console.error(
    `[extension] Failed to resolve runtime config base URL: ${String(error)}`,
  );
  process.exit(1);
}

const content = `globalThis.WEBCLIPPINGS_RUNTIME_CONFIG = {
  apiBaseUrl: ${JSON.stringify(apiBaseUrl)},
};
`;

fs.writeFileSync(runtimeConfigPath, content, "utf8");
console.log(`[extension] wrote ${runtimeConfigPath}`);
