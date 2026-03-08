// @ts-nocheck
export {};
const test = require("node:test");
const assert = require("node:assert/strict");

const { registerContentMessageHandlers } = require("./messageHandlers");

function setupChromeOnMessage() {
  let listener;
  global.chrome = {
    runtime: {
      onMessage: {
        addListener(fn) {
          listener = fn;
        },
      },
    },
  };
  return () => listener;
}

test("registerContentMessageHandlers exits when chrome runtime API is unavailable", () => {
  global.chrome = undefined;
  assert.doesNotThrow(() => registerContentMessageHandlers());
});

test("registerContentMessageHandlers ignores unrelated messages", () => {
  const getListener = setupChromeOnMessage();
  global.MESSAGE_TYPES = { GET_CLIP_DATA: "GET_CLIP_DATA" };

  registerContentMessageHandlers();
  const listener = getListener();

  const result = listener({ type: "OTHER" }, {}, () => {
    throw new Error("should not respond");
  });

  assert.equal(result, undefined);
});

test("registerContentMessageHandlers returns clip payload for GET_CLIP_DATA", () => {
  const getListener = setupChromeOnMessage();
  global.MESSAGE_TYPES = { GET_CLIP_DATA: "GET_CLIP_DATA" };
  global.buildClipFromPage = () => ({
    title: "Page",
    url: "https://x",
    raw_content: "sel",
  });
  global.successResponse = (payload) => ({ success: true, ...payload });
  global.errorResponse = (message) => ({ success: false, error: message });

  registerContentMessageHandlers();
  const listener = getListener();

  let sent;
  const result = listener({ type: "GET_CLIP_DATA" }, {}, (response) => {
    sent = response;
  });

  assert.equal(result, true);
  assert.deepEqual(sent, {
    success: true,
    clip: { title: "Page", url: "https://x", raw_content: "sel" },
  });
});

test("registerContentMessageHandlers returns structured error when clip extraction throws", () => {
  const getListener = setupChromeOnMessage();
  global.MESSAGE_TYPES = { GET_CLIP_DATA: "GET_CLIP_DATA" };
  global.buildClipFromPage = () => {
    throw new Error("cannot read selection");
  };
  global.successResponse = (payload) => ({ success: true, ...payload });
  global.errorResponse = (message) => ({ success: false, error: message });

  registerContentMessageHandlers();
  const listener = getListener();

  let sent;
  listener({ type: "GET_CLIP_DATA" }, {}, (response) => {
    sent = response;
  });

  assert.deepEqual(sent, { success: false, error: "cannot read selection" });
});
