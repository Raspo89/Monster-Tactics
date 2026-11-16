import {it,expect} from 'vitest';
import {newGame,cards,combatClass,canAttack,key,attackRange,type Unit} from '../src/engine/game';
import {aiDeck} from '../src/engine/progression';
// Original Combat Monsters has no line of sight: CMap::MarkTargetsIfInRange marks targets by hex distance only,
// so archers and mages shoot over rocks. The legacy ruleset keeps its rock blocking.
function setup(originalRules:boolean,cls:'archer'|'mage'){
 const s=newGame(5,aiDeck('human','hard'),'human',aiDeck('orc','hard'),'orc','plain',originalRules,'standard',true);s.phase='battle';
 const card=cards.find(c=>c.type==='unit'&&combatClass({cardId:c.id,isLeader:false} as Unit)===cls&&(c.attack??0)>0)!;
 const me:Unit={...s.units[0],uid:900,cardId:card.id,isLeader:false,owner:s.current,pos:{q:0,r:0},health:5,attacked:false,moved:false,movesUsed:0,summoned:false} as Unit;
 const foe:Unit={...s.units[1],uid:901,cardId:cards.find(c=>c.type==='unit'&&c.race==='orc')!.id,isLeader:false,owner:1-s.current,pos:{q:2,r:0},health:5} as Unit;
 s.units.push(me,foe);s.tiles[key({q:1,r:0})]='rock';delete s.tokens[key({q:1,r:0})];
 return {s,me,foe};}
for(const cls of ['archer','mage'] as const){
 it(`${cls} hits over a rock under the original rules`,()=>{const {s,me,foe}=setup(true,cls);expect(attackRange(s,me).max).toBeGreaterThanOrEqual(2);expect(canAttack(s,me,foe)).toBe(true);});
 it(`${cls} is still blocked by a rock in the legacy rules`,()=>{const {s,me,foe}=setup(false,cls);if(attackRange(s,me).max<2)return;expect(canAttack(s,me,foe)).toBe(false);});
}
