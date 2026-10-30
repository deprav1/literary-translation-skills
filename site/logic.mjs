export const METHODS = ['skilled', 'published', 'baseline', 'reviewed'];
export const COHORT_ALGORITHM = 3;
export function hashSeed(value) { let h = 2166136261; for (const ch of value) { h ^= ch.codePointAt(0); h = Math.imul(h, 16777619); } return h >>> 0; }
export function seededRandom(seed) { let x = seed >>> 0; return () => { x += 0x6D2B79F5; let t = x; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
export function shuffled(values, random = () => crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296) {
  const result = [...values];
  for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [result[i], result[j]] = [result[j], result[i]]; }
  return result;
}
export function cohortFor(data, participantId) {
  const size = Math.min(data.cohortSize || data.rounds.length, data.rounds.length);
  const ranked = data.rounds.map(r => ({ id: r.id, title: r.title, source: r.source.replace(/\s+/g, ' ').trim(), score: hashSeed(`${data.version}:${COHORT_ALGORITHM}:${participantId}:${r.id}`) })).sort((a,b) => a.score - b.score || a.id.localeCompare(b.id));
  const selected = [];
  const add = row => { if (selected.length < size && !selected.some(previous => previous.id === row.id || previous.source.includes(row.source) || row.source.includes(previous.source))) selected.push(row); };
  // Give each available work a presence before filling the remainder by rank.
  for (const title of [...new Set(ranked.map(r => r.title))].sort()) {
    for (const row of ranked.filter(r => r.title === title)) {
      if (selected.filter(r => r.title === title).length >= 2) break;
      add(row);
    }
  }
  for (const row of ranked) {
    if (selected.length === size) break;
    add(row);
  }
  return selected.map(r => r.id).sort();
}
export function createState(data, participantId = crypto.randomUUID()) {
  const cohortIds = cohortFor(data, participantId); const order = shuffled(cohortIds, seededRandom(hashSeed(`${data.version}:${COHORT_ALGORITHM}:${participantId}:order`)));
  return { version: data.version, cohortAlgorithm: COHORT_ALGORITHM, participantId, cohortIds, order, candidateOrders: Object.fromEntries(cohortIds.map(id => [id, shuffled(data.rounds.find(r => r.id === id).candidates.map(c => c.id), seededRandom(hashSeed(`${data.version}:${participantId}:${id}:candidates`)))])), choices: {}, skipped: [], index: 0 };
}
export function validState(state, data) {
  if (!state || state.version !== data.version || state.cohortAlgorithm !== COHORT_ALGORITHM || typeof state.participantId !== 'string' || !/^[a-f0-9-]{36}$/i.test(state.participantId)) return false;
  const expectedCohort = cohortFor(data, state.participantId); if (!Array.isArray(state.cohortIds) || state.cohortIds.join() !== expectedCohort.join()) return false;
  const ids = data.rounds.map(r => r.id);
  if (!Array.isArray(state.order) || state.order.length !== expectedCohort.length || new Set(state.order).size !== expectedCohort.length || state.order.some(id => !expectedCohort.includes(id))) return false;
  if (!Number.isInteger(state.index) || state.index < 0 || state.index >= state.order.length || !state.choices || typeof state.choices !== 'object') return false;
  if (state.skipped !== undefined && (!Array.isArray(state.skipped) || new Set(state.skipped).size !== state.skipped.length || state.skipped.some(id => !expectedCohort.includes(id) || state.choices[id]))) return false;
  if (state.resultsViewedAt !== undefined && (!Number.isSafeInteger(state.resultsViewedAt) || state.resultsViewedAt < 0)) return false;
  for (const round of data.rounds.filter(r => expectedCohort.includes(r.id))) {
    const order = state.candidateOrders?.[round.id];
    if (!Array.isArray(order) || order.length !== round.candidates.length || new Set(order).size !== round.candidates.length || !order.every(id => round.candidates.some(c => c.id === id))) return false;
    const choice = state.choices[round.id];
    if (choice && (!round.candidates.some(c => c.id === choice.candidateId) || typeof choice.voteId !== 'string' || !/^[a-f0-9-]{36}$/i.test(choice.voteId) || !['pending','saved','failed'].includes(choice.status))) return false;
  }
  return Object.keys(state.choices).every(id => expectedCohort.includes(id));
}
export function personalCounts(state, data) {
  const counts = Object.fromEntries(METHODS.map(method => [method, 0]));
  for (const round of data.rounds.filter(r => state.cohortIds.includes(r.id))) {
    const selected = round.candidates.find(c => c.id === state.choices[round.id]?.candidateId);
    if (selected) counts[selected.method]++;
  }
  return counts;
}
export function percentage(count, total) { return total ? Math.round(count / total * 100) : 0; }
export function nextUnanswered(state, from = state.index) {
  for (let step = 1; step <= state.order.length; step++) {
    const index = (from + step) % state.order.length;
    const id = state.order[index];
    if (!state.choices[id] && !(state.skipped || []).includes(id)) return index;
  }
  return -1;
}
export function countsForGroup(payload, group = 'all', rounds = []) {
  const counts = Object.fromEntries(METHODS.map(method => [method, 0]));
  if (group === 'all') return payload.methods;
  if (!['original', 'new'].includes(group) || !rounds.length) throw new Error('missing comparison groups');
  const desired = group === 'new' ? 'shared_context' : 'original';
  const groups = new Map(rounds.map(round => [round.id, round.comparisonGroup]));
  for (const [id, row] of Object.entries(payload.fragments || {})) {
    if (!['original','shared_context'].includes(groups.get(id))) throw new Error('unknown comparison group');
    if (groups.get(id) !== desired) continue;
    for (const method of METHODS) {
      if (!Number.isSafeInteger(row[method]) || row[method] < 0) throw new Error('invalid fragment counts');
      counts[method] += row[method];
    }
  }
  return counts;
}
export function rememberLegacy(saved, legacy, currentVersion) {
  if (!Array.isArray(legacy)) legacy = [];
  if (!saved?.version || saved.version === currentVersion || !/^[a-f0-9-]{36}$/i.test(saved.participantId || '')) return legacy;
  const existing = legacy.find(entry => entry.dataset === saved.version && entry.participantId === saved.participantId);
  if (!existing) legacy.push({ dataset: saved.version, participantId: saved.participantId, choices: saved.choices || {} });
  else if (!existing.choices && saved.choices) existing.choices = saved.choices;
  return legacy;
}
