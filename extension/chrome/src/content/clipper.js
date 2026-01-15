// Content script for capturing selected text, page title, and URL.

function getCurrentSelection() {
  const selection = window.getSelection();
  if (!selection) {
    return "";
  }
  return selection.toString();
}

function getPageMetadata() {
  return {
    title: document.title || "",
    url: window.location.href || "",
  };
}

function getClipData() {
  const raw_content = getCurrentSelection();
  const { title, url } = getPageMetadata();

  return {
    title,
    url,
    raw_content,
  };
}

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!message || message.type !== "GET_CLIP_DATA") {
      return;
    }

    try {
      const clip = getClipData();
      sendResponse({ success: true, clip });
    } catch (error) {
      // Avoid throwing inside content script; report a structured error instead.
      sendResponse({ success: false, error: error && error.message ? error.message : "Failed to capture clip data" });
    }

    // Indicate that we responded synchronously.
    return true;
  });
}
