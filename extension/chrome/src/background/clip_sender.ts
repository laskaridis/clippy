declare function importScripts(...paths: string[]): void;
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

// Load shared message type constants, shared configuration, the API client,
// and background handler modules for internal runtime messaging.
if (typeof importScripts === "function") {
  try {
    importScripts(
      "../shared/messages.js",
      "../shared/config.js",
      "../api/clipClient.js",
      "./contextMenuHandlers.js",
      "./messageHandlers.js"
    );
  } catch (e) {
    console.error("Failed to load background scripts:", e);
    // If this fails, messaging based on MESSAGE_TYPES will not work; the
    // rest of the script may still function for context-menu flows.
    // We avoid throwing here to keep the worker loading resilient.
  }
}

// Initialise background handlers when the worker loads.
if (typeof chrome !== "undefined" && chrome.runtime) {
  if (typeof registerContextMenuHandlers === "function") {
    registerContextMenuHandlers();
  }
  if (typeof registerMessageHandlers === "function") {
    registerMessageHandlers();
  }
}

