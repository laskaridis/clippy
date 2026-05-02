// Shared configuration helpers for the WebClippings extension.
// This module centralizes how the backend API base URL and endpoints
// are derived from the extension manifest.

/**
 * Derive the API base URL from runtime configuration or manifest.
 *
 * Preference order:
 * - globalThis.WEBCLIPPINGS_RUNTIME_CONFIG.apiBaseUrl when present.
 * - The first valid host in host_permissions (manifest order).
 * - Fallback to http://localhost:8000.
 */
function getApiBaseUrl() {
  const runtimeConfig = (
    globalThis as { WEBCLIPPINGS_RUNTIME_CONFIG?: { apiBaseUrl?: unknown } }
  ).WEBCLIPPINGS_RUNTIME_CONFIG;
  if (runtimeConfig && typeof runtimeConfig.apiBaseUrl === "string") {
    try {
      return new URL(runtimeConfig.apiBaseUrl).origin;
    } catch (_e) {
      // Ignore invalid runtime override and continue with manifest fallback.
    }
  }

  try {
    const manifest =
      chrome && chrome.runtime && chrome.runtime.getManifest
        ? chrome.runtime.getManifest()
        : null;

    const hosts =
      manifest && Array.isArray(manifest.host_permissions)
        ? manifest.host_permissions
        : [];

    // host_permissions are like "http://localhost/*"; strip the path.
    for (let i = 0; i < hosts.length; i += 1) {
      const candidate = hosts[i];
      if (!candidate || typeof candidate !== "string") {
        continue;
      }
      try {
        const url = new URL(candidate.replace(/\*$/, ""));
        return url.origin;
      } catch (_e) {
        // Try the next host permission.
      }
    }

    return "http://localhost:8000";
  } catch (e) {
    // Fallback for any parsing error.
    return "http://localhost:8000";
  }
}

/**
 * Convenience helper for the clips collection endpoint.
 */
function getClipsEndpoint() {
  return getApiBaseUrl() + "/api/clips/";
}

/**
 * Convenience helper for the login page URL.
 */
function getLoginPageUrl() {
  return getApiBaseUrl() + "/accounts/login/";
}

// Export helpers for unit testing and Node environments while
// remaining compatible with the extension runtime.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    getApiBaseUrl: getApiBaseUrl,
    getClipsEndpoint: getClipsEndpoint,
    getLoginPageUrl: getLoginPageUrl,
  };
}
