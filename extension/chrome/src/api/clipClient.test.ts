// @ts-nocheck
export {}
const test = require('node:test');
const assert = require('node:assert/strict');

const { buildClipCreatePayload, createClip, isUserAuthenticated } = require('./clipClient');

// Helpers
function makeClip(overrides = {}) {
  return Object.assign(
    {
      title: 'My clip',
      url: 'https://example.com',
      raw_content: '<p>Hello</p>',
      notes: 'Some notes',
      labels: ['tag1', 'tag2'],
    },
    overrides,
  );
}

function makeResponse({ ok, status, jsonValue = {}, textValue = '', jsonThrows = false }) {
  return {
    ok,
    status,
    json: jsonThrows
      ? async () => {
          throw new Error('bad json');
        }
      : async () => jsonValue,
    text: async () => textValue,
  };
}

// buildClipCreatePayload tests

test('buildClipCreatePayload throws for non-object input', () => {
  assert.throws(() => buildClipCreatePayload(null), /Invalid clip data/);
  assert.throws(() => buildClipCreatePayload(undefined), /Invalid clip data/);
  assert.throws(() => buildClipCreatePayload('not-an-object'), /Invalid clip data/);
});

test('buildClipCreatePayload throws when url or raw_content are missing', () => {
  assert.throws(
    () => buildClipCreatePayload({ raw_content: '<p>hi</p>' }),
    /Clip must include url and raw_content/,
  );
  assert.throws(
    () => buildClipCreatePayload({ url: 'https://example.com' }),
    /Clip must include url and raw_content/,
  );
});

test('buildClipCreatePayload applies defaults for optional fields', () => {
  const payload = buildClipCreatePayload({
    url: 'https://example.com',
    raw_content: '<p>hello</p>',
  });

  assert.equal(payload.title, '');
  assert.equal(payload.url, 'https://example.com');
  assert.equal(payload.raw_content, '<p>hello</p>');
  assert.equal(payload.notes, null);
  assert.deepEqual(payload.labels, []);
});

test('buildClipCreatePayload preserves provided values', () => {
  const clip = makeClip();
  const payload = buildClipCreatePayload(clip);

  assert.equal(payload.title, clip.title);
  assert.equal(payload.url, clip.url);
  assert.equal(payload.raw_content, clip.raw_content);
  assert.equal(payload.notes, clip.notes);
  assert.deepEqual(payload.labels, clip.labels);
});

// createClip tests

test('createClip uses getClipsEndpoint when provided', async () => {
  const clip = makeClip();
  const calls = [];

  global.getClipsEndpoint = () => 'https://api.example.com/clips/';
  global.fetch = async (url, options) => {
    calls.push({ url, options });
    return makeResponse({ ok: true, status: 201, jsonValue: { id: 123 } });
  };

  const result = await createClip(clip);

  assert.equal(result.id, 123);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, 'https://api.example.com/clips/');
  assert.equal(calls[0].options.method, 'POST');
  assert.equal(calls[0].options.credentials, 'include');
  assert.equal(calls[0].options.headers['Content-Type'], 'application/json');

  const body = JSON.parse(calls[0].options.body);
  assert.equal(body.url, clip.url);
  assert.equal(body.raw_content, clip.raw_content);
});

test('createClip falls back to default endpoint when getClipsEndpoint is not a function', async () => {
  const clip = makeClip();
  let usedUrl;

  // Ensure getClipsEndpoint is not a function
  global.getClipsEndpoint = 'not-a-function';

  global.fetch = async (url, options) => {
    usedUrl = url;
    return makeResponse({ ok: true, status: 201, jsonValue: { id: 1 } });
  };

  const result = await createClip(clip);
  assert.equal(result.id, 1);
  assert.equal(usedUrl, 'http://localhost:8000/api/clips/');
});

test('createClip throws friendly error for 401/403 responses', async () => {
  const clip = makeClip();

  global.getClipsEndpoint = () => 'https://api.example.com/clips/';
  global.fetch = async () => makeResponse({
    ok: false,
    status: 401,
    textValue: 'Unauthorized',
  });

  await assert.rejects(
    () => createClip(clip),
    (err) => {
      assert.equal(err.status, 401);
      assert.equal(err.body, 'Unauthorized');
      assert.match(
        err.message,
        /Not signed in\. Open the WebClippings site, sign in, and then try saving again\./,
      );
      return true;
    },
  );
});

test('createClip throws descriptive error for non-OK responses with body text', async () => {
  const clip = makeClip();

  global.getClipsEndpoint = () => 'https://api.example.com/clips/';
  global.fetch = async () => makeResponse({
    ok: false,
    status: 500,
    textValue: 'Server error',
  });

  await assert.rejects(
    () => createClip(clip),
    (err) => {
      assert.equal(err.status, 500);
      assert.equal(err.body, 'Server error');
      assert.match(err.message, /Failed to create clip: HTTP 500 - Server error/);
      return true;
    },
  );
});

test('createClip returns parsed JSON on success', async () => {
  const clip = makeClip();
  const responseBody = { id: 42, title: 'Saved clip' };

  delete global.getClipsEndpoint;

  global.fetch = async () => makeResponse({ ok: true, status: 201, jsonValue: responseBody });

  const result = await createClip(clip);
  assert.deepEqual(result, responseBody);
});

test('createClip returns null when response.json throws', async () => {
  const clip = makeClip();

  global.getClipsEndpoint = () => 'https://api.example.com/clips/';
  global.fetch = async () => makeResponse({ ok: true, status: 201, jsonThrows: true });

  const result = await createClip(clip);
  assert.equal(result, null);
});


// isUserAuthenticated tests

test('isUserAuthenticated returns true on successful authenticated response', async () => {
  global.getClipsEndpoint = () => 'https://api.example.com/clips/';
  global.fetch = async () => makeResponse({ ok: true, status: 200, jsonValue: [] });

  const isAuthenticated = await isUserAuthenticated();
  assert.equal(isAuthenticated, true);
});

test('isUserAuthenticated returns false on unauthorized response', async () => {
  global.getClipsEndpoint = () => 'https://api.example.com/clips/';
  global.fetch = async () => makeResponse({ ok: false, status: 403, textValue: 'Forbidden' });

  const isAuthenticated = await isUserAuthenticated();
  assert.equal(isAuthenticated, false);
});
