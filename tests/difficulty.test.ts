import {it,expect} from 'vitest';
import {compare} from './ai-match';
// Real games under the rules the app plays (original rules, round arena, the four starter decks).
// Each seed is played twice with the levels swapping seats, so race and first-player luck cancel out.
const seeds=(from:number,n:number)=>Array.from({length:n},(_,i)=>from+i);
it('normal clearly beats easy',async()=>{const r=await compare('normal','easy',seeds(700,12));console.log('normal vs easy',JSON.stringify(r));expect(r.rate).toBeGreaterThanOrEqual(.8);},600000);
it('hard clearly beats normal across race match-ups',async()=>{const r=await compare('hard','normal',seeds(700,16));console.log('hard vs normal',JSON.stringify(r));expect(r.rate).toBeGreaterThanOrEqual(.65);expect(r.sweeps).toBeGreaterThan(r.swept*3);},900000);
it('hard clearly beats normal in mirror matches',async()=>{const r=await compare('hard','normal',seeds(800,16),true);console.log('hard vs normal mirror',JSON.stringify(r));expect(r.rate).toBeGreaterThanOrEqual(.6);},900000);
it('hard crushes easy',async()=>{const r=await compare('hard','easy',seeds(900,6));console.log('hard vs easy',JSON.stringify(r));expect(r.rate).toBeGreaterThanOrEqual(.85);},900000);
