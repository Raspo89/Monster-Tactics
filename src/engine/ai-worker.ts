/// <reference lib="webworker" />
// Runs the computer's thinking off the main thread so the board keeps animating while it searches.
import {chooseAI,type GameState} from './game';
self.onmessage=(e:MessageEvent<{id:number,state:GameState,level:string}>)=>{
 const {id,state,level}=e.data;
 try{const action=chooseAI(state,level);(self as any).postMessage({id,action});}
 catch(err){(self as any).postMessage({id,error:String((err as any)?.stack||err)});}
};
