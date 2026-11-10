import sys,numpy as np
from zipfile import ZipFile
sys.path.insert(0,'model-conversion');from convert import parse_mda
with ZipFile('xapk-review/main.obb') as z:
 model=parse_mda(z.read('Archetypes/Human_fighter/human_fighter.MDA'));anim=parse_mda(z.read('Animation/character_anims.MDA'))
poses={b['name']:b['frames'][4] for b in anim['bones']}
for conjugate in [False,True]:
 mats=[]
 for bone in model['bones']:
  v=poses.get(bone['name'],[0,0,0,30000,0,0,0]);x,y,z,w=np.array(v[:4])/30000
  if conjugate:x,y,z=-x,-y,-z
  R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
  M=np.eye(4);M[:3,:3]=R;M[:3,3]=np.array(v[4:])/10000;mats.append(M)
 verts=[]
 for g in model['groups']:
  p=np.array(g['positions']).reshape(-1,3);w=np.array(g['skinWeights']).reshape(-1,4);j=np.array(g['skinIndices']).reshape(-1,4);out=np.zeros_like(p)
  for vi in range(len(p)):
   for k in range(4):
    if w[vi,k]:out[vi]+=w[vi,k]*(mats[g['bonePalette'][j[vi,k]]]@np.r_[p[vi],1])[:3]
  verts.append(out)
 v=np.concatenate(verts);print('conjugate',conjugate,'bounds',v.min(0),v.max(0),'width',np.ptp(v,axis=0))
 np.save('model-conversion/pose-'+str(conjugate)+'.npy',v)
