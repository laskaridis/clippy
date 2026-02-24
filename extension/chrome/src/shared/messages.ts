// Shared message types and simple protocol docs for the WebClippings extension.
// This file is loaded by the popup, content script, and background service worker.

// Message type identifiers used across extension components.
const MESSAGE_TYPES = {
  // Request from the popup to the content script asking for clip data
  // from the current page (title, URL, selected text).
  GET_CLIP_DATA: "GET_CLIP_DATA",

  // Request from the popup (or other parts) to the background service worker
  // to save a clip via the backend API.
  SAVE_CLIP: "SAVE_CLIP",
};

// Helper to build a standard "success" response envelope.
// Example: successResponse({ clip }) => { success: true, clip }
function successResponse(payload) {
  const base = { success: true };
  if (!payload || typeof payload !== "object") {
    return base;
  }
  for (const key in payload) {
    if (Object.prototype.hasOwnProperty.call(payload, key)) {
      base[key] = payload[key];
    }
  }
  return base;
}

// Export shared message helpers for unit testing and Node
// environments while remaining compatible with the extension
// runtime.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    MESSAGE_TYPES: MESSAGE_TYPES,
    successResponse: successResponse,
    errorResponse: errorResponse,
  };
}

// Helper to build a standard "error" response envelope.
// Example: errorResponse("Failed", { status: 500 }) =>
// { success: false, error: "Failed", status: 500 }
function errorResponse(message, extra) {
  const base = {
    success: false,
    error: message || "Unexpected error",
  };

  if (!extra || typeof extra !== "object") {
    return base;
  }

  for (const key in extra) {
    if (Object.prototype.hasOwnProperty.call(extra, key) && key !== "success" && key !== "error") {
      base[key] = extra[key];
    }
  }

  return base;
}
