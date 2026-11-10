import json,numpy as np,math,os
from PIL import Image
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path('/workspace/scratch/d96bc0fd2488/model-conversion/ready');OUT=ROOT.parent/'fallback';(OUT/'portraits').mkdir(parents=True,exist_ok=True);(OUT/'sheets').mkdir(exist_ok=True)
MAN=json.loads((ROOT/'model-manifest.json').read_text());AN=json.loads((ROOT/'animations.json').read_text());AN_NAMES=AN['boneNames']
EYE=np.array([-1.1,.9,-2.2]);EYE/=np.linalg.norm(EYE);RIGHT=np.cross([0,1,0],EYE);RIGHT/=np.linalg.norm(RIGHT);UP=np.cross(EYE,RIGHT)
def pose_matrices(model,clip,frame):
 arr=AN['clips'][clip]['frames'][frame];mats=[]
 for bone in model['bones']:
  v=arr[AN_NAMES.index(bone['name'])] if bone['name'] in AN_NAMES else [0,0,0,30000,0,0,0];q=np.array(v[:4],float)/30000;q/=max(np.linalg.norm(q),1e-10);x,y,z,w=q
  R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
  M=np.eye(4);M[:3,:3]=R;M[:3,3]=np.array(v[4:])/10000;mats.append(M)
 return np.array(mats)
def skin(model,g,mats):
 v=np.array(g['positions']).reshape(-1,3)
 if not g['skinWeights'] or not len(mats):return v
 w=np.array(g['skinWeights']).reshape(-1,4);j=np.array(g['skinIndices']).reshape(-1,4);p=np.array(g['bonePalette']);out=np.zeros_like(v)
 for k in range(4):
  active=w[:,k]>0
  if np.any(active):
   mm=mats[p[j[active,k]]];vv=np.einsum('nij,nj->ni',mm[:,:3,:3],v[active])+mm[:,:3,3];out[active]+=vv*w[active,k,None]
 return out

def prepare(model,path,variant):
 groups=[]
 for g in model['groups']:
  texture=str(variant)+'.png' if (path/(str(variant)+'.png')).exists() else g['texture'];im=Image.open(path/texture).convert('RGBA');groups.append((g,np.array(im)))
 return groups

def render(model,groups,W,H,clip='idle',frame=0,framing=None):
 mats=pose_matrices(model,clip,frame);posegroups=[(g,skin(model,g,mats),t) for g,t in groups]
 # Fix framing to the original model size so actions animate without breathing in scale.
 bb=model['bounds'];height=max(.3,bb[5]-bb[2]);scale=(H*.83)/height;center=np.array([0,bb[2]+height*.48,0]);
 if framing is not None:scale=framing[0]
 img=np.zeros((H,W,4),dtype=np.uint8);depth=np.full((H,W),-1e9,dtype=np.float32)
 for g,v,tex in posegroups:
  vv=v-center
  if framing is None:px,py=vv@RIGHT*scale+W/2,-vv@UP*scale+H*.52
  else:px,py=(v@RIGHT-framing[1])*scale+W/2,-(v@UP-framing[2])*scale+H/2
  proj=np.c_[px,py,vv@EYE];uv=np.array(g['uv']).reshape(-1,2);uv[:,1]=1-uv[:,1];idx=np.array(g['indices']).reshape(-1,3)
  for tri in idx:
   p=proj[tri];tt=uv[tri];xmin=max(0,int(p[:,0].min()));xmax=min(W-1,int(p[:,0].max())+1);ymin=max(0,int(p[:,1].min()));ymax=min(H-1,int(p[:,1].max())+1)
   if xmin>xmax or ymin>ymax:continue
   yy,xx=np.mgrid[ymin:ymax+1,xmin:xmax+1];x=xx+.5;y=yy+.5;x0,y0=p[0,:2];x1,y1=p[1,:2];x2,y2=p[2,:2];den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
   if abs(den)<1e-7:continue
   a=((y1-y2)*(x-x2)+(x2-x1)*(y-y2))/den;b=((y2-y0)*(x-x2)+(x0-x2)*(y-y2))/den;c=1-a-b;z=a*p[0,2]+b*p[1,2]+c*p[2,2]
   mask=(a>=0)&(b>=0)&(c>=0)&(z>depth[ymin:ymax+1,xmin:xmax+1]);u=a*tt[0,0]+b*tt[1,0]+c*tt[2,0];vt=a*tt[0,1]+b*tt[1,1]+c*tt[2,1]
   col=tex[np.clip((vt*(tex.shape[0]-1)).astype(int),0,tex.shape[0]-1),np.clip((u*(tex.shape[1]-1)).astype(int),0,tex.shape[1]-1)].copy();mask&=col[:,:,3]>100
   n=np.cross(v[tri[1]]-v[tri[0]],v[tri[2]]-v[tri[0]]);n/=max(np.linalg.norm(n),1e-8);light=.66+.34*abs(n@EYE);col[:,:,:3]=(col[:,:,:3]*light).astype(np.uint8)
   img[ymin:ymax+1,xmin:xmax+1][mask]=col[mask];depth[ymin:ymax+1,xmin:xmax+1][mask]=z[mask]
 return Image.fromarray(img)

