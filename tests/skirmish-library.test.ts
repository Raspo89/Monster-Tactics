import {it,expect,describe} from 'vitest';
import {newGame,validateDeck,nativeHeroes,dealExtraCards,cardById} from '../src/engine/game';
import {originalSkirmishDeck} from '../src/engine/progression';
import lib from '../src/data/skirmish-decks.json';

const seq=(seed:number)=>{let r=seed;return ()=>{r=(r*16807)%2147483647;return r/2147483647;};};
describe('original Skirmish deck library (CEnemyDeckMgr)',()=>{
 it('imports the whole library of 227 decks',()=>{expect(lib.decks.length).toBe(227);});
 it('always hands out a legal deck with monsters, led by a hero this game has',()=>{
  const rand=seq(7);
  for(let i=0;i<300;i++){const p=originalSkirmishDeck('standard',rand);
   expect(validateDeck(p.deck,'human','standard')).toBe('');
   expect(p.deck.some(id=>cardById[id]?.type==='unit')).toBe(true);
   expect((nativeHeroes as any)[p.hero]).toBeTruthy();}
 });
 it('leads a deck with a hero of an allowed class whose Mojo covers the deck, when one exists',()=>{
  const rand=seq(11);
  for(let i=0;i<300;i++){const p=originalSkirmishDeck('standard',rand);const d=lib.decks.find(x=>x.name===p.name)!;
   const h=(nativeHeroes as any)[p.hero];const cands=d.heroClasses.flatMap(c=>(lib.heroes as any)[c]).filter((x:any)=>(nativeHeroes as any)[x.key]&&x.mojo>=d.mojoNeeded);
   if(cands.length){expect(d.heroClasses).toContain(h.combatClass);expect(h.mojo).toBeGreaterThanOrEqual(d.mojoNeeded);}}
 });
 it('uses many different decks and heroes',()=>{
  const rand=seq(3),decks=new Set<string>(),heroes=new Set<string>();
  for(let i=0;i<500;i++){const p=originalSkirmishDeck('standard',rand);decks.add(p.name);heroes.add(p.hero);}
  expect(decks.size).toBeGreaterThan(100);expect(heroes.size).toBeGreaterThan(12);
 });
 it('extra starting cards move from the deck to the hand',()=>{
  const p=originalSkirmishDeck('standard',seq(5));
  const s=newGame(1,p.deck,p.hero,p.deck,p.hero,'plain',true,'standard',true);
  const hand=s.players[1].hand.length,deck=s.players[1].deck.length;
  dealExtraCards(s,1,3);
  expect(s.players[1].hand.length).toBe(hand+3);expect(s.players[1].deck.length).toBe(deck-3);
 });
});
