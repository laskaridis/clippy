// @ts-nocheck
export {};
const test = require("node:test");
const assert = require("node:assert/strict");

const { mapChromeRuntimeErrorToMessage } = require("./errors");

// Basic mapping behavior

test("returns string error as-is when lastError is a string", () => {
  const msg = mapChromeRuntimeErrorToMessage(
    "Something went wrong",
    "Fallback",
  );
  assert.equal(msg, "Something went wrong");
});

test("returns lastError.message when lastError is an object with message", () => {
  const msg = mapChromeRuntimeErrorToMessage(
    { message: "Object error message" },
    "Fallback",
  );
  assert.equal(msg, "Object error message");
});

test("uses fallbackMessage when no usable error message is present", () => {
  const msg1 = mapChromeRuntimeErrorToMessage(null, "Fallback message");
  assert.equal(msg1, "Fallback message");

  const msg2 = mapChromeRuntimeErrorToMessage(
    { code: 123 },
    "Another fallback",
  );
  assert.equal(msg2, "Another fallback");
});

test('falls back to "Unexpected error" when neither error nor fallback is provided', () => {
  const msg1 = mapChromeRuntimeErrorToMessage(null);
  assert.equal(msg1, "Unexpected error");

  const msg2 = mapChromeRuntimeErrorToMessage({});
  assert.equal(msg2, "Unexpected error");
});

// Special-case message normalization

test('normalizes "Receiving end does not exist" string errors to a friendly message', () => {
  const raw = "Error: Receiving end does not exist. Maybe not injected?";
  const msg = mapChromeRuntimeErrorToMessage(raw, "Fallback");

  assert.equal(
    msg,
    "This page does not allow the WebClippings extension to run. Try a normal website (not a Chrome settings or Web Store page).",
  );
});

test('normalizes "Receiving end does not exist" object.message errors to a friendly message', () => {
  const raw = "Receiving end does not exist in this context";
  const msg = mapChromeRuntimeErrorToMessage({ message: raw }, "Fallback");

  assert.equal(
    msg,
    "This page does not allow the WebClippings extension to run. Try a normal website (not a Chrome settings or Web Store page).",
  );
});

// Precedence behavior

test("error message takes precedence over fallback when both are present", () => {
  const msg = mapChromeRuntimeErrorToMessage("Primary message", "Fallback");
  assert.equal(msg, "Primary message");
});

test("handles non-string lastError values gracefully", () => {
  const msg = mapChromeRuntimeErrorToMessage(42, "Fallback");
  assert.equal(msg, "Fallback");
});
