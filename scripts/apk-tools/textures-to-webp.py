"""Convert model textures to WebP (about 4x smaller) and update model-manifest.json and the model JSON files."""
import json, os
from PIL import Image
root = 'public/original3d/'
mm = json.load(open(root + 'model-manifest.json'))
saved = 0
for name, e in mm.items():
    d = root + os.path.dirname(e['json']) + '/'
    js = json.load(open(root + e['json']))
    def conv(f):
        global saved
        if not f.endswith('.png'): return f
        w = f[:-4] + '.webp'
        if os.path.isfile(d + f):
            Image.open(d + f).save(d + w, 'WEBP', quality=90, method=6); saved += os.path.getsize(d + f) - os.path.getsize(d + w); os.remove(d + f)
        return w
    e['skins'] = [conv(f) for f in e['skins']]
    e['defaultTexture'] = conv(e['defaultTexture'])
    for g in js['groups']: g['texture'] = conv(g['texture'])
    json.dump(js, open(root + e['json'], 'w'), separators=(',', ':'))
json.dump(mm, open(root + 'model-manifest.json', 'w'), separators=(',', ':'))
left = [f for f in os.popen(f'find {root}models -name "*.png"').read().split()]
print('saved MB', round(saved / 1e6, 1), 'png left', len(left), left[:5])
