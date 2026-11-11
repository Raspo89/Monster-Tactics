/**
 * Moving progress between devices. Every device keeps its own save in the browser (localStorage), and the game has
 * no server, so progress travels as a "save code": the game's own keys (mt-*) as JSON, gzip-compressed when the
 * browser can, then base64url. The code starts with MT1: (gzip) or MT0: (plain).
 */
const PREFIX='mt-';
/** The running battle is left out: it is large and belongs to the device it was played on. */
const SKIP=new Set(['mt-battle']);
export type SaveBundle={v:1,at:string,data:Record<string,string>};
const toB64=(bytes:Uint8Array)=>{let s='';for(let i=0;i<bytes.length;i+=0x8000)s+=String.fromCharCode(...bytes.subarray(i,i+0x8000));return btoa(s).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');};
const fromB64=(text:string)=>{const b=atob(text.replace(/-/g,'+').replace(/_/g,'/'));const out=new Uint8Array(b.length);for(let i=0;i<b.length;i++)out[i]=b.charCodeAt(i);return out;};
async function pipe(bytes:Uint8Array,stream:CompressionStream|DecompressionStream){const out=new Response(new Blob([bytes as BlobPart]).stream().pipeThrough(stream));return new Uint8Array(await out.arrayBuffer());}
export function collectSave(storage:Storage=localStorage):SaveBundle{const data:Record<string,string>={};for(let i=0;i<storage.length;i++){const k=storage.key(i)!;if(k.startsWith(PREFIX)&&!SKIP.has(k))data[k]=storage.getItem(k)!;}return {v:1,at:new Date().toISOString(),data};}
export async function encodeSave(bundle:SaveBundle){const bytes=new TextEncoder().encode(JSON.stringify(bundle));if(typeof CompressionStream!=='undefined'){try{return 'MT1:'+toB64(await pipe(bytes,new CompressionStream('gzip')));}catch{}}return 'MT0:'+toB64(bytes);}
export async function decodeSave(code:string):Promise<SaveBundle>{const text=code.replace(/\s+/g,'');const m=/^MT([01]):([A-Za-z0-9_-]+)$/.exec(text);if(!m)throw new Error('هذا مو رمز حفظ من اللعبة');let bytes=fromB64(m[2]);if(m[1]==='1'){if(typeof DecompressionStream==='undefined')throw new Error('المتصفح ما يقدر يفك هذا الرمز');bytes=await pipe(bytes,new DecompressionStream('gzip'));}const bundle=JSON.parse(new TextDecoder().decode(bytes));if(bundle?.v!==1||typeof bundle.data!=='object')throw new Error('رمز الحفظ تالف');for(const [k,v] of Object.entries(bundle.data))if(!k.startsWith(PREFIX)||typeof v!=='string')throw new Error('رمز الحفظ تالف');return bundle;}
/** Replaces this device's save with the bundle (the running battle is cleared too). */
export function applySave(bundle:SaveBundle,storage:Storage=localStorage){const old:string[]=[];for(let i=0;i<storage.length;i++){const k=storage.key(i)!;if(k.startsWith(PREFIX))old.push(k);}for(const k of old)storage.removeItem(k);for(const [k,v] of Object.entries(bundle.data))storage.setItem(k,v);}
