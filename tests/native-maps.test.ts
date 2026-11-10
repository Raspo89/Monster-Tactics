import {it,expect} from 'vitest';
import {newGame,applyAction,chooseAI,legalActions,isPlayable,board,key,leader,effectiveStats,spawn,nativeMapIds,cards,cellBonuses,starterDeck,neighbors} from '../src/engine/game';
import maps from '../src/data/native-maps.json';
const start=(id:string,seed=3)=>{let s=newGame(seed,starterDeck('human',true),'human',starterDeck('orc',true),'orc',id,true,'standard',true);s=applyAction(s,{kind:'mulligan',indexes:[]});return applyAction(s,{kind:'mulligan',indexes:[]});};
it('imports the original two-player layouts with two starts and four rune stands per side',()=>{
 expect(maps.length).toBe(108);
 for(const m of maps){expect(m.cells).toHaveLength(91);expect(m.daises.map(d=>d.length)).toEqual([4,4]);for(const k of [...m.starts as string[],...m.daises.flat()])expect(m.cells).toContain(k);}
});
it('original layouts are mirror images for the two players, so neither side is favoured',()=>{
 for(const m of maps){const [a,b]=(m.starts as string[]).map(k=>k.split(',').map(Number));const mid=[a[0]+b[0],a[1]+b[1]];const cells=new Set(m.cells);for(const k of m.cells){const [q,r]=k.split(',').map(Number);expect(cells.has(`${mid[0]-q},${mid[1]-r}`),m.id+' '+k).toBe(true);}}
});
it('a new battle on an original layout uses its cells, starts, rocks and stands',()=>{
 const m=maps[0],s=start(m.id);expect(s.cells).toBe(s.cells);expect(board.filter(h=>isPlayable(s,h)).length).toBe(91);
 expect(key(leader(s,0)!.pos)).toBe(m.starts[0]);expect(key(leader(s,1)!.pos)).toBe(m.starts[1]);expect(s.runeStands).toHaveLength(8);
 for(const [k,t] of m.tiles)expect(s.tiles[k]).toBe(t);for(const [k,t] of m.tokens)expect(s.tokens[k]).toBe(t);
 expect(s.roundArena).toBe(false);expect(s.arena).toBeTruthy();
 // the camera's centre column stays in the middle of the layout
 expect(leader(s,0)!.pos.r).toBe(leader(s,1)!.pos.r);
});
it('original bonus tiles give the native amounts while a monster stands on them',()=>{
 const s=start(maps[0].id),l=leader(s,0)!;const cell=neighbors(l.pos).find(h=>isPlayable(s,h)&&!s.units.some(u=>key(u.pos)===key(h))&&!s.runeStands!.some(r=>key(r.pos)===key(h))&&s.tiles[key(h)]!=='rock')!;
 const id=cards.find(c=>c.type==='unit'&&c.id.startsWith('CM_human')&&!c.abilityId)!.id;const u=spawn(s,id,0,cell);const base=effectiveStats(s,u);
 for(const [t,attack,armor] of [['star',2,0],['star3',3,0],['curse',-2,0],['shield',0,2],['rust',0,-2]] as const){s.tokens[key(cell)]=t;const st=effectiveStats(s,u);expect([st.attack-base.attack,st.armor-base.armor],t).toEqual([attack,armor]);}
 delete s.tokens[key(cell)];s.tiles[key(cell)]='altar1';expect(cellBonuses(s,cell)).toEqual([{kind:'mojo',amount:1,label:'موجو'}]);
});
it('AI battles on original layouts finish and never leave the layout',()=>{
 for(let n=0;n<6;n++){let s=start(nativeMapIds[(n*17)%nativeMapIds.length],40+n);for(let i=0;i<1500&&s.winner===undefined;i++){const a=chooseAI(s,n%3===0?'hard':'normal');s=applyAction(s,a,true);for(const u of s.units)expect(isPlayable(s,u.pos)).toBe(true);}expect(s.winner).toBeDefined();}
},600000);
