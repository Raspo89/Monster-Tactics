import {chooseAI,type Action,type GameState} from '../engine/game';
// Asks the background worker for the computer's next action; falls back to thinking on the main thread
// if workers are unavailable (old WebViews) or the worker fails.
let worker:Worker|null|undefined,seq=0;const waiting=new Map<number,(r:{action?:Action,error?:string})=>void>();
function getWorker(){if(worker!==undefined)return worker;try{worker=new Worker(new URL('../engine/ai-worker.ts',import.meta.url),{type:'module'});worker.onmessage=e=>{const f=waiting.get(e.data.id);if(f){waiting.delete(e.data.id);f(e.data);}};worker.onerror=()=>{worker?.terminate();worker=null;for(const f of waiting.values())f({error:'worker'});waiting.clear();};}catch{worker=null;}return worker;}
export function thinkAsync(state:GameState,level:string):Promise<Action>{
 const w=getWorker();if(!w)return new Promise(r=>setTimeout(()=>r(chooseAI(state,level)),0));
 const id=++seq;return new Promise(resolve=>{waiting.set(id,r=>resolve(r.action||chooseAI(state,level)));try{w.postMessage({id,state,level});}catch{waiting.delete(id);resolve(chooseAI(state,level));}});}
