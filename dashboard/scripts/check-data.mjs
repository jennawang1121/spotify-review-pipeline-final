import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
const db=new DatabaseSync('.sites-runtime/validation.sqlite');
const adapter={prepare(sql){let params=[];return {bind(...values){params=values;return this;},async first(){return db.prepare(sql).get(...params)??null;},async all(){return {results:db.prepare(sql).all(...params)};},async run(){db.prepare(sql).run(...params);return {success:true};}};},async batch(statements){db.exec('BEGIN');try{for(const s of statements)await s.run();db.exec('COMMIT');return [];}catch(e){db.exec('ROLLBACK');throw e;}}};
const worker=(await import('../dist/server/index.js')).default;
const seed=JSON.parse(readFileSync('data/seed.json','utf8'));
async function get(path){const r=await worker.fetch(new Request('https://example.invalid'+path),{DB:adapter});assert.equal(r.status,200,path);return r.json();}
const summary=await get('/api/summary');assert.equal(summary.coverage.completed,100000);assert.equal(summary.coverage.quarantined,13);
const quality=await get('/api/quality');assert.deepEqual(quality.verification,seed.verification);
const issues=await get('/api/issues');for(let i=0;i<issues.length;i++)for(const field of ['issue_id','rank','complaint_count','severity_sum','mean_severity','priority_score'])assert.equal(issues[i][field],seed.pack.ranking[i][field]);
assert.equal((await get('/api/integrity?page=100')).rows,13);
assert.equal((await worker.fetch(new Request('https://example.invalid/api/import',{method:'POST',body:'{}'}),{DB:adapter})).status,405);
const sizes=db.prepare('SELECT max(length(CAST(value AS BLOB))) AS n FROM analysis').get();assert.ok(sizes.n<2_000_000,'D1 value size');
console.log(JSON.stringify({coverage:summary.coverage,verification_roundtrip:quality.verification.length,rankings_match:true,import_endpoint_disabled:true,max_database_value_bytes:sizes.n}));db.close();
