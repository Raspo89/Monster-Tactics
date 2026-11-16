/**
 * The advanced opponent (7.22). It thinks with the original game's own evaluation — the one ported in native-ai.ts —
 * and then does the thing the original never does: it plays the opponent's answer before committing.
 *
 * For each of the best turns it can find, it ends the turn, lets the opponent take its best turn in reply (the same
 * original-style search, run for the other side), and scores the board that comes out of it. The turn with the best
 * board *after the reply* wins, so a plan that wins material now and loses the hero next turn is rejected.
 *
 * It never looks at the opponent's hand: the reply is played with the opponent's hand emptied, so only what is on the
 * board can influence the plan.
 */
import {GameState,Action,applyAction,cloneForAI,mix} from './game';
import {buildMaps,nativeEvaluate,nativeSearch,pathOf,type NativeMaps,type NativeNode} from './native-ai';

export const smartStats:{nodes:number,candidates:number,ms:number,lastPlan:number,predicted:number,maps?:NativeMaps}={nodes:0,candidates:0,ms:0,lastPlan:0,predicted:0};

/** Positions whose boards differ only in spent moves are the same turn for our purposes; this key ignores those. */
function coarseKey(s:GameState){let k='';for(const u of s.units)k+=u.uid+':'+u.pos.q+','+u.pos.r+','+u.health+','+(u.weapon||'')+(u.armorItem||'')+(u.shieldItem||'')+(u.flaming?'f':'')+(u.poisoned?'p':'')+';';
 for(const p of s.players)k+=p.energy+'/'+p.hand.length+';';if(s.runeStands)for(const r of s.runeStands)k+=(r.cardId||'')+r.health+';';return k;}

/**
 * Plays the opponent's best answer to `state` and returns the board it leaves behind.
 * The real hand is never read. With `ghost` the opponent gets a hand of the right size drawn from the cards they have
 * not played yet, so the answer includes summons and spells; without it they answer with the board alone.
 */
function reply(state:GameState,owner:number,budget:number,timeMs:number,ghost:boolean):GameState{
 let t=applyAction(state,{kind:'endTurn'},true);
 if(t.winner!==undefined||t.current===owner)return t;
 const enemy=t.current;
 t=cloneForAI(t);const p=t.players[enemy];
 let hand:string[]=[];
 if(ghost){const pool=[...p.hand,...p.deck];let h=mix(state.seed,state.turn,pool.length,p.energy);for(let i=0;i<p.hand.length&&pool.length;i++){h=mix(h*4294967296,i+1);hand.push(pool.splice(Math.floor(h*pool.length),1)[0]);}}
 t.players[enemy]={...p,hand};t.log=[];t.events=[];
 const plan=nativeSearch(t,budget,timeMs);
 if(plan.best&&plan.best.score>plan.rootScore)for(const a of pathOf(plan.best)){const n=applyAction(t,a,true);if(n===t)break;t=n;t.log=[];t.events=[];if(t.winner!==undefined||t.current!==enemy)break;}
 smartStats.nodes+=plan.nodes;
 return t;}

/**
 * The advanced AI's plan for this turn.
 * `budget`/`replyBudget` are how many positions it may try for its own turn and for each answer it checks.
 */
