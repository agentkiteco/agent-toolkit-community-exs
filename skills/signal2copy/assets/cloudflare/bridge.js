// Encrypted checkpoint CAS; reusable infrastructure, no application/broker decisions.
export const MAX_BYTES=1024*1024, CHUNK=60000;
export class Problem extends Error { constructor(message,status=400){super(message);this.status=status;} }
export async function digest(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(x=>x.toString(16).padStart(2,'0')).join('');}
async function read(tx){
 const head=await tx.get('head');if(!head)return {revision:0,ciphertext:null,mutation_id:null,keep_alive:false};
 const chunks=await tx.get(Array.from({length:head.chunks},(_,n)=>'state:'+n));
 const ciphertext=Array.from({length:head.chunks},(_,n)=>chunks.get('state:'+n)).join('');
 if(ciphertext.length!==head.bytes || await digest(ciphertext)!==head.sha256)throw new Problem('Stored checkpoint integrity failure',503);
 return {...head,ciphertext};
}
export async function restore(storage,instance){
 return storage.transaction(async tx=>{if(await tx.get('instance')!==instance)throw new Problem('Stale instance',409);return read(tx);});
}
export async function commit(storage,instance,body){
 if(!Number.isSafeInteger(body.expected_revision)||body.expected_revision<0 || typeof body.mutation_id!=='string'||!/^[-a-zA-Z0-9_]{8,128}$/.test(body.mutation_id))throw new Problem('Invalid checkpoint identity');
 if(typeof body.ciphertext!=='string'||!/^gAAAA[A-Za-z0-9_=-]+$/.test(body.ciphertext)||body.ciphertext.length>MAX_BYTES)throw new Problem('Invalid or oversized encrypted checkpoint',413);
 if(body.keep_alive!==undefined && typeof body.keep_alive!=='boolean')throw new Problem('Invalid execution keep-alive flag');
 const sha256=await digest(body.ciphertext);
 return storage.transaction(async tx=>{
  if(await tx.get('instance')!==instance)throw new Problem('Stale instance',409);
  const old=await tx.get('head');
  if(old?.mutation_id===body.mutation_id){if(old.sha256!==sha256||old.keep_alive!==!!body.keep_alive)throw new Problem('Checkpoint identity conflict',409);return {revision:old.revision,mutation_id:old.mutation_id};}
  if((old?.revision||0)!==body.expected_revision)throw new Problem('Stale checkpoint revision',409);
  const chunks=Math.ceil(body.ciphertext.length/CHUNK);
  for(let n=0;n<chunks;n++)await tx.put('state:'+n,body.ciphertext.slice(n*CHUNK,(n+1)*CHUNK));
  for(let n=chunks;n<(old?.chunks||0);n++)await tx.delete('state:'+n);
  const head={revision:body.expected_revision+1,mutation_id:body.mutation_id,sha256,bytes:body.ciphertext.length,chunks,keep_alive:!!body.keep_alive,at:new Date().toISOString()};
  await tx.put('head',head);return {revision:head.revision,mutation_id:head.mutation_id};
 });
}
export async function backup(storage,bucket){
 const state=await storage.transaction(read);if(!state.ciphertext)return {revision:0,backed_up:false};
 if(await storage.get('backup_revision')===state.revision)return {revision:state.revision,backed_up:true};
 await bucket.put('checkpoints/'+String(state.revision).padStart(12,'0')+'.json',JSON.stringify(state),{httpMetadata:{contentType:'application/json'}});
 await storage.put('backup_revision',state.revision);return {revision:state.revision,backed_up:true};
}

// Owner administration remains independent from resettable application checkpoints.
export async function adminRestore(storage,instance){
 return storage.transaction(async tx=>{if(await tx.get('instance')!==instance)throw new Problem('Stale instance',409);return await tx.get('owner_admin')||{revision:0,ciphertext:null};});
}
export async function adminCommit(storage,instance,b){
 if(!Number.isSafeInteger(b.expected_revision)||typeof b.mutation_id!=='string'||!/^[-a-zA-Z0-9_]{8,128}$/.test(b.mutation_id)||typeof b.ciphertext!=='string'||!/^gAAAA[A-Za-z0-9_=-]+$/.test(b.ciphertext)||b.ciphertext.length>65536)throw new Problem('Invalid owner checkpoint',400);
 const hash=await digest(b.ciphertext);
 return storage.transaction(async tx=>{
  if(await tx.get('instance')!==instance)throw new Problem('Stale instance',409);
  const old=await tx.get('owner_admin');
  if(old?.mutation_id===b.mutation_id){if(old.sha256!==hash)throw new Problem('Owner checkpoint identity conflict',409);return old;}
  if((old?.revision||0)!==b.expected_revision)throw new Problem('Stale owner revision',409);
  const next={revision:b.expected_revision+1,ciphertext:b.ciphertext,mutation_id:b.mutation_id,sha256:hash,at:new Date().toISOString()};await tx.put('owner_admin',next);return next;
 });
}
export async function resetApplication(storage,instance,b,bucket,drain){
 if(typeof b.request_id!=='string'||!/^[-a-zA-Z0-9_]{12,96}$/.test(b.request_id)||!Number.isSafeInteger(b.expected_revision)||b.acknowledge_broker_exposure!==true||typeof b.ciphertext!=='string'||!/^gAAAA[A-Za-z0-9_=-]+$/.test(b.ciphertext)||b.ciphertext.length>MAX_BYTES)throw new Problem('Invalid confirmed reset',400);
 const hash=await digest(b.ciphertext);
 const job=await storage.transaction(async tx=>{
  if(await tx.get('instance')!==instance)throw new Problem('Stale instance',409);
  const old=await tx.get('reset_job');
  if(old?.id===b.request_id){if(old.sha256!==hash||old.expected_revision!==b.expected_revision)throw new Problem('Reset identity conflict',409);return old;}
  const head=await tx.get('head');if((head?.revision||0)!==b.expected_revision)throw new Problem('Inventory revision changed',409);
  if(old&&old.phase!=='complete')throw new Problem('Another reset is unresolved',409);
  const next={id:b.request_id,expected_revision:b.expected_revision,sha256:hash,phase:'frozen',at:new Date().toISOString()};await tx.put('maintenance',true);await tx.put('reset_job',next);return next;
 });
 if(job.phase==='complete')return job;
 await drain();
 let cursor;
 do{const page=await bucket.list({prefix:'checkpoints/',...(cursor?{cursor}:{})});for(let n=0;n<page.objects.length;n+=100)await bucket.delete(page.objects.slice(n,n+100).map(o=>o.key));cursor=page.truncated?page.cursor:null;}while(cursor);
 const result=await commit(storage,instance,{expected_revision:b.expected_revision,mutation_id:'reset-'+b.request_id,ciphertext:b.ciphertext,keep_alive:false});
 return storage.transaction(async tx=>{
  if(await tx.get('instance')!==instance)throw new Problem('Stale reset instance',409);
  const current=await tx.get('reset_job');if(current.phase==='complete')return current;if(current.id!==b.request_id)throw new Problem('Reset job changed',409);
  const completed={...current,phase:'complete',revision:result.revision,epoch:(await tx.get('reset_epoch')||0)+1};await tx.put('reset_epoch',completed.epoch);await tx.put('reset_job',completed);await tx.delete('backup_revision');await tx.delete('maintenance');return completed;
 });
}
