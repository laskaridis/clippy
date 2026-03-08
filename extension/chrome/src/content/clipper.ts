// Thin entrypoint for the content script. All DOM logic and
// message handling live in dedicated modules.
if (typeof registerContentMessageHandlers === "function") {
  registerContentMessageHandlers();
}
