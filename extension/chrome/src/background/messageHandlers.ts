// Message handlers for the WebClippings extension background service worker.

function registerMessageHandlers() {
  if (typeof chrome === "undefined" || !chrome.runtime || !chrome.runtime.onMessage) {
    return;
  }

  chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
    if (!message || message.type !== MESSAGE_TYPES.SAVE_CLIP) {
      return; // Not our concern.
    }

    (async function () {
      try {
        // createClip is provided by api/clipClient.js loaded in the worker.
        var result = await createClip(message.clip);
        sendResponse(successResponse({ clip: result }));
      } catch (error) {
        // Avoid throwing out of the listener; surface a structured error payload.
        var status = error && typeof error.status === "number" ? error.status : undefined;
        var body = error && typeof error.body === "string" ? error.body : undefined;
        var messageText = error && error.message ? error.message : "Failed to save clip";
        sendResponse(errorResponse(messageText, { status: status, body: body }));
      }
    })();

    // Indicate we will respond asynchronously.
    return true;
  });
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { registerMessageHandlers };
}
