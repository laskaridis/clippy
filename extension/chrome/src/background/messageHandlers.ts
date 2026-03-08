// Message handlers for the WebClippings extension background service worker.
type ErrorWithDetails = {
  message?: string;
  status?: number;
  body?: string;
};

function toErrorWithDetails(error: unknown): ErrorWithDetails {
  if (error && typeof error === "object") {
    return error as ErrorWithDetails;
  }
  return {};
}

function registerMessageHandlers() {
  if (
    typeof chrome === "undefined" ||
    !chrome.runtime ||
    !chrome.runtime.onMessage
  ) {
    return;
  }

  chrome.runtime.onMessage.addListener(
    function (message, sender, sendResponse) {
      if (!message || !message.type) {
        return; // Not our concern.
      }

      if (message.type === MESSAGE_TYPES.SAVE_CLIP) {
        (async function () {
          try {
            // createClip is provided by api/clipClient.js loaded in the worker.
            var result = await createClip(message.clip);
            sendResponse(successResponse({ clip: result }));
          } catch (error) {
            var errorDetails = toErrorWithDetails(error);
            // Avoid throwing out of the listener; surface a structured error payload.
            var status =
              typeof errorDetails.status === "number"
                ? errorDetails.status
                : undefined;
            var body =
              typeof errorDetails.body === "string"
                ? errorDetails.body
                : undefined;
            var messageText =
              typeof errorDetails.message === "string"
                ? errorDetails.message
                : "Failed to save clip";
            sendResponse(
              errorResponse(messageText, { status: status, body: body }),
            );
          }
        })();

        // Indicate we will respond asynchronously.
        return true;
      }

      if (message.type === MESSAGE_TYPES.GET_AUTH_STATUS) {
        (async function () {
          try {
            var isAuthenticated = await isUserAuthenticated();
            sendResponse(successResponse({ isAuthenticated: isAuthenticated }));
          } catch (error) {
            var errorDetails = toErrorWithDetails(error);
            var messageText =
              typeof errorDetails.message === "string"
                ? errorDetails.message
                : "Failed to check auth status";
            sendResponse(errorResponse(messageText));
          }
        })();

        return true;
      }

      return; // Not our concern.
    },
  );
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { registerMessageHandlers };
}
