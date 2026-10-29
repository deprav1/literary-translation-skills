import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import { createState, validState, shuffled, personalCounts } from '../logic.mjs';
globalThis.crypto ??= webcrypto;
const data = JSON.parse(await readFile(new URL('../data.json', import.meta.url), 'utf8'));

test('randomization assigns a deterministic cohort and preserves candidates', () => {
  const fixture = {...data, cohortSize: Math.min(10, data.rounds.length)};
  const state = createState(fixture, '00000000-0000-4000-8000-000000000001');
  const stateAgain = createState(fixture, '00000000-0000-4000-8000-000000000001');
  assert.equal(validState(state, fixture), true);
  assert.deepEqual(state.cohortIds, stateAgain.cohortIds);
  assert.deepEqual(state.order, stateAgain.order);
  assert.equal(state.order.length, fixture.cohortSize);
  assert.ok(state.order.every(id => fixture.rounds.some(r => r.id === id)));
  assert.notDeepEqual(shuffled(['a','b','c'], () => 0), ['a','b','c']);
  assert.equal(new Set(state.candidateOrders[state.order[0]]).size, 3);
});
test('restored state cannot silently mix dataset versions or candidate identities', () => {
  const fixture = {...data, cohortSize: Math.min(10, data.rounds.length)};
  const state = createState(fixture, '00000000-0000-4000-8000-000000000002'); state.version = 'an-old-dataset';
  assert.equal(validState(state, fixture), false);
  state.version = fixture.version; state.candidateOrders[state.order[0]][0] = 'invented';
  assert.equal(validState(state, fixture), false);
});
test('personal totals use actual selected identities, independent of card positions', () => {
  const fixture = {...data, cohortSize: Math.min(10, data.rounds.length)};
  const state = createState(fixture, '00000000-0000-4000-8000-000000000003');
  for (const id of state.cohortIds) { const round = fixture.rounds.find(r => r.id === id); state.choices[id] = { candidateId: round.candidates.find(c => c.method === 'baseline').id, voteId: crypto.randomUUID(), status: 'saved' }; }
  assert.deepEqual(personalCounts(state, fixture), { skilled: 0, published: 0, baseline: state.cohortIds.length });
  assert.equal(validState(state, fixture), true);
});
test('different participant IDs usually receive different cohorts', () => {
  const fixture = {...data, cohortSize: Math.min(10, data.rounds.length)};
  const first = createState(fixture, '00000000-0000-4000-8000-000000000004');
  const second = createState(fixture, '00000000-0000-4000-8000-000000000005');
  if (fixture.rounds.length > fixture.cohortSize) assert.notDeepEqual(first.cohortIds, second.cohortIds);
});
