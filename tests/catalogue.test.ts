import {it,expect} from 'vitest';
// @ts-ignore node module in tests
import {readFileSync,existsSync} from 'node:fs';
import {cards,cardById,starterDeck,formatStarterDeck,validateDeck} from '../src/engine/game';
import {starterCards} from '../src/engine/progression';
import abilities from '../src/data/abilities.json';
import visual from '../src/data/visual-manifest.json';
const table=(JSON.parse(readFileSync('reference/native-rules/table-3189a0.json','utf8')) as any[]).filter(r=>r.Race&&r.Rarity!=='B');
const CLASS:Record<string,[string,number]>={CT_FIGHTER:['warrior',1],CT_RANGER:['archer',3],CT_MAGE:['mage',2],CT_ARTIL:['artillery',3]};
it('every original monster is in the game exactly once, with its printed stats',()=>{
 const byTag=new Map<string,any[]>();for(const c of cards)if(c.nativeTag?.startsWith('RT_'))byTag.set(c.nativeTag,[...(byTag.get(c.nativeTag)||[]),c]);
 expect(table).toHaveLength(1536);
 for(const r of table){const found=byTag.get(`${r.Race}:${r.Name}`)||[];expect(found,r.Name).toHaveLength(1);const c=found[0];
  expect([c.cost,c.attack,c.health,c.rarity,c.combatClass,c.range,c.abilityId||'AT_NONE']).toEqual([+r.Mojo,+r.Power,+r.Health,r.Rarity,CLASS[r.Class][0],CLASS[r.Class][1],r.Ability]);}
 expect(new Set(cards.map(c=>c.id)).size).toBe(cards.length);
 for(const c of cards)if(c.abilityId)expect((abilities as any)[c.abilityId],c.id).toBeDefined();
});
it('every original monster has a portrait and a 3D texture that exist in the package',()=>{
 const models=JSON.parse(readFileSync('public/original3d/model-manifest.json','utf8'));
 for(const c of cards.filter(c=>c.nativeTag?.startsWith('RT_'))){const p=(visual.portraits as any)[c.id];expect(p,c.id).toBeDefined();
  if(existsSync('public/original3d')){const dir=models[p.model].json.replace(/[^/]+$/,'');expect(models[p.model].skins.some((f:string)=>parseInt(f)===p.skin&&existsSync(`public/original3d/${dir}${f}`)),c.id).toBe(true);}
  if(existsSync('public/assets/original'))expect(existsSync('public/assets/original/'+p.path),c.id).toBe(true);}
});
it('starter decks and AI decks are unchanged by the catalogue import',()=>{
 for(const race of ['human','zombie','orc','elf']){expect(starterCards(race).every((c:any)=>!String(c?.id??c).startsWith('NM_'))).toBe(true);expect(starterDeck(race,true).some(id=>id.startsWith('NM_'))).toBe(false);}
 for(const rule of ['standard','singleton','tribal','pauper','hordes'] as const)for(const race of ['human','orc','lizard','vampire']){const d=formatStarterDeck(race,rule,true);expect(d.some(id=>id.startsWith('NM_'))).toBe(false);expect(validateDeck(d,race,rule)).toBe('');}
 expect(cardById['NM_human_002']===undefined||cardById['NM_human_002'].race==='human').toBe(true);
});
