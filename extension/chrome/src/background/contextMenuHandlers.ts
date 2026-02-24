// Context menu setup and handlers for the WebClippings extension background
// service worker.

function registerContextMenuHandlers() {
  if (typeof chrome === "undefined" || !chrome.runtime || !chrome.runtime.onInstalled) {
    return;
  }

  chrome.runtime.onInstalled.addListener(function () {
    if (chrome.contextMenus && chrome.contextMenus.create) {
      chrome.contextMenus.create({
        id: "GET-CLIP-DATA",
        title: "Clip text",
        contexts: ["selection"],
      });
    }
  });

  // Handle clicks on the "Clip text" context-menu item.
  if (chrome.contextMenus && chrome.contextMenus.onClicked) {
    chrome.contextMenus.onClicked.addListener(function (info, tab) {
      if (info.menuItemId !== "GET-CLIP-DATA") {
        return;
      }
      if (chrome.action && chrome.action.openPopup) {
        try {
          chrome.action.openPopup(function () {
            if (chrome.runtime && chrome.runtime.lastError) {
              console.error(
                "Failed to open WebClippings popup from context menu:",
                chrome.runtime.lastError
              );
            }
          });
        } catch (error) {
          console.error("Unexpected error while opening WebClippings popup:", error);
        }
      }
    });
  }
}


if (typeof module !== "undefined" && module.exports) {
  module.exports = { registerContextMenuHandlers };
}
