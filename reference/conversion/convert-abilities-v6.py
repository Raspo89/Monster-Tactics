import sys,json,re,math
from pathlib import Path
from zipfile import ZipFile
import numpy as np
BASE=Path('/workspace/scratch/d96bc0fd2488');SITE=BASE/'races-site/.sites-checkout';ROOT=SITE/'public/original3d'
sys.path.insert(0,str(BASE/'race-texture-deps'));sys.path.insert(0,str(BASE/'model-conversion'))
from convert import parse_mda,convert,decode_texture
plan=json.loads((SITE/'src/data/ability-card-plan.json').read_text());manifest=json.loads((ROOT/'model-manifest.json').read_text());animation=json.loads((ROOT/'animations.json').read_text());animNames=animation['boneNames']
with ZipFile(BASE/'xapk-review/main.obb') as z:
 names=z.namelist()
 for item in plan:
  key=item['model']
  if key in manifest:continue
  sources=[n for n in names if n.lower().startswith(('Archetypes/'+item['folder']+'/').lower()) and n.endswith('.MDA')];assert sources,item
  source=sources[0];dst=ROOT/'models'/key;dst.mkdir(parents=True,exist_ok=True);model=convert(z,source,dst);folder=source.rsplit('/',1)[0];skins=[]
  for n in names:
   if n.rsplit('/',1)[0]==folder and re.search(r'/\d+\.ETC$',n):
    target=Path(n).stem+'.png';decode_texture(z,n,dst/target);skins.append(target)
  skins.sort(key=lambda x:int(x.split('.')[0]));model['source']=source;model['skins']=skins
  poses=[]
  for bone in model['bones']:
   v=animation['clips']['idle']['frames'][0][animNames.index(bone['name'])] if bone['name'] in animNames else [0,0,0,30000,0,0,0]
   x,y,zz,w=np.array(v[:4],dtype=float)/30000;q=np.array([x,y,zz,w]);q/=np.linalg.norm(q);x,y,zz,w=q
   R=np.array([[1-2*(y*y+zz*zz),2*(x*y-zz*w),2*(x*zz+y*w)],[2*(x*y+zz*w),1-2*(x*x+zz*zz),2*(y*zz-x*w)],[2*(x*zz-y*w),2*(y*zz+x*w),1-2*(x*x+y*y)]])
   M=np.eye(4);M[:3,:3]=R;M[:3,3]=np.array(v[4:])/10000;poses.append(M)
  for g in model['groups']:
   p=np.array(g['positions']).reshape(-1,3);normals=np.array(g['normals'],dtype=float).reshape(-1,3)/127;lens=np.linalg.norm(normals,axis=1);normals/=np.where(lens>0,lens,1)[:,None];g['normals']=np.round(normals,6).reshape(-1).tolist()
   if g['skinWeights'] and poses:
    ww=np.array(g['skinWeights']).reshape(-1,4);jj=np.array(g['skinIndices']).reshape(-1,4);out=np.zeros_like(p);nn=np.zeros_like(normals)
    for vi in range(len(p)):
     for k in range(4):
      if ww[vi,k]:
       bone=g['bonePalette'][jj[vi,k]];out[vi]+=ww[vi,k]*(poses[bone]@np.r_[p[vi],1])[:3];nn[vi]+=ww[vi,k]*(poses[bone][:3,:3]@normals[vi])
    g['idlePositions']=np.round(out,6).reshape(-1).tolist();g['idleNormals']=np.round(nn,6).reshape(-1).tolist()
  filename=Path(source).stem+'.json';(dst/filename).write_text(json.dumps(model,separators=(',',':')))
  manifest[key]={'source':source,'json':f'models/{key}/{filename}','skins':skins,'defaultTexture':model['defaultTexture'],'vertices':sum(len(g['positions'])//3 for g in model['groups']),'triangles':sum(len(g['indices'])//3 for g in model['groups']),'bones':len(model['bones'])}
  print('CONVERTED',key,flush=True)
(ROOT/'model-manifest.json').write_text(json.dumps(manifest,indent=2))
print('DONE',len(manifest),flush=True)
