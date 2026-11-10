import {compare} from '../tests/ai-match';
const [hi,lo,from,count,w]=process.argv.slice(2);if(w){const {hardWeights}=await import('../src/engine/game');(globalThis as any).__HARDW={...hardWeights,...JSON.parse(w)};}
const seeds=Array.from({length:+count},(_,i)=>+from+i);
const t=Date.now();console.log(hi,'vs',lo,JSON.stringify(await compare(hi,lo,seeds,process.env.MIRROR==='1')),((Date.now()-t)/1000).toFixed(0)+'s');
