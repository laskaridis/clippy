// Shared configuration helpers for the WebClippings extension.
// This module centralizes how the backend API base URL and endpoints
// are derived from the extension manifest.

/**
 * Derive the API base URL from the extension manifest.
 *
 * Preference order:
 * - The first suitable host in host_permissions (preferring localhost).
 * - Fallback to http://localhost:8000.
 */
function getApiBaseUrl() {
  try {
    const manifest = chrome && chrome.runtime && chrome.runtime.getManifest
      ? chrome.runtime.getManifest()
      : null;

    const hosts = manifest && Array.isArray(manifest.host_permissions)
      ? manifest.host_permissions
      : [];

    // Prefer localhost for local dev, otherwise first host permission.
    let candidate = hosts.find(function (h) { return h && h.indexOf("localhost") !== -1; });
    if (!candidate && hosts.length > 0) {
      candidate = hosts[0];
    }

    if (!candidate) {
      return "http://localhost:8000";
    }

    // host_permissions are like "http://localhost:8000/*"; strip the path.
    const url = new URL(candidate.replace(/\*$/, ""));
    return url.origin;
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
