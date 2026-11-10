/** Absolute site root, so asset URLs also work inside CSS variables and when the game is served from a sub-folder (GitHub Pages). */
export const BASE=new URL(import.meta.env.BASE_URL,location.href).href;
import visual from '../data/visual-manifest.json';
import magic from '../data/catalog-magic.json';
const magicArt=Object.fromEntries((magic as any[]).map(c=>[c.id,(c.type==='rune'?'runes/':'spells/')+c.art+'.webp']));
/** Image path of a rune card, used for both the card and the stone on its stand. */
export const runeArtPath=(id:string)=>magicArt[id]||'runes/'+id+'.webp';
export function art(id:string){if(id.startsWith('LEADER_'))return {human:'a0',zombie:'a8',orc:'b0',elf:'b8'}[id.slice(7)]||'a0';const prefix=id[0],n=+id.slice(1);if(prefix==='H')return ['a1','a2','a3','a4','a5','a6','a7','a0'][n-1];if(prefix==='Z')return ['a9','a10','a11','a12','a13','a14','a15','a8'][n-1];if(prefix==='O')return ['b1','b2','b3','b4','b5','b6','b0','b7'][n-1];if(prefix==='E')return ['b9','b10','b11','b12','b13','b14','b15','b8'][n-1];if(prefix==='N')return 'p'+(n-1);return ({S01:'p8',S02:'p9',S03:'p6',S04:'p10',S05:'p11',W01:'p12',W02:'p13',A01:'p14',A02:'p15',R01:'p6',R02:'p11'} as Record<string,string>)[id]||'p6';}
export const assetUrl=(name:string)=>(window as any).__ASSETS__?.[name]||`${BASE}assets/${name}.webp`;
export const originalUrl=(path:string)=>(window as any).__ORIGINAL__?.[path]||`${BASE}assets/original/${path}`;
export const artUrl=(id:string)=>magicArt[id]?originalUrl(magicArt[id]):(id.startsWith('CM_')||id.startsWith('NA_')||id.startsWith('NM_'))?originalUrl((visual.portraits as any)[id]?.path||`portraits/${id}.webp`):/^R0[1-7]$/.test(id)?originalUrl('runes/'+id+'.webp'):/^(H|Z|O|E|N)\d{2}$/.test(id)||id.startsWith('LEADER_')?originalUrl(`portraits/${id}.webp`):id==='W01'?originalUrl('portraits/weapon_staff.webp'):id==='W02'?originalUrl('portraits/weapon_axe.webp'):assetUrl(art(id));
