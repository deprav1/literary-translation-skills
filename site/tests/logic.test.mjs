import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { webcrypto } from 'node:crypto';
import { createState, validState, shuffled, personalCounts, rememberLegacy } from '../logic.mjs';
globalThis.crypto ??= webcrypto;
const data = JSON.parse(await readFile(new URL('../data.json', import.meta.url), 'utf8'));

test('randomization assigns a deterministic cohort and preserves candidates', () => {
  const fixture = {...data, cohortSize: Math.min(20, data.rounds.length)};
  const state = createState(fixture, '00000000-0000-4000-8000-000000000001');
  const stateAgain = createState(fixture, '00000000-0000-4000-8000-000000000001');
  assert.equal(validState(state, fixture), true);
  assert.deepEqual(state.cohortIds, stateAgain.cohortIds);
  assert.deepEqual(state.order, stateAgain.order);
  assert.equal(state.order.length, fixture.cohortSize);
  assert.ok(state.order.every(id => fixture.rounds.some(r => r.id === id)));
  assert.notDeepEqual(shuffled(['a','b','c'], () => 0), ['a','b','c']);
  assert.equal(new Set(state.candidateOrders[state.order[0]]).size, fixture.rounds[0].candidates.length);
});
test('restored state cannot silently mix dataset versions or candidate identities', () => {
  const fixture = {...data, cohortSize: Math.min(20, data.rounds.length)};
  const state = createState(fixture, '00000000-0000-4000-8000-000000000002'); state.version = 'an-old-dataset';
  assert.equal(validState(state, fixture), false);
  state.version = fixture.version; state.candidateOrders[state.order[0]][0] = 'invented';
  assert.equal(validState(state, fixture), false);
});
test('personal totals use actual selected identities, independent of card positions', () => {
  const fixture = {...data, cohortSize: Math.min(20, data.rounds.length)};
  const state = createState(fixture, '00000000-0000-4000-8000-000000000003');
  for (const id of state.cohortIds) { const round = fixture.rounds.find(r => r.id === id); state.choices[id] = { candidateId: round.candidates.find(c => c.method === 'baseline').id, voteId: crypto.randomUUID(), status: 'saved' }; }
  assert.deepEqual(personalCounts(state, fixture), { skilled: 0, published: 0, baseline: state.cohortIds.length, reviewed: 0 });
  assert.equal(validState(state, fixture), true);
});
test('different participant IDs usually receive different cohorts', () => {
  const fixture = {...data, cohortSize: Math.min(20, data.rounds.length)};
  const first = createState(fixture, '00000000-0000-4000-8000-000000000004');
  const second = createState(fixture, '00000000-0000-4000-8000-000000000005');
  if (fixture.rounds.length > fixture.cohortSize) assert.notDeepEqual(first.cohortIds, second.cohortIds);
});
test('the reported Wilde fragments keep their original and historical translation together', () => {
  const one = data.rounds.find(r => r.id === 'wilde-extra-01');
  const two = data.rounds.find(r => r.id === 'wilde-extra-02');
  assert.match(one.source, /walls of a round city/);
  assert.match(one.candidates.find(c => c.method === 'published').text, /стены круглого города/);
  assert.match(two.source, /many lutes/);
  assert.match(two.candidates.find(c => c.method === 'published').text, /многих лютней/);
  assert.doesNotMatch(two.candidates.find(c => c.method === 'published').text, /стены круглого города/);
});
test('a cohort does not repeat a passage already included in a longer excerpt', () => {
  for (let i=0; i<50; i++) {
    const id = `00000000-0000-4000-8000-${String(i).padStart(12,'0')}`;
    const state = createState(data, id);
    assert.equal(state.order.length, data.cohortSize);
    assert.ok(state.cohortIds.filter(id => id.startsWith('cat-')).length >= 2);
    const sources = state.cohortIds.map(id => data.rounds.find(r => r.id === id).source.replace(/\s+/g, ' ').trim());
    for (let a=0; a<sources.length; a++) for (let b=a+1; b<sources.length; b++) assert.ok(!sources[a].includes(sources[b]) && !sources[b].includes(sources[a]));
  }
});
test('a dataset update preserves the old identity and personal choices once', () => {
  const saved = {version:'blind-v3-bd065db04a20', participantId:'00000000-0000-4000-8000-000000000001', choices:{'wilde-extra-02':{candidateId:'c1', status:'saved'}}};
  const legacy = rememberLegacy(saved, [], data.version);
  assert.equal(legacy.length, 1);
  assert.equal(legacy[0].participantId, saved.participantId);
  assert.deepEqual(legacy[0].choices, saved.choices);
  assert.equal(rememberLegacy(saved, legacy, data.version).length, 1);
});
