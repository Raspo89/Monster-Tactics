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
export type Profile={version:1,coins:number,inventory:Record<string,number>,starterRace?:string,starterDeck:string[],wins:number,receipts:Record<string,Reward>,quests?:Record<string,number[]>,chests?:Partial<Record<ChestType,number>>,gifts?:string[]};
export const emptyProfile=():Profile=>({version:1,coins:100,inventory:{},starterDeck:[],wins:0,receipts:{}});
export function loadProfile(raw:any):Profile{const p=emptyProfile();if(!raw||raw.version!==1)return p;p.coins=Number.isSafeInteger(raw.coins)&&raw.coins>=0?raw.coins:100;p.wins=Number.isSafeInteger(raw.wins)&&raw.wins>=0?raw.wins:0;for(const [id,n] of Object.entries(raw.inventory||{}))if(cardById[id]&&Number.isSafeInteger(n)&&Number(n)>0)p.inventory[id]=Number(n);p.starterRace=typeof raw.starterRace==='string'?raw.starterRace:undefined;p.starterDeck=Array.isArray(raw.starterDeck)?raw.starterDeck.filter((id:any)=>typeof id==='string'&&cardById[id]):[];for(const [id,r] of Object.entries(raw.receipts||{}))if(r&&typeof r==='object'&&cardById[(r as Reward).cardId])p.receipts[id]=r as Reward;if(Array.isArray(raw.gifts))p.gifts=raw.gifts.filter((g:any)=>typeof g==='string').slice(0,100);if(raw.chests&&typeof raw.chests==='object'){p.chests={};for(const k of CHEST_TYPES){const n=raw.chests[k];if(Number.isSafeInteger(n)&&n>0)p.chests[k]=n;}}if(raw.quests&&typeof raw.quests==='object'){p.quests={};for(const q of QUESTS){const won=raw.quests[q.id];if(Array.isArray(won))p.quests[q.id]=[...new Set(won.filter((n:any)=>q.rooms.some(r=>r.n===n)))] as number[];}}upgradeStarter(p);return p;}
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
export type QuestPrize={coins:number,chest?:ChestType};
export function questPrize(q:Quest,room:QuestRoom):QuestPrize{const coins=QUEST_COINS[q.id]??100;return room.boss==='last'?{coins:coins*3,chest:q.id==='hard3'?'epic':'mega'}:room.boss==='sub'?{coins:coins*2,chest:'full'}:{coins};}
export const questWon=(p:Profile,qid:string)=>p.quests?.[qid]||[];
export const questComplete=(p:Profile,q:Quest)=>q.rooms.filter(r=>r.boss==='last').every(r=>questWon(p,q.id).includes(r.n));
/** A quest opens when the one before it is finished (the tutorial and the easy quest are open from the start). */
export const questOpen=(p:Profile,q:Quest)=>{const i=QUESTS.indexOf(q);return i<=1||questComplete(p,QUESTS[i-1]);};
/** Room 1 is open; every other room opens once the room it hangs off has been won. */
export const roomOpen=(p:Profile,q:Quest,room:QuestRoom)=>questOpen(p,q)&&(room.parent===null||questWon(p,q.id).includes(room.parent));
export function cardOfRarity(r:Rarity,random=Math.random){const pool=cards.filter(c=>cardRarity(c)===r);return pool[Math.min(pool.length-1,Math.floor(Math.max(0,Math.min(.9999999,random()))*pool.length))];}
/** Records a won room once; the first win pays the room's prize. Returns the prize only when it was paid now. */
export function grantQuestRoom(profile:Profile,qid:string,n:number):{profile:Profile,prize?:QuestPrize}{const q=questById[qid],room=q?.rooms.find(r=>r.n===n);if(!q||!room||questWon(profile,qid).includes(n)||!roomOpen(profile,q,room))return {profile};const p=structuredClone(profile),prize=questPrize(q,room);p.quests={...(p.quests||{}),[qid]:[...questWon(p,qid),n]};p.coins+=prize.coins;if(prize.chest)p.chests={...(p.chests||{}),[prize.chest]:(p.chests?.[prize.chest]||0)+1};return {profile:p,prize};}

