// Background service worker for sending clips to the WebClippings backend.
//
// Responsibilities (T017):
// - Receive clip data from the popup or other extension components via chrome.runtime messaging.
// - Construct a ClipCreateRequest payload as defined in specs/001-web-clipping-app/contracts/openapi.yaml.
// - Send POST /api/clips/ to the backend, relying on same-domain cookies for authentication.
//
// This script intentionally does NOT reach into tabs or content scripts directly.
// The popup (T018) is responsible for collecting clip data from the content
// script and then forwarding a complete clip object here.

/**
 * Derive the API base URL from the extension manifest's host_permissions.
 * Falls back to http://localhost:8000 if no suitable host is found.
 */
function getApiBaseUrl() {
  try {
    const manifest = chrome.runtime.getManifest();
    const hosts = manifest && Array.isArray(manifest.host_permissions)
      ? manifest.host_permissions
      : [];

    // Prefer localhost for local dev, otherwise first host permission.
    let candidate = hosts.find((h) => h.includes("localhost"));
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

const API_BASE_URL = getApiBaseUrl();
const CLIPS_ENDPOINT = `${API_BASE_URL}/api/clips/`;

/**
 * Build payload matching ClipCreateRequest schema.
 * See specs/001-web-clipping-app/contracts/openapi.yaml components.schemas.ClipCreateRequest.
 */
function buildClipCreatePayload(clip) {
  if (!clip || typeof clip !== "object") {
    throw new Error("Invalid clip data");
  }

  const { title, url, raw_content, notes, labels } = clip;

  if (!url || !raw_content) {
    throw new Error("Clip must include url and raw_content");
  }

  return {
    title: title || "",
    url,
    raw_content,
    // Notes are optional and nullable in the contract.
    notes: typeof notes === "string" && notes.length > 0 ? notes : null,
    // Labels are an array of label names (strings).
    labels: Array.isArray(labels) ? labels : [],
  };
}

/**
 * Send a single clip to the backend using fetch with cookies.
 * Returns a promise that resolves with the created clip response body.
 */
async function sendClipToBackend(clip) {
  const payload = buildClipCreatePayload(clip);

  const response = await fetch(CLIPS_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    // Use include so that same-domain cookies are sent when available.
    credentials: "include",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    const error = new Error(
      `Failed to create clip: HTTP ${response.status}` + (text ? ` - ${text}` : ""),
    );
    error.status = response.status;
    error.body = text;
    throw error;
  }

  // Response schema is components.schemas.Clip, but we treat it as opaque here.
  const data = await response.json().catch(() => null);
  return data;
}

// Listen for messages from the popup or other extension parts.
// Expected message shape for saving a clip:
// { type: "SAVE_CLIP", clip: { title, url, raw_content, notes?, labels? } }
if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || message.type !== "SAVE_CLIP") {
      return; // Not our concern.
    }

    (async () => {
      try {
        const result = await sendClipToBackend(message.clip);
        sendResponse({ success: true, clip: result });
      } catch (error) {
        // Avoid throwing out of the listener; surface a structured error payload.
        const status = error && typeof error.status === "number" ? error.status : undefined;
        const body = error && typeof error.body === "string" ? error.body : undefined;

        sendResponse({
          success: false,
          error: error && error.message ? error.message : "Failed to save clip",
          status,
          body,
        });
      }
    })();

    // Indicate we will respond asynchronously.
    return true;
  });
}
