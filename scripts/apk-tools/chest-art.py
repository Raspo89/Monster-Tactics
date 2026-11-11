"""Render the original booster chests (Furniture/Chest/chest.MDA with each chest texture) for the chest UI.
usage: chest-art.py OBB_DIR WORK_DIR WORK_URL OUT_DIR    (WORK_URL = WORK_DIR served over http for the renderer)
"""
import sys, os, json, asyncio
sys.path.insert(0, os.path.dirname(__file__)); sys.path.insert(0, '/home/claude/scripts')
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'reference', 'conversion'))
from convert import parse_mda
from etc1 import decode_alpha
from rlib import R
obb, work, url, out = sys.argv[1:5]
# chestanimated.MDA is the chest the game shows (98 vertices, lid on its own bone); chest.MDA is a low-detail stand-in.
model = parse_mda(open(f'{obb}/Furniture/Chest/chestanimated.MDA', 'rb').read())
for g in model['groups']:
    n = np.array(g['normals'], dtype=float).reshape(-1, 3) / 127; n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-6)
    g['normals'] = n.round(5).ravel().tolist()
TEX = {'mini': 'mini', 'full': 'full', 'mega': 'mega', 'epic': 'epic', 'monster': 'Monster', 'equipment': 'Equip', 'rune': 'Rune', 'spell': 'Spell', 'black': 'Black'}
for key, t in TEX.items():
    src = f'{obb}/Furniture/Chest/fan_furniture_chest_{t}'
    decode_alpha(src + '.ETC', src + '_a.A8').convert('RGB').save(f'{work}/{key}.png')  # alpha holds gloss, not transparency
    json.dump({**model, 'defaultTexture': f'{key}.png', 'groups': [{**g, 'texture': f'{key}.png'} for g in model['groups']]}, open(f'{work}/{key}.json', 'w'))
# the mystery chest is a different model; its texture is shown on the same chest shape
src = f'{obb}/Furniture/Epicbooster/fan_furniture_chest_mystery'
decode_alpha(src + '.ETC', src + '_a.A8').convert('RGB').save(f'{work}/mystery.png')
os.makedirs(out, exist_ok=True)
async def main():
    async with R() as r:
        for key in list(TEX) + ['mystery']:
            j = f'{work}/{key}.json'
            if key == 'mystery':
                d = json.load(open(f'{work}/full.json')); d['defaultTexture'] = 'mystery.png'; d['groups'] = [{**g, 'texture': 'mystery.png'} for g in d['groups']]; json.dump(d, open(j, 'w'))
            im = await r.render(json=f'{url}{key}.json', texBase=url, w=360, h=320, yaw=150, pitch=24)
            im.save(f'{out}/chest-{key}.webp', 'WEBP', quality=88, method=6)
asyncio.run(main())
print('chests rendered')
