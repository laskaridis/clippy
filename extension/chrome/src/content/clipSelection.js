// DOM helpers for capturing selected text and page metadata.

function getCurrentSelection() {
  var selection = window.getSelection && window.getSelection();
  if (!selection) {
    return "";
  }
  return selection.toString();
}

function getPageMetadata() {
  return {
    title: document && document.title ? document.title : "",
    url: window && window.location && window.location.href ? window.location.href : "",
  };
}

function buildClipFromPage() {
  var raw_content = getCurrentSelection();
  var metadata = getPageMetadata();

  return {
    title: metadata.title,
    url: metadata.url,
    raw_content: raw_content,
  };
}

// Export helpers for unit testing in Node while remaining
// compatible with the content-script runtime in the browser.
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    getCurrentSelection: getCurrentSelection,
    getPageMetadata: getPageMetadata,
    buildClipFromPage: buildClipFromPage,
  };
}
