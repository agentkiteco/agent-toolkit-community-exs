import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {commit,restore,backup,MAX_BYTES,adminCommit,adminRestore,resetApplication} from './bridge.js';
if(!globalThis.crypto)globalThis.crypto=webcrypto;
class Store{
 constructor(){this.map=new Map([['instance','instance-a']]);}
 async get(key){return Array.isArray(key)?new Map(key.map(k=>[k,this.map.get(k)])):this.map.get(key);}
 async put(key,value){this.map.set(key,structuredClone(value));}
 async delete(key){this.map.delete(key);}
 async transaction(fn){const saved=structuredClone(this.map);try{return await fn(this);}catch(e){this.map=saved;throw e;}}
}
const body=(rev=0,id='mutation-0001')=>({expected_revision:rev,mutation_id:id,ciphertext:'gAAAA'+ 'a'.repeat(120000),keep_alive:true});
test('nonempty multi-chunk restore, duplicate ack and conflict preserve revision',async()=>{
 const s=new Store(),b=body();const ack=await commit(s,'instance-a',b);assert.equal(ack.revision,1);
 assert.deepEqual(await commit(s,'instance-a',b),ack);assert.equal((await restore(s,'instance-a')).ciphertext,b.ciphertext);
 await assert.rejects(commit(s,'instance-a',{...b,ciphertext:b.ciphertext+'b'}),{status:409});
 await assert.rejects(commit(s,'instance-a',body(0,'mutation-0002')),{status:409});
 assert.equal((await restore(s,'instance-a')).revision,1);
});
test('stale instance denied after restart, newest instance restores same nonempty state',async()=>{
 const s=new Store();await commit(s,'instance-a',body());await s.put('instance','instance-b');
 await assert.rejects(commit(s,'instance-a',body(1,'mutation-0002')),{status:409});
 await assert.rejects(restore(s,'instance-a'),{status:409});
 assert.equal((await restore(s,'instance-b')).mutation_id,'mutation-0001');
});
test('size/shape/integrity fail closed and backup contains encrypted payload only',async()=>{
 const s=new Store();await assert.rejects(commit(s,'instance-a',{...body(),ciphertext:'gAAAA'+'a'.repeat(MAX_BYTES)}),{status:413});
 await assert.rejects(commit(s,'instance-a',{...body(),ciphertext:'plaintext'}),{status:413});
 await commit(s,'instance-a',body());const objects=new Map();const bucket={put:async(k,v)=>objects.set(k,v)};
 await backup(s,bucket);await backup(s,bucket);assert.equal(objects.size,1);
 assert.equal(JSON.parse([...objects.values()][0]).ciphertext,body().ciphertext);
 await s.put('state:0','tampered');await assert.rejects(restore(s,'instance-a'),{status:503});
});

test('independent owner checkpoint survives drained idempotent application reset and old revision is fenced',async()=>{
 const s=new Store(),objects=new Map();const bucket={put:async(k,v)=>objects.set(k,v),list:async({prefix})=>({objects:[...objects.keys()].filter(k=>k.startsWith(prefix)).map(key=>({key})),truncated:false}),delete:async(keys)=>keys.forEach(k=>objects.delete(k))};
 await commit(s,'instance-a',body());await backup(s,bucket);
 const owner=await adminCommit(s,'instance-a',{expected_revision:0,mutation_id:'owner-00000001',ciphertext:'gAAAA'+'x'.repeat(100)});await bucket.put('owner/000000000001.json',JSON.stringify(owner));
 let drained=false;const b={request_id:'reset-0000000001',expected_revision:1,ciphertext:'gAAAA'+'e'.repeat(100),acknowledge_broker_exposure:true};
 const result=await resetApplication(s,'instance-a',b,bucket,async()=>{assert.equal(await s.get('maintenance'),true);drained=true;});
 assert.equal(drained,true);assert.equal(result.phase,'complete');assert.equal(result.revision,2);assert.equal((await restore(s,'instance-a')).ciphertext,b.ciphertext);assert.equal((await adminRestore(s,'instance-a')).ciphertext,owner.ciphertext);assert.equal(objects.has('owner/000000000001.json'),true);assert.equal([...objects.keys()].some(k=>k.startsWith('checkpoints/')),false);
 assert.deepEqual(await resetApplication(s,'instance-a',b,bucket,async()=>{throw Error('must not drain twice')}),result);await assert.rejects(commit(s,'instance-a',body(1,'stale-after-reset')),{status:409});await assert.rejects(resetApplication(s,'instance-a',{...b,ciphertext:b.ciphertext+'x'},bucket,async()=>{}),{status:409});
});
