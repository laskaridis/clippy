// @ts-nocheck
export {}
const test = require('node:test');
const assert = require('node:assert/strict');

const { MESSAGE_TYPES, successResponse, errorResponse } = require('./messages');

// MESSAGE_TYPES tests

test('MESSAGE_TYPES contains expected message identifiers', () => {
  assert.equal(MESSAGE_TYPES.GET_CLIP_DATA, 'GET_CLIP_DATA');
  assert.equal(MESSAGE_TYPES.SAVE_CLIP, 'SAVE_CLIP');
  assert.equal(MESSAGE_TYPES.GET_AUTH_STATUS, 'GET_AUTH_STATUS');
});

// successResponse tests

test('successResponse returns base envelope when payload is missing or non-object', () => {
  assert.deepEqual(successResponse(), { success: true });
  assert.deepEqual(successResponse(null), { success: true });
  assert.deepEqual(successResponse('not-an-object'), { success: true });
});

test('successResponse merges own enumerable properties from payload', () => {
  const payload = { clip: { id: 1 }, count: 2 };
  const result = successResponse(payload);

  assert.deepEqual(result, {
    success: true,
    clip: { id: 1 },
    count: 2,
  });
});

test('successResponse does not copy inherited properties', () => {
  const base = { inherited: 'value' };
  const payload = Object.create(base);
  payload.own = 'own-value';

  const result = successResponse(payload);

  assert.deepEqual(result, {
    success: true,
    own: 'own-value',
  });
  assert.equal(result.inherited, undefined);
});

// errorResponse tests

test('errorResponse builds standard error envelope with given message', () => {
  const result = errorResponse('Failed to save');

  assert.deepEqual(result, {
    success: false,
    error: 'Failed to save',
  });
});

test('errorResponse falls back to "Unexpected error" when message is missing', () => {
  const result1 = errorResponse();
  const result2 = errorResponse(null);

  assert.deepEqual(result1, {
    success: false,
    error: 'Unexpected error',
  });
  assert.deepEqual(result2, {
    success: false,
    error: 'Unexpected error',
  });
});

test('errorResponse merges extra own properties, excluding success and error keys', () => {
  const extra = {
    status: 500,
    code: 'SERVER_ERROR',
    success: true,
    error: 'Overridden',
  };

  const result = errorResponse('Failed', extra);

  assert.deepEqual(result, {
    success: false,
    error: 'Failed',
    status: 500,
    code: 'SERVER_ERROR',
  });
});

test('errorResponse ignores non-object extra values', () => {
  const result1 = errorResponse('Failed', null);
  const result2 = errorResponse('Failed', 'not-an-object');

  assert.deepEqual(result1, {
    success: false,
    error: 'Failed',
  });
  assert.deepEqual(result2, {
    success: false,
    error: 'Failed',
  });
});
