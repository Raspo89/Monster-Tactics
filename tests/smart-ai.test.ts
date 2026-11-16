import {it,expect,describe} from 'vitest';
import {newGame,applyAction,chooseAI,legalActions,cloneForAI} from '../src/engine/game';
import {aiDeck} from '../src/engine/progression';
import {smartPlan} from '../src/engine/smart-ai';

const LEVEL='smart#{"budget":900,"cands":3,"replyBudget":400,"ghost":true}';
function start(seed=701,turns=6){
 let s=newGame(seed,aiDeck('orc','hard'),'orc',aiDeck('elf','hard'),'elf','river',true,'standard',true);
 while(s.phase==='mulligan')s=applyAction(s,{kind:'mulligan',indexes:[]});
 for(let n=0;n<turns*8&&s.winner===undefined&&s.turn<turns;n++)s=applyAction(s,chooseAI(s,'native:500'),true);
 return s;}

describe('advanced AI (lookahead on the original evaluation)',()=>{
 it('every action it plays is legal, and a whole game finishes',()=>{
  let s=start(702,1),n=0;
  while(s.winner===undefined&&n<1200){const a=chooseAI(s,s.current===0?LEVEL:'native:400');
   if(a.kind!=='endTurn'){const legal=legalActions(s).map(x=>JSON.stringify(x));expect(legal).toContain(JSON.stringify(a));}
   s=applyAction(s,a,true);n++;}
  expect(s.winner).not.toBeUndefined();
 },180000);

 it('never reads the opponent\'s hand: moving a card between their hand and deck does not change its plan',()=>{
  const s=start(703,6);
  const enemy=1-s.current,p=s.players[enemy];
  expect(p.hand.length).toBeGreaterThan(0);expect(p.deck.length).toBeGreaterThan(0);
  const a=JSON.stringify(smartPlan(s,{budget:900,cands:3,replyBudget:400,ghost:true}));
  const swapped=cloneForAI(s);                     // same cards unplayed, a different one held
  swapped.players[enemy]={...p,hand:[...p.hand.slice(1),p.deck[0]],deck:[p.hand[0],...p.deck.slice(1)]};
  const b=JSON.stringify(smartPlan(swapped,{budget:900,cands:3,replyBudget:400,ghost:true}));
  expect(b).toBe(a);
 },120000);

 it('ends the turn when there is nothing worth doing',()=>{
  const s=start(704,4);s.players[s.current].energy=0;s.players[s.current].hand=[];
  for(const u of s.units)if(u.owner===s.current){u.moved=true;u.attacked=true;u.movesUsed=9;u.summoned=true;}
  expect(smartPlan(s,{budget:300,cands:2,replyBudget:200})[0].kind).toBe('endTurn');
 },60000);
});
