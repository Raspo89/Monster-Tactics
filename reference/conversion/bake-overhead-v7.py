"""Bake native model animation fallbacks at the v7 camera elevation.
Only writes pov-v7 sheets and pov-sprites-v7.json; retains older fallbacks.
Run from any directory: python3 reference/conversion/bake-overhead-v7.py
"""
import json,sys,math,types
import numpy as np
from pathlib import Path
from PIL import Image
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor,as_completed
SITE=Path(__file__).resolve().parents[2]
ROOT=SITE/'public/original3d'
OUT=SITE/'public/assets/original/pov-v7'
OUT.mkdir(parents=True,exist_ok=True)
b=types.SimpleNamespace()
helper=Path(__file__).with_name('bake_fallback.py').read_text()
functions=helper[helper.index('def pose_matrices'):helper.index('def cardmap')]
ns={'np':np,'Image':Image,'json':json,'math':math,'Path':Path}
ns['AN']=json.loads((ROOT/'animations.json').read_text());ns['AN_NAMES']=ns['AN']['boneNames']
exec(functions,ns)
b.__dict__.update(ns)
b.ROOT=ROOT;b.MAN=json.loads((ROOT/'model-manifest.json').read_text())
def sheet(job):
 key,side=job
 angle=math.atan2(15,6)
 ns['EYE']=np.array([0,np.sin(angle),np.cos(angle)*(1 if side=='back' else -1)])
 ns['RIGHT']=np.cross([0,1,0],ns['EYE']);ns['RIGHT']/=np.linalg.norm(ns['RIGHT']);ns['UP']=np.cross(ns['EYE'],ns['RIGHT'])
 entry=b.MAN[key];path=(ROOT/entry['json']).parent;model=json.loads((ROOT/entry['json']).read_text())
 groups=b.prepare(model,path,0);atlas=Image.new('RGBA',(160*8,180*3));bounds=[]
 for clip in ['idle','walk','attack']:
  count=len(b.AN['clips'][clip]['frames'])
  for col in range(8):
   mm=b.pose_matrices(model,clip,round(col*(count-1)/7))
   for g,t in groups:
    v=b.skin(model,g,mm);bounds.append(np.c_[v@ns['RIGHT'],v@ns['UP']])
 xy=np.concatenate(bounds);lo=xy.min(0);hi=xy.max(0);scale=min(160*.88/(hi[0]-lo[0]),180*.88/(hi[1]-lo[1]));center=(lo+hi)/2;framing=(scale,center[0],center[1])
 for row,clip in enumerate(['idle','walk','attack']):
  count=len(b.AN['clips'][clip]['frames'])
  for col in range(8):atlas.paste(b.render(model,groups,160,180,clip,round(col*(count-1)/7),framing),(col*160,row*180))
 buf=BytesIO();atlas.save(buf,format='WEBP',quality=88,method=3);encoded=buf.getvalue();assert encoded, key+' '+side
 Image.open(BytesIO(encoded)).verify();target=OUT/f'{key}-{side}.webp';temporary=target.with_suffix('.tmp');temporary.write_bytes(encoded);temporary.replace(target)
 verts=np.concatenate([np.array(g.get('idlePositions') or g['positions']).reshape(-1,3) for g in model['groups']]);height=float(np.ptp(verts[:,1]))
 return key+'-'+side,{'originX':float((80-center[0]*scale)/160),'originY':float((90+center[1]*scale)/180),'pixelsPerUnit':float(scale),'height':height}
if __name__=='__main__':
 metadata={}
 with ProcessPoolExecutor(max_workers=6) as ex:
  jobs=[(k,side) for k in b.MAN for side in ['back','front']]
  for f in as_completed([ex.submit(sheet,j) for j in jobs]):
   k,v=f.result();metadata[k]=v;print(len(metadata),'/',len(jobs),k,flush=True)
 (SITE/'src/data/pov-sprites-v7.json').write_text(json.dumps(metadata,indent=2,sort_keys=True))
 print('DONE',len(metadata),flush=True)
