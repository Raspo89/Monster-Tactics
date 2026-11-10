import sys,os,json,numpy as np
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from PIL import Image
sys.path.insert(0,'/workspace/scratch/d96bc0fd2488/model-conversion')
import bake_fallback as b
OUT=Path('/workspace/scratch/d96bc0fd2488/pov-site/.sites-checkout/public/assets/original/pov');OUT.mkdir(exist_ok=True)
def bake(job):
 key,side=job;angle=np.deg2rad(54.25);b.EYE=np.array([0,np.sin(angle),np.cos(angle)*(1 if side=='back' else -1)]);b.RIGHT=np.cross([0,1,0],b.EYE);b.RIGHT/=np.linalg.norm(b.RIGHT);b.UP=np.cross(b.EYE,b.RIGHT)
 entry=b.MAN[key];path=(b.ROOT/entry['json']).parent;model=json.loads((b.ROOT/entry['json']).read_text());groups=b.prepare(model,path,0);atlas=Image.new('RGBA',(160*8,180*3));bounds=[]
 for clip in ['idle','walk','attack']:
  count=len(b.AN['clips'][clip]['frames'])
  for col in range(8):
   mm=b.pose_matrices(model,clip,round(col*(count-1)/7))
   for g,t in groups:
    v=b.skin(model,g,mm);bounds.append(np.c_[v@b.RIGHT,v@b.UP])
 xy=np.concatenate(bounds);lo=xy.min(0);hi=xy.max(0);framing=(min(160*.88/(hi[0]-lo[0]),180*.88/(hi[1]-lo[1])),(lo[0]+hi[0])/2,(lo[1]+hi[1])/2)
 for row,clip in enumerate(['idle','walk','attack']):
  count=len(b.AN['clips'][clip]['frames'])
  for col in range(8):atlas.paste(b.render(model,groups,160,180,clip,round(col*(count-1)/7),framing),(col*160,row*180))
 atlas.save(OUT/f'{key}-{side}.webp',quality=88,method=3);return key+' '+side
if __name__=='__main__':
 with ProcessPoolExecutor(max_workers=6) as ex:
  for f in as_completed([ex.submit(bake,(k,s)) for k in b.MAN for s in ['back','front']]):print(f.result(),flush=True)
