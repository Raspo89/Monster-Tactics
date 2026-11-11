import {it,expect,describe} from 'vitest';
import {collectSave,encodeSave,decodeSave,applySave} from '../src/ui/save-transfer';
class Mem implements Storage{m=new Map<string,string>();get length(){return this.m.size;}clear(){this.m.clear();}getItem(k:string){return this.m.get(k)??null;}key(i:number){return [...this.m.keys()][i]??null;}removeItem(k:string){this.m.delete(k);}setItem(k:string,v:string){this.m.set(k,String(v));}}
describe('moving progress between devices',()=>{
 it('a save code carries every game key except the running battle, and restores it on another device',async()=>{const phone=new Mem();const inv:Record<string,number>={};for(let i=0;i<900;i++)inv['CM_'+i]=1+i%4;phone.setItem('mt-profile-v7',JSON.stringify({version:1,coins:1234,inventory:inv,starterRace:'human',starterDeck:[],wins:7,receipts:{},quests:{easy:[1,2]},chests:{full:2}}));phone.setItem('mt-saved-decks','[{"id":"d1"}]');phone.setItem('mt-battle','{"huge":true}');phone.setItem('other-site','x');
  const code=await encodeSave(collectSave(phone));expect(code.startsWith('MT1:')).toBe(true);expect(code.length).toBeLessThan(6000);
  const pc=new Mem();pc.setItem('mt-profile-v7','{"coins":5}');pc.setItem('mt-battle','{"old":1}');pc.setItem('other-site','keep');
  applySave(await decodeSave('  '+code.slice(0,40)+'\n'+code.slice(40)+' '),pc);
  expect(JSON.parse(pc.getItem('mt-profile-v7')!).coins).toBe(1234);expect(pc.getItem('mt-saved-decks')).toBe('[{"id":"d1"}]');expect(pc.getItem('mt-battle')).toBeNull();expect(pc.getItem('other-site')).toBe('keep');});
 it('rejects text that is not a save code or was damaged',async()=>{await expect(decodeSave('hello')).rejects.toThrow();const code=await encodeSave({v:1,at:'x',data:{'mt-a':'1'}});await expect(decodeSave(code.slice(0,-6))).rejects.toThrow();await expect(decodeSave('MT0:'+btoa('{"v":1,"data":{"evil":"x"}}'))).rejects.toThrow();});
});
