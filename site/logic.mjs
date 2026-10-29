export const METHODS = ['skilled', 'published', 'baseline'];
export function shuffled(values, random = () => crypto.getRandomValues(new Uint32Array(1))[0] / 4294967296) {
  const result = [...values];
  for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [result[i], result[j]] = [result[j], result[i]]; }
  return result;
}
export function createState(data) {
  return { version: data.version, participantId: crypto.randomUUID(), order: shuffled(data.rounds.map(r => r.id)), candidateOrders: Object.fromEntries(data.rounds.map(r => [r.id, shuffled(r.candidates.map(c => c.id))])), choices: {}, index: 0 };
}
export function validState(state, data) {
  if (!state || state.version !== data.version || typeof state.participantId !== 'string' || !/^[a-f0-9-]{36}$/i.test(state.participantId)) return false;
  const ids = data.rounds.map(r => r.id);
  if (!Array.isArray(state.order) || state.order.length !== ids.length || new Set(state.order).size !== ids.length || !state.order.every(id => ids.includes(id))) return false;
  if (!Number.isInteger(state.index) || state.index < 0 || state.index >= ids.length || !state.choices || typeof state.choices !== 'object') return false;
  for (const round of data.rounds) {
    const order = state.candidateOrders?.[round.id];
    if (!Array.isArray(order) || order.length !== 3 || new Set(order).size !== 3 || !order.every(id => round.candidates.some(c => c.id === id))) return false;
    const choice = state.choices[round.id];
    if (choice && (!round.candidates.some(c => c.id === choice.candidateId) || typeof choice.voteId !== 'string')) return false;
  }
  return Object.keys(state.choices).every(id => ids.includes(id));
}
export function personalCounts(state, data) {
  const counts = { skilled: 0, published: 0, baseline: 0 };
  for (const round of data.rounds) {
    const selected = round.candidates.find(c => c.id === state.choices[round.id]?.candidateId);
    if (selected) counts[selected.method]++;
  }
  return counts;
}
export function percentage(count, total) { return total ? Math.round(count / total * 100) : 0; }
