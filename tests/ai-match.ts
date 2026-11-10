// Shared harness: plays real games under the rules the app uses (original rules, round arena, starter decks).
import {newGame,applyAction,chooseAI,GameState} from '../src/engine/game';
import {starterCards} from '../src/engine/progression';
export const RACES=['human','zombie','orc','elf'];
export const MAPS=['river','plain','towers','desert'];
export function playMatch(seed:number,levels:[string,string],mirror=false,maxActions=1500){
  const a=RACES[seed%4],b=mirror?a:RACES[Math.floor(seed/4)%4],map=MAPS[(mirror?Math.floor(seed/4):Math.floor(seed/16))%4];
  let s:GameState=newGame(1000+seed,starterCards(a),a,starterCards(b),b,map,true,'standard',true);
  let think=[0,0],moves=[0,0],max=0;
  for(let n=0;n<maxActions&&s.winner===undefined;n++){
    const who=s.current;
    if(s.phase==='mulligan'){s=applyAction(s,{kind:'mulligan',indexes:[]});continue;}
    const t=performance.now(),act=chooseAI(s,levels[who]);const dt=performance.now()-t;
    think[who]+=dt;moves[who]++;max=Math.max(max,dt);
    const next=applyAction(s,act,true);
    if(next===s&&act.kind!=='endTurn')throw new Error('AI chose an illegal action '+JSON.stringify(act));
    s=next;
    if(s.players.some(p=>p.energy<0))throw new Error('negative energy');
  }
  return {winner:s.winner,turns:s.turn,maxThink:max,avgThink:[think[0]/Math.max(1,moves[0]),think[1]/Math.max(1,moves[1])]};
}
/** Paired comparison: every seed is played twice with the two levels swapping seats. */
export async function compare(higher:string,lower:string,seeds:number[],mirror=false){
  let wins=0,losses=0,draws=0,max=0,turns=0,sweeps=0,swept=0;
  for(const seed of seeds){let pairWins=0;for(const seat of [0,1]){
    const levels:[string,string]=seat===0?[higher,lower]:[lower,higher];
    const r=playMatch(seed,levels,mirror);await new Promise(done=>setTimeout(done,0));max=Math.max(max,r.maxThink);turns+=r.turns;
    if(r.winner===seat){wins++;pairWins++;}else if(r.winner===1-seat)losses++;else draws++;
  }if(pairWins===2)sweeps++;if(pairWins===0)swept++;}
  return {wins,losses,draws,sweeps,swept,games:wins+losses+draws,rate:wins/(wins+losses+draws),maxThinkMs:Math.round(max),avgTurns:Math.round(turns/(seeds.length*2))};
}
