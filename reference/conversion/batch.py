import sys,json,re,math
from pathlib import Path
from zipfile import ZipFile
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from convert import parse_mda,convert,decode_texture
root=Path('/workspace/scratch/d96bc0fd2488/model-conversion/ready');root.mkdir(parents=True,exist_ok=True)
with ZipFile('/workspace/scratch/d96bc0fd2488/xapk-review/main.obb') as z:
 names=z.namelist();animation=parse_mda(z.read('Animation/character_anims.MDA'));boneNames=[b['name'] for b in animation['bones']]
 clips={}
 for key,a,b,fps in [('idle',4,33,1/.035),('walk',310,329,40),('run',336,351,40),('attack',2013,2050,40),('shoot',2270,2316,40),('cast',358,408,40),('death',1300,1342,40),('hit',460,479,1/.03)]:
  clips[key]={'fps':fps,'frames':[[bone['frames'][i] for bone in animation['bones']] for i in range(a,b+1)]}
 (root/'animations.json').write_text(json.dumps({'format':'rubicon-compressed-skin-clips','boneNames':boneNames,'clips':clips},separators=(',',':')))
 wanted={}
 for race in ['Human','Undead','Orc','Elf']:
  for role in ['fighter','rogue','artillery','spellcaster']:
   prefix=f'Archetypes/{race}_{role}/'.lower();matches=[n for n in names if n.lower().startswith(prefix) and n.endswith('.MDA')]
   if matches:wanted[f'{race.lower()}_{role}']=matches[0]
 for key,pattern in {'leader_human':'Archetypes/Bosses/Dean/','leader_zombie':'Archetypes/Bosses/Mummy/','leader_orc':'Archetypes/Bosses/Orcqueen/','leader_elf':'Archetypes/Bosses/Elverkonge/','neutral_golem':'Archetypes/Golem_fighter/','neutral_mercenary':'Archetypes/Human_Rogue/','neutral_assassin':'Archetypes/Spectre_Rogue/','neutral_dragon':'Archetypes/Lizard_fighter/'}.items():
  matches=[n for n in names if n.lower().startswith(pattern.lower()) and n.endswith('.MDA')]
  if matches:wanted[key]=matches[0]
 manifest={}
 for key,source in wanted.items():
  dst=root/'models'/key;dst.mkdir(parents=True,exist_ok=True)
  model=convert(z,source,dst);folder=source.rsplit('/',1)[0]
  skins=[]
  for n in names:
   if n.rsplit('/',1)[0]==folder and re.search(r'/\d+\.ETC$',n):
    target=Path(n).stem+'.png';decode_texture(z,n,dst/target);skins.append(target)
  skins.sort(key=lambda x:int(x.split('.')[0]))
  model['source']=source;model['skins']=skins
  # Keep a pre-skinned original idle pose as a fallback for regular Mesh rendering.
  poses=[]
  for bone in model['bones']:
   an=next((b for b in animation['bones'] if b['name']==bone['name']),None)
   v=an['frames'][4] if an else [0,0,0,30000,0,0,0];x,y,zz,w=np.array(v[:4],dtype=float)/30000
   q=np.array([x,y,zz,w]);q/=np.linalg.norm(q);x,y,zz,w=q
   R=np.array([[1-2*(y*y+zz*zz),2*(x*y-zz*w),2*(x*zz+y*w)],[2*(x*y+zz*w),1-2*(x*x+zz*zz),2*(y*zz-x*w)],[2*(x*zz-y*w),2*(y*zz+x*w),1-2*(x*x+y*y)]])
   M=np.eye(4);M[:3,:3]=R;M[:3,3]=np.array(v[4:])/10000;poses.append(M)
  for g in model['groups']:
   p=np.array(g['positions']).reshape(-1,3);normals=np.array(g['normals'],dtype=float).reshape(-1,3)/127
   lens=np.linalg.norm(normals,axis=1);normals/=np.where(lens>0,lens,1)[:,None];g['normals']=np.round(normals,6).reshape(-1).tolist()
   if g['skinWeights'] and poses:
    ww=np.array(g['skinWeights']).reshape(-1,4);jj=np.array(g['skinIndices']).reshape(-1,4);out=np.zeros_like(p);nn=np.zeros_like(normals)
    for vi in range(len(p)):
     for k in range(4):
      if ww[vi,k]:
       bone=g['bonePalette'][jj[vi,k]];out[vi]+=ww[vi,k]*(poses[bone]@np.r_[p[vi],1])[:3];nn[vi]+=ww[vi,k]*(poses[bone][:3,:3]@normals[vi])
    g['idlePositions']=np.round(out,6).reshape(-1).tolist();g['idleNormals']=np.round(nn,6).reshape(-1).tolist()
  filename=Path(source).stem+'.json';(dst/filename).write_text(json.dumps(model,separators=(',',':')))
  manifest[key]={'source':source,'json':f'models/{key}/{filename}','skins':skins,'defaultTexture':model['defaultTexture'],'vertices':sum(len(g['positions'])//3 for g in model['groups']),'triangles':sum(len(g['indices'])//3 for g in model['groups']),'bones':len(model['bones'])}
  print(key,manifest[key]['vertices'],manifest[key]['triangles'],len(skins))
 (root/'model-manifest.json').write_text(json.dumps(manifest,indent=2))
 (root/'animation-source.txt').write_bytes(z.read('Animation/Raz0rroot.txt'))
print('READY',root)
