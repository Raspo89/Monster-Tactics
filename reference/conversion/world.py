import sys,json
from zipfile import ZipFile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from convert import convert
root=Path('/workspace/scratch/d96bc0fd2488/model-conversion/ready')
with ZipFile('/workspace/scratch/d96bc0fd2488/xapk-review/main.obb') as z:
 names=z.namelist();wanted={}
 for key,folder in {'sword':'Weapons/Sword/','axe':'Weapons/Axe/','bow':'Weapons/Bow/','staff':'Weapons/Staff/','dagger':'Weapons/Dagger/','shield':'Shields/Shield/'}.items():
  matches=[n for n in names if n.lower().startswith(folder.lower()) and n.endswith('.MDA')]
  if matches:wanted['weapon_'+key]=matches[0]
 for i in range(1,5):wanted['arena_'+str(i)]=f'Arenas/Arena_0{i}/arena_0{i}.MDA'
 manifest={}
 for key,source in wanted.items():
  dst=root/'world'/key;dst.mkdir(parents=True,exist_ok=True)
  try:
   m=convert(z,source,dst);filename=Path(source).stem+'.json';manifest[key]={'source':source,'json':f'world/{key}/{filename}','vertices':sum(len(g['positions'])//3 for g in m['groups']),'groups':len(m['groups'])};print(key,manifest[key])
  except Exception as e:print('FAILED',key,repr(e))
 (root/'world-manifest.json').write_text(json.dumps(manifest,indent=2))
