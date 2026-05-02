// @ts-nocheck
export {};
const test = require("node:test");
const assert = require("node:assert/strict");

const {
  getApiBaseUrl,
  getClipsEndpoint,
  getLoginPageUrl,
} = require("./config");

function resetChrome() {
  global.chrome = undefined;
  global.WEBCLIPPINGS_RUNTIME_CONFIG = undefined;
}

function setManifest(manifest) {
  global.chrome = {
    runtime: {
      getManifest() {
        return manifest;
      },
    },
  };
}

// getApiBaseUrl tests

test("getApiBaseUrl falls back to localhost when chrome is missing", () => {
  resetChrome();

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, "http://localhost:8000");
});

test("getApiBaseUrl prefers runtime config over manifest host_permissions", () => {
  resetChrome();

  global.WEBCLIPPINGS_RUNTIME_CONFIG = {
    apiBaseUrl: "http://localhost:8123",
  };
  setManifest({
    host_permissions: ["http://localhost/*", "http://127.0.0.1/*"],
  });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, "http://localhost:8123");
});

test("getApiBaseUrl falls back to the first valid manifest host in order", () => {
  resetChrome();

  setManifest({
    host_permissions: ["http://localhost/*", "http://127.0.0.1/*"],
  });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, "http://localhost");
});

test("getApiBaseUrl ignores invalid runtime config and falls back to manifest host_permissions", () => {
  resetChrome();

  global.WEBCLIPPINGS_RUNTIME_CONFIG = { apiBaseUrl: "invalid-url" };
  setManifest({
    host_permissions: ["not-a-valid-url", "http://127.0.0.1/*"],
  });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, "http://127.0.0.1");
});

test("getApiBaseUrl returns localhost when no valid host permission exists", () => {
  resetChrome();

  setManifest({
    host_permissions: ["not-a-valid-url", "", null],
  });

  const baseUrl = getApiBaseUrl();
  assert.equal(getApiBaseUrl(), "http://localhost:8000");
});

test("getApiBaseUrl falls back to localhost on invalid URL entries", () => {
  resetChrome();

  setManifest({ host_permissions: ["not-a-valid-url"] });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, "http://localhost:8000");
});

test("getApiBaseUrl skips invalid host entries and uses the first valid one", () => {
  resetChrome();

  setManifest({
    host_permissions: ["not-a-valid-url", "https://api.example.com/*"],
  });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, "https://api.example.com");
});

// getClipsEndpoint tests

test("getClipsEndpoint appends /api/clips/ to base URL", () => {
  resetChrome();

  setManifest({ host_permissions: ["http://localhost/*"] });

  const endpoint = getClipsEndpoint();
  assert.equal(endpoint, "http://localhost/api/clips/");
});

test("getClipsEndpoint uses localhost base URL when chrome is missing", () => {
  resetChrome();

  const endpoint = getClipsEndpoint();
  assert.equal(endpoint, "http://localhost:8000/api/clips/");
});

test("getLoginPageUrl appends /accounts/login/ to base URL", () => {
  resetChrome();

  setManifest({ host_permissions: ["http://localhost/*"] });

  const endpoint = getLoginPageUrl();
  assert.equal(endpoint, "http://localhost/accounts/login/");
});
