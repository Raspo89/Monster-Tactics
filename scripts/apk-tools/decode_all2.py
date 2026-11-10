import json,os,sys,re
sys.path.insert(0,'/home/claude/scripts')
from etc1 import decode
G='/home/claude/game/SOURCE/public/original3d/'
mm=json.load(open(G+'model-manifest.json'))
added=0
for name,e in mm.items():
    src='/home/claude/apk/obb/'+os.path.dirname(e['source'])
    dst=G+os.path.dirname(e['json'])
    for f in sorted(os.listdir(src)):
        m=re.fullmatch(r'(\d+)\.ETC',f)
        if not m: continue
        png=m.group(1)+'.png'
        if not os.path.isfile(os.path.join(dst,png)):
            decode(os.path.join(src,f)).convert('RGBA').save(os.path.join(dst,png),optimize=True);added+=1
        if png not in e['skins']: e['skins'].append(png)
    e['skins'].sort(key=lambda s:int(s[:-4]))
open(G+'model-manifest.json','w').write(json.dumps(mm,indent=1))
print('added',added,'skins total',sum(len(e['skins']) for e in mm.values()))
