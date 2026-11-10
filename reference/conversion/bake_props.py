import sys,json,numpy as np
from pathlib import Path
from zipfile import ZipFile
sys.path.insert(0,'model-conversion')
from convert import convert,decode_texture
from bake_fallback import render,prepare,RIGHT,UP,OUT,ROOT
with ZipFile('xapk-review/main.obb') as z:
 for name,src in [('source-crystal','Furniture/Crystals/crystal_01.MDA'),('source-crystal2','Furniture/Crystals/crystal_02.MDA'),('source-dais','Furniture/Dais/dais.MDA'),('source-rock','Furniture/Rock/rock_01.MDA')]:
  dst=ROOT/'props'/name;dst.mkdir(parents=True,exist_ok=True);model=convert(z,src,dst)
  if name=='source-dais':
   decode_texture(z,'Furniture/Dais/fan_furniture_dais.ETC',dst/'fan_furniture_dais.png')
   for g in model['groups']:
    if not g['material'].lower().endswith('shine'):g['texture']='fan_furniture_dais.png'
  groups=[(g,t) for g,t in prepare(model,dst,0) if 'shine' not in g['material'].lower()];v=np.concatenate([np.array(g['positions']).reshape(-1,3) for g,t in groups]);xy=np.c_[v@RIGHT,v@UP];lo=xy.min(0);hi=xy.max(0);framing=(min(256*.88/(hi[0]-lo[0]),256*.88/(hi[1]-lo[1])),(lo[0]+hi[0])/2,(lo[1]+hi[1])/2)
  im=render(model,groups,256,256,framing=framing);im.save(OUT/(name+'.webp'),quality=94);print(name,im.getbbox())
