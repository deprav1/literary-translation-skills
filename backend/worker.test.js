import { test } from 'node:test';
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
import { createHandler, readJson } from './worker.js';
import { DATASETS } from './catalog.js';
globalThis.crypto ??= webcrypto;
const catalog = { 'blind-v1': { f1: { a: 'skilled', b: 'published' }, f2: { c: 'baseline' } } };
const p1 = '00000000-0000-4000-8000-000000000001';
const p2 = '00000000-0000-4000-8000-000000000002';
const v1 = '10000000-0000-4000-8000-000000000001';
const v2 = '10000000-0000-4000-8000-000000000002';
class FakeDB {
  votes = []; buckets = new Map(); erasures = new Set();
  async batch(statements) { const results = []; for (const statement of statements) results.push(await statement.run()); return results; }
  prepare(sql) { const db = this; return { bind(...args) { return {
    async run() {
      if (sql.startsWith('DELETE FROM rate_buckets')) { for (const [key, value] of db.buckets) if (value.expires <= args[0]) db.buckets.delete(key); return {}; }
      if (sql.startsWith('INSERT OR IGNORE')) {
        if (sql.includes('INTO participant_erasure')) { db.erasures.add(JSON.stringify(args.slice(0,2))); return {}; }
        const [vote_id,dataset,fragment_id,candidate_id,method,participant_hash] = args;
        if (db.erasures.has(JSON.stringify([dataset,participant_hash]))) return {};
        if (!db.votes.some(v => v.vote_id === vote_id || (v.dataset === dataset && v.fragment_id === fragment_id && v.participant_hash === participant_hash))) db.votes.push({vote_id,dataset,fragment_id,candidate_id,method,participant_hash});
        return {};
      }
      if (sql.startsWith('DELETE FROM votes')) { const before = db.votes.length; db.votes = db.votes.filter(v => v.dataset !== args[0] || v.participant_hash !== args[1]); return {meta:{changes:before-db.votes.length}}; }
      throw new Error(sql);
    },
    async first() {
      if (sql.startsWith('INSERT INTO rate_buckets')) { const old = db.buckets.get(args[0]); const value = {count:(old?.count || 0)+1, expires:old?.expires || args[1]}; db.buckets.set(args[0], value); return value; }
      if (sql.startsWith('SELECT dataset, fragment_id')) return db.votes.find(v => v.vote_id === args[0]) || null;
      if (sql.startsWith('SELECT vote_id, candidate_id')) return db.votes.find(v => v.dataset === args[0] && v.fragment_id === args[1] && v.participant_hash === args[2]) || null;
      if (sql.startsWith('SELECT 1 AS erased')) return db.erasures.has(JSON.stringify(args)) ? {erased:1} : null;
      if (sql.startsWith('SELECT COUNT(*)')) { const rows = db.votes.filter(v => v.dataset === args[0]); return {totalVotes:rows.length, participantBrowsers:new Set(rows.map(v=>v.participant_hash)).size}; }
      throw new Error(sql);
    },
    async all() { const groups = new Map(); const votes = db.votes.filter(v=>v.dataset === args[0]); for (const v of votes) { const key = JSON.stringify([v.fragment_id,v.method]); groups.set(key,(groups.get(key)||0)+1); } return {results:[...groups].map(([key,count]) => {const [fragment_id,method] = JSON.parse(key); return {fragment_id,method,count,participantBrowsers:new Set(votes.map(v=>v.participant_hash)).size};})}; }
  }; } }; }
}
function setup() {
  const env = { DB:new FakeDB(), VOTE_SALT:'test secret', ALLOWED_ORIGIN:'https://deprav1.github.io' };
  const handle = createHandler(catalog);
  const call = (path, method='GET', body, origin='https://deprav1.github.io') => handle(new Request('https://api.example'+path, { method, headers:{origin,'content-type':'application/json','CF-Connecting-IP':'192.0.2.1'}, ...(body === undefined ? {} : {body:JSON.stringify(body)}) }), env);
  return {env,call};
}
test('CORS, catalog and validation fail closed', async () => {
  const {call} = setup();
  assert.equal((await call('/health','GET',undefined,'https://evil.example')).status,403);
  assert.equal((await call('/stats?dataset=unknown')).status,404);
  assert.equal((await call('/votes','POST',{dataset:'blind-v1',participantId:p1,voteId:v1,fragmentId:'f1',candidateId:'bad'})).status,400);
  assert.equal((await createHandler({})(new Request('https://api.example/stats?dataset=blind-v1'),{})).status,404);
  const response = await call('/health'); assert.equal(response.headers.get('access-control-allow-origin'),'https://deprav1.github.io');
});
test('votes are idempotent, conflicts are explicit, stats and deletion reflect stored votes', async () => {
  const {env,call} = setup();
  const vote = {dataset:'blind-v1',participantId:p1,voteId:v1,fragmentId:'f1',candidateId:'a'};
  assert.equal((await call('/votes','POST',vote)).status,200);
  assert.equal((await call('/votes','POST',vote)).status,200);
  const conflict = await call('/votes','POST',{...vote,voteId:v2,candidateId:'b'});
  assert.deepEqual(await conflict.json(),{error:'already_voted',candidateId:'a'});
  assert.equal(conflict.status,409);
  assert.equal((await call('/votes','POST',{...vote,participantId:p2})).status,409);
  assert.equal((await call('/votes','POST',{...vote,voteId:v2,fragmentId:'f2',candidateId:'c'})).status,200);
  const stats = await (await call('/stats?dataset=blind-v1')).json();
  assert.deepEqual(stats.methods,{skilled:1,published:0,baseline:1,reviewed:0}); assert.equal(stats.totalVotes,2); assert.equal(stats.participantBrowsers,1);
  assert.ok(!JSON.stringify(env.DB.votes).includes(p1));
  assert.deepEqual(await (await call('/votes','DELETE',{dataset:'blind-v1',participantId:p1})).json(),{dataset:'blind-v1',deletedVotes:2});
  assert.equal((await (await call('/stats?dataset=blind-v1')).json()).totalVotes,0);
  assert.equal((await call('/votes','POST',vote)).status,410);
});
test('body limit is enforced without trusting content-length', async () => {
  const req = new Request('https://api.example/votes',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({x:'x'.repeat(4096)})});
  await assert.rejects(readJson(req), /body_too_large/);
});
test('rate limit counts mutation attempts atomically', async () => {
  const {call} = setup(); const vote = {dataset:'blind-v1',participantId:p1,voteId:v1,fragmentId:'f1',candidateId:'a'};
  for (let i=0;i<100;i++) assert.equal((await call('/votes','POST',vote)).status,200);
  assert.equal((await call('/votes','POST',vote)).status,429);
  assert.equal((await call('/votes','DELETE',{dataset:'blind-v1',participantId:p1})).status,200);
});
test('historical and current datasets remain separate and both can be erased', async () => {
  const versions = Object.keys(DATASETS);
  const oldVersion = versions.find(v => v.startsWith('blind-v2-'));
  const newVersion = versions.find(v => v.startsWith('blind-v4-'));
  assert.ok(oldVersion && newVersion);
  const db = new FakeDB();
  const env = { DB: db, VOTE_SALT: 'test secret', ALLOWED_ORIGIN: 'https://deprav1.github.io' };
  const handle = createHandler(DATASETS);
  const call = (path, method, body) => handle(new Request('https://api.example'+path, { method, headers: {origin: env.ALLOWED_ORIGIN, 'content-type':'application/json', 'CF-Connecting-IP':'192.0.2.1'}, ...(body ? {body: JSON.stringify(body)} : {}) }), env);
  for (const [i, version] of [oldVersion,newVersion].entries()) {
    const fragmentId = Object.keys(DATASETS[version])[0];
    const entries = Object.entries(DATASETS[version][fragmentId]);
    const candidateId = version === newVersion ? entries.find(([,method]) => method === 'reviewed')[0] : entries[0][0];
    const voteId = i ? v2 : v1;
    assert.equal((await call('/votes','POST',{dataset:version, participantId:p1, voteId, fragmentId, candidateId})).status,200);
  }
  const newStats = await (await call('/stats?dataset='+newVersion,'GET')).json();
  assert.equal(newStats.methods.reviewed,1);
  assert.equal(newStats.totalVotes,1);
  for (const version of [oldVersion,newVersion]) {
    assert.equal((await (await call('/votes','DELETE',{dataset:version,participantId:p1})).json()).deletedVotes,1);
    assert.equal((await (await call('/stats?dataset='+version,'GET')).json()).totalVotes,0);
  }
});
