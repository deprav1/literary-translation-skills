import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import { createState, validState, shuffled, personalCounts } from '../logic.mjs';
globalThis.crypto ??= webcrypto;
const data = JSON.parse(await readFile(new URL('../data.json', import.meta.url), 'utf8'));

test('randomization preserves each round and candidate exactly once', () => {
  const state = createState(data);
  assert.equal(validState(state, data), true);
  assert.deepEqual([...state.order].sort(), data.rounds.map(r => r.id).sort());
  assert.notDeepEqual(shuffled(['a','b','c'], () => 0), ['a','b','c']);
  assert.equal(new Set(state.candidateOrders[state.order[0]]).size, 3);
});
test('restored state cannot silently mix dataset versions or candidate identities', () => {
  const state = createState(data); state.version = 'an-old-dataset';
  assert.equal(validState(state, data), false);
  state.version = data.version; state.candidateOrders[state.order[0]][0] = 'invented';
  assert.equal(validState(state, data), false);
});
test('personal totals use actual selected identities, independent of card positions', () => {
  const state = createState(data);
  for (const round of data.rounds) state.choices[round.id] = { candidateId: round.candidates.find(c => c.method === 'baseline').id, voteId: crypto.randomUUID(), status: 'saved' };
  assert.deepEqual(personalCounts(state, data), { skilled: 0, published: 0, baseline: data.rounds.length });
  assert.equal(validState(state, data), true);
});
