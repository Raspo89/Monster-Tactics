import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from concurrent.futures import ProcessPoolExecutor,as_completed
BASE=Path('/workspace/scratch/d96bc0fd2488');SITE=BASE/'races-site/.sites-checkout'
sys.path.insert(0,str(BASE/'model-conversion'))
import bake_fallback as b
b.ROOT=SITE/'public/original3d';b.MAN=json.loads((b.ROOT/'model-manifest.json').read_text());b.AN=json.loads((b.ROOT/'animations.json').read_text());b.AN_NAMES=b.AN['boneNames']
plan=json.loads((SITE/'src/data/race-card-plan.json').read_text());OUT=SITE/'public/assets/original';VIS=json.loads((SITE/'src/data/visual-manifest.json').read_text());META=json.loads((SITE/'src/data/pov-sprites.json').read_text())
def portrait(item):
 key=item['model'];entry=b.MAN[key];path=(b.ROOT/entry['json']).parent;model=json.loads((b.ROOT/entry['json']).read_text());groups=b.prepare(model,path,item['skin']);b.EYE=np.array([-1.1,.9,-2.2]);b.EYE/=np.linalg.norm(b.EYE);b.RIGHT=np.cross([0,1,0],b.EYE);b.RIGHT/=np.linalg.norm(b.RIGHT);b.UP=np.cross(b.EYE,b.RIGHT)
 im=b.render(model,groups,256,300);im.save(OUT/'portraits'/f'{item["id"]}.webp',quality=91,method=3);return item['id']
def sheet(job):
 key,side=job;angle=np.deg2rad(54.25);b.EYE=np.array([0,np.sin(angle),np.cos(angle)*(1 if side=='back' else -1)]);b.RIGHT=np.cross([0,1,0],b.EYE);b.RIGHT/=np.linalg.norm(b.RIGHT);b.UP=np.cross(b.EYE,b.RIGHT)
 entry=b.MAN[key];path=(b.ROOT/entry['json']).parent;model=json.loads((b.ROOT/entry['json']).read_text());groups=b.prepare(model,path,0);atlas=Image.new('RGBA',(160*8,180*3));bounds=[]
 for clip in ['idle','walk','attack']:
  count=len(b.AN['clips'][clip]['frames'])
  for col in range(8):
   mm=b.pose_matrices(model,clip,round(col*(count-1)/7))
   for g,t in groups:
    v=b.skin(model,g,mm);bounds.append(np.c_[v@b.RIGHT,v@b.UP])
 xy=np.concatenate(bounds);lo=xy.min(0);hi=xy.max(0);scale=min(160*.88/(hi[0]-lo[0]),180*.88/(hi[1]-lo[1]));center=(lo+hi)/2;framing=(scale,center[0],center[1])
 for row,clip in enumerate(['idle','walk','attack']):
  count=len(b.AN['clips'][clip]['frames'])
  for col in range(8):atlas.paste(b.render(model,groups,160,180,clip,round(col*(count-1)/7),framing),(col*160,row*180))
 atlas.save(OUT/'pov'/f'{key}-{side}.webp',quality=88,method=3)
 verts=np.concatenate([np.array(g.get('idlePositions') or g['positions']).reshape(-1,3) for g in model['groups']]);height=float(np.ptp(verts[:,1]));meta={'originX':float((80-center[0]*scale)/160),'originY':float((90+center[1]*scale)/180),'pixelsPerUnit':float(scale),'height':height}
 return key+'-'+side,meta
if __name__=='__main__':
 jobs=[]
 for key in sorted(set(x['model'] for x in plan)):
  for side in ['back','front']:
   if not (OUT/'pov'/f'{key}-{side}.webp').exists():jobs.append((key,side))
 with ProcessPoolExecutor(max_workers=6) as ex:
  futures={ex.submit(sheet,job):'sheet' for job in jobs};futures.update({ex.submit(portrait,item):'portrait' for item in plan})
  for f in as_completed(futures):
   r=f.result()
   if futures[f]=='sheet':META[r[0]]=r[1];print('SHEET',r[0],flush=True)
   else:print('PORTRAIT',r,flush=True)
 for item in plan:VIS['portraits'][item['id']]={'model':item['model'],'skin':item['skin'],'path':'portraits/'+item['id']+'.webp'}
 for key in set(x['model'] for x in plan):
  VIS['sheets'][key]=('sheets/'+key+'.webp') if (OUT/'sheets'/f'{key}.webp').exists() else ('pov/'+key+'-front.webp')
 (SITE/'src/data/visual-manifest.json').write_text(json.dumps(VIS,indent=2));(SITE/'src/data/pov-sprites.json').write_text(json.dumps(META,indent=2))
 print('DONE',len(plan),len(jobs),flush=True)
