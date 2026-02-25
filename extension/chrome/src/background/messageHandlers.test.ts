// @ts-nocheck
export {}
const test = require('node:test');
const assert = require('node:assert/strict');

const { registerMessageHandlers } = require('./messageHandlers');

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

test('registerMessageHandlers ignores registration when chrome runtime API is unavailable', () => {
  global.chrome = undefined;
  assert.doesNotThrow(() => registerMessageHandlers());
});

test('registerMessageHandlers ignores non SAVE_CLIP messages', () => {
  const getListener = setupChromeOnMessage();
  global.MESSAGE_TYPES = { SAVE_CLIP: 'SAVE_CLIP', GET_AUTH_STATUS: 'GET_AUTH_STATUS' };

  registerMessageHandlers();
  const listener = getListener();

  const result = listener({ type: 'OTHER' }, {}, () => {
    throw new Error('should not send response');
  });

  assert.equal(result, undefined);
});

test('registerMessageHandlers returns async true and sends success response for SAVE_CLIP', async () => {
  const getListener = setupChromeOnMessage();
  global.MESSAGE_TYPES = { SAVE_CLIP: 'SAVE_CLIP', GET_AUTH_STATUS: 'GET_AUTH_STATUS' };
  global.successResponse = (payload) => ({ success: true, ...payload });
  global.errorResponse = (message, extra) => ({ success: false, error: message, ...extra });
  global.createClip = async (clip) => ({ id: 99, ...clip });

  registerMessageHandlers();
  const listener = getListener();

  let sent;
  const result = listener({ type: 'SAVE_CLIP', clip: { raw_content: 'x' } }, {}, (response) => {
    sent = response;
  });

  assert.equal(result, true);
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(sent, { success: true, clip: { id: 99, raw_content: 'x' } });
});

test('registerMessageHandlers maps createClip errors into structured error response', async () => {
  const getListener = setupChromeOnMessage();
  global.MESSAGE_TYPES = { SAVE_CLIP: 'SAVE_CLIP', GET_AUTH_STATUS: 'GET_AUTH_STATUS' };
  global.successResponse = (payload) => ({ success: true, ...payload });
  global.errorResponse = (message, extra) => ({ success: false, error: message, ...extra });
  global.createClip = async () => {
    const err = new Error('boom');
    err.status = 500;
    err.body = 'bad';
    throw err;
  };

  registerMessageHandlers();
  const listener = getListener();

  let sent;
  listener({ type: 'SAVE_CLIP', clip: { raw_content: 'x' } }, {}, (response) => {
    sent = response;
  });

  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(sent, {
    success: false,
    error: 'boom',
    status: 500,
    body: 'bad',
  });
});


test('registerMessageHandlers returns async true and sends auth status response', async () => {
  const getListener = setupChromeOnMessage();
  global.MESSAGE_TYPES = { SAVE_CLIP: 'SAVE_CLIP', GET_AUTH_STATUS: 'GET_AUTH_STATUS' };
  global.successResponse = (payload) => ({ success: true, ...payload });
  global.errorResponse = (message, extra) => ({ success: false, error: message, ...extra });
  global.isUserAuthenticated = async () => true;

  registerMessageHandlers();
  const listener = getListener();

  let sent;
  const result = listener({ type: 'GET_AUTH_STATUS' }, {}, (response) => {
    sent = response;
  });

  assert.equal(result, true);
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(sent, { success: true, isAuthenticated: true });
});

test('registerMessageHandlers maps auth status errors into structured error response', async () => {
  const getListener = setupChromeOnMessage();
  global.MESSAGE_TYPES = { SAVE_CLIP: 'SAVE_CLIP', GET_AUTH_STATUS: 'GET_AUTH_STATUS' };
  global.successResponse = (payload) => ({ success: true, ...payload });
  global.errorResponse = (message, extra) => ({ success: false, error: message, ...extra });
  global.isUserAuthenticated = async () => {
    throw new Error('auth check failed');
  };

  registerMessageHandlers();
  const listener = getListener();

  let sent;
  listener({ type: 'GET_AUTH_STATUS' }, {}, (response) => {
    sent = response;
  });

  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(sent, {
    success: false,
    error: 'auth check failed',
  });
});
