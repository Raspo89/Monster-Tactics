"""Render card art for every exported equipment mesh (see export-equipment.py) with three.js in headless Chrome.
Weapons lie diagonally, shields face the camera, helmets use the monster-portrait camera. 40 per run;
run repeatedly until it prints 'left 0'. Usage: python3 render-equipment.py <export-dir-url> <export-dir> <out-dir>"""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, '/home/claude/scripts')
from rlib import R, Image
url, src, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
tags = sorted(f[:-5] for f in os.listdir(src) if f.endswith('.json'))
todo = [t for t in tags if not os.path.isfile(os.path.join(out, t + '.webp'))]
async def main():
    async with R() as r:
        for t in todo[:40]:
            o = {'yaw': 153.4, 'pitch': 20} if t.startswith('A_') else {} if t.startswith('S_') else {'roll': -42}
            im = await asyncio.wait_for(r.render(json=url + t + '.json', texBase=url, w=320, h=320, **o), 40)
            im.save(os.path.join(out, t + '.webp'), 'WEBP', quality=88, method=6)
asyncio.run(main())
print('left', len(todo) - min(40, len(todo)))
