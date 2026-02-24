// Message handling for the WebClippings content script.
function registerContentMessageHandlers() {
  if (typeof chrome === "undefined" || !chrome.runtime || !chrome.runtime.onMessage) {
    return;
  }

  chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (!message || message.type !== MESSAGE_TYPES.GET_CLIP_DATA) {
      return;
    }

    try {
      var clip = typeof buildClipFromPage === "function" ? buildClipFromPage() : null;
      sendResponse(successResponse({ clip: clip }));
    } catch (error) {
      // Avoid throwing inside content script; report a structured error instead.
      var messageText = error && error.message ? error.message : "Failed to capture clip data";
      sendResponse(errorResponse(messageText));
    }

    // Indicate that we responded synchronously.
    return true;
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { registerContentMessageHandlers };
}
