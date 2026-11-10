#!/usr/bin/env python3
"""Decode Rubicon optimized .MDA meshes and !ETC/LUM8 textures from an OBB.
Static geometry, original UVs, per-vertex weights/indices and bone palettes.
Animation tracks and bind-pose matrices are intentionally not yet interpreted.
"""
import struct,json,sys,re,math
from pathlib import Path
from zipfile import ZipFile
class Reader:
 def __init__(self,b):self.b=b;self.p=0
 def read(self,f):
  v=struct.unpack_from('<'+f,self.b,self.p);self.p+=struct.calcsize('<'+f);return v[0] if len(v)==1 else v
 def array(self,f,n):
  v=struct.unpack_from('<'+str(n)+f,self.b,self.p);self.p+=struct.calcsize('<'+f)*n;return v
 def string(self):
  n=self.read('B');s=self.b[self.p:self.p+n].decode('utf8','replace');self.p+=n;return s

def parse_mda(b):
 r=Reader(b);groups=r.read('I');marker=r.read('i');counts=r.array('I',7);nposition,nuv,nnorm,ntan,ncolor,nweight,njoint=counts
 if groups>100 or nposition>1000000:raise ValueError('unsupported header')
 if marker<0:positions=list(r.array('f',nposition*3))
 else:positions=[v/1024 for v in r.array('h',nposition*3)]
 uvs=r.array('I',nuv);normals=r.array('I',nnorm);tangents=r.array('I',ntan);colors=r.array('I',ncolor);weights=r.array('I',nweight);joints=r.array('I',njoint)
 out=[]
 for gi in range(groups):
  bounds=list(r.array('f',4));fmt=r.read('H');material=r.string();nv,ni=r.array('H',2);indices=list(r.array('H',ni));verts=[];uv=[];norm=[];skinw=[];skini=[]
  if fmt not in (4,5):raise ValueError('vertex format '+str(fmt))
  for vi in range(nv):
   refs=r.array('H',8 if fmt==5 else 6);pi,normal,tangent,color,ui,vi=refs[:6]
   assert pi<nposition and ui<nuv and vi<nuv
   verts.extend(positions[pi*3:pi*3+3]);packed=uvs[ui];uu=packed&65535;vv=packed>>16;uu=uu-65536 if uu>32767 else uu;vv=vv-65536 if vv>32767 else vv;uv.extend([uu/4096,1-vv/4096])
   n=normals[normal];norm.extend([((n>>(8*k))&255)-127 for k in range(3)])
   if fmt==5:
    w=weights[refs[6]];j=joints[refs[7]];skinw.extend([(w>>(8*k)&255)/255 for k in range(4)]);skini.extend([(j>>(8*k)&255) for k in range(4)])
  npalette=r.read('B');palette=list(r.array('B',npalette))
  assert not indices or max(indices)<nv
  out.append(dict(material=material,vertexFormat=fmt,bounds=bounds,positions=verts,uv=uv,normals=norm,indices=indices,skinWeights=skinw,skinIndices=skini,bonePalette=palette))
 meshEnd=r.p
 nhit=r.read('I');r.p+=nhit*3
 modelBounds=list(r.array('f',10));nbones=r.read('h');bones=[]
 for bi in range(nbones):
  nframes,parent=r.array('h',2);poise=list(r.array('f',12));name=r.string();frames=[list(r.array('h',7)) for _ in range(nframes)];nr=r.read('H');remap=list(r.array('H',nr))
  bones.append(dict(name=name,parent=parent,poise=poise,frames=frames,remap=remap))
 return dict(format='rubicon-mda-optimized-decoded',groups=out,unparsedOffset=r.p,meshEnd=meshEnd,totalBytes=len(b),globalCounts=list(counts),bounds=modelBounds,bones=bones)

def decode_texture(z,n,out):
 import texture2ddecoder as dec
 from PIL import Image
 b=z.read(n);w,h=struct.unpack_from('<HH',b,4);rgba=dec.decode_etc1(b[10:10+w*h//2],w,h);im=Image.frombytes('RGBA',(w,h),rgba,'raw','BGRA')
 an=n[:-4]+'_a.A8'
 if an in z.namelist():
  a=z.read(an);aw,ah=struct.unpack_from('<HH',a,4)
  if(aw,ah)==(w,h):im.putalpha(Image.frombytes('L',(w,h),a[8:8+w*h]))
 im.save(out)
 return (w,h)

def convert(z,n,dst):
 model=parse_mda(z.read(n));folder=n.rsplit('/',1)[0];files=[f for f in z.namelist() if f.rsplit('/',1)[0]==folder]
 mats={}
 for f in files:
  if f.endswith('.mtl'):
   b=z.read(f);match=re.search(rb'(?:Archetypes|Arenas|Weapons|Shields|Common|Armour|Furniture)\\',b)
   if match and match.start()>0:
    length=b[match.start()-1];tex=b[match.start():match.start()+length].decode('utf8','replace').replace('\\','/');target=next((x for x in z.namelist() if x.lower()==(tex+'.ETC').lower()),None)
    if target:
     outname=Path(target).stem+'.png';decode_texture(z,target,dst/outname);mats[Path(f).stem]=outname
 model['materials']=mats
 # Default material is assigned through the outer .cnt container; prefer a matching basename.
 basename=Path(n).stem.lower();default=next((v for k,v in mats.items() if k.lower()==basename),next(iter(mats.values()),None))
 model['defaultTexture']=default
 for g in model['groups']:
  g['texture']=mats.get(g['material'].replace('\\','/').rsplit('/',1)[-1],default)
 (dst/(Path(n).stem+'.json')).write_text(json.dumps(model,separators=(',',':')))
 return model
if __name__=='__main__':
 obb=Path(sys.argv[1]);n=sys.argv[2];dst=Path(sys.argv[3]);dst.mkdir(parents=True,exist_ok=True)
 with ZipFile(obb) as z:m=convert(z,n,dst)
 print(json.dumps({'mesh':n,'groups':len(m['groups']),'vertices':sum(len(g['positions'])//3 for g in m['groups']),'triangles':sum(len(g['indices'])//3 for g in m['groups']),'materials':m['materials'],'tailBytes':m['totalBytes']-m['unparsedOffset']}))
