/**
 * Moving progress between devices. Every device keeps its own save in the browser (localStorage), and the game has
 * no server, so progress travels as a "save code": the game's own keys (mt-*) as JSON, gzip-compressed when the
 * browser can, then base64url. The code starts with MT1: (gzip) or MT0: (plain).
 * 7.33: M2 codes are about 8x shorter: match receipts are left out (they only guard the running battle, which never
 * travels), card ids become their index in the game's card table (base 36), and the JSON is raw-deflated. The code
 * carries a fingerprint of the card table, so two different game versions refuse each other's codes instead of
 * mixing cards up. Old MT1/MT0 codes still load.
 */
import {cardById} from '../engine/game';
const PREFIX='mt-';
/** The running battle is left out: it is large and belongs to the device it was played on. */
const SKIP=new Set(['mt-battle']);
export type SaveBundle={v:1,at:string,data:Record<string,string>};
const toB64=(bytes:Uint8Array)=>{let s='';for(let i=0;i<bytes.length;i+=0x8000)s+=String.fromCharCode(...bytes.subarray(i,i+0x8000));return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');};
const fromB64=(text:string)=>{const b=atob(text.replace(/-/g,'+').replace(/_/g,'/'));const out=new Uint8Array(b.length);for(let i=0;i<b.length;i++)out[i]=b.charCodeAt(i);return out;};
async function pipe(bytes:Uint8Array,stream:CompressionStream|DecompressionStream){const out=new Response(new Blob([bytes as BlobPart]).stream().pipeThrough(stream));return new Uint8Array(await out.arrayBuffer());}
export function collectSave(storage:Storage=localStorage):SaveBundle{const data:Record<string,string>={};for(let i=0;i<storage.length;i++){const k=storage.key(i)!;if(k.startsWith(PREFIX)&&!SKIP.has(k))data[k]=storage.getItem(k)!;}return {v:1,at:new Date().toISOString(),data};}
const ids=Object.keys(cardById).sort(),index=new Map(ids.map((id,i)=>[id,i]));
const FP=(()=>{let h=2166136261;for(const c of ids.join(',')){h^=c.charCodeAt(0);h=Math.imul(h,16777619)>>>0;}return (h%1679616).toString(36).padStart(4,'0');})();
const tok=(id:string)=>index.has(id)?index.get(id)!.toString(36):'~'+id;
const untok=(t:string)=>t.startsWith('~')?t.slice(1):ids[parseInt(t,36)];
const packList=(l:string[])=>l.map(tok).join('.');
const unpackList=(s:string)=>s?s.split('.').map(untok):[];
const packInv=(inv:Record<string,number>)=>Object.entries(inv).map(([id,n])=>tok(id)+(n===1?'':'*'+n)).join('.');
const unpackInv=(s:string)=>Object.fromEntries((s?s.split('.'):[]).map(t=>{const [a,n]=t.split('*');return [untok(a),n?+n:1];}));
function compact(bundle:SaveBundle){const other:Record<string,string>={},out:any={v:2,o:other,t:Math.round((Date.parse(bundle.at)||Date.now())/1000).toString(36)};for(const [k,v] of Object.entries(bundle.data)){
  try{if(k==='mt-profile-v7'){const p=JSON.parse(v);if(p&&typeof p==='object'){p.receipts={};if(p.inventory)p.inventory=packInv(p.inventory);if(Array.isArray(p.starterDeck))p.starterDeck=packList(p.starterDeck);out.p=p;continue;}}
   if(k==='mt-saved-decks'){const d=JSON.parse(v);if(Array.isArray(d)){out.k=d.map((x:any)=>Array.isArray(x?.cards)?{...x,cards:packList(x.cards)}:x);continue;}}}catch{}
  other[k]=v;}return out;}
function expand(c:any):SaveBundle{const data:Record<string,string>={...c.o};if(c.p){const p={...c.p};if(typeof p.inventory==='string')p.inventory=unpackInv(p.inventory);if(typeof p.starterDeck==='string')p.starterDeck=unpackList(p.starterDeck);data['mt-profile-v7']=JSON.stringify(p);}
 if(c.k)data['mt-saved-decks']=JSON.stringify(c.k.map((x:any)=>typeof x?.cards==='string'?{...x,cards:unpackList(x.cards)}:x));return {v:1,at:c.t?new Date(parseInt(c.t,36)*1000).toISOString():new Date().toISOString(),data};}
export async function encodeSave(bundle:SaveBundle){if(typeof CompressionStream!=='undefined'){try{return 'M2'+FP+':'+toB64(await pipe(new TextEncoder().encode(JSON.stringify(compact(bundle))),new CompressionStream('deflate-raw')));}catch{}}return encodeSaveV1(bundle);}
export async function encodeSaveV1(bundle:SaveBundle){const bytes=new TextEncoder().encode(JSON.stringify(bundle));if(typeof CompressionStream!=='undefined'){try{return 'MT1:'+toB64(await pipe(bytes,new CompressionStream('gzip')));}catch{}}return 'MT0:'+toB64(bytes);}
export async function decodeSave(code:string):Promise<SaveBundle>{const text=code.replace(/\s+/g,'');const m2=/^M2([0-9a-z]{4}):([A-Za-z0-9_-]+)$/.exec(text);if(m2){if(m2[1]!==FP)throw new Error('الرمز من نسخة ثانية من اللعبة — حدّث اللعبة في الجهازين وطلّع رمز جديد');if(typeof DecompressionStream==='undefined')throw new Error('المتصفح ما يقدر يفك هذا الرمز');let c:any;try{c=JSON.parse(new TextDecoder().decode(await pipe(fromB64(m2[2]),new DecompressionStream('deflate-raw'))));}catch{throw new Error('رمز الحفظ تالف');}if(c?.v!==2||typeof c.o!=='object')throw new Error('رمز الحفظ تالف');const b=expand(c);for(const [k,v] of Object.entries(b.data))if(!k.startsWith(PREFIX)||typeof v!=='string')throw new Error('رمز الحفظ تالف');return b;}const m=/^MT([01]):([A-Za-z0-9_-]+)$/.exec(text);if(!m)throw new Error('هذا مو رمز حفظ من اللعبة');let bytes=fromB64(m[2]);if(m[1]==='1'){if(typeof DecompressionStream==='undefined')throw new Error('المتصفح ما يقدر يفك هذا الرمز');bytes=await pipe(bytes,new DecompressionStream('gzip'));}const bundle=JSON.parse(new TextDecoder().decode(bytes));if(bundle?.v!==1||typeof bundle.data!=='object')throw new Error('رمز الحفظ تالف');for(const [k,v] of Object.entries(bundle.data))if(!k.startsWith(PREFIX)||typeof v!=='string')throw new Error('رمز الحفظ تالف');return bundle;}
/** Replaces this device's save with the bundle (the running battle is cleared too). */
export function applySave(bundle:SaveBundle,storage:Storage=localStorage){const old:string[]=[];for(let i=0;i<storage.length;i++){const k=storage.key(i)!;if(k.startsWith(PREFIX))old.push(k);}for(const k of old)storage.removeItem(k);for(const [k,v] of Object.entries(bundle.data))storage.setItem(k,v);}
