import nativeQuests from '../data/native-quests.json';
import {cards,cardById,validateDeck} from './game';
import type {Card,DeckRule} from './game';
export type Rarity='C'|'U'|'R'|'L';
export const rarityOrder:Rarity[]=['C','U','R','L'];
export const rarityInfo:Record<Rarity,{name:string,english:string,weight:number,price:number,color:string}>={C:{name:'عادي',english:'Common',weight:70,price:60,color:'#e5d9ad'},U:{name:'غير شائع',english:'Uncommon',weight:23,price:180,color:'#8ccc74'},R:{name:'نادر',english:'Rare',weight:6,price:600,color:'#83bdf6'},L:{name:'أسطوري',english:'Legendary',weight:1,price:1800,color:'#ffd575'}};
export const cardRarity=(c:Card):Rarity=>c.rarity==='E'?'R':rarityOrder.includes(c.rarity as Rarity)?c.rarity as Rarity:'C';
export const cardPrice=(c:Card)=>rarityInfo[cardRarity(c)].price;
export const WIN_COINS=120;
export type Reward={matchId:string,cardId:string,coins:number,rarity:Rarity,newCard:boolean};
export type Profile={version:1,coins:number,inventory:Record<string,number>,starterRace?:string,starterDeck:string[],wins:number,receipts:Record<string,Reward>,quests?:Record<string,number[]>};
export const emptyProfile=():Profile=>({version:1,coins:100,inventory:{},starterDeck:[],wins:0,receipts:{}});
export function loadProfile(raw:any):Profile{const p=emptyProfile();if(!raw||raw.version!==1)return p;p.coins=Number.isSafeInteger(raw.coins)&&raw.coins>=0?raw.coins:100;p.wins=Number.isSafeInteger(raw.wins)&&raw.wins>=0?raw.wins:0;for(const [id,n] of Object.entries(raw.inventory||{}))if(cardById[id]&&Number.isSafeInteger(n)&&Number(n)>0)p.inventory[id]=Number(n);p.starterRace=typeof raw.starterRace==='string'?raw.starterRace:undefined;p.starterDeck=Array.isArray(raw.starterDeck)?raw.starterDeck.filter((id:any)=>typeof id==='string'&&cardById[id]):[];for(const [id,r] of Object.entries(raw.receipts||{}))if(r&&typeof r==='object'&&cardById[(r as Reward).cardId])p.receipts[id]=r as Reward;if(raw.quests&&typeof raw.quests==='object'){p.quests={};for(const q of QUESTS){const won=raw.quests[q.id];if(Array.isArray(won))p.quests[q.id]=[...new Set(won.filter((n:any)=>q.rooms.some(r=>r.n===n)))] as number[];}}upgradeStarter(p);return p;}
export function starterCards(race:string){const pool=cards.filter(c=>c.type==='unit'&&c.race===race&&(c.id.startsWith('CM_')||c.id.startsWith('NA_'))&&['C','U'].includes(cardRarity(c))&&c.cost<=4).sort((a,b)=>a.cost-b.cost||Number(!!b.abilityId)-Number(!!a.abilityId));const selected:Card[]=[];for(const cls of ['warrior','archer','mage']){const c=pool.find(c=>c.combatClass===cls);if(c)selected.push(c);}const active=pool.find(c=>c.abilityId);if(active&&!selected.includes(active))selected.push(active);for(const c of pool)if(selected.length<5&&!selected.includes(c))selected.push(c);if(selected.length<5)throw Error('لا توجد مجموعة بداية كافية');return [...selected.slice(0,5).flatMap(c=>[c.id,c.id,c.id,c.id]),'R03','R03','S01','S01','S02','A01',...starterWeapons()];}
/** Two warrior weapons, one bow and one staff: the cheapest common original weapon of each class. */
const drawback=(c:Card)=>Object.values(c.equip||{}).filter(v=>typeof v==='number'&&v<0).length;
export function starterWeapons(){const pick=(cls:string)=>cards.filter(c=>c.type==='weapon'&&c.id.startsWith('NE_')&&c.forClass===cls&&cardRarity(c)==='C'&&(c.equip?.attack||0)>0).sort((a,b)=>drawback(a)-drawback(b)||a.cost-b.cost||(b.equip?.attack||0)-(a.equip?.attack||0)||a.id.localeCompare(b.id))[0]?.id||(cls==='warrior'?'W01':'W02');const w=pick('warrior');return [w,w,pick('archer'),pick('mage')];}
/** Older saves got a starter deck without weapons: give them the new one and the cards it needs. */
function upgradeStarter(p:Profile){if(!p.starterRace||!p.starterDeck.length||p.starterDeck.some(id=>cardById[id]?.type==='weapon'&&id.startsWith('NE_')))return;let next:string[];try{next=starterCards(p.starterRace);}catch{return;}const need:Record<string,number>={};for(const id of next)need[id]=(need[id]||0)+1;for(const [id,n] of Object.entries(need))if((p.inventory[id]||0)<n)p.inventory[id]=n;p.starterDeck=next;}

