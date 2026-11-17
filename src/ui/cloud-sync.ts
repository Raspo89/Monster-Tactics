/**
 * 7.34: automatic save sync between devices through the owner's Firebase project (monster-tactics-68610).
 *
 * - Each device signs in anonymously (Identity Toolkit REST) and talks to Firestore over REST: no SDK in the bundle.
 * - A set of linked devices shares one document saves/{key}, key = 32 random characters that never leave the devices.
 *   The document holds the same save code as "export" (MT1 format: card ids spelled out, so two game versions never
 *   misread each other), the time it was written and which device wrote it.
 * - Linking a second device: the first one writes pair/{6 digits} -> key, valid for 10 minutes; the second reads it.
 * - Every write to a game key (mt-*, except the running battle) marks the device dirty and pushes a few seconds later.
 *   On start and whenever the game comes back to the foreground, the newer side wins: a newer remote save replaces
 *   the local one (then the page reloads); local changes made offline after the last sync are pushed instead.
 * Firestore rules (in the console) only let signed-in devices touch saves/{key} with a key of 24+ characters.
 */
import {collectSave,encodeSaveV1,decodeSave,applySave} from './save-transfer';

const CFG={apiKey:'AIzaSyBp9wnBADU85xTdHOpAzsyYYrUVPQqKZcM',projectId:'monster-tactics-68610'};
const DOCS=`https://firestore.googleapis.com/v1/projects/${CFG.projectId}/databases/(default)/documents`;
const STATE_KEY='monster-sync',AUTH_KEY='monster-sync-auth';
type SyncState={key:string,dev:string,syncedAt:number,dirtyAt?:number,lastOk?:number};
type Auth={idToken:string,refreshToken:string,exp:number};
const rnd=(n:number,abc='ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789')=>Array.from(crypto.getRandomValues(new Uint32Array(n)),x=>abc[x%abc.length]).join('');
const read=<T>(k:string):T|undefined=>{try{const v=localStorage.getItem(k);return v?JSON.parse(v):undefined;}catch{return undefined;}};
const write=(k:string,v:unknown)=>{try{rawSet.call(localStorage,k,JSON.stringify(v));}catch{}};
const rawSet=Storage.prototype.setItem,rawRemove=Storage.prototype.removeItem;
export const syncState=()=>read<SyncState>(STATE_KEY);
let applying=false,pushTimer:any,onStatus:(s:string)=>void=()=>{};
export function onSyncStatus(fn:(s:string)=>void){onStatus=fn;}

