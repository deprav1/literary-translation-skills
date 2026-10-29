import { DATASETS } from './catalog.js';

const MAX_BODY = 4096;
const DAILY_LIMIT = 100;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const METHODS = new Set(['skilled', 'published', 'baseline']);
const own = (obj, key) => obj != null && typeof key === 'string' && Object.hasOwn(obj, key);
const isUuid = value => typeof value === 'string' && UUID.test(value);

export async function readJson(request) {
  if (!/^application\/json(?:\s*;|\s*$)/i.test(request.headers.get('content-type') || '')) throw new Error('content_type');
  const length = request.headers.get('content-length');
  if (length && (!/^\d+$/.test(length) || Number(length) > MAX_BODY)) throw new Error('body_too_large');
  const reader = request.body?.getReader();
  if (!reader) throw new Error('invalid_json');
  const chunks = []; let size = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > MAX_BODY) { await reader.cancel(); throw new Error('body_too_large'); }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size); let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  try {
    const value = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(bytes));
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error();
    return value;
  } catch { throw new Error('invalid_json'); }
}

async function hmac(salt, value) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey('raw', encoder.encode(salt), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const bytes = new Uint8Array(await crypto.subtle.sign('HMAC', key, encoder.encode(value)));
  return Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
}

export async function consumeRate(db, salt, ip, now = Date.now(), purpose = 'vote') {
  const date = new Date(now).toISOString().slice(0, 10);
  const bucket = await hmac(salt, `ip:${purpose}:${date}:${ip}`);
  // Each UPSERT is atomic; expiry is bounded independently of future requests.
  await db.prepare('DELETE FROM rate_buckets WHERE expires_at <= ?').bind(now).run();
  const row = await db.prepare('INSERT INTO rate_buckets (bucket_key, count, expires_at) VALUES (?, 1, ?) ON CONFLICT(bucket_key) DO UPDATE SET count = count + 1 RETURNING count').bind(bucket, now + 48 * 60 * 60 * 1000).first();
  return row.count <= DAILY_LIMIT;
}

