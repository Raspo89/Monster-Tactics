import {it,expect,describe} from 'vitest';
import {newGame,applyAction,chooseAI,legalActions,leader,effectiveStats,key} from '../src/engine/game';
import {aiDeck} from '../src/engine/progression';
import {buildMaps,nativeEvaluate,nativePlan} from '../src/engine/native-ai';

const start=(seed=701)=>{let s=newGame(seed,aiDeck('orc','hard'),'orc',aiDeck('elf','hard'),'elf','river',true,'standard',true);while(s.phase==='mulligan')s=applyAction(s,{kind:'mulligan',indexes:[]});return s;};

describe('original AI port (CAIWorker_BruteForce)',()=>{
 it('every action of its plan is legal when it is played, and a whole game finishes',()=>{
  let s=start(),n=0;
  while(s.winner===undefined&&n<1500){const a=chooseAI(s,s.current===0?'native:800':'native:400');if(a.kind!=='endTurn'){const legal=legalActions(s).map(x=>JSON.stringify(x));expect(legal).toContain(JSON.stringify(a));}s=applyAction(s,a,true);n++;}
  expect(s.winner).not.toBeUndefined();
 },120000);
 it('values a dead enemy monster and a wounded enemy hero like the original (enemy creatures count against it)',()=>{
  const s=start(),owner=s.current,maps=buildMaps(s,owner),base=nativeEvaluate(s,owner,maps);
  const hurt=structuredClone(s);leader(hurt,1-owner)!.health-=5;
  expect(nativeEvaluate(hurt,owner,maps)).toBeCloseTo(base+15,5);
  const enemy=s.units.find(u=>u.owner!==owner&&!u.isLeader);
  if(enemy){const gone=structuredClone(s);gone.units=gone.units.filter(u=>u.uid!==enemy.uid);expect(nativeEvaluate(gone,owner,maps)).toBeGreaterThan(base);}
 });
 it('threat map: enemies cover the cells they can hit, half one step beyond',()=>{
  const s=start(),owner=s.current,maps=buildMaps(s,owner),e=leader(s,1-owner)!,P=Math.max(1,effectiveStats(s,e).attack);
  const near=s.units.length&&[...maps.threat.keys()].length;expect(near).toBeGreaterThan(0);
  expect(maps.threat.get(key(e.pos))||0).toBeLessThan(P*s.units.length+1);
 });
 it('ends its turn when nothing beats the current board',()=>{
  const s=start();s.players[s.current].energy=0;s.players[s.current].hand=[];for(const u of s.units)if(u.owner===s.current){u.moved=true;u.attacked=true;u.movesUsed=9;u.summoned=true;}
  expect(nativePlan(s,200)[0].kind).toBe('endTurn');
 });
});
