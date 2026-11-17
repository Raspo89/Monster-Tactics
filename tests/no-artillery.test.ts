import {it,expect,describe} from 'vitest';
import {cards,cardById,retiredIds,validateDeck,formatStarterDeck} from '../src/engine/game';
import {aiDeck,raceDeck,starterCards,originalSkirmishDeck,loadProfile,retireArtillery,cardPrice,CHEST_TYPES,openChest,emptyProfile,chooseStarter} from '../src/engine/progression';
import raceData from '../src/data/races.json';

const races=Object.keys(raceData as any);
const isArt=(id:string)=>retiredIds.has(id);
describe('artillery is out of the game (7.26)',()=>{
 it('retires every artillery monster and every artillery weapon, and nothing else',()=>{
  expect(retiredIds.size).toBe(384+24+2);                       // + the two legacy artillery cards O03 and Z07
  for(const id of retiredIds){const c=cardById[id];expect(c.type==='unit'?(c.combatClass==='artillery'||id==='O03'||id==='Z07'):c.forClass==='artillery').toBe(true);}
  expect(cards.some(c=>isArt(c.id))).toBe(false);
 });
 it('old ids still resolve so saves load, but no deck with them is legal',()=>{
  const id=[...retiredIds][0];expect(cardById[id]).toBeTruthy();
  const deck=starterCards('human');deck[0]=id;expect(validateDeck(deck,'human','standard')).toMatch(/المدفعية/);
 });
 it('no deck the game builds contains them',()=>{
  for(const r of races){for(const t of ['normal','hard','expert'])expect(aiDeck(r,t).some(isArt)).toBe(false);}
  expect(raceDeck(races,'expert').some(isArt)).toBe(false);
  for(const r of ['human','zombie','orc','elf']){expect(starterCards(r).some(isArt)).toBe(false);for(const rule of ['standard','legacy','pauper','tribal','hordes','singleton'] as const)expect(formatStarterDeck(r,rule,true).some(isArt)).toBe(false);}
  let x=1;const rand=()=>{x=(x*16807)%2147483647;return x/2147483647;};
  for(let i=0;i<200;i++)expect(originalSkirmishDeck('standard',rand).deck.some(isArt)).toBe(false);
 });
 it('chests never hand them out',()=>{
  let p=chooseStarter(emptyProfile(),'human');p.chests={} as any;for(const t of CHEST_TYPES)(p.chests as any)[t]=20;
  for(const t of CHEST_TYPES)for(let i=0;i<20;i++){const o=openChest(p,t);p=o.profile;for(const id of o.opened?.cards||[])expect(isArt(id)).toBe(false);}
 });
 it('owned copies are refunded at shop price, once',()=>{
  const ids=[...retiredIds].slice(0,3);const raw={version:1,coins:50,inventory:{[ids[0]]:2,[ids[1]]:1,[ids[2]]:4,S01:3},starterRace:'human',starterDeck:[],wins:0,receipts:{}};
  const want=50+cardPrice(cardById[ids[0]])*2+cardPrice(cardById[ids[1]])+cardPrice(cardById[ids[2]])*4;
  const p=loadProfile(raw);expect(p.coins).toBe(want);expect(p.refund).toEqual({cards:7,coins:want-50});
  expect(Object.keys(p.inventory).some(isArt)).toBe(false);expect(p.inventory.S01).toBe(3);
  const again=retireArtillery({...p,refund:undefined,inventory:{...p.inventory}});expect(again.coins).toBe(want);expect(again.refund).toBeUndefined();
 });
 it('a starter deck that held them is rebuilt without them',()=>{
  const deck=starterCards('orc');deck[0]=[...retiredIds][0];
  const p=loadProfile({version:1,coins:0,inventory:{},starterRace:'orc',starterDeck:deck,wins:0,receipts:{}});
  expect(p.starterDeck.some(isArt)).toBe(false);expect(validateDeck(p.starterDeck,'orc','standard')).toBe('');
 });
});
