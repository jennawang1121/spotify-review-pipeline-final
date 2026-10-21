// Temporary import endpoint: deploy only while the Site is owner-private.
// Remove this handler before enabling public access.
async function importRows(request,env){
  if(request.method!=="POST")return json({error:"POST required"},405);
  const body=await request.json();
  if(body.revision!==revision()||!Array.isArray(body.rows)||body.rows.length>100)return json({error:"Invalid batch"},400);
  for(const r of body.rows){
    if(!r.review_id||!/^[a-f0-9]{64}$/.test(r.source_sha256)||!r.source||!["completed","quarantined"].includes(r.status))return json({error:"Invalid record"},400);
    if(r.status==="completed"&&(!r.prediction||r.provenance?.kind!=="provider_response"))return json({error:"Missing real classification"},400);
  }
  await env.DB.batch(body.rows.map(r=>{
    const p=r.prediction;
    return env.DB.prepare("INSERT OR IGNORE INTO reviews(dataset_id,review_id,source_hash,source_json,prediction_json,status,topic,intent,severity,needs_review) VALUES(?,?,?,?,?,?,?,?,?,?)")
      .bind(revision(),r.review_id,r.source_sha256,JSON.stringify(r.source),p?JSON.stringify({prediction:p,provenance:r.provenance,cache_source_id:r.cache_source_id,label_config:r.label_config}):null,r.status,p?.topic??null,p?.intent??null,p?.severity??null,p?Number(p.needs_review):null);
  }));
  return json({accepted:body.rows.length,revision:revision()});
}