// ---- Booster chests (original Furniture/Chest textures, contents from the original chest descriptions) ----
export type ChestType='mini'|'full'|'monster'|'equipment'|'rune'|'spell'|'mega'|'epic'|'mystery';
export const CHEST_TYPES:ChestType[]=['mini','full','monster','equipment','rune','spell','mega','epic','mystery'];
type Slot=Rarity|'roll'|'rare+';
export const CHESTS:Record<ChestType,{name:string,english:string,text:string,price?:number,slots?:Slot[],pool?:(c:Card)=>boolean}>={
 mini:{name:'الصندوق الصغير',english:'Mini Chest',text:'6 بطاقات عشوائية. ما فيه شي مضمون، بس من يدري...',price:300,slots:Array(6).fill('roll')},
 full:{name:'الصندوق الكامل',english:'Full Chest',text:'12 بطاقة عشوائية، مضمون فيها: بطاقة نادرة (وفيه احتمال بسيط تطلع أسطورية) و3 غير شائعة.',price:900,slots:['rare+','U','U','U',...Array(8).fill('roll')]},
 monster:{name:'صندوق الوحوش',english:'Monster Chest',text:'12 وحش عشوائي، مضمون فيها: وحش نادر (أو أسطوري أحيانًا) و3 غير شائعة.',price:900,slots:['rare+','U','U','U',...Array(8).fill('roll')],pool:c=>c.type==='unit'},
 equipment:{name:'صندوق المعدات',english:'Equipment Chest',text:'12 قطعة سلاح ودرع وترس عشوائية، مضمون فيها: قطعة نادرة (أو أسطورية أحيانًا) و3 غير شائعة.',price:900,slots:['rare+','U','U','U',...Array(8).fill('roll')],pool:c=>c.type==='weapon'||c.type==='armor'},
 rune:{name:'صندوق الرونات',english:'Rune Chest',text:'12 رون عشوائي، مضمون فيها: رون نادر (أو أسطوري أحيانًا) و3 غير شائعة.',price:900,slots:['rare+','U','U','U',...Array(8).fill('roll')],pool:c=>c.type==='rune'},
 spell:{name:'صندوق التعاويذ',english:'Spell Chest',text:'12 تعويذة عشوائية، مضمون فيها: تعويذة نادرة (أو أسطورية أحيانًا) و3 غير شائعة.',price:900,slots:['rare+','U','U','U',...Array(8).fill('roll')],pool:c=>c.type==='spell'},
 mega:{name:'الصندوق الضخم',english:'Mega Chest',text:'12 بطاقة عشوائية، مضمون فيها: بطاقة أسطورية و3 نادرة و8 غير شائعة.',price:2800,slots:['L','R','R','R',...Array(8).fill('U')]},
 epic:{name:'الصندوق الملحمي',english:'Epic Chest',text:'12 بطاقة أسطورية! ما ينباع، لازم تكسبه.',slots:Array(12).fill('L')},
 mystery:{name:'الصندوق الغامض',english:'Mystery Chest',text:'جائزة خاصة، ومحتواه عشوائي: بطاقات أو عملات أو صناديق ثانية.'},
};
export const chestCount=(p:Profile,t:ChestType)=>p.chests?.[t]||0;
export function grantChest(profile:Profile,t:ChestType,n=1):Profile{const p=structuredClone(profile);p.chests={...(p.chests||{}),[t]:chestCount(p,t)+n};return p;}
export function buyChest(profile:Profile,t:ChestType):{profile:Profile,error?:string}{const price=CHESTS[t].price;if(!price)return {profile,error:'هذا الصندوق ما ينباع، لازم تكسبه'};if(!profile.starterRace)return {profile,error:'اختر مجموعة البداية أولًا'};if(profile.coins<price)return {profile,error:'رصيد العملات غير كافٍ'};const p=grantChest(profile,t);p.coins-=price;return {profile:p};}
const RARITIES:Rarity[]=['C','U','R','L'];
function slotRarity(slot:Slot,random:()=>number):Rarity{if(slot==='roll'){let v=Math.max(0,Math.min(.9999999,random()))*100;for(const r of rarityOrder){v-=rarityInfo[r].weight;if(v<0)return r;}return 'L';}if(slot==='rare+')return random()<.1?'L':'R';return slot;}
function pickCard(pool:Card[],r:Rarity,random:()=>number){let list=pool.filter(c=>cardRarity(c)===r);for(let i=RARITIES.indexOf(r);!list.length&&i>=0;i--)list=pool.filter(c=>cardRarity(c)===RARITIES[i]);if(!list.length)list=pool;return list[Math.min(list.length-1,Math.floor(Math.max(0,Math.min(.9999999,random()))*list.length))];}
export type ChestOpening={type:ChestType,cards:string[],coins:number,chests:ChestType[]};
/** Opens one chest of the given type: removes it, adds its cards / coins / chests to the profile. */
export function openChest(profile:Profile,t:ChestType,random=Math.random):{profile:Profile,opened?:ChestOpening,error?:string}{if(chestCount(profile,t)<1)return {profile,error:'ما عندك من هذا الصندوق'};const p=structuredClone(profile);p.chests={...p.chests,[t]:chestCount(p,t)-1};const opened:ChestOpening={type:t,cards:[],coins:0,chests:[]};const def=CHESTS[t];
 if(t==='mystery'){const roll=random();if(roll<.35)opened.coins=150+Math.floor(random()*10)*50;else if(roll<.75){const c=random();opened.chests.push(c<.01?'epic':c<.1?'mega':c<.4?'full':c<.65?(['monster','equipment','rune','spell'] as ChestType[])[Math.floor(random()*4)]:'mini');}else for(let i=0;i<3;i++)opened.cards.push(rollCard(random).id);}
 else{const pool=cards.filter(c=>!def.pool||def.pool(c));for(const slot of def.slots!)opened.cards.push(pickCard(pool,slotRarity(slot,random),random).id);}
 for(const id of opened.cards)p.inventory[id]=(p.inventory[id]||0)+1;p.coins+=opened.coins;for(const c of opened.chests)p.chests[c]=(p.chests[c]||0)+1;return {profile:p,opened};}

