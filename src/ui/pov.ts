import {PerspectiveCamera,Vector3} from 'three';
import {Hex} from '../engine/game';
export const VIEW_WIDTH=1120,VIEW_HEIGHT=650,CELL=1.05;
export function world(h:Hex,owner=0){const sign=owner===0?1:-1;return {x:(h.r-3)*Math.sqrt(3)/2*CELL*sign,z:(4.25-h.q-h.r/2)*CELL*sign};}
/** One shared camera projects the grid, hit targets, models, props and labels. */
export class PovCamera{
 camera=new PerspectiveCamera(35,VIEW_WIDTH/VIEW_HEIGHT,.1,120);zoom=1;panX=0;panY=0;owner=0;
 constructor(public overhead=false){this.camera.position.set(0,overhead?15:12.5,overhead?6:9);this.camera.lookAt(0,0,0);this.refresh();}
 refresh(){this.camera.zoom=this.zoom;this.camera.setViewOffset(VIEW_WIDTH,VIEW_HEIGHT,-this.panX,-this.panY,VIEW_WIDTH,VIEW_HEIGHT);this.camera.updateProjectionMatrix();this.camera.updateMatrixWorld();}
 point(x:number,y:number,z:number){const v=new Vector3(x,y,z).project(this.camera);return {x:(v.x+1)*VIEW_WIDTH/2,y:(1-v.y)*VIEW_HEIGHT/2};}
 project(h:Hex,height=0){const w=world(h,this.owner);return this.point(w.x,height,w.z);}
 pixels(h:Hex){const w=world(h,this.owner),a=this.point(w.x,0,w.z),b=this.point(w.x+1,0,w.z);return Math.hypot(a.x-b.x,a.y-b.y);}
 polygon(h:Hex,scale=1){const w=world(h,this.owner);return Array.from({length:6},(_,i)=>{const a=i*Math.PI/3;return this.point(w.x+Math.cos(a)*CELL/Math.sqrt(3)*scale,0,w.z+Math.sin(a)*CELL/Math.sqrt(3)*scale);});}
 zoomBy(factor:number){this.zoom=Math.max(.45,Math.min(1.65,this.zoom*factor));this.refresh();}
 reset(){this.zoom=1;this.panX=this.panY=0;this.refresh();}
}
export function insidePolygon(x:number,y:number,p:{x:number,y:number}[]){let inside=false;for(let i=0,j=p.length-1;i<p.length;j=i++)if((p[i].y>y)!==(p[j].y>y)&&x<(p[j].x-p[i].x)*(y-p[i].y)/(p[j].y-p[i].y)+p[i].x)inside=!inside;return inside;}
