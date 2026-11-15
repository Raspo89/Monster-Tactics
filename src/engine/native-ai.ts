/**
 * Computer opponent ported from the original Combat Monsters (libCombatMonsters.so, CAIWorker_BruteForce / CAIBattleState).
 *
 * How the original thinks (recovered from the ARM code, addresses in docs/AI-NATIVE.md):
 * - Once per turn it builds influence maps: a threat map of what the enemy can hit, and for each class a "where should my
 *   hero / my monsters stand" map (Mojo altars and card tiles pull, the enemy hero pulls from round 2, a wounded hero is
 *   pushed away from enemies).
 * - It then searches only its own turn: every move, attack, ability, summon, item, spell and rune is tried, level by level,
 *   the best nodes of each level are expanded first, up to a node budget. The best state found anywhere is the plan.
 * - A state is scored with CAIBattleState::Evaluate: each creature is worth its "excellence" (health, power, armour,
 *   afflictions, Mojo it produces, race quirks), own creatures add their influence-map value, enemy creatures are
 *   subtracted, runes add their value, unspent Mojo adds a little.
 * - It never simulates the opponent's reply; danger is handled by the threat map (moving into reach costs points).
 */
import {GameState,Unit,Action,Hex,key,distance,board,isPlayable,leader,def,cardById,effectiveStats,combatClass,attackRange,legalActions,applyAction,nativeHeroes,tileMojoBonus,itemSum,castingCost,activeRunes} from './game';
import {effect} from './abilities';
import nativeRuneTable from '../data/native-rune-order.json';

type Cls=0|1|2|3;
const CLASS:Record<string,Cls>={warrior:0,archer:1,mage:2,artillery:3};
const clsOf=(s:GameState,u:Unit):Cls=>u.isLeader?CLASS[(nativeHeroes as any)[s.players[u.owner].race]?.combatClass||'warrior']??0:CLASS[combatClass(u)]??0;
const neighbours=(h:Hex)=>[[1,0],[1,-1],[0,-1],[-1,0],[-1,1],[0,1]].map(([q,r])=>({q:h.q+q,r:h.r+r}));

/** Cell kinds of the original map (eMapCellType): 2 power+2, 3 armour, 4 regen, 5 Mojo+2, 6 card, 7 Mojo+1, 8 power+3, 9 power-, 10 armour-. */
function cellType(s:GameState,h:Hex):number{const k=key(h),t=s.tiles[k],tok=s.tokens[k];if(t==='altar')return 5;if(t==='altar1')return 7;if(t==='draw'||tok==='card')return 6;if(t==='spring'||tok==='heart')return 4;if(tok==='star')return 2;if(tok==='shield')return 3;if(tok==='star3')return 8;if(tok==='curse')return 9;if(tok==='rust')return 10;return 1;}
const onRegen=(s:GameState,u:Unit)=>cellType(s,u.pos)===4;
function passable(s:GameState,h:Hex){if(!isPlayable(s,h))return false;const k=key(h);if(s.tiles[k]==='rock')return false;if(s.tileEffects?.[k]?.kind==='barrier')return false;return !s.runeStands?.some(r=>r.pos.q===h.q&&r.pos.r===h.r);}

type Grid=Map<string,number>;
/** CMap::RecurseRangeCalculatorAvoidingObstacles: walking distance (creatures do not block), up to `max` steps. */
function walk(s:GameState,from:Hex,max:number):Grid{const d:Grid=new Map([[key(from),0]]);let front=[from];for(let step=1;step<=max&&front.length;step++){const next:Hex[]=[];for(const h of front)for(const n of neighbours(h)){const k=key(n);if(d.has(k)||!passable(s,n))continue;d.set(k,step);next.push(n);}front=next;}return d;}
const cells=(s:GameState)=>board.filter(h=>isPlayable(s,h));

export type NativeMaps={threat:Grid,hero:Record<number,Grid>,monster:Record<number,Grid>,A:number,D:number};

/** CTeam::PrepareForAIThink: A = how much the hand wants to spend (avg cost x min(hand,3) / Mojo), D = dominance 0..1. */
function teamParams(s:GameState,owner:number){let myP=0,myDef=0,enP=0,enDef=0;for(const u of s.units){const st=effectiveStats(s,u);if(u.owner===owner){myP+=st.attack;myDef+=u.health+2*st.armor;}else{enP+=st.attack;if(!u.isLeader)enDef+=u.health+2*st.armor;}}
 const off=myP+enDef?myP/(myP+enDef):.5,dfn=myDef+enP?myDef/(myDef+enP):.5,D=(off+dfn)/2;
 const p=s.players[owner],costs=p.hand.map(id=>castingCost(s,cardById[id],owner)),avg=costs.length?costs.reduce((a,b)=>a+b,0)/costs.length:0;
 let A=avg*Math.min(p.hand.length,3)/Math.max(1,p.energy);if(round(s)>1&&D>.5)A*=1-2*(D-.5);return {A,D};}
