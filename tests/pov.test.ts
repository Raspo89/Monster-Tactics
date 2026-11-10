import {it,expect} from 'vitest';
import {PovCamera,insidePolygon,world} from '../src/ui/pov';
import {offset,board,key} from '../src/engine/game';
it('places our starting hero in the foreground and enemy behind',()=>{const p=new PovCamera();expect(p.project(offset(1,3)).y).toBeGreaterThan(p.project(offset(7,3)).y);expect(Math.abs(p.project(offset(1,3)).x-560)).toBeLessThan(1);});
it('all cell centers select the same projected cell',()=>{const p=new PovCamera();for(const owner of [0,1])for(const zoom of [.3,.45,.75,1,1.65]){p.owner=owner;p.zoom=zoom;p.panX=80;p.panY=-30;p.refresh();for(const h of board){const v=p.project(h),found=board.filter(c=>insidePolygon(v.x,v.y,p.polygon(c)));expect(found.map(key)).toEqual([key(h)]);}}});
it('the near side is larger, and opposite player sees their own army closest',()=>{const p=new PovCamera();expect(p.pixels(offset(1,3))).toBeGreaterThan(p.pixels(offset(7,3)));p.owner=1;expect(p.project(offset(7,3)).y).toBeGreaterThan(p.project(offset(1,3)).y);expect(world(offset(1,3),0).z).toBe(-world(offset(1,3),1).z);});
it('camera zoom respects its bounds and resets panning',()=>{const p=new PovCamera();p.zoomBy(99);expect(p.zoom).toBe(1.65);p.zoomBy(.0001);expect(p.zoom).toBe(.3);p.panX=100;p.reset();expect([p.zoom,p.panX,p.panY]).toEqual([1,0,0]);});
