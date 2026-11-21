// HTF.dragReorder.targetIndex (assets/js/drag-reorder.js): where a dragged row
// lands: the arithmetic, which needs no browser. MANUAL §8.9.
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { targetIndex } = require('../../assets/js/drag-reorder.js');

// Four rows 40px tall, their middles at 20, 60, 100 and 140.
const MIDS = [20, 60, 100, 140];

test('a row not dragged past another\'s middle stays where it was', () => {
  assert.strictEqual(targetIndex(20, MIDS, 0), 0);
  assert.strictEqual(targetIndex(55, MIDS, 0), 0);
  assert.strictEqual(targetIndex(105, MIDS, 2), 2);
  assert.strictEqual(targetIndex(140, MIDS, 3), 3);
});

test('a row dragged down passes every middle it crosses', () => {
  assert.strictEqual(targetIndex(61, MIDS, 0), 1);
  assert.strictEqual(targetIndex(101, MIDS, 0), 2);
  assert.strictEqual(targetIndex(500, MIDS, 0), 3);
});

test('a tall row grabbed near its top stays put, and moves once the pointer crosses a middle', () => {
  // The fourth row runs from 120 to 280; its grip is near 130.
  const mids = [20, 60, 100, 200];
  assert.strictEqual(targetIndex(130, mids, 3), 3);
  assert.strictEqual(targetIndex(95, mids, 3), 2);
  assert.strictEqual(targetIndex(10, mids, 3), 0);
});

test('a row dragged up passes every middle it crosses', () => {
  assert.strictEqual(targetIndex(99, MIDS, 3), 2);
  assert.strictEqual(targetIndex(59, MIDS, 3), 1);
  assert.strictEqual(targetIndex(-200, MIDS, 3), 0);
});
