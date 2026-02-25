// Client for talking to the WebClippings backend clips API.
// This module is intended to be used from the background service worker
// and does not depend on chrome.* APIs.

/**
 * Build payload matching ClipCreateRequest schema.
 * See specs/001-web-clipping-app/contracts/openapi.yaml components.schemas.ClipCreateRequest.
 */
function buildClipCreatePayload(clip) {
  if (!clip || typeof clip !== "object") {
    throw new Error("Invalid clip data");
  }

  var title = clip.title;
  var url = clip.url;
  var raw_content = clip.raw_content;
  var notes = clip.notes;
  var labels = clip.labels;

  if (!url || !raw_content) {
    throw new Error("Clip must include url and raw_content");
  }

  return {
    title: title || "",
    url: url,
    raw_content: raw_content,
    // Notes are optional and nullable in the contract.
    notes: typeof notes === "string" && notes.length > 0 ? notes : null,
    // Labels are an array of label names (strings).
    labels: Array.isArray(labels) ? labels : [],
  };
}

/**
 * Create a single clip in the backend using fetch with cookies.
 * Returns a promise that resolves with the created clip response body.
 *
 * Expects that getClipsEndpoint() is available globally (from shared/config.js).
 */
async function createClip(clip) {
  var endpoint = typeof getClipsEndpoint === "function"
    ? getClipsEndpoint()
    : "http://localhost:8000/api/clips/";

  var payload = buildClipCreatePayload(clip);

  var response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    // Use include so that same-domain cookies are sent when available.
    credentials: "include",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    var text = "";
    try {
      text = await response.text();
    } catch (e) {
      text = "";
    }

    var message = "Failed to create clip: HTTP " + response.status;
    if (response.status === 401 || response.status === 403) {
      message = "Not signed in. Open the WebClippings site, sign in, and then try saving again.";
    } else if (text) {
      message += " - " + text;
    }

    var error = new Error(message);
    error.status = response.status;
    error.body = text;
    throw error;
  }

  // Response schema is components.schemas.Clip, but we treat it as opaque here.
  try {
    return await response.json();
  } catch (e) {
    return null;
  }
}


/**
 * Check whether the user is currently authenticated.
 * Returns true when the backend accepts an authenticated request.
 */
async function isUserAuthenticated() {
  var endpoint = typeof getClipsEndpoint === "function"
    ? getClipsEndpoint()
    : "http://localhost:8000/api/clips/";

  var response = await fetch(endpoint, {
    method: "GET",
    credentials: "include",
  });

  if (response.status >= 300 && response.status < 400) {
    return false;
  }

  if (response.redirected && response.url) {
    try {
      var redirectedUrl = new URL(response.url);
      if (redirectedUrl.pathname.indexOf("/accounts/login/") !== -1) {
        return false;
      }
    } catch (e) {
      // Ignore URL parsing errors and fall back to response.ok.
    }
  }

  return response.ok;
}

// Export for use in tests and Node environments while remaining
// compatible with the browser extension runtime.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    buildClipCreatePayload: buildClipCreatePayload,
    createClip: createClip,
    isUserAuthenticated: isUserAuthenticated,
  };
}