def sheet(key):
 entry=MAN[key];path=(ROOT/entry['json']).parent;model=json.loads((ROOT/entry['json']).read_text());groups=prepare(model,path,0);atlas=Image.new('RGBA',(160*8,180*3))
 bounds=[]
 for clip in ['idle','walk','attack']:
  count=len(AN['clips'][clip]['frames'])
  for col in range(8):
   mm=pose_matrices(model,clip,round(col*(count-1)/7))
   for g,t in groups:
    v=skin(model,g,mm);bounds.append(np.c_[v@RIGHT,v@UP])
 xy=np.concatenate(bounds);lo=xy.min(0);hi=xy.max(0);framing=(min(160*.88/(hi[0]-lo[0]),180*.88/(hi[1]-lo[1])),(lo[0]+hi[0])/2,(lo[1]+hi[1])/2)
 for row,clip in enumerate(['idle','walk','attack']):
  count=len(AN['clips'][clip]['frames'])
  for col in range(8):atlas.paste(render(model,groups,160,180,clip,round(col*(count-1)/7),framing),(col*160,row*180))
 atlas.save(OUT/'sheets'/f'{key}.webp',quality=91,method=4);return key

def cardmap():
 result={}
 for prefix,race in [('H','human'),('Z','undead'),('O','orc'),('E','elf')]:
  for n in range(1,9):
   role='fighter'
   if prefix=='H':role='rogue' if n==3 else 'spellcaster' if n==5 else 'fighter'
   if prefix=='Z':role='spellcaster' if n in(4,6) else 'artillery' if n==7 else 'fighter'
   if prefix=='O':role='artillery' if n==3 else 'fighter'
   if prefix=='E':role='rogue' if n==2 else 'spellcaster' if n in(5,8) else 'fighter'
   result[f'{prefix}{n:02}']=(f'{race}_{role}',n%12)
 for n,key in enumerate(['neutral_mercenary','neutral_assassin','neutral_golem','neutral_dragon'],1):result[f'N{n:02}']=(key,0)
 for r in ['human','zombie','orc','elf']:result['LEADER_'+r]=('leader_'+r,0)
 return result

def portraits(item):
 id,(key,variant)=item;entry=MAN[key];path=(ROOT/entry['json']).parent;model=json.loads((ROOT/entry['json']).read_text());groups=prepare(model,path,variant);im=render(model,groups,256,300);im.save(OUT/'portraits'/f'{id}.webp',quality=94,method=4);return id
if __name__=='__main__':
 with ProcessPoolExecutor(max_workers=6) as ex:
  futures=[ex.submit(sheet,key) for key in MAN]+([] if os.environ.get('SHEETS_ONLY') else [ex.submit(portraits,item) for item in cardmap().items()])
  for f in as_completed(futures):print('BAKED',f.result(),flush=True)
 (OUT/'manifest.json').write_text(json.dumps({'frameWidth':160,'frameHeight':180,'columns':8,'rows':['idle','walk','attack'],'fps':[8/1.05,8/.5,8/.95],'portraits':{id:{'model':key,'skin':n,'path':'portraits/'+id+'.webp'} for id,(key,n) in cardmap().items()},'sheets':{key:'sheets/'+key+'.webp' for key in MAN}},indent=2))
 print('DONE',OUT,flush=True)
