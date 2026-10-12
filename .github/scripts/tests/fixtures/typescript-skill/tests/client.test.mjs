import assert from 'node:assert/strict';
import test from 'node:test';
import { twice } from '../dist/client.js';

test('shipped JavaScript exposes the expected contract', () => {
    assert.equal(twice(21), 42);
    assert.equal(twice(-3), -6);
});
