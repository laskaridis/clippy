// @ts-nocheck
export {}
const test = require('node:test');
const assert = require('node:assert/strict');

const {
  getCurrentSelection,
  getPageMetadata,
  buildClipFromPage,
} = require('./clipSelection');

// Helper to reset globals between tests
function resetGlobals() {
  global.window = undefined;
  global.document = undefined;
}

// getCurrentSelection tests

test('getCurrentSelection returns empty string when no selection', () => {
  resetGlobals();
  global.window = {};

  const result = getCurrentSelection();
  assert.equal(result, '');
});

test('getCurrentSelection returns string from window.getSelection', () => {
  resetGlobals();
  global.window = {
    getSelection() {
      return {
        toString() {
          return 'Selected text';
        },
      };
    },
  };

  const result = getCurrentSelection();
  assert.equal(result, 'Selected text');
});

// getPageMetadata tests

test('getPageMetadata returns empty strings when document and window are missing', () => {
  resetGlobals();

  const metadata = getPageMetadata();
  assert.deepEqual(metadata, { title: '', url: '' });
});

test('getPageMetadata reads document.title and window.location.href when available', () => {
  resetGlobals();

  global.document = { title: 'My Page Title' };
  global.window = {
    location: {
      href: 'https://example.com/page',
    },
  };

  const metadata = getPageMetadata();
  assert.deepEqual(metadata, {
    title: 'My Page Title',
    url: 'https://example.com/page',
  });
});

test('getPageMetadata falls back to empty strings when properties are missing', () => {
  resetGlobals();

  global.document = { title: '' };
  global.window = {
    location: {},
  };

  const metadata = getPageMetadata();
  assert.deepEqual(metadata, { title: '', url: '' });
});

// buildClipFromPage tests

test('buildClipFromPage composes selection and metadata into a clip object', () => {
  resetGlobals();

  global.window = {
    getSelection() {
      return {
        toString() {
          return 'Highlighted content';
        },
      };
    },
    location: {
      href: 'https://example.com/article',
    },
  };
  global.document = { title: 'An Example Article' };

  const clip = buildClipFromPage();

  assert.deepEqual(clip, {
    title: 'An Example Article',
    url: 'https://example.com/article',
    raw_content: 'Highlighted content',
  });
});
