import { handleApi } from '../cloud/app/src/index.js';
import { assets } from './assets.js';
import { ApiError } from '../cloud/app/src/exness.js';
import { EngineError } from '../cloud/app/src/engine.js';
import { loadCredentials, saveCredentials } from './credentials.js';
// Access is enforced by the owner-only Sites policy, without a second app login.
export default {
 async fetch(request, env) {
  const url = new URL(request.url);
  if (url.pathname.startsWith('/api/')) {
   const write=request.method!=='GET';
   if(write&&(request.headers.get('x-studio')!=='1'||(request.headers.get('origin')&&request.headers.get('origin')!==url.origin))) return Response.json({detail:'Forbidden'},{status:403});
   const json=(data,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store'}});
   if(url.pathname==='/api/settings/credentials') {
    if(request.method!=='POST')return json({detail:'Method not allowed'},405);
    try{return json(await saveCredentials(env,await request.json()));}
    catch(e){return json({detail:e.status?'Exness rejected the connection. Check the key, secret, report permissions and IP restrictions.':e.message},400);}
   }
   if (/\/(pay|autopay)$/.test(url.pathname)) return json({detail:'Money transfers and automatic payouts are not enabled in this version.'},403);
   try {
    const credentials=await loadCredentials(env);
    if(write&&url.pathname==='/api/promos') {const body=await request.clone().json();if(body.auto_pay)return json({detail:'Automatic payouts are not enabled in this version.'},400);}
    const response=await handleApi(request,{DB:env.DB,...credentials},{demo:!credentials});
    if(url.pathname==='/api/session') {const data=await response.json();return json({...data,payouts_enabled:false});}
    return response;
   } catch(e) {
    if(e instanceof ApiError) return json({detail:`Exness API HTTP ${e.status}: ${e.path || 'partner request'}.`},502);
    if(e instanceof EngineError) return json({detail:e.message},400);
    return json({detail:'An internal application error prevented loading this page.'},500);
   }
  }
  const asset=assets[url.pathname];
  if (!asset) return new Response('Not found',{status:404});
  return new Response(asset.body,{headers:{'Content-Type':asset.type,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin'}});
 }
};
