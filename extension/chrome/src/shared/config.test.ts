// @ts-nocheck
export {}
const test = require('node:test');
const assert = require('node:assert/strict');

const { getApiBaseUrl, getClipsEndpoint, getLoginPageUrl } = require('./config');

function resetChrome() {
  global.chrome = undefined;
}

function setManifest(manifest) {
  global.chrome = {
    runtime: {
      getManifest() {
        return manifest;
      },
    },
  };
}

// getApiBaseUrl tests

test('getApiBaseUrl falls back to localhost when chrome is missing', () => {
  resetChrome();

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, 'http://localhost:8000');
});

test('getApiBaseUrl uses first host_permission when localhost is not present', () => {
  resetChrome();

  setManifest({
    host_permissions: ['https://api.example.com/*', 'https://other.example.com/*'],
  });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, 'https://api.example.com');
});

test('getApiBaseUrl uses manifest order when multiple host_permissions exist', () => {
  resetChrome();

  setManifest({
    host_permissions: [
      'https://api.example.com/*',
      'http://localhost:8000/*',
    ],
  });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, 'https://api.example.com');
});

test('getApiBaseUrl returns localhost when host_permissions are missing or empty', () => {
  resetChrome();

  setManifest({});
  assert.equal(getApiBaseUrl(), 'http://localhost:8000');

  setManifest({ host_permissions: [] });
  assert.equal(getApiBaseUrl(), 'http://localhost:8000');
});

test('getApiBaseUrl falls back to localhost on invalid URL entries', () => {
  resetChrome();

  setManifest({ host_permissions: ['not-a-valid-url'] });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, 'http://localhost:8000');
});

test('getApiBaseUrl skips invalid host entries and uses the first valid one', () => {
  resetChrome();

  setManifest({ host_permissions: ['not-a-valid-url', 'https://api.example.com/*'] });

  const baseUrl = getApiBaseUrl();
  assert.equal(baseUrl, 'https://api.example.com');
});

// getClipsEndpoint tests

test('getClipsEndpoint appends /api/clips/ to base URL', () => {
  resetChrome();

  setManifest({ host_permissions: ['https://api.example.com/*'] });

  const endpoint = getClipsEndpoint();
  assert.equal(endpoint, 'https://api.example.com/api/clips/');
});

test('getClipsEndpoint uses localhost base URL when chrome is missing', () => {
  resetChrome();

  const endpoint = getClipsEndpoint();
  assert.equal(endpoint, 'http://localhost:8000/api/clips/');
});


test('getLoginPageUrl appends /accounts/login/ to base URL', () => {
  resetChrome();

  setManifest({ host_permissions: ['https://api.example.com/*'] });

  const endpoint = getLoginPageUrl();
  assert.equal(endpoint, 'https://api.example.com/accounts/login/');
});
