import {it,expect} from 'vitest';
import {newGame,applyAction,chooseAI,useStructuredClone,type GameState} from '../src/engine/game';
import {aiDeck} from '../src/engine/progression';
// The fast state copy must behave exactly like structuredClone: same games, and the previous state is never touched.
function play(seed:number,race:[string,string],map:string,fast:boolean){useStructuredClone(!fast);const out:string[]=[];
 let s=newGame(seed,aiDeck(race[0],'hard'),race[0],aiDeck(race[1],'expert'),race[1],map,true,'standard',true);let n=0;
 while(s.winner===undefined&&n<500){const a=s.phase==='mulligan'?{kind:'mulligan',indexes:[]} as any:chooseAI(s,'normal');const before=JSON.stringify(s);const t=applyAction(s,a,true);expect(JSON.stringify(s)).toBe(before);out.push(JSON.stringify(t.units)+JSON.stringify(t.players)+JSON.stringify(t.runeStands)+JSON.stringify(t.tileEffects)+JSON.stringify(t.tokens));s=t;n++;}
 useStructuredClone(false);return out;}
it('fast state copy plays the same games as structuredClone and never mutates the old state',()=>{
 for(const [seed,r,m] of [[11,['human','orc'],'river'],[12,['elf','zombie'],'towers'],[13,['orc','elf'],'desert']] as const){expect(play(seed,r as any,m,true)).toEqual(play(seed,r as any,m,false));}
},300000);