async function auth():Promise<string>{let a=read<Auth>(AUTH_KEY);if(a&&a.exp>Date.now()+60000)return a.idToken;
 if(a?.refreshToken){const r=await fetch(`https://securetoken.googleapis.com/v1/token?key=${CFG.apiKey}`,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'grant_type=refresh_token&refresh_token='+encodeURIComponent(a.refreshToken)});
  if(r.ok){const j=await r.json();a={idToken:j.id_token,refreshToken:j.refresh_token,exp:Date.now()+(+j.expires_in)*1000};write(AUTH_KEY,a);return a.idToken;}}
 const r=await fetch(`https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${CFG.apiKey}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({returnSecureToken:true})});
 if(!r.ok)throw new Error('ما قدرت أتصل بخدمة المزامنة ('+r.status+')');const j=await r.json();a={idToken:j.idToken,refreshToken:j.refreshToken,exp:Date.now()+(+j.expiresIn)*1000};write(AUTH_KEY,a);return a.idToken;}
async function api(path:string,init:RequestInit={}){const t=await auth();const r=await fetch(DOCS+path,{...init,headers:{'Content-Type':'application/json',Authorization:'Bearer '+t,...(init.headers||{})}});return r;}
type Remote={d:string,at:number,dev:string};
async function getSave(key:string):Promise<Remote|null>{const r=await api('/saves/'+key);if(r.status===404)return null;if(!r.ok)throw new Error('المزامنة: '+r.status);const f=(await r.json()).fields||{};return {d:f.d?.stringValue||'',at:+(f.at?.integerValue||0),dev:f.dev?.stringValue||''};}
async function putSave(key:string,dev:string){const at=Date.now(),d=await encodeSaveV1(collectSave());const r=await api('/saves/'+key,{method:'PATCH',body:JSON.stringify({fields:{d:{stringValue:d},at:{integerValue:String(at)},dev:{stringValue:dev}}})});if(!r.ok)throw new Error('المزامنة: '+r.status);return at;}
async function applyRemote(s:SyncState,rem:Remote){const bundle=await decodeSave(rem.d);applying=true;try{applySave(bundle);}finally{applying=false;}write(STATE_KEY,{...s,syncedAt:rem.at,dirtyAt:undefined,lastOk:Date.now()});}

/** Push now (after a short debounce when called from a storage write). */
export async function pushNow(){const s=syncState();if(!s)return;clearTimeout(pushTimer);try{const at=await putSave(s.key,s.dev);write(STATE_KEY,{...s,syncedAt:at,dirtyAt:undefined,lastOk:Date.now()});onStatus('تمت المزامنة');}catch(e){onStatus((e as Error).message);}}
/** Compare with the cloud. Returns 'pulled' when the local save was replaced (the caller should reload). */
export async function syncNow(canApply=true):Promise<'pulled'|'pushed'|'same'|'off'>{const s=syncState();if(!s)return 'off';const rem=await getSave(s.key);
 if(!rem){await pushNow();return 'pushed';}
 if(rem.at>s.syncedAt&&rem.dev!==s.dev&&!(s.dirtyAt&&s.dirtyAt>rem.at)){if(!canApply)return 'same';await applyRemote(s,rem);return 'pulled';}
 if(s.dirtyAt||rem.at<s.syncedAt){await pushNow();return 'pushed';}
 write(STATE_KEY,{...s,lastOk:Date.now()});return 'same';}

/** First device: start a new cloud save from this device's progress. */
export async function enableSync(){const s:SyncState={key:rnd(32),dev:rnd(10),syncedAt:0};write(STATE_KEY,s);await pushNow();if(!syncState()?.lastOk){rawRemove.call(localStorage,STATE_KEY);throw new Error('ما قدرت أرفع الحفظ، تأكد من الإنترنت');}}
/** A 6-digit code another device can type within 10 minutes. */
export async function makePairCode(){const s=syncState();if(!s)throw new Error('شغّل المزامنة أول');for(let i=0;i<5;i++){const code=String(100000+(crypto.getRandomValues(new Uint32Array(1))[0]%900000));
  const r=await api('/pair?documentId='+code,{method:'POST',body:JSON.stringify({fields:{key:{stringValue:s.key},at:{integerValue:String(Date.now())}}})});if(r.ok)return code;if(r.status!==409)throw new Error('المزامنة: '+r.status);}
 throw new Error('جرّب مرة ثانية');}
/** Second device: join with the code, then take the cloud save. */
export async function joinWithCode(code:string){code=code.replace(/\D/g,'');if(code.length!==6)throw new Error('الرقم لازم يكون 6 أرقام');const r=await api('/pair/'+code);if(r.status===404)throw new Error('الرقم غلط أو انتهى، اطلب رقم جديد');if(!r.ok)throw new Error('المزامنة: '+r.status);
 const f=(await r.json()).fields||{};const key=f.key?.stringValue,at=+(f.at?.integerValue||0);if(!key||Date.now()-at>10*60000)throw new Error('الرقم انتهى، اطلب رقم جديد من الجهاز الأول');
 void api('/pair/'+code,{method:'DELETE'}).catch(()=>{});const s:SyncState={key,dev:rnd(10),syncedAt:0};write(STATE_KEY,s);const rem=await getSave(key);if(rem){await applyRemote(s,rem);return 'pulled';}await pushNow();return 'pushed';}
export function disableSync(){rawRemove.call(localStorage,STATE_KEY);}

/** Watch game-key writes so every change gets pushed, and sync on start / when the game comes back to the front. */
export function startSync(reload:()=>void,canApply:()=>boolean){
 Storage.prototype.setItem=function(k:string,v:string){rawSet.call(this,k,v);if(this===localStorage&&!applying&&k.startsWith('mt-')&&k!=='mt-battle')markDirty();};
 Storage.prototype.removeItem=function(k:string){rawRemove.call(this,k);if(this===localStorage&&!applying&&k.startsWith('mt-')&&k!=='mt-battle')markDirty();};
 const check=()=>{if(!syncState()||!navigator.onLine)return;syncNow(canApply()).then(r=>{if(r==='pulled')reload();}).catch(e=>onStatus((e as Error).message));};
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')check();else if(syncState()?.dirtyAt)void pushNow();});
 window.addEventListener('online',check);check();}
function markDirty(){const s=syncState();if(!s)return;write(STATE_KEY,{...s,dirtyAt:Date.now()});clearTimeout(pushTimer);pushTimer=setTimeout(()=>void pushNow(),4000);}
