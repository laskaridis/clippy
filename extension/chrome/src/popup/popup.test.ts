// @ts-nocheck
export {};
const test = require("node:test");
const assert = require("node:assert/strict");

function makeClassList() {
  const set = new Set();
  return {
    add(name) {
      set.add(name);
    },
    toggle(name, force) {
      if (force === undefined) {
        if (set.has(name)) {
          set.delete(name);
        } else {
          set.add(name);
        }
        return;
      }

      if (force) {
        set.add(name);
      } else {
        set.delete(name);
      }
    },
  };
}

function makeElement(id, textContent = "") {
  const listeners = {};
  return {
    id,
    textContent,
    className: "",
    classList: makeClassList(),
    style: {},
    disabled: false,
    value: "",
    parentNode: {
      insertBefore() {},
    },
    appendChild() {},
    addEventListener(type, fn) {
      listeners[type] = fn;
    },
    trigger(type) {
      if (listeners[type]) {
        listeners[type]();
      }
    },
  };
}

function createPopupHarness(options = {}) {
  const onDomReady = { fn: null };

  const status = makeElement("status");
  const saveControls = makeElement("save-controls");
  const authControls = makeElement("auth-controls");
  const labelsInput = makeElement("labels-input");
  const labelsLabel = makeElement("labels-label");
  const saveButton = makeElement("save-clip", "Save selected text");
  const loginButton = makeElement("open-login", "Log in");
  const previewText = makeElement(
    "selection-preview-text",
    "No text selected on active page.",
  );

  const elements = {
    status,
    saveControls,
    authControls,
    labelsInput,
    saveButton,
    loginButton,
    previewText,
  };

  global.document = {
    body: {
      appendChild() {},
    },
    getElementById(id) {
      return (
        elements[
          id === "selection-preview-text"
            ? "previewText"
            : id === "save-clip"
              ? "saveButton"
              : id === "open-login"
                ? "loginButton"
                : id
        ] || null
      );
    },
    querySelector(selector) {
      if (selector === 'label[for="labels-input"]') {
        return labelsLabel;
      }
      return null;
    },
    querySelectorAll() {
      return [];
    },
    createElement(tag) {
      return makeElement(tag);
    },
    addEventListener(type, fn) {
      if (type === "DOMContentLoaded") {
        onDomReady.fn = fn;
      }
    },
  };

  global.window = {
    open() {},
  };

  global.MESSAGE_TYPES = {
    GET_AUTH_STATUS: "GET_AUTH_STATUS",
    GET_CLIP_DATA: "GET_CLIP_DATA",
    SAVE_CLIP: "SAVE_CLIP",
  };

  global.mapChromeRuntimeErrorToMessage = (_lastError, fallback) =>
    fallback || "Unexpected error";
  global.getLoginPageUrl = () => "http://localhost:8000/accounts/login/";

  let saveClipCalls = 0;
  const authResponse = options.authResponse || {
    success: true,
    isAuthenticated: true,
  };
  const clipResponse = options.clipResponse || {
    success: true,
    clip: {
      title: "Page",
      url: "https://example.com",
      raw_content: "Selected text",
    },
  };

  global.chrome = {
    runtime: {
      sendMessage(message, callback) {
        if (message.type === "GET_AUTH_STATUS") {
          callback(authResponse);
          return;
        }

        if (message.type === "SAVE_CLIP") {
          saveClipCalls += 1;
          callback({ success: true, clip: { id: 1 } });
          return;
        }

        callback({ success: false, error: "Unknown message type" });
      },
      lastError: null,
    },
    tabs: {
      query(_query, callback) {
        callback([{ id: 1 }]);
      },
      sendMessage(_tabId, message, callback) {
        if (message.type === "GET_CLIP_DATA") {
          callback(clipResponse);
          return;
        }

        callback({ success: false, error: "Unknown tab message type" });
      },
      create() {},
    },
  };

  return {
    elements,
    getSaveClipCalls() {
      return saveClipCalls;
    },
    fireDomReady() {
      assert.equal(typeof onDomReady.fn, "function");
      onDomReady.fn();
    },
  };
}

function loadPopupModule() {
  const modulePath = require.resolve("./popup");
  delete require.cache[modulePath];
  require("./popup");
}

async function flushMicrotasks() {
  await Promise.resolve();
  await Promise.resolve();
  await new Promise((resolve) => setTimeout(resolve, 0));
}

test("popup disables save button and keeps default preview when there is no selected text", async () => {
  const harness = createPopupHarness({
    clipResponse: {
      success: false,
      error: "No text selected. Select text on the page and try again.",
    },
  });

  loadPopupModule();
  harness.fireDomReady();
  await flushMicrotasks();

  assert.equal(harness.elements.saveButton.disabled, true);
  assert.equal(
    harness.elements.previewText.textContent,
    "No text selected on active page.",
  );
});

test("popup enables save button and renders a normalized, truncated selection preview", async () => {
  const longSelection = `\n  This   is    a very long selection with extra whitespace that should be collapsed into single spaces before truncation.\n  `;
  const harness = createPopupHarness({
    clipResponse: {
      success: true,
      clip: {
        title: "Page",
        url: "https://example.com",
        raw_content: longSelection.repeat(2),
      },
    },
  });

  loadPopupModule();
  harness.fireDomReady();
  await flushMicrotasks();

  const normalized = longSelection.repeat(2).replace(/\s+/g, " ").trim();
  const expected = normalized.slice(0, 120) + "...";

  assert.equal(harness.elements.saveButton.disabled, false);
  assert.equal(harness.elements.previewText.textContent, expected);
});

test("popup does not submit save when no selection is available", async () => {
  const harness = createPopupHarness({
    clipResponse: {
      success: false,
      error: "No text selected. Select text on the page and try again.",
    },
  });

  loadPopupModule();
  harness.fireDomReady();
  await flushMicrotasks();

  harness.elements.saveButton.trigger("click");

  assert.equal(harness.getSaveClipCalls(), 0);
  assert.match(harness.elements.status.textContent || "", /No text selected/i);
});

test("popup prevents duplicate submit after a successful save of the same selection", async () => {
  const harness = createPopupHarness({
    clipResponse: {
      success: true,
      clip: {
        title: "Page",
        url: "https://example.com",
        raw_content: "Repeated selection",
      },
    },
  });

  loadPopupModule();
  harness.fireDomReady();
  await flushMicrotasks();

  assert.equal(harness.elements.saveButton.disabled, false);

  harness.elements.saveButton.trigger("click");
  await flushMicrotasks();

  assert.equal(harness.getSaveClipCalls(), 1);
  assert.equal(harness.elements.saveButton.disabled, true);
  assert.equal(harness.elements.saveButton.textContent, "Already saved");
  assert.match(
    harness.elements.status.textContent || "",
    /saved successfully/i,
  );

  harness.elements.saveButton.trigger("click");
  await flushMicrotasks();

  assert.equal(harness.getSaveClipCalls(), 1);
  assert.match(harness.elements.status.textContent || "", /already saved/i);
});
