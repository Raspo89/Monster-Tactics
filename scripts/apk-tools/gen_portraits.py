"""Render one portrait per model/texture pair used by the original monster table, framed exactly like the
original portraits of the same model (camera yaw 153.4 deg, pitch 20 deg, flat ambient light)."""
import asyncio,json,sys,os
sys.path.insert(0,'/home/claude/scripts')
from rlib import *
CLS={'CT_FIGHTER':'fighter','CT_RANGER':'rogue','CT_MAGE':'spellcaster','CT_ARTIL':'artillery'}
async def main():
    P=json.load(open('/tmp/visual-manifest.orig.json'))['portraits']
    ref={}
    for v in P.values(): ref.setdefault(v['model'],v['path'])
    rows=[r for r in json.load(open(G+'reference/native-rules/table-3189a0.json'))[1:] if r['Race'] and r['Rarity']!='B']
    need=sorted({(r['Race'][3:].lower()+'_'+CLS[r['Class']],int(r['Texture Name'])) for r in rows})
    out=G+'public/assets/original/portraits/'
    print('to render',len(need),flush=True)
    todo=[(m,s) for m,s in need if not os.path.isfile(out+f'm_{m}_{s}.webp')]
    print('left',len(todo),flush=True)
    async with R() as r:
        for m,s in todo[:40]:
            t=Image.open(G+'public/assets/original/'+ref[m]).convert('RGBA')
            im=fit((await asyncio.wait_for(r.render(model=m,skin=s,yaw=153.4,pitch=20,hemi=0,sun=0,amb=2,w=512,h=600),40)),t)
            im.save(out+f'm_{m}_{s}.webp','WEBP',quality=88,method=6)
    print('done',flush=True)
asyncio.run(main())