const round=(s:GameState)=>Math.ceil(s.turn/2);

/** Threat map: every enemy adds its power (at least 1) to every cell within its attack reach, half one step beyond. */
function threatMap(s:GameState,owner:number):Grid{const g:Grid=new Map();for(const e of s.units){if(e.owner===owner)continue;const P=Math.max(1,effectiveStats(s,e).attack),max=attackRange(s,e).max;for(const h of cells(s)){const d=distance(e.pos,h);if(d<1||d>max+1)continue;let v=P-1/(max+10-d);if(d>max)v*=.5;g.set(key(h),(g.get(key(h))||0)+v);}}return g;}

function tilePulls(s:GameState,g:Grid,A:number,power:number,withMojo1:boolean,handCount:number){for(const t of cells(s)){const ct=cellType(s,t);if(ct!==5&&ct!==6&&!(withMojo1&&ct===7))continue;const d=walk(s,t,13);for(const h of cells(s)){if(!passable(s,h))continue;const dist=d.get(key(h))??0,k=key(h);let v;if(ct===6)v=36/(handCount+1)/(dist+1);else v=Math.pow(A,power)/(dist+1)+(ct===5?7:3.5);g.set(k,(g.get(k)||0)+v);}}}
function heroPull(s:GameState,g:Grid,owner:number,minDist:number,late:boolean,B:number){for(const e of s.units){if(e.owner===owner||!e.isLeader)continue;const d=walk(s,e.pos,13);for(const h of cells(s)){const dist=d.get(key(h));if(dist===undefined||dist<minDist)continue;const v=75/(dist+1),k=key(h);g.set(k,(g.get(k)||0)+(late?250+50*v:v*B));}}}

/** Builds the maps the original builds once per AI turn (CAIWorker_BruteForce constructor). */
export function buildMaps(s:GameState,owner:number):NativeMaps{
 const {A,D}=teamParams(s,owner),B=round(s)>1?3*D:0,p=s.players[owner],deck=p.deck.length,hand=p.hand.length;
 const threat=threatMap(s,owner),hero:Record<number,Grid>={},monster:Record<number,Grid>={};
 const me=leader(s,owner);
 for(const c of [0,1,2,3] as Cls[]){
  // Monsters: altars and card tiles pull while the deck lasts; from round 2 the enemy hero pulls (archers keep 2 away, artillery 3).
  const m:Grid=new Map();if(deck>3)tilePulls(s,m,A,2,true,hand);heroPull(s,m,owner,c===1?2:c===3?3:1,deck<=2,B);monster[c]=m;
  // Hero: same idea with its own thresholds; a hero under 15 health is pushed away from what can reach it.
  const h:Grid=new Map();
  if(deck>8){tilePulls(s,h,A,3,false,hand);
   if(me&&me.health<15)for(const e of s.units){if(e.owner===owner)continue;const ec=clsOf(s,e),far=ec===1||ec===2,maxd=far?3:2,base=far?4:3,P=effectiveStats(s,e).attack;if(!P)continue;const d=walk(s,e.pos,maxd);for(const [k,dist] of d){if(!dist)continue;h.set(k,(h.get(k)||0)-(base-dist)*(P/me.health)**2*300);}}}
  heroPull(s,h,owner,c===1?2:1,deck<=8,B);hero[c]=h;
 }
 return {threat,hero,monster,A,D};
}

/** CCharacterMin::GetAIScoreForAfflictions — how good the creature's own afflictions are for it. Bad ones do not count on a regen cell. */
function afflictionScore(s:GameState,u:Unit,H:number,P:number){let v=0;const safe=onRegen(s,u);
 if(effect(u,'regen'))v+=Math.max(20-H,5);
 if(!safe&&effect(u,'vengeance')){v+=-5;if(H<=5)v+=2*H;}
 if(!safe&&u.flaming)v-=Math.max(30-H,10);
 if(!safe&&u.poisoned)v-=15;
 if(!safe&&effect(u,'stun'))v-=P;
 if(effect(u,'mighty'))v+=3;
 if(effect(u,'berserk'))v+=H-3;
 if(!safe&&effect(u,'snare'))v-=Math.ceil(P/2);
 if(!safe&&effect(u,'deathmark'))v-=Math.max(10-H,5);
 if(u.shielded)v+=Math.max(10-H,3);
 if(!safe&&effect(u,'cripple')&&def(u).abilityId)v-=10;
 return v;}

