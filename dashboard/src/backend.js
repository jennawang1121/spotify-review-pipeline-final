const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"}});
const revision=()=>SEED.revision;
async function stored(db,key){const row=await db.prepare("SELECT value FROM analysis WHERE key=?").bind(revision()+":"+key).first();return row?JSON.parse(row.value):null;}
let initialization;
async function initialize(db){
  if(!initialization)initialization=seedDatabase(db).catch(error=>{initialization=null;throw error;});
  return initialization;
}
async function seedDatabase(db){
  if(!db)throw new Error("Database is unavailable");
  if(await stored(db,"ready"))return;
  // Schema-only Drizzle migrations run before deployment. This separately seeds
  // saved real results; interrupted batches resume idempotently on the next read.
  for(let offset=0;offset<SEED.reviews.length;offset+=50){
    await db.batch(SEED.reviews.slice(offset,offset+50).map(r=>{
      const p=r.prediction;
      return db.prepare("INSERT OR IGNORE INTO reviews(dataset_id,review_id,source_hash,source_json,prediction_json,status,topic,intent,severity,needs_review) VALUES(?,?,?,?,?,?,?,?,?,?)")
        .bind(revision(),r.review_id,r.source_sha256,JSON.stringify(r.source),p?JSON.stringify({prediction:p,provenance:r.provenance,cache_source_id:r.cache_source_id,label_config:r.label_config}):null,r.status,p?.topic??null,p?.intent??null,p?.severity??null,p?Number(p.needs_review):null);
    }));
  }
  for(const key of ["summary","memo","raw_memo","recommendation","names","pack","taxonomy","verification","final_scope"])
    await db.prepare("INSERT OR REPLACE INTO analysis(key,value) VALUES(?,?)").bind(revision()+":"+key,JSON.stringify(SEED[key])).run();
  const n=await db.prepare("SELECT COUNT(*) AS n FROM reviews WHERE dataset_id=?").bind(revision()).first();
  if(n.n!==SEED.reviews.length)throw new Error("Database coverage mismatch");
  await db.prepare("INSERT OR REPLACE INTO analysis(key,value) VALUES(?,?)").bind(revision()+":ready",JSON.stringify({count:n.n,revision:revision()})).run();
}
function mean(sum,count){const s=BigInt(sum)*1000000n,c=BigInt(count);const n=(s+c/2n)/c;return (n/1000000n).toString()+"."+(n%1000000n).toString().padStart(6,"0");}
async function api(request,env,url){
  if(request.method!=="GET")return json({error:"Read-only endpoint"},405);
  await initialize(env.DB);
  const db=env.DB;
  if(url.pathname==="/api/summary"){
    const row=await db.prepare("SELECT COUNT(*) AS total,SUM(status='completed') AS completed,SUM(status='pending') AS pending,SUM(status='quarantined') AS quarantined,SUM(needs_review=1) AS needs_review FROM reviews WHERE dataset_id=?").bind(revision()).first();
    return json({coverage:row,experiment:await stored(db,"summary"),scope:await stored(db,"final_scope"),database:{revision:revision(),source:"D1 SQL queries over saved processed records"}});
  }
  if(url.pathname==="/api/issues"){
    const data=await db.prepare("SELECT topic,COUNT(*) AS complaint_count,SUM(severity) AS severity_sum FROM reviews WHERE dataset_id=? AND status='completed' AND intent IN ('complaint','cancellation') GROUP BY topic ORDER BY severity_sum DESC,topic ASC").bind(revision()).all();
    const names=(await stored(db,"names")).issues;
    return json(data.results.map((r,i)=>({...r,issue_id:"issue-"+r.topic,name:names.find(x=>x.issue_id==="issue-"+r.topic)?.name??r.topic,priority_score:r.severity_sum,mean_severity:mean(r.severity_sum,r.complaint_count),rank:i+1})));
  }
  if(url.pathname==="/api/reviews"){
    const topic=url.searchParams.get("topic"),intent=url.searchParams.get("intent"),query=url.searchParams.get("q")??"";
    const page=Math.max(1,Math.min(10000,parseInt(url.searchParams.get("page")??"1",10)||1));
    let where="dataset_id=?";const values=[revision()];
    if(topic){where+=" AND topic=?";values.push(topic);}
    if(intent){where+=" AND intent=?";values.push(intent);}
    if(query){where+=" AND (review_id LIKE ? ESCAPE '\\' OR source_json LIKE ? ESCAPE '\\')";const q="%"+query.replace(/[\\%_]/g,"\\$&")+"%";values.push(q,q);}
    const count=await db.prepare("SELECT COUNT(*) AS n FROM reviews WHERE "+where).bind(...values).first();
    const data=await db.prepare("SELECT review_id,source_hash,source_json,prediction_json,status FROM reviews WHERE "+where+" ORDER BY review_id LIMIT ? OFFSET ?").bind(...values,20,(page-1)*20).all();
    return json({total:count.n,page,page_size:20,rows:data.results.map(r=>({review_id:r.review_id,source_sha256:r.source_hash,source:JSON.parse(r.source_json),status:r.status,...JSON.parse(r.prediction_json??"{}")}))});
  }
  if(url.pathname.startsWith("/api/reviews/")){
    const id=decodeURIComponent(url.pathname.slice(13));
    const r=await db.prepare("SELECT * FROM reviews WHERE dataset_id=? AND review_id=?").bind(revision(),id).first();
    return r?json({review_id:r.review_id,source_sha256:r.source_hash,source:JSON.parse(r.source_json),status:r.status,...JSON.parse(r.prediction_json??"{}") }):json({error:"Review not found"},404);
  }
  if(url.pathname==="/api/recommendation")return json({memo:await stored(db,"memo"),raw_memo:await stored(db,"raw_memo"),structured:await stored(db,"recommendation"),pack:await stored(db,"pack"),student_review_pending:true});
  if(url.pathname==="/api/quality")return json({verification:await stored(db,"verification"),taxonomy:await stored(db,"taxonomy"),summary:(await stored(db,"summary")).quality});
  return json({error:"Endpoint not found"},404);
}
export default {
  async fetch(request,env){
    const url=new URL(request.url);
    if(url.pathname.startsWith("/api/")){
      try{return await api(request,env,url);}catch(error){console.error("Saved-data query failed",error.message);return json({error:"Saved data is temporarily unavailable. Please retry."},503);}
    }
    if(request.method!=="GET"&&request.method!=="HEAD")return new Response("Method not allowed",{status:405});
    const routes={"/": [HTML,"text/html"],"/client.js":[CLIENT,"application/javascript"],"/style.css":[CSS,"text/css"],"/favicon.svg":[`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#111c16"/><path d="M7 11h18M7 16h14M7 21h9" stroke="#73ed9c" stroke-width="3" stroke-linecap="round"/></svg>`,"image/svg+xml"]};
    const data=routes[url.pathname];if(!data)return new Response("Not found",{status:404});
    return new Response(request.method==="HEAD"?null:data[0],{headers:{"content-type":data[1]+"; charset=utf-8","x-content-type-options":"nosniff","content-security-policy":"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'self'"}});
  }
};
