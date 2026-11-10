import {it,expect} from 'vitest';
import {newGame,starterDeck,applyAction,legalActions,spawn,offset,cards,leader,upgradeState,GameState} from '../src/engine/game';
import {afflict,afflictionDuration,cannotAttack,monsterAbilityActions} from '../src/engine/abilities';
const tag=(name:string)=>cards.find(c=>c.nativeTag===name)!.id;
function game(){let s=newGame(123,starterDeck('human',true),'human',starterDeck('orc',true),'orc','plain',true);s=applyAction(s,{kind:'mulligan',indexes:[]});s=applyAction(s,{kind:'mulligan',indexes:[]});s.current=0;s.tiles={};s.tokens={};s.players[0].energy=100;return s;}
function add(s:GameState,owner=0,id='H04'){const u=spawn(s,id,owner,offset(owner?4:3,3));u.summoned=false;u.moved=false;u.health=u.maxHealth=30;return u;}
function play(s:GameState,name:string,target?:{q:number,r:number}){s.players[s.current].energy=100;s.players[s.current].hand=[tag(name)];const a=legalActions(s).find(a=>a.kind==='playCard'&&(!target||a.target?.q===target.q&&a.target?.r===target.r));expect(a,name).toBeDefined();return applyAction(s,a!);}
const unit=(s:GameState,uid:number)=>s.units.find(u=>u.uid===uid)!;

