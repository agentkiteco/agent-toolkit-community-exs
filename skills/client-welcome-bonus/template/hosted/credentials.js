import { Exness } from '../cloud/app/src/exness.js';
const encode = b => btoa(String.fromCharCode(...new Uint8Array(b)));
const decode = s => Uint8Array.from(atob(s), c=>c.charCodeAt(0));
async function key(env) {
 if (!/^[a-f0-9]{64}$/i.test(env.STUDIO_CREDENTIALS_KEY||'')) throw Error('Credential storage is not configured');
 return crypto.subtle.importKey('raw', Uint8Array.from(env.STUDIO_CREDENTIALS_KEY.match(/../g),h=>parseInt(h,16)), 'AES-GCM', false, ['encrypt','decrypt']);
}
export async function loadCredentials(env) {
 const row=await env.DB.prepare("SELECT v FROM meta WHERE k='credentials_v1'").first();
 if(!row) return null;
 const {iv,data}=JSON.parse(row.v);
 return JSON.parse(new TextDecoder().decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:decode(iv)},await key(env),decode(data))));
}
export async function saveCredentials(env, body) {
 const apiKey=String(body.api_key||'').trim(), secret=String(body.api_secret||'').trim();
 if(!apiKey||apiKey.length>1024||!/^\S+$/.test(apiKey)||!/^[a-f0-9]{128}$/i.test(secret)) throw Error('Enter an API key and a secret containing 128 hexadecimal characters.');
 const credentials={EXN_API_KEY:apiKey,EXN_API_SECRET:secret,EXN_API_HOST:'api.exness.com'};
 const profile=await new Exness(credentials).call('GET','/v1/partnership/partner/summary');
 if(!profile.uid)throw Error('The API did not return a partner profile.');
 const old=await env.DB.prepare("SELECT v FROM meta WHERE k='connected_partner'").first();
 if(old&&old.v!==profile.uid){const p=await env.DB.prepare('SELECT id FROM promos LIMIT 1').first();if(p)throw Error('This studio already has promotions for another partner. Use a separate studio.');}
 const iv=crypto.getRandomValues(new Uint8Array(12));
 const data=await crypto.subtle.encrypt({name:'AES-GCM',iv},await key(env),new TextEncoder().encode(JSON.stringify(credentials)));
 await env.DB.batch([
 env.DB.prepare("INSERT OR REPLACE INTO meta(k,v) VALUES('credentials_v1',?)").bind(JSON.stringify({iv:encode(iv),data:encode(data)})),
 env.DB.prepare("INSERT OR REPLACE INTO meta(k,v) VALUES('connected_partner',?)").bind(profile.uid),
 env.DB.prepare("DELETE FROM meta WHERE k IN ('wallet','partner_uid')")]);
 return {ok:true};
}
