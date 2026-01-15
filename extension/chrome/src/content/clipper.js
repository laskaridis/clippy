// Placeholder content script for capturing selected text.
export function getCurrentSelection() {
  const selection = window.getSelection();
  return selection ? selection.toString() : "";
}
