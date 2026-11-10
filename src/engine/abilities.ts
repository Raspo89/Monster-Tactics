import definitions from '../data/abilities.json';
import parameters from '../../reference/native-rules/native-parameters.json';
import * as G from './game';
import type {GameState,Unit,Hex,Action,Card} from './game';
export type Ability={name:string,nameEnglish:string,cost:number,minRange:number,maxRange:number,useOn:string,offensive:boolean,description:string};
export const abilities=definitions as Record<string,Ability>;
const P=parameters as Record<string,number>;
export const abilityFor=(u:Unit|Card)=>abilities['cardId' in u?G.def(u).abilityId||'':u.abilityId||''];
export const effect=(u:Unit,name:string)=>!!u.effects?.[name];
export const frozen=(u:Unit)=>effect(u,'ice');
export const cannotAttack=(u:Unit)=>frozen(u)||effect(u,'stun');
export const cannotMove=(u:Unit)=>frozen(u)||effect(u,'snare');
export const afflictionDuration=(name:string)=>({stun:P.AF_Stun_Turns,ice:P.AF_IceBlock_Turns,snare:P.AF_Snare_Turns} as Record<string,number>)[name]??-1;
/** Repair impossible permanent timed effects in battles saved by 7.4. */
export function repairTimedEffects(s:GameState){for(const u of s.units)for(const name of ['stun','ice','snare'])if((u.effects?.[name]??0)<0)u.effects![name]=afflictionDuration(name);}
export function afflict(s:GameState,u:Unit,name:string,turns=afflictionDuration(name)){if((!u.isLeader&&G.def(u).race==='robot')||frozen(u))return false;if(name==='flame')u.flaming=true;else if(name==='shield')u.shielded=true;else {u.effects??={};if(u.effects[name])return false;u.effects[name]=turns;}s.events.push({kind:'status',uid:u.uid,text:name});return true;}
export function cure(u:Unit){u.flaming=false;u.poisoned=false;for(const k of ['stun','snare','ice','vengeance','deathmark'])if(u.effects)delete u.effects[k];}
export function stripGood(u:Unit){u.shielded=false;for(const k of ['mighty','berserk','regen'])if(u.effects)delete u.effects[k];}
export function statusLabels(u:Unit){return [u.flaming?'اشتعال':'',u.poisoned?'سم':'',u.shielded?'حاجز سحري':'',...Object.keys(u.effects||{}).filter(k=>effect(u,k)).map(k=>({ice:'تجميد',stun:'ذهول',snare:'تقييد',mighty:'قوة +2',berserk:'هياج',regen:'تجدد',vengeance:'انتقام',deathmark:'علامة الموت'} as Record<string,string>)[k]||k)].filter(Boolean);}
export const effectPower=(u:Unit)=>(effect(u,'mighty')?P.AF_Mighty_Power:0)+(effect(u,'berserk')?P.AF_Berserk_Power:0);
export const incomingPower=(u:Unit)=>(effect(u,'berserk')?P.AF_Berserk_AttackerPower:0)+(effect(u,'deathmark')?P.AF_DeathMark_AttackerPower:0);
export const barrierArmour=(s:GameState,u:Unit)=>s.tileEffects?.[G.key(u.pos)]?.kind==='barrier'?P.TI_Barrier_Armour:0;
export function expireEffects(s:GameState){for(const u of s.units.filter(v=>v.owner===s.current))for(const [name,remaining] of Object.entries(u.effects||{}))if(remaining>0){u.effects![name]=remaining-1;if(u.effects![name]===0)delete u.effects![name];}for(const [key,e] of Object.entries(s.tileEffects||{}))if(e.expires>0&&s.turn>=e.expires)delete s.tileEffects![key];}
export function abilityUpkeep(s:GameState,u:Unit){u.abilityUsed=false;if(effect(u,'regen'))G.grow(s,u,P.AF_Regen_Health);}
export function triggerVengeance(s:GameState,u:Unit){if(effect(u,'vengeance')){delete u.effects!.vengeance;G.hit(s,u,-P.AF_Vengeance_Health,'vengeance');}}
function vacant(s:GameState,h:Hex){return G.isPlayable(s,h)&&!G.occupant(s,h)&&!G.runeAt(s,h)&&s.tiles[G.key(h)]!=='rock';}
function inRange(s:GameState,u:Unit,h:Hex,a:Ability){const d=G.distance(u.pos,h);return d>=a.minRange&&d<=a.maxRange;}
export function monsterAbilityActions(s:GameState,u?:Unit):Extract<Action,{kind:'monsterAbility'}>[] {if(!u||!s.originalRules||s.phase!=='battle'||s.winner!==undefined||u.isLeader||u.owner!==s.current||u.health<=0||u.attacked||u.abilityUsed||cannotAttack(u))return [];const a=abilityFor(u);if(!a||s.players[u.owner].energy<a.cost)return [];const id=G.def(u).abilityId!;if((u.movesUsed||0)>=2&&id!=='AT_SPRINT')return [];if(G.combatClass(u)==='artillery'&&u.moved)return [];let targets:(Hex|undefined)[]=[];
 switch(a.useOn){case'UO_SELF_MOVED':if(!u.moved&&!u.summoned)return [];targets=[undefined];break;case'UO_SELF':case'UO_TEAM_MINE':targets=[undefined];break;case'UO_UNOBSTRUCTED_TILE':targets=G.board.filter(h=>vacant(s,h)&&inRange(s,u,h,a));break;case'UO_INRANGE_TILE':targets=G.board.filter(h=>G.isPlayable(s,h)&&inRange(s,u,h,a));break;default:targets=s.units.filter(v=>{if(v.health<=0||frozen(v))return false;if(a.useOn==='UO_ENEMY'||a.useOn==='UO_ENEMY_HERO'){if(v.owner===u.owner||v.stealthed)return false;if(a.useOn==='UO_ENEMY_HERO'&&!v.isLeader)return false;}if(a.useOn==='UO_FRIEND'||a.useOn==='UO_TEAM_MOVED'){if(v.owner!==u.owner)return false;if(a.useOn==='UO_TEAM_MOVED'&&((!v.moved&&!v.summoned)||v.uid===u.uid))return false;}if(a.useOn==='UO_ANYBODY_ELSE'&&v.uid===u.uid)return false;return inRange(s,u,v.pos,a);}).map(v=>v.pos);}
 targets=targets.filter(h=>!h||G.isPlayable(s,h)&&!G.runeAt(s,h));
 return targets.map(target=>({kind:'monsterAbility',uid:u.uid,...(target?{target:{...target}}:{})}));}