for(const [name,status] of [['SPT_MAFF_STUN','stun'],['SPT_MAFF_ICEBLOCK','ice']]){
 it(`${name} blocks the enemy only for its native duration`,()=>{
  let s=game();const u=add(s,1);s=play(s,name,u.pos);
  expect(unit(s,u.uid).effects![status]).toBe(afflictionDuration(status));expect(cannotAttack(unit(s,u.uid))).toBe(true);
  s=applyAction(s,{kind:'endTurn'});expect(unit(s,u.uid).effects![status]).toBe(1);
  s=applyAction(s,{kind:'endTurn'});s=applyAction(s,{kind:'endTurn'});
  expect(unit(s,u.uid).effects?.[status]).toBeUndefined();expect(cannotAttack(unit(s,u.uid))).toBe(false);
 });
}
for(const [name,status] of [['SP_H_AFF_STUN','stun'],['SP_H_AFF_ICEBLOCK','ice']]){
 it(`${name} expires on both heroes instead of locking the match`,()=>{
  let s=play(game(),name);expect(s.units.filter(u=>u.isLeader).every(u=>cannotAttack(u))).toBe(true);
  for(let n=0;n<4;n++)s=applyAction(s,{kind:'endTurn'});
  for(const owner of [0,1])expect(leader(s,owner)!.effects?.[status]).toBeUndefined();
 });
}
it('repairing a 7.4 save restores finite durations without renewing valid or permanent statuses',()=>{
 const s=game(),u=add(s);u.effects={stun:-1,ice:-1,snare:1,vengeance:-1,berserk:-1};
 const next=upgradeState(JSON.parse(JSON.stringify(s)));
 expect(unit(next,u.uid).effects).toEqual({stun:2,ice:2,snare:1,vengeance:-1,berserk:-1});
 const before=JSON.stringify(next);upgradeState(next);expect(JSON.stringify(next)).toBe(before);
});
it('Berserk blocks attacks and special abilities now, then allows attacks on the next turn',()=>{
 let s=game();const c=cards.find(c=>c.abilityId==='AT_ENCOURAGE')!,u=add(s,0,c.id);add(s,1);
 s=play(s,'SPT_MAFF_BERSERK',u.pos);
 expect(unit(s,u.uid).effects?.berserk).toBe(-1);
 expect(legalActions(s).some(a=>(a.kind==='attack'||a.kind==='attackRune'||a.kind==='monsterAbility')&&a.uid===u.uid)).toBe(false);
 s=applyAction(s,{kind:'endTurn'});s=applyAction(s,{kind:'endTurn'});
 expect(unit(s,u.uid).attacked).toBe(false);expect(monsterAbilityActions(s,unit(s,u.uid)).length).toBeGreaterThan(0);
});
it('reapplying Berserk still blocks the attack when the monster already has the status',()=>{
 let s=game();const u=add(s);add(s,1);afflict(s,u,'berserk');
 s=play(s,'SPT_MAFF_BERSERK',u.pos);expect(unit(s,u.uid).attacked).toBe(true);
});
it('hero Berserk spells retain their printed no-attack restriction',()=>{
 const s=play(game(),'SP_H_AFF_BERSERK');
 expect(leader(s,0)!.attacked).toBe(true);expect(leader(s,1)!.attacked).toBe(true);
});
it('robot immunity prevents the Berserk spell from disabling its attack',()=>{
 let s=game();const id=cards.find(c=>c.race==='robot'&&c.type==='unit')!.id,u=add(s,0,id);
 s=play(s,'SPT_MAFF_BERSERK',u.pos);expect(unit(s,u.uid).effects?.berserk).toBeUndefined();expect(unit(s,u.uid).attacked).toBe(false);
});
it('Vengeance selects the enemy, rejects allies and costs its victim five health when attacking',()=>{
 let s=game();const mine=add(s),enemy=add(s,1);s.players[0].hand=[tag('SPT_MAFF_VENGEANCE')];
 const actions=legalActions(s).filter(a=>a.kind==='playCard');expect(actions.some(a=>(a as any).target.q===enemy.pos.q)).toBe(true);expect(actions.some(a=>(a as any).target.q===mine.pos.q)).toBe(false);
 expect(applyAction(s,{kind:'playCard',handIndex:0,target:mine.pos})).toBe(s);
 s=play(s,'SPT_MAFF_VENGEANCE',enemy.pos);s=applyAction(s,{kind:'endTurn'});
 const attack=legalActions(s).find(a=>a.kind==='attack'&&a.uid===enemy.uid&&a.targetUid===mine.uid);expect(attack).toBeDefined();
 const hp=unit(s,enemy.uid).health;s=applyAction(s,attack!);expect(unit(s,enemy.uid).health).toBe(hp-5);expect(unit(s,enemy.uid).effects?.vengeance).toBeUndefined();
});
it('Second Wind permits a previously used special ability once again',()=>{
 let s=game();const c=cards.find(c=>c.abilityId==='AT_ENCOURAGE')!,u=add(s,0,c.id);
 s=applyAction(s,monsterAbilityActions(s,u)[0]);expect(unit(s,u.uid).abilityUsed).toBe(true);
 s=play(s,'SP_2NDWIND');expect(unit(s,u.uid).abilityUsed).toBe(false);
 const a=monsterAbilityActions(s,unit(s,u.uid))[0];expect(a).toBeDefined();s=applyAction(s,a);expect(unit(s,u.uid).abilityUsed).toBe(true);expect(monsterAbilityActions(s,unit(s,u.uid))).toHaveLength(0);
});
it('class-limited Second Wind resets only that class and preserves existing afflictions',()=>{
 let s=game();const mageId=cards.find(c=>c.combatClass==='mage'&&c.type==='unit')!.id,mage=add(s,0,mageId),warrior=spawn(s,'H04',0,offset(2,4));
 for(const u of [mage,warrior]){u.attacked=true;u.abilityUsed=true;u.moved=true;u.movesUsed=1;}
 mage.effects={stun:2};s=play(s,'SP_2NDWINDMAG');
 expect(unit(s,mage.uid).abilityUsed).toBe(false);expect(unit(s,mage.uid).movesUsed).toBe(0);expect(cannotAttack(unit(s,mage.uid))).toBe(true);
 expect(unit(s,warrior.uid).attacked).toBe(true);expect(unit(s,warrior.uid).abilityUsed).toBe(true);
});