/** Power and armour with buff tiles counted only where an enemy can actually fight (ProduceInfluenceMap_TileMultipliers). */
function aiStats(s:GameState,u:Unit,maps:NativeMaps){const st=effectiveStats(s,u);let P=st.attack,A=st.armor;const ct=cellType(s,u.pos);if((ct===2||ct===8||ct===3)&&!((maps.threat.get(key(u.pos))||0)>0)){if(ct===2)P-=2;else if(ct===8)P-=3;else A-=2;}return {P:Math.max(0,P),A:Math.max(0,A)};}
/** CAIBattleState::GetMonsterExcellence. */
function excellence(s:GameState,u:Unit,owner:number,maps:NativeMaps){const H=u.health,race=u.isLeader?'':def(u).race,{P,A:Ar}=aiStats(s,u,maps);
 let v=0;if(u.isLeader){v=2*H;if(H<=15)v-=(15-H)**3;}else if(race==='vampire')v=u.attacked?0:-20;else if(race==='imp')v=u.flaming?30:-20;
 v+=H+P/2;
 if(u.owner===owner)v+=2*Ar+P;else v+=.3*Ar;
 const m=u.owner===owner?2*maps.D:1,auto=Math.max(0,(u.isLeader?0:tileMojoBonus(s,u.pos))+itemSum(u,'mojo'));v+=5*auto*H*m*m;
 v+=afflictionScore(s,u,H,P);
 if(!onRegen(s,u)){const adj=s.units.filter(w=>w!==u&&distance(w.pos,u.pos)===1);if(u.poisoned){const n=adj.length;if(n)v-=n*(u.isLeader?40:20);}else{const n=adj.filter(w=>w.poisoned).length;if(n)v-=n*(u.isLeader?50:30);}}
 if(race==='spectre')v*=2.5;
 return v;}

/** Original rune values (CAIBattleState::ValueThisRune): Mojo runes are worth A² x 10/20/30, card runes depend on the deck, the rest 3. */
const RUNE_KIND:Record<string,string>=nativeRuneTable as any;
const ownTag:Record<string,string>={R03:'R_MINORMOJO',R07:'R_MAJORMOJO',R04:'R_EXTRACARD'};
function runeValue(s:GameState,cardId:string,team:number,owner:number,maps:NativeMaps){const tag=(cardById[cardId] as any).nativeTag||ownTag[cardId]||'',kind=RUNE_KIND[tag]||'',A=team===owner?maps.A:0;
 if(kind==='mojo10')return 10*A*A;if(kind==='mojo20')return 20*A*A;if(kind==='mojo30')return 30*A*A;
 if(kind==='bankers')return A<1?40:40/A;
 if(kind==='card'){const n=activeRunes(s,team).filter(r=>r.cardId===cardId).length,deck=s.players[team].deck.length;if(deck<10*n)return deck-9*n;return A<1?50:50/A;}
 return 3;}
function runesValue(s:GameState,team:number,owner:number,maps:NativeMaps){let v=0;for(const r of activeRunes(s,team)){let x=runeValue(s,r.cardId!,team,owner,maps);if(team===owner){const t=maps.threat.get(key(r.pos))||0;if(t>0&&r.health>0)x*=t/r.health<=1?1-t/r.health:0;}v+=x;}return v;}

/** CAIBattleState::Evaluate for the side `owner` that is thinking. */
export function nativeEvaluate(s:GameState,owner:number,maps:NativeMaps){
 if(s.winner!==undefined)return s.winner==='draw'?0:s.winner===owner?1e6:-1e6;
 let score=0;
 for(const u of s.units){let v=excellence(s,u,owner,maps);const k=key(u.pos),trap=s.tileEffects?.[k]?.kind==='trap',fire=s.tileEffects?.[k]?.kind==='flame';
  if(u.owner===owner){v+=((u.isLeader?maps.hero:maps.monster)[clsOf(s,u)].get(k)||0);if(u.isLeader){if(trap)v-=10;if(fire)v-=5;}else if(trap)v-=5;score+=v;}
  else{if(!u.isLeader){const ct=cellType(s,u.pos);v+=ct===3?1:ct===4?5:ct===5?7:ct===6?9:ct===7?3.5:ct===9||ct===10?-1:0;if(trap)v-=5;}score-=v;}}
 score+=.1*s.players[owner].energy;
 const mine=s.units.filter(u=>u.owner===owner&&!u.isLeader).length;if(maps.D>.6&&mine>4)score-=100*mine*((maps.D-.5)*2)**5;
 score+=runesValue(s,owner,owner,maps);
 const enemy=1-owner;score-=activeRunes(s,enemy).length+.75*runesValue(s,enemy,owner,maps);
 return score;}

