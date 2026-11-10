"""Decode the original rune and spell card textures from an extracted OBB into public/assets/original.
Usage: python3 scripts/decode-magic-art.py <extracted-obb-dir> <etc1-decoder-dir>"""
import json, os, sys
sys.path.insert(0, sys.argv[2])
from etc1 import decode_alpha
obb = sys.argv[1]
cards = json.load(open('src/data/catalog-magic.json'))
os.makedirs('public/assets/original/runes', exist_ok=True); os.makedirs('public/assets/original/spells', exist_ok=True)
done = set()
for c in cards:
    folder, dest = ('Runes', 'runes') if c['type'] == 'rune' else ('Spells', 'spells')
    out = f"public/assets/original/{dest}/{c['art']}.webp"
    if out in done or os.path.isfile(out): done.add(out); continue
    etc = f"{obb}/{folder}/{c['art']}.ETC"
    if not os.path.isfile(etc):
        match = [f for f in os.listdir(f'{obb}/{folder}') if f.lower() == c['art'].lower() + '.etc']
        if not match: print('missing', c['id'], c['art']); continue
        etc = f'{obb}/{folder}/{match[0]}'
    a8 = etc[:-4] + '_a.A8'
    decode_alpha(etc, a8).save(out, 'WEBP', quality=88, method=6); done.add(out)
print('images', len(done))
