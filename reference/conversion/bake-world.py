from pathlib import Path
import numpy as np,json,math
from PIL import Image
ROOT=Path('/workspace/scratch/d96bc0fd2488/pov-site/.sites-checkout/public/original3d/world');OUT=Path('/workspace/scratch/d96bc0fd2488/pov-site/.sites-checkout/public/assets/original/pov');OUT.mkdir(exist_ok=True)
W,H=1600,929;eye=np.array([0,12.5,9]);F=-eye/np.linalg.norm(eye);R=np.cross(F,[0,1,0]);R/=np.linalg.norm(R);U=np.cross(R,F);f=H/2/math.tan(math.radians(35/2))
for number in range(1,5):
 path=ROOT/f'arena_{number}';d=json.load(open(next(path.glob('*.json'))));img=np.zeros((H,W,4),np.uint8);img[:,:,:]=[32,40,20,255];depth=np.full((H,W),1e9)
 floor={'1':'CM_lava_floor_02','2':'CM_forest_floor_02','3':'CM_mountain_floor_02','4':'CM_desert_floor_02'}[str(number)]
 base=next(x for x in Path('/workspace/scratch/d96bc0fd2488/original-assets/decoded').rglob('*.webp') if x.stem.lower()==floor.lower())
 basegroup={'texture':str(base),'positions':[],'uv':[],'indices':[]}
 for iz in range(33):
  for ix in range(33):basegroup['positions'] += [-32+ix*2,-.03,-32+iz*2];basegroup['uv'] += [ix/2,iz/2]
 for iz in range(32):
  for ix in range(32):
   i=iz*33+ix;basegroup['indices'] += [i,i+1,i+34,i,i+34,i+33]
 for g in [basegroup]+d['groups']:
  if 'sky' in g['texture'].lower():continue
  tex=np.array(Image.open(g['texture'] if g is basegroup else path/g['texture']).convert('RGBA'));v=np.array(g['positions']).reshape(-1,3);vv=v-eye;zz=vv@F;proj=np.c_[W/2+f*(vv@R)/zz,H/2-f*(vv@U)/zz,zz];uv=np.array(g['uv']).reshape(-1,2);uv[:,1]=1-uv[:,1]
  for tri in np.array(g['indices']).reshape(-1,3):
   p=proj[tri];tt=uv[tri]
   if p[:,2].min()<.2:continue
   xmin=max(0,int(p[:,0].min()));xmax=min(W-1,int(p[:,0].max())+1);ymin=max(0,int(p[:,1].min()));ymax=min(H-1,int(p[:,1].max())+1)
   if xmin>xmax or ymin>ymax:continue
   yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1];x=xx+.5;y=yy+.5;x0,y0=p[0,:2];x1,y1=p[1,:2];x2,y2=p[2,:2];den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
   if abs(den)<1e-7:continue
   a=((y1-y2)*(x-x2)+(x2-x1)*(y-y2))/den;b=((y2-y0)*(x-x2)+(x0-x2)*(y-y2))/den;c=1-a-b;inv=a/p[0,2]+b/p[1,2]+c/p[2,2];z=1/np.maximum(inv,1e-9);mask=(a>=0)&(b>=0)&(c>=0)&(z<depth[ymin:ymax+1,xmin:xmax+1]);u=(a*tt[0,0]/p[0,2]+b*tt[1,0]/p[1,2]+c*tt[2,0]/p[2,2])*z;vt=(a*tt[0,1]/p[0,2]+b*tt[1,1]/p[1,2]+c*tt[2,1]/p[2,2])*z
   # Atlas UVs use clamped sampling; the authored floor already carries its tiling.
   if g is basegroup or 'floor' in g['texture'].lower():u=u%1;vt=vt%1
   col=tex[np.clip((vt*(tex.shape[0]-1)).astype(int),0,tex.shape[0]-1),np.clip((u*(tex.shape[1]-1)).astype(int),0,tex.shape[1]-1)].copy();mask&=col[:,:,3]>100
   if number==2:col[:,:,:3]=np.minimum(255,col[:,:,:3].astype(float)*[1.35,1.5,1.1]).astype(np.uint8)
   img[ymin:ymax+1,xmin:xmax+1][mask]=col[mask];depth[ymin:ymax+1,xmin:xmax+1][mask]=z[mask]
 Image.fromarray(img).convert('RGB').save(OUT/f'arena-{number}.webp',quality=94,method=4);print('Arena',number,flush=True)
