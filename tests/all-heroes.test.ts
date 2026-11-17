import {describe,it,expect} from 'vitest';
import {nativeHeroes,newGame,applyAction,chooseAI,starterDeck,leader,effectiveStats} from '../src/engine/game';
import visual from '../src/data/visual-manifest.json';
import models from '../public/original3d/model-manifest.json';

// 7.26: the four heroes the quests never used (Minotrix, Booga, Ocularus, Kargadan) are in the game too.
const NEW={hero_minotrix:{attack:0,health:30,armor:2,mojo:5,combatClass:'warrior',abilityId:'AT_BOO'},hero_slime:{attack:0,health:10,armor:1,mojo:6,combatClass:'archer',abilityId:'AT_SNIPE'},hero_artil1:{attack:0,health:15,armor:0,mojo:7,combatClass:'artillery'},hero_artil2:{attack:3,health:30,armor:1,mojo:5,combatClass:'artillery'}};
describe('all original heroes',()=>{
 it('has all 22 heroes of the original hero table',()=>{expect(Object.keys(nativeHeroes)).toHaveLength(22);for(const [k,h] of Object.entries(NEW))expect(nativeHeroes[k]).toMatchObject(h);});
 it('every hero has a portrait and a 3D model',()=>{for(const k of Object.keys(nativeHeroes)){expect((visual as any).portraits['LEADER_'+k],k).toBeTruthy();if(k.startsWith('hero_'))expect((models as any)[k],k).toBeTruthy();}});
 it('the new heroes lead a player side and finish a match',()=>{for(const [i,k] of Object.keys(NEW).entries()){let s=newGame(900+i,starterDeck('lizard',true),k,starterDeck('orc',true),Object.keys(NEW)[(i+1)%4],'plain',true);const l=leader(s,0)!;expect(effectiveStats(s,l).attack).toBe((NEW as any)[k].attack);expect(l.health).toBe((NEW as any)[k].health);s=applyAction(s,{kind:'mulligan',indexes:[]});s=applyAction(s,{kind:'mulligan',indexes:[]});for(let n=0;n<2000&&s.winner===undefined;n++)s=applyAction(s,chooseAI(s,'normal'));expect(s.winner,k).toBeDefined();}},120000);
});