export function onAbilityTile(s:GameState,u:Unit){const k=G.key(u.pos),tile=s.tileEffects?.[k];if(!tile)return;if(tile.kind==='flame'&&!frozen(u)){if(u.isLeader||G.def(u).race!=='imp'){const armour=G.defence(s,u);u.defenceSpent=(u.defenceSpent||0)+Math.min(armour,P.TI_IgniteFlame_Damage);G.hit(s,u,Math.max(0,P.TI_IgniteFlame_Damage-armour),'tileFire');}if(u.health>0)afflict(s,u,'flame');}if(tile.kind==='trap'){delete s.tileEffects![k];G.hit(s,u,-P.TI_Trap_Health,'trap');s.events.push({kind:'status',to:{...u.pos},text:'فخ'});}}
function putTile(s:GameState,u:Unit,h:Hex,kind:'flame'|'trap'|'barrier'){if(!G.isPlayable(s,h))return;(s.tileEffects??={})[G.key(h)]={kind,owner:u.owner,expires:kind==='trap'?-1:s.turn+(kind==='flame'?P.TI_IgniteFlame_Rounds:P.TI_Barrier_Rounds)*2};const v=G.occupant(s,h);if(v&&kind==='flame')afflict(s,v,'flame');s.events.push({kind:'tileAbility',to:{...h},text:kind});}
function push(s:GameState,u:Unit,v:Unit){if(v.health<=0)return;const d=G.distance(u.pos,v.pos);if(d!==1)return;const dest={q:v.pos.q+(v.pos.q-u.pos.q),r:v.pos.r+(v.pos.r-u.pos.r)};if(vacant(s,dest)){const from={...v.pos};v.pos=dest;onAbilityTile(s,v);s.events.push({kind:'move',uid:v.uid,from,to:dest});}}
function disarm(s:GameState,u:Unit){for(const field of ['weapon','shieldItem','armorItem'] as const){const id=u[field];if(!id)continue;s.players[u.owner].graveyard.push(id);if(id==='A02'){u.maxHealth-=3;u.health-=3;}u[field]=undefined;}}
/** All native ability power fields are additive to the attacker's current power. */
export function combatHit(s:GameState,u:Unit,v:Unit,power:number){if(frozen(v))return 0;const armour=G.defence(s,v),attack=Math.max(0,power+incomingPower(v)),shield=v.shielded,amount=shield?0:Math.max(0,attack-armour);if(!shield)v.defenceSpent=(v.defenceSpent||0)+Math.min(armour,attack);G.hit(s,v,amount);G.creditDamage(s,u,amount);if(v.health>0&&!v.isLeader&&G.def(v).race==='dwarf')v.bonusAttack+=P.RB_DwarfBonus_Power;return amount;}
export function applyMonsterAbility(s:GameState,u:Unit,target?:Hex){const id=G.def(u).abilityId!,a=abilities[id],p=s.players[u.owner],v=target?G.occupant(s,target):undefined,base=G.effectiveStats(s,u).attack;
 p.energy-=a.cost;u.attacked=true;u.abilityUsed=true;u.stealthed=false;G.log(s,`${G.def(u).name}: ${a.name} • ${a.cost} موجو`);s.events.push({kind:'ability',uid:u.uid,from:{...u.pos},to:target||{...u.pos},text:id});
 const hit=(victim:Unit,delta=0)=>{s.events.push({kind:'attack',uid:u.uid,from:{...u.pos},to:{...victim.pos}});return combatHit(s,u,victim,base+delta);};
 let attacked=false;
 switch(id){
 case'AT_ATTACK':case'AT_BLAST':case'AT_SHOOT':case'AT_LOB':if(v){hit(v);attacked=true;}break;
 case'AT_SMASH':if(v){hit(v,P.AB_Smash_Power);attacked=true;}break;
 case'AT_SAVAGESTRIKE':if(v){hit(v,P.AB_SavageStrike_Power);attacked=true;}break;
 case'AT_HEROICSHOUT':for(const ally of s.units.filter(x=>x.owner===u.owner))afflict(s,ally,'mighty');break;
 case'AT_ENCOURAGE':p.energy+=P.AB_Encourage_Mojo;break;
 case'AT_BERSERK':afflict(s,u,'berserk');break;
 case'AT_FURIOUSASSAULT':case'AT_BARRAGE':for(const enemy of s.units.filter(x=>x.owner!==u.owner&&inRange(s,u,x.pos,a))){hit(enemy);attacked=true;}break;
 case'AT_RALLY':p.energy+=s.units.filter(x=>x.owner===u.owner&&x.uid!==u.uid&&G.distance(x.pos,u.pos)<=P.AB_Rally_EffectRange).length*P.AB_Rally_BonusMojo;break;
 case'AT_VENGEANCE':if(v)afflict(s,v,'vengeance');break;
 case'AT_ENERGISINGSTRIKE':if(v){hit(v,P.AB_EnergisingStrike_Power);G.grow(s,u,P.AB_EnergisingStrike_Health);attacked=true;}break;
 case'AT_INSPIRINGSTRIKE':if(v){hit(v);for(const ally of s.units.filter(x=>x.owner===u.owner&&!x.isLeader))G.grow(s,ally,P.AB_InspiringStrike_AllyHealth);attacked=true;}break;
 case'AT_MIGHTYBLOW':if(v){hit(v,P.AB_MightyBlow_Power);push(s,u,v);attacked=true;}break;
 case'AT_HEAVE':if(v)push(s,u,v);break;
 case'AT_CRUSH':if(v){hit(v);afflict(s,v,'stun',P.AF_Stun_Turns);attacked=true;}break;
 case'AT_PHALANX':if(v){hit(v,s.units.filter(x=>x.owner===u.owner&&x.uid!==u.uid&&!x.isLeader&&G.distance(x.pos,u.pos)===1).length*P.AB_Phalanx_BonusPower);attacked=true;}break;
 case'AT_DEMOLISH':if(v){hit(v,P.AB_Demolish_Power);attacked=true;}break;
 case'AT_DESPERATESTRIKE':if(v){hit(v,P.AB_DesperateStrike_Power);G.hit(s,u,-P.AB_DesperateStrike_Health,'selfDamage');attacked=true;}break;
 case'AT_BLOODLUST':if(v){hit(v,s.units.filter(x=>x.owner!==u.owner&&!x.isLeader&&G.distance(x.pos,u.pos)===1).length*P.AB_Bloodlust_BonusPower);attacked=true;}break;
 case'AT_COLOSSUSSMASH':for(const victim of s.units.filter(x=>x.uid!==u.uid&&G.distance(x.pos,u.pos)===1)){hit(victim,P.AB_ColossusSmash_Power);push(s,u,victim);attacked=true;}break;
 case'AT_LEVIATHANBLOW':if(v){hit(v,P.AB_LeviathanBlow_Power);afflict(s,v,'flame');attacked=true;}break;
 case'AT_FIREBALL':if(v){hit(v,P.AB_FireBall_Power);afflict(s,v,'flame');attacked=true;}break;
 case'AT_LIGHTNING':if(v){for(const victim of s.units.filter(x=>x.owner!==u.owner&&G.distance(x.pos,v.pos)<=1)){hit(victim,victim.uid===v.uid?P.AB_Lightning_Power:P.AB_Lightning_SecondaryPower);}attacked=true;}break;
 case'AT_METEOR':if(target){for(const victim of s.units.filter(x=>G.distance(x.pos,target)<=1)){hit(victim,P.AB_Meteor_Power);afflict(s,victim,'flame');}attacked=true;}break;
 case'AT_HEAL':case'AT_FASTHEAL':if(v)G.grow(s,v,id==='AT_HEAL'?P.AB_Heal_Health:P.AB_FastHeal_Health);break;
 case'AT_CURE':if(v)cure(v);break;
 case'AT_MASSHEAL':if(v)for(const ally of s.units.filter(x=>x.owner===u.owner&&G.distance(x.pos,v.pos)<=P.AB_MassHeal_EffectRange))G.grow(s,ally,P.AB_MassHeal_Health);break;
 case'AT_REGEN':if(v){G.grow(s,v,P.AB_Regen_Health);afflict(s,v,'regen');}break;
 case'AT_MAGICSHIELD':if(v)afflict(s,v,'shield');break;
 case'AT_ICEBLOCK':if(v)afflict(s,v,'ice',P.AF_IceBlock_Turns);break;
 case'AT_LIFESTEAL':if(v){hit(v,P.AB_LifeSteal_Power);G.grow(s,u,P.AB_LifeSteal_Health);attacked=true;}break;
 case'AT_BARRIER':if(target)putTile(s,u,target,'barrier');break;
 case'AT_BLINK':if(target){const from={...u.pos};u.pos={...target};onAbilityTile(s,u);s.events.push({kind:'move',uid:u.uid,from,to:{...target}});}break;
 case'AT_EXPLODE':for(const victim of s.units.filter(x=>G.distance(x.pos,u.pos)<=1))hit(victim,victim.uid===u.uid?P.AB_Explode_Power:P.AB_Explode_SecondaryPower);attacked=true;break;
 case'AT_ZAP':if(v)afflict(s,v,'stun',P.AF_Stun_Turns);break;
 case'AT_COMBUSTION':if(v){hit(v,v.flaming?P.AB_Combustion_OnFirePower:0);attacked=true;}break;
 case'AT_HEADSHOT':if(v){hit(v,P.AB_HeadShot_Power);attacked=true;}break;
 case'AT_SHATTER':if(v){hit(v);stripGood(v);attacked=true;}break;
 case'AT_DEATHMARK':if(v)afflict(s,v,'deathmark');break;
 case'AT_TRICKSHOT':if(v)p.energy+=s.units.filter(x=>x.owner!==u.owner&&G.distance(x.pos,v.pos)<=P.AB_TrickShot_EffectRange).length*P.AB_TrickShot_Mojo;break;
 case'AT_SNIPE':if(v){hit(v,P.AB_Snipe_Power);attacked=true;}break;
 case'AT_TRAP':case'AT_IGNITE':if(target)putTile(s,u,target,id==='AT_TRAP'?'trap':'flame');break;
 case'AT_SNARE':if(v){hit(v,P.AB_Snare_Power);afflict(s,v,'snare',P.AF_Snare_Turns);attacked=true;}break;
 case'AT_LONERANGER':if(v){hit(v,G.neighbors(u.pos).filter(h=>vacant(s,h)).length*P.AB_LoneRanger_BonusPower);attacked=true;}break;
 case'AT_FIRSTAID':u.bonusAttack+=P.AB_FirstAid_Power;break;
 case'AT_INFERNO':for(const h of [u.pos,...G.neighbors(u.pos)])putTile(s,u,h,'flame');break;
 case'AT_SPRINT':u.moved=false;u.movesUsed=0;u.summoned=false;break;
 case'AT_SUPERSPRINT':if(v&&!cannotMove(v)){v.moved=false;v.movesUsed=0;v.summoned=false;}break;
 case'AT_DISARM':if(v)disarm(s,v);break;
 case'AT_SELFCURE':cure(u);break;
 case'AT_DRAWCARD':G.draw(s,u.owner);break;
 case'AT_BOO':if(v){push(s,u,v);disarm(s,v);}break;
 }
 if(a.offensive)triggerVengeance(s,u);G.deaths(s,u);
}