type Node={s:GameState,first:Action|null,score:number,bonus:number,depth:number};
function stateKey(s:GameState){let k='';for(const u of s.units){k+=u.uid+','+u.pos.q+','+u.pos.r+','+u.health+','+(u.moved?1:0)+(u.attacked?1:0)+(u.abilityUsed?1:0)+(u.movesUsed||0)+','+(u.weapon||'')+(u.armorItem||'')+(u.shieldItem||'')+(u.flaming?'f':'')+(u.shielded?'s':'')+(u.poisoned?'p':'')+','+u.bonusAttack+','+u.bonusArmor+',';if(u.effects)for(const e in u.effects)k+=e+u.effects[e];k+='|';}
 for(const p of s.players)k+=p.energy+'/'+p.hand.length+'/'+p.deck.length+';';if(s.runeStands)for(const r of s.runeStands)k+=(r.cardId||'')+r.health+';';if(s.tileEffects)for(const t in s.tileEffects)k+=t+s.tileEffects[t].kind;for(const t in s.tokens)k+=t+s.tokens[t];return k+(s.winner??'');}

export const nativeStats={nodes:0,lastPlan:0};
/**
 * CAIWorker_BruteForce::Start: breadth-first over this turn's actions, best nodes of each level first, up to `budget`
 * nodes and 11 actions deep. Moves into enemy reach are charged with the threat map like the original
 * (more if the creature has already attacked and can no longer strike first).
 */
export function nativePlan(root:GameState,budget=1500,timeMs=Infinity):Action[]{
 const t0=Date.now();
 const owner=root.current,maps=buildMaps(root,owner);
 const rootScore=nativeEvaluate(root,owner,maps);
 let level:Node[]=[{s:root,first:null,score:rootScore,bonus:0,depth:0}],best:Node|null=null,used=0;const seen=new Set<string>([stateKey(root)]);
 const paths=new Map<Node,Action[]>();paths.set(level[0],[]);
 for(let depth=1;depth<=11&&level.length&&used<budget;depth++){
  const next:Node[]=[];
  for(const node of level){if(used>=budget)break;
   for(const a of legalActions(node.s)){if(a.kind==='endTurn'||a.kind==='mulligan')continue;if(used>=budget)break;if((used&63)===0&&Date.now()-t0>timeMs){used=budget;break;}
    const t=applyAction(node.s,a,true);if(t===node.s||t.current!==owner&&t.winner===undefined)continue;used++;
    const k=stateKey(t);if(seen.has(k))continue;seen.add(k);t.log=[];t.events=[];
    const bonus=node.bonus+(a.kind==='move'||a.kind==='attack'||a.kind==='attackRune'||a.kind==='teleport'?-.0001:a.kind==='monsterAbility'||a.kind==='leaderAbility'?-.0001:0)-(depth)*.001;
    let score=nativeEvaluate(t,owner,maps)+bonus;
    if(a.kind==='move'||a.kind==='teleport'){const u=t.units.find(v=>v.uid===a.uid);if(u){const st=effectiveStats(t,u),x=(maps.threat.get(key(u.pos))||0)-(u.health+st.armor);if(x>0)score-=u.attacked?20+20*x:15+5*x;}}
    if(t.winner===owner)score=1e7-depth;
    const child:Node={s:t,first:node.first||a,score,bonus,depth};paths.set(child,[...paths.get(node)!,a]);next.push(child);
    if(!best||score>best.score)best=child;}}
  next.sort((a,b)=>b.score-a.score);level=next;}
 nativeStats.nodes=used;
 if(!best||best.score<=rootScore)return [{kind:'endTurn'}];
 const plan=paths.get(best)!;nativeStats.lastPlan=plan.length;return plan;}

const planCache=new Map<string,Action[]>();
const sig=(s:GameState)=>JSON.stringify([s.seed,s.turn,s.current,s.rng,s.nextUid,stateKey(s),s.players.map(p=>p.hand)]);
/** Plays the original AI's plan one action at a time; replans whenever the board is not what the plan expected. */
export function nativeChoose(s:GameState,budget=1500,timeMs=Infinity):Action{
 const k=sig(s);let plan=planCache.get(k);
 if(!plan){plan=nativePlan(s,budget,timeMs);}
 planCache.clear();
 const a=plan[0]||{kind:'endTurn'};
 if(a.kind!=='endTurn'&&plan.length>1){const t=applyAction(s,a,true);if(t!==s)planCache.set(sig(t),plan.slice(1));}
 return a;}
