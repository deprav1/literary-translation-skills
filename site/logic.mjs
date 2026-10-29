export const METHODS = ['skilled', 'published', 'baseline'];
export const COHORT_ALGORITHM = 1;
export function hashSeed(value) { let h = 2166136261; for (const ch of value) { h ^= ch.codePointAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
export function seededRandom(seed) { let x = seed >>> 0; return () => { x += 0x6D2B79F5; let t = x; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
export function shuffled(values, random = () => crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296) {
  const result = [...values];
  for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [result[i], result[j]] = [result[j], result[i]]; }
  return result;
}
export function cohortFor(data, participantId) {
  const size = Math.min(data.cohortSize || data.rounds.length, data.rounds.length);
  return data.rounds.map(r => ({ id: r.id, score: hashSeed(`${data.version}:${COHORT_ALGORITHM}:${participantId}:${r.id}`) })).sort((a,b) => a.score - b.score || a.id.localeCompare(b.id)).slice(0, size).map(r => r.id).sort();
}
export function createState(data, participantId = crypto.randomUUID()) {
  const cohortIds = cohortFor(data, participantId); const order = shuffled(cohortIds, seededRandom(hashSeed(`${data.version}:${COHORT_ALGORITHM}:${participantId}:order`)));
  return { version: data.version, cohortAlgorithm: COHORT_ALGORITHM, participantId, cohortIds, order, candidateOrders: Object.fromEntries(cohortIds.map(id => [id, shuffled(data.rounds.find(r => r.id === id).candidates.map(c => c.id), seededRandom(hashSeed(`${data.version}:${participantId}:${id}:candidates`)))])), choices: {}, index: 0 };
}
export function validState(state, data) {
  if (!state || state.version !== data.version || state.cohortAlgorithm !== COHORT_ALGORITHM || typeof state.participantId !== 'string' || !/^[a-f0-9-]{36}$/i.test(state.participantId)) return false;
  const expectedCohort = cohortFor(data, state.participantId); if (!Array.isArray(state.cohortIds) || state.cohortIds.join() !== expectedCohort.join()) return false;
  const ids = data.rounds.map(r => r.id);
  if (!Array.isArray(state.order) || state.order.length !== expectedCohort.length || new Set(state.order).size !== expectedCohort.length || state.order.some(id => !expectedCohort.includes(id))) return false;
  if (!Number.isInteger(state.index) || state.index < 0 || state.index >= ids.length || !state.choices || typeof state.choices !== 'object') return false;
  for (const round of data.rounds.filter(r => expectedCohort.includes(r.id))) {
    const order = state.candidateOrders?.[round.id];
    if (!Array.isArray(order) || order.length !== 3 || new Set(order).size !== 3 || !order.every(id => round.candidates.some(c => c.id === id))) return false;
    const choice = state.choices[round.id];
    if (choice && (!round.candidates.some(c => c.id === choice.candidateId) || typeof choice.voteId !== 'string' || !/^[a-f0-9-]{36}$/i.test(choice.voteId) || !['pending','saved','failed'].includes(choice.status))) return false;
  }
  return Object.keys(state.choices).every(id => expectedCohort.includes(id));
}
export function personalCounts(state, data) {
  const counts = { skilled: 0, published: 0, baseline: 0 };
  for (const round of data.rounds.filter(r => state.cohortIds.includes(r.id))) {
    const selected = round.candidates.find(c => c.id === state.choices[round.id]?.candidateId);
    if (selected) counts[selected.method]++;
  }
  return counts;
}
export function percentage(count, total) { return total ? Math.round(count / total * 100) : 0; }
