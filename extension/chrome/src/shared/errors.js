// Shared error handling helpers for the WebClippings extension.

/**
 * Map a chrome.runtime.lastError-like value into a user-facing message.
 * Optionally accepts a fallback message used when no better message exists.
 *
 * In addition to passing through most messages, this helper normalises
 * some common cases (e.g. "Receiving end does not exist").
 */
function mapChromeRuntimeErrorToMessage(lastError, fallbackMessage) {
  var raw = "";

  if (lastError) {
    if (typeof lastError === "string") {
      raw = lastError;
    } else if (typeof lastError.message === "string") {
      raw = lastError.message;
    }
  }

  var message = raw || fallbackMessage || "Unexpected error";

  // Improve the common case where the content script is not injected
  // into a given page (e.g. Chrome Web Store, internal pages).
  if (raw && raw.indexOf("Receiving end does not exist") !== -1) {
    message =
      "This page does not allow the WebClippings extension to run. Try a normal website (not a Chrome settings or Web Store page).";
  }

  return message;
}