export function chooseStarter(profile:Profile,race:string){if(profile.starterRace)throw Error('اخترت مجموعة البداية مسبقًا');if(!['human','zombie','orc','elf'].includes(race))throw Error('اختر مجموعة بداية صالحة');const p=structuredClone(profile);p.starterRace=race;p.starterDeck=starterCards(race);for(const id of p.starterDeck)p.inventory[id]=(p.inventory[id]||0)+1;return p;}
export const ownedCount=(p:Profile,id:string)=>p.inventory[id]||0;
export function ownershipError(p:Profile,deck:string[]){const counts:Record<string,number>={};for(const id of deck){counts[id]=(counts[id]||0)+1;if(counts[id]>ownedCount(p,id))return `لا تملك نسخًا كافية من ${cardById[id]?.name||id} (${ownedCount(p,id)}/${counts[id]})`;}return '';}
export const playableError=(p:Profile,deck:string[],hero:string,rule:DeckRule='standard')=>validateDeck(deck,hero,rule)||ownershipError(p,deck);
export function purchaseCard(profile:Profile,id:string):{profile:Profile,error?:string}{const c=cardById[id];if(!c)return {profile,error:'البطاقة غير موجودة'};if(!profile.starterRace)return {profile,error:'اختر مجموعة البداية أولًا'};if(ownedCount(profile,id)>=4)return {profile,error:'لديك أربع نسخ أو أكثر؛ الحد في التشكيلة أربع نسخ'};if(profile.coins<cardPrice(c))return {profile,error:'رصيد العملات غير كافٍ'};const p=structuredClone(profile);p.coins-=cardPrice(c);p.inventory[id]=(p.inventory[id]||0)+1;return {profile:p};}
export function rollCard(random=Math.random){let value=Math.max(0,Math.min(.9999999,random()))*100;let r:Rarity='L';for(const tier of rarityOrder){value-=rarityInfo[tier].weight;if(value<0){r=tier;break;}}const pool=cards.filter(c=>cardRarity(c)===r);return pool[Math.min(pool.length-1,Math.floor(Math.max(0,Math.min(.9999999,random()))*pool.length))];}
export function grantVictory(profile:Profile,matchId:string,eligible:boolean,won:boolean,random=Math.random):{profile:Profile,reward?:Reward,alreadyClaimed:boolean}{if(profile.receipts[matchId])return {profile,reward:profile.receipts[matchId],alreadyClaimed:true};if(!eligible||!won||!profile.starterRace||!matchId)return {profile,alreadyClaimed:false};const c=rollCard(random),p=structuredClone(profile),reward:Reward={matchId,cardId:c.id,coins:WIN_COINS,rarity:cardRarity(c),newCard:!ownedCount(p,c.id)};p.coins+=WIN_COINS;p.inventory[c.id]=(p.inventory[c.id]||0)+1;p.wins++;p.receipts[matchId]=reward;return {profile:p,reward,alreadyClaimed:false};}

// ---- Solo quests (original Quests/*.txt, imported by scripts/import-native-quests.py) ----
export type QuestRoom={n:number,parent:number|null,x:number,y:number,hero:string,deckName:string,deck:string[],map:string,boss?:'sub'|'last'};
export type Quest={id:string,title:string,english:string,text:string,ai:string,enemyBonusMojo:number,rooms:QuestRoom[]};
export const QUESTS=(nativeQuests.quests as Quest[]);
export const questById=Object.fromEntries(QUESTS.map(q=>[q.id,q])) as Record<string,Quest>;
/** First-win prize of every room grows with the quest's difficulty; mini bosses add a rare card, the last battle a legendary one. */
export const QUEST_COINS:Record<string,number>={tut:60,easy:100,medium:150,hard:200,hard2:260,hard3:320};
export type QuestPrize={coins:number,rarity?:Rarity};
export function questPrize(q:Quest,room:QuestRoom):QuestPrize{const coins=QUEST_COINS[q.id]??100;return room.boss==='last'?{coins:coins*3,rarity:'L'}:room.boss==='sub'?{coins:coins*2,rarity:'R'}:{coins};}
export const questWon=(p:Profile,qid:string)=>p.quests?.[qid]||[];
export const questComplete=(p:Profile,q:Quest)=>q.rooms.filter(r=>r.boss==='last').every(r=>questWon(p,q.id).includes(r.n));
/** A quest opens when the one before it is finished (the tutorial and the easy quest are open from the start). */
export const questOpen=(p:Profile,q:Quest)=>{const i=QUESTS.indexOf(q);return i<=1||questComplete(p,QUESTS[i-1]);};
/** Room 1 is open; every other room opens once the room it hangs off has been won. */
export const roomOpen=(p:Profile,q:Quest,room:QuestRoom)=>questOpen(p,q)&&(room.parent===null||questWon(p,q.id).includes(room.parent));
export function cardOfRarity(r:Rarity,random=Math.random){const pool=cards.filter(c=>cardRarity(c)===r);return pool[Math.min(pool.length-1,Math.floor(Math.max(0,Math.min(.9999999,random()))*pool.length))];}
/** Records a won room once; the first win pays the room's prize. Returns the prize only when it was paid now. */
export function grantQuestRoom(profile:Profile,qid:string,n:number,random=Math.random):{profile:Profile,prize?:QuestPrize&{cardId?:string}}{const q=questById[qid],room=q?.rooms.find(r=>r.n===n);if(!q||!room||questWon(profile,qid).includes(n)||!roomOpen(profile,q,room))return {profile};const p=structuredClone(profile),prize:QuestPrize&{cardId?:string}=questPrize(q,room);p.quests={...(p.quests||{}),[qid]:[...questWon(p,qid),n]};p.coins+=prize.coins;if(prize.rarity){const c=cardOfRarity(prize.rarity,random);prize.cardId=c.id;p.inventory[c.id]=(p.inventory[c.id]||0)+1;}return {profile:p,prize};}