export function createHandler(catalog = DATASETS) {
  return async function handle(request, env) {
    const origin = request.headers.get('origin');
    const allowed = origin && (origin === env.ALLOWED_ORIGIN || (env.DEV_ORIGIN && origin === env.DEV_ORIGIN && /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin)));
    const cors = allowed ? { 'Access-Control-Allow-Origin': origin, 'Vary': 'Origin' } : { 'Vary': 'Origin' };
    const reply = (status, data, extra = {}) => new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', ...cors, ...extra } });
    if (origin && !allowed) return reply(403, { error: 'origin_denied' });
    if (request.method === 'OPTIONS') {
      if (!allowed) return reply(403, { error: 'origin_denied' });
      return new Response(null, { status: 204, headers: { ...cors, 'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Access-Control-Max-Age': '600' } });
    }
    const url = new URL(request.url);
    if (request.method === 'GET' && url.pathname === '/health') return reply(200, { ok: true });
    try {
      if (request.method === 'GET' && url.pathname === '/stats') {
        const dataset = url.searchParams.get('dataset');
        if (!own(catalog, dataset) || !Object.keys(catalog[dataset]).length) return reply(404, { error: 'unknown_dataset' });
        // One SQLite read snapshot: percentages and totals cannot disagree during a concurrent vote.
        const rows = await env.DB.prepare('SELECT fragment_id, method, COUNT(*) AS count, (SELECT COUNT(DISTINCT participant_hash) FROM votes WHERE dataset = ?) AS participantBrowsers FROM votes WHERE dataset = ? GROUP BY fragment_id, method').bind(dataset, dataset).all();
        const methods = { skilled: 0, published: 0, baseline: 0 };
        const fragments = Object.create(null);
        for (const id of Object.keys(catalog[dataset])) fragments[id] = { skilled: 0, published: 0, baseline: 0 };
        for (const row of rows.results) {
          if (own(fragments, row.fragment_id) && METHODS.has(row.method)) {
            fragments[row.fragment_id][row.method] += row.count;
            methods[row.method] += row.count;
          }
        }
        return reply(200, { dataset, totalVotes: Object.values(methods).reduce((a, b) => a + b, 0), participantBrowsers: rows.results[0]?.participantBrowsers || 0, methods, fragments });
      }
      if (url.pathname !== '/votes' || !['POST', 'DELETE'].includes(request.method)) return reply(404, { error: 'not_found' });
      if (!allowed) return reply(403, { error: 'origin_denied' });
      if (!env.VOTE_SALT || !env.DB || !request.headers.get('CF-Connecting-IP')) return reply(503, { error: 'unavailable' });
      let body;
      try { body = await readJson(request); } catch (error) { return reply(error.message === 'body_too_large' ? 413 : 400, { error: error.message }); }
      const { dataset, participantId } = body;
      if (!own(catalog, dataset) || !Object.keys(catalog[dataset]).length) return reply(404, { error: 'unknown_dataset' });
      if (!isUuid(participantId)) return reply(400, { error: 'invalid_request' });
      if (request.method === 'POST' && (!isUuid(body.voteId) || !own(catalog[dataset], body.fragmentId) || !own(catalog[dataset][body.fragmentId], body.candidateId) || !METHODS.has(catalog[dataset][body.fragmentId][body.candidateId]))) return reply(400, { error: 'invalid_request' });
      if (!await consumeRate(env.DB, env.VOTE_SALT, request.headers.get('CF-Connecting-IP'), Date.now(), request.method === 'DELETE' ? 'delete' : 'vote')) return reply(429, { error: 'rate_limited' });
      const participant = await hmac(env.VOTE_SALT, `participant:${dataset}:${participantId.toLowerCase()}`);
      if (request.method === 'DELETE') {
        // Tombstone and deletion share one transaction. A delayed POST cannot recreate an erased vote.
        const result = await env.DB.batch([
          env.DB.prepare('INSERT OR IGNORE INTO participant_erasure (dataset, participant_hash, created_at) VALUES (?, ?, ?)').bind(dataset, participant, Date.now()),
          env.DB.prepare('DELETE FROM votes WHERE dataset = ? AND participant_hash = ?').bind(dataset, participant),
        ]);
        return reply(200, { dataset, deletedVotes: result[1].meta.changes });
      }
      const voteId = body.voteId.toLowerCase();
      const method = catalog[dataset][body.fragmentId][body.candidateId];
      await env.DB.prepare('INSERT OR IGNORE INTO votes (vote_id, dataset, fragment_id, candidate_id, method, participant_hash, created_at) SELECT ?, ?, ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM participant_erasure WHERE dataset = ? AND participant_hash = ?)').bind(voteId, dataset, body.fragmentId, body.candidateId, method, participant, Date.now(), dataset, participant).run();
      const byId = await env.DB.prepare('SELECT dataset, fragment_id, participant_hash FROM votes WHERE vote_id = ?').bind(voteId).first();
      if (byId && (byId.dataset !== dataset || byId.fragment_id !== body.fragmentId || byId.participant_hash !== participant)) return reply(409, { error: 'vote_id_conflict' });
      const existing = await env.DB.prepare('SELECT vote_id, candidate_id FROM votes WHERE dataset = ? AND fragment_id = ? AND participant_hash = ?').bind(dataset, body.fragmentId, participant).first();
      if (!existing) {
        const erased = await env.DB.prepare('SELECT 1 AS erased FROM participant_erasure WHERE dataset = ? AND participant_hash = ?').bind(dataset, participant).first();
        return reply(erased ? 410 : 409, { error: erased ? 'participant_erased' : 'vote_id_conflict' });
      }
      if (existing.candidate_id !== body.candidateId) return reply(409, { error: 'already_voted', candidateId: existing.candidate_id });
      return reply(200, { dataset, fragmentId: body.fragmentId, candidateId: existing.candidate_id, voteId: existing.vote_id });
    } catch {
      return reply(500, { error: 'internal_error' });
    }
  };
}
export default { fetch: createHandler() };
