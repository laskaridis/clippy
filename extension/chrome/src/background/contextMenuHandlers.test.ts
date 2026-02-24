// @ts-nocheck
export {}
const test = require('node:test');
const assert = require('node:assert/strict');

const { registerContextMenuHandlers } = require('./contextMenuHandlers');

function createChrome() {
  let installedListener;
  let clickedListener;
  const createCalls = [];
  const openPopupCalls = [];

  global.chrome = {
    runtime: {
      onInstalled: {
        addListener(fn) {
          installedListener = fn;
        },
      },
      lastError: null,
    },
    contextMenus: {
      create(details) {
        createCalls.push(details);
      },
      onClicked: {
        addListener(fn) {
          clickedListener = fn;
        },
      },
    },
    action: {
      openPopup(callback) {
        openPopupCalls.push(true);
        if (callback) callback();
      },
    },
  };

  return {
    getInstalledListener: () => installedListener,
    getClickedListener: () => clickedListener,
    createCalls,
    openPopupCalls,
  };
}

test('registerContextMenuHandlers no-ops when runtime API is unavailable', () => {
  global.chrome = undefined;
  assert.doesNotThrow(() => registerContextMenuHandlers());
});

test('registerContextMenuHandlers creates Clip text menu on install', () => {
  const mock = createChrome();

  registerContextMenuHandlers();
  const onInstalled = mock.getInstalledListener();
  onInstalled();

  assert.deepEqual(mock.createCalls, [
    { id: 'GET-CLIP-DATA', title: 'Clip text', contexts: ['selection'] },
  ]);
});

test('registerContextMenuHandlers opens popup only for GET-CLIP-DATA clicks', () => {
  const mock = createChrome();

  registerContextMenuHandlers();
  const onClicked = mock.getClickedListener();

  onClicked({ menuItemId: 'OTHER' }, {});
  onClicked({ menuItemId: 'GET-CLIP-DATA' }, {});

  assert.equal(mock.openPopupCalls.length, 1);
});