// ---- Computer decks that grow with the difficulty ----
/** Rough strength of a monster for its Mojo cost (power counts more than health; an active ability is worth about two points). */
const unitScore=(c:Card)=>((c.attack||0)*1.6+(c.health||0)+(c.armor||0)*1.5+(c.abilityId?2:0))/Math.max(1.5,c.cost);
const AI_TIERS:Record<string,{rarities:Rarity[],maxCost:number,weaponRarities:Rarity[]}>={hard:{rarities:['C','U','R'],maxCost:5,weaponRarities:['C','U','R']},expert:{rarities:['C','U','R','L'],maxCost:6,weaponRarities:['U','R','L']}};
/**
 * Easy and normal play the starter deck. Hard plays a veteran deck (best commons to rares of its race, up to 5 Mojo)
 * and expert a champion deck (rares and legendaries allowed, up to 6 Mojo), each with weapons for its classes.
 */
export function aiDeck(race:string,difficulty:string){const tier=AI_TIERS[difficulty];if(!tier)return starterCards(race);const pool=cards.filter(c=>c.type==='unit'&&c.race===race&&(c.id.startsWith('CM_')||c.id.startsWith('NA_'))&&tier.rarities.includes(cardRarity(c))&&c.cost>=2&&c.cost<=tier.maxCost).sort((a,b)=>unitScore(b)-unitScore(a)||a.id.localeCompare(b.id));if(pool.length<5)return starterCards(race);const picked:Card[]=[];for(const cls of ['warrior','archer','mage','warrior']){const c=pool.find(c=>c.combatClass===cls&&!picked.includes(c));if(c)picked.push(c);}for(const c of pool)if(picked.length<5&&!picked.includes(c))picked.push(c);
 const weapon=(cls:string)=>cards.filter(c=>c.type==='weapon'&&c.id.startsWith('NE_')&&c.forClass===cls&&tier.weaponRarities.includes(cardRarity(c))&&!Object.values(c.equip||{}).some(v=>typeof v==='number'&&v<0)).sort((a,b)=>(b.equip?.attack||0)/Math.max(1,b.cost)-(a.equip?.attack||0)/Math.max(1,a.cost)||a.cost-b.cost||a.id.localeCompare(b.id))[0]?.id;
 const classes=[...new Set(picked.map(c=>c.combatClass||'warrior'))],weapons=[...classes,classes[0]].flatMap(cls=>{const w=weapon(cls);return w?[w]:[];}).slice(0,4);
 const armour=cards.filter(c=>c.id.startsWith('NE_')&&c.slot==='armor'&&tier.weaponRarities.includes(cardRarity(c))&&(c.equip?.armor||0)>0&&!Object.values(c.equip||{}).some(v=>typeof v==='number'&&v<0)).sort((a,b)=>(b.equip!.armor!+(b.equip!.health||0)/2)/b.cost-(a.equip!.armor!+(a.equip!.health||0)/2)/a.cost||a.id.localeCompare(b.id))[0]?.id;
 const deck=[...picked.slice(0,5).flatMap(c=>[c.id,c.id,c.id,c.id]),'R03','R03','S01','S02',...weapons,...(armour?[armour]:[])];while(deck.length<30)deck.push(deck.length%2?'S02':'S01');return deck.slice(0,30);}

// ---- One-time gifts (each is given once per save) ----
export const GIFTS:{id:string,title:string,chests:ChestType[]}[]=[
 {id:'gift-2026-11-chests10',title:'هدية: 10 صناديق',chests:['full','full','full','full','monster','equipment','rune','spell','mega','mystery']},
];
export function claimGifts(profile:Profile):{profile:Profile,claimed:typeof GIFTS}{if(!profile.starterRace)return {profile,claimed:[]};const todo=GIFTS.filter(g=>!profile.gifts?.includes(g.id));if(!todo.length)return {profile,claimed:[]};let p=structuredClone(profile);for(const g of todo){for(const c of g.chests)p=grantChest(p,c);p.gifts=[...(p.gifts||[]),g.id];}return {profile:p,claimed:todo};}