export type SmartOpts={budget?:number,timeMs?:number,cands?:number,replyBudget?:number,ghost?:boolean,followBudget?:number,followWeight?:number,perFirst?:boolean,threatCharge?:boolean,shortlist?:number,scoutBudget?:number,blend?:number};
export function smartPlan(root:GameState,o:SmartOpts={}):Action[]{
 const budget=o.budget??12000,timeMs=o.timeMs??Infinity,cands=o.cands??8,replyBudget=o.replyBudget??2500,ghost=!!o.ghost,followBudget=o.followBudget??0,followWeight=o.followWeight??0,blend=o.blend??.002;
 const t0=Date.now(),owner=root.current;
 smartStats.nodes=0;smartStats.candidates=0;
 const maps:NativeMaps=buildMaps(root,owner);
 const search=nativeSearch(root,budget,timeMs*.55,maps,cands*3,true,o.threatCharge!==false);
 smartStats.nodes+=search.nodes;
 if(search.best&&search.best.s?.winner===owner){smartStats.lastPlan=pathOf(search.best).length;return pathOf(search.best);}
 /** What a candidate turn is really worth: the board left after the opponent's best answer to it. */
 const valueOf=(c:NativeNode,rb:number,ms:number)=>{
  const after=reply(c.s!,owner,rb,ms,ghost);smartStats.candidates++;
  let value;
  if(after.winner!==undefined)value=after.winner==='draw'?0:after.winner===owner?1e6:-1e6;
  else{value=nativeEvaluate(after,owner,maps);
   // Third half-move: what the best follow-up next turn would be worth, measured on the same yardstick.
   if(followBudget&&followWeight&&after.current===owner){const f=nativeSearch(after,followBudget,ms/2,maps);smartStats.nodes+=f.nodes;const top=f.best?Math.max(f.best.score,value):value;value=value*(1-followWeight)+top*followWeight;}}
  // The answer we simulate is only a guess, so the turn's own worth keeps a share of the vote: it steadies the
  // comparison when two candidates differ by less than the error in guessing the opponent's turn.
  return value*(1-blend)+c.score*blend;
 };
 // Candidates: the most promising distinct turns, plus doing nothing at all.
 const picked:NativeNode[]=[],seen=new Set<string>();
 const pool=o.perFirst===false?search.top:[...search.top,...search.byFirst].sort((a,b)=>b.score-a.score);
 for(const n of pool){if(!n.s)continue;const k=coarseKey(n.s);if(seen.has(k))continue;seen.add(k);picked.push(n);if(picked.length>=cands)break;}
 picked.push(search.root);
 // Two passes: a quick answer for every candidate turn, then a careful answer for the few that survive.
 const shortlist=o.shortlist??0,scoutBudget=o.scoutBudget??Math.max(400,Math.round(replyBudget/4));
 let list=picked;
 if(shortlist&&picked.length>shortlist){
  const ms=Math.max(60,(timeMs-(Date.now()-t0))*.35/picked.length);
  list=picked.map(c=>({c,v:valueOf(c,scoutBudget,ms)})).sort((a,b)=>b.v-a.v).slice(0,shortlist).map(x=>x.c);
 }
 const replyMs=Math.max(120,(timeMs-(Date.now()-t0))/Math.max(1,list.length));
 let best=search.root,bestValue=-Infinity;
 for(const c of list){
  const value=valueOf(c,replyBudget,replyMs);
  if(value>bestValue){bestValue=value;best=c;}
  if(timeMs!==Infinity&&Date.now()-t0>timeMs)break;
 }
 smartStats.ms=Date.now()-t0;smartStats.predicted=bestValue;smartStats.maps=maps;
 const plan=pathOf(best);smartStats.lastPlan=plan.length;
 return plan.length?plan:[{kind:'endTurn'}];}

const planCache=new Map<string,Action[]>();
const sig=(s:GameState)=>JSON.stringify([s.seed,s.turn,s.current,s.rng,s.nextUid,s.units,s.players.map(p=>[p.energy,p.hand,p.deck.length]),s.runeStands,s.tileEffects,s.tokens]);
/** Plays the plan one action at a time, and replans whenever the board is not what the plan expected. */
export function smartChoose(s:GameState,o:SmartOpts={}):Action{
 const k=sig(s);let plan=planCache.get(k);
 if(!plan)plan=smartPlan(s,o);
 planCache.clear();
 const a=plan[0]||{kind:'endTurn'};
 if(a.kind!=='endTurn'&&plan.length>1){const t=applyAction(s,a,true);if(t!==s)planCache.set(sig(t),plan.slice(1));}
 return a;}
