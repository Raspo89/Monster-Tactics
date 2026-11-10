import json,numpy as np
from pathlib import Path
from PIL import Image
root=Path('model-conversion/ready/models/human_fighter');m=json.loads((root/'human_fighter.json').read_text());tex=np.array(Image.open(root/'0.png').convert('RGB'))
for flip in [False,True]:
 W=480;H=560;img=np.full((H,W,3),(28,30,45),dtype=np.uint8);depth=np.full((H,W),-1e9,dtype=float)
 eye=np.array([1.5,1.0,2.6]);eye/=np.linalg.norm(eye);right=np.cross([0,1,0],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
 for g in m['groups']:
  v=np.array(g['idlePositions']).reshape(-1,3);v-=np.array([0,.48,0]);proj=np.c_[v@right*450+W/2,-v@up*450+H/2,v@eye];uv=np.array(g['uv']).reshape(-1,2)
  if flip:uv[:,1]=1-uv[:,1]
  idx=np.array(g['indices']).reshape(-1,3)
  for tri in idx:
   p=proj[tri];tt=uv[tri];xmin=max(0,int(p[:,0].min()));xmax=min(W-1,int(p[:,0].max())+1);ymin=max(0,int(p[:,1].min()));ymax=min(H-1,int(p[:,1].max())+1)
   if xmin>xmax or ymin>ymax:continue
   yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1];x=xx+.5;y=yy+.5;x0,y0=p[0,:2];x1,y1=p[1,:2];x2,y2=p[2,:2];den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
   if abs(den)<1e-9:continue
   a=((y1-y2)*(x-x2)+(x2-x1)*(y-y2))/den;b=((y2-y0)*(x-x2)+(x0-x2)*(y-y2))/den;c=1-a-b;z=a*p[0,2]+b*p[1,2]+c*p[2,2]
   mask=(a>=0)&(b>=0)&(c>=0)&(z>depth[ymin:ymax+1,xmin:xmax+1]);u=a*tt[0,0]+b*tt[1,0]+c*tt[2,0];vv=a*tt[0,1]+b*tt[1,1]+c*tt[2,1]
   col=tex[np.clip((vv*(tex.shape[0]-1)).astype(int),0,tex.shape[0]-1),np.clip((u*(tex.shape[1]-1)).astype(int),0,tex.shape[1]-1)]
   n=np.cross(v[tri[1]]-v[tri[0]],v[tri[2]]-v[tri[0]]);n/=max(np.linalg.norm(n),1e-8);light=.55+.45*abs(n@eye);col=(col*light).astype(np.uint8)
   img[ymin:ymax+1,xmin:xmax+1][mask]=col[mask];depth[ymin:ymax+1,xmin:xmax+1][mask]=z[mask]
 Image.fromarray(img).save(f'model-conversion/render-{flip}.png')
