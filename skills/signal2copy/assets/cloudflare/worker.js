import {DurableObject} from 'cloudflare:workers';
import {commit,restore,backup,digest,Problem,MAX_BYTES,adminRestore,adminCommit,resetApplication} from './bridge.js';
const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'no-store'}});
function authorized(request,token){return !!token && request.headers.get('Authorization')==='Bearer '+token;}
export class AppHost extends DurableObject {
 constructor(ctx,env){super(ctx,env);this.ctx=ctx;this.env=env;this.starting=null;this.backups=new Set();}
 async start(){
  if(this.ctx.container.running)return;
  if(this.starting)return this.starting;
  this.starting=(async()=>{
   const instance=crypto.randomUUID();await this.ctx.storage.put('instance',instance);
   this.ctx.container.start({image:this.ctx.container.images.base,enableInternet:true,instance:'lite',env:{
    APP_INSTANCE_ID:instance,CLOUD_BRIDGE_URL:this.env.PUBLIC_ORIGIN,CLOUD_BRIDGE_TOKEN:this.env.BRIDGE_TOKEN,
    STATE_KEY:this.env.STATE_KEY,INSTALLATION_INVITATION:this.env.INSTALLATION_INVITATION,OWNER_PASSWORD:this.env.OWNER_PASSWORD,
    INSTALLATION_MODE:this.env.INSTALLATION_MODE||'synthetic',NATIVE_GATEWAY:this.env.NATIVE_GATEWAY||'',NATIVE_PARTNERSHIP_ORIGIN:this.env.NATIVE_PARTNERSHIP_ORIGIN||'',PUBLIC_ORIGIN:this.env.PUBLIC_ORIGIN,APP_HOST:'0.0.0.0',APP_PORT:'8080',PYTHONDONTWRITEBYTECODE:'1'
   }});
   await this.ctx.container.setInactivityTimeout(125000);
   this.ctx.waitUntil(this.ctx.container.monitor().catch(()=>{}));
  })().finally(()=>{this.starting=null;});return this.starting;
 }
 async backupState(){if(await this.ctx.storage.get('maintenance'))throw new Problem('Backups frozen for maintenance',409);const promise=backup(this.ctx.storage,this.env.BACKUPS);this.backups.add(promise);try{return await promise;}finally{this.backups.delete(promise);}}
 async alarm(){
  if(await this.ctx.storage.get('maintenance'))return;
  try{await this.backupState();await this.ctx.storage.delete('backup_error');}catch{await this.ctx.storage.put('backup_error',true);}
  const head=await this.ctx.storage.get('head');
  if(head?.keep_alive){await this.start();await this.ctx.container.setInactivityTimeout(125000);await this.ctx.storage.setAlarm(Date.now()+60000);}
 }
 async fetch(request){
  try{
   const url=new URL(request.url),path=url.pathname;
   if(path.startsWith('/__bridge/')||path.startsWith('/__ops/')){
    if(!authorized(request,path.startsWith('/__ops/')?this.env.OPS_TOKEN:this.env.BRIDGE_TOKEN))return json({error:'Unauthorized'},401);
    if(path==='/__ops/status'&&request.method==='GET')return json({running:this.ctx.container.running,image:await this.ctx.container.inspect(),checkpoint:await this.ctx.storage.get('head')||null,backup_revision:await this.ctx.storage.get('backup_revision')||0,backup_error:!!await this.ctx.storage.get('backup_error')});
    if(path==='/__ops/backup'&&request.method==='POST')return json(await this.backupState());
    if(path==='/__ops/restart'&&request.method==='POST'){await this.ctx.container.destroy('Authorized isolated app restart');return json({stopped:true});}
    if(path==='/__ops/restore'&&request.method==='POST'){
     const b=await request.json();const head=await this.ctx.storage.get('head');
     if(b.confirm!=='RESTORE '+this.env.APP_NAME||b.acknowledge_broker_exposure!==true||!head||b.expected_revision!==head.revision||!/^checkpoints\/[0-9]{12}\.json$/.test(b.key))throw new Problem('Explicit current-revision restore confirmation required',409);
     const object=await this.env.BACKUPS.get(b.key);if(!object)throw new Problem('Backup not found',404);
     const saved=await object.json();
     if(saved.revision!==head.revision||saved.sha256!==head.sha256||await digest(saved.ciphertext)!==head.sha256)throw new Problem('Backup rollback or integrity mismatch; reconcile separately',409);
     await this.ctx.storage.transaction(async tx=>{const current=await tx.get('head');if(current.revision!==head.revision)throw new Problem('State changed before restore',409);await tx.put('maintenance',true);await tx.put('instance','restore-fenced');});
     try{
      await this.ctx.container.destroy('Authorized exact-revision checkpoint restore');
      const result=await commit(this.ctx.storage,'restore-fenced',{expected_revision:head.revision,mutation_id:crypto.randomUUID(),ciphertext:saved.ciphertext,keep_alive:saved.keep_alive});
      return json({...result,restored_from:b.key,rolled_back:false});
     }finally{await this.ctx.storage.delete('maintenance');}
    }
    const instance=request.headers.get('X-Instance-ID');if(!instance)return json({error:'Missing instance'},409);
    if(path==='/__bridge/admin/restore'&&request.method==='GET')return json(await adminRestore(this.ctx.storage,instance));
    if(path==='/__bridge/admin/commit'&&request.method==='POST'){
     const head=await adminCommit(this.ctx.storage,instance,await request.json());await this.env.BACKUPS.put('owner/'+String(head.revision).padStart(12,'0')+'.json',JSON.stringify(head));return json({revision:head.revision,mutation_id:head.mutation_id});
    }
    if(path==='/__bridge/reset'&&request.method==='POST'){
     const body=await request.json();if(body.confirm!=='RESET '+this.env.PUBLIC_ORIGIN)throw new Problem('Exact reset target required',409);
     return json(await resetApplication(this.ctx.storage,instance,body,this.env.BACKUPS,()=>Promise.all([...this.backups])));
    }
    if(path==='/__bridge/restore'&&request.method==='GET')return json(await restore(this.ctx.storage,instance));
    if(path==='/__bridge/commit'&&request.method==='POST'){
     if(await this.ctx.storage.get('maintenance'))throw new Problem('Application frozen for maintenance',409);
     const raw=await request.text();if(raw.length>MAX_BYTES+1024)return json({error:'Oversized checkpoint'},413);
     const result=await commit(this.ctx.storage,instance,JSON.parse(raw));
     if(await this.ctx.storage.getAlarm()===null)await this.ctx.storage.setAlarm(Date.now()+60000);
     return json(result);
    }
    return json({error:'Unknown protected operation'},404);
   }
   if(await this.ctx.storage.get('maintenance'))return json({error:'Restore maintenance in progress'},503);
   await this.start();
   let ready=false;
   for(let n=0;n<60;n++){
    try{const health=await this.ctx.container.getTcpPort(8080).fetch('http://container:8080/healthz');if(health.ok){ready=true;break;}}catch{}
    await new Promise(resolve=>setTimeout(resolve,250));
   }
   if(!ready)return json({error:'Application restoring; retry shortly'},503);
   const headers=new Headers(request.headers);headers.delete('X-Forwarded-Host');headers.delete('X-Instance-ID');headers.delete('X-Forwarded-Proto');
   headers.set('X-Forwarded-Host',new URL(this.env.PUBLIC_ORIGIN).host);headers.set('X-Forwarded-Proto','https');
   const forward=new Request('http://container:8080'+path+url.search,{method:request.method,headers,body:['GET','HEAD'].includes(request.method)?undefined:request.body,redirect:'manual'});
   return await this.ctx.container.getTcpPort(8080).fetch(forward);
  }catch(error){return json({error:error instanceof Problem?error.message:'Application/state operation unavailable'},error instanceof Problem?error.status:503);}
 }
}
export default {fetch(request,env){return env.APP_HOST.getByName('primary').fetch(request);}};
