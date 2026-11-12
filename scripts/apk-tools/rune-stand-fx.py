"""Export the original rune stand for the 3D board: Furniture/Dais (stone pedestal, grey texture tinted by the
owner's colour in game), Furniture/Crystals crystal_01 (the glowing crystal on an empty stand) and Runes/rune_01
(the rune stone that floats on a filled stand) with one texture per rune card.
Writes public/original3d/fx/{dais,crystal,runestone}.json + textures and fx/runes/<cardId>.webp.
usage: rune-stand-fx.py OBB_DIR
"""
import sys, os, json, csv
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import mda, etc1
obb = sys.argv[1]; out = 'public/original3d/fx'; os.makedirs(out + '/runes', exist_ok=True)
def mesh(src, name, tex, first_only=True):
    parts = mda.read(f'{obb}/{src}.MDA')
    parts = [p for p in parts if not p['texture'] or 'shine' not in p['texture'].lower()] if first_only else parts
    json.dump({'texture': tex, 'groups': [{'positions': p['positions'].round(4).ravel().tolist(), 'uv': p['uv'].round(4).ravel().tolist(), 'indices': p['indices'].tolist()} for p in parts]}, open(f'{out}/{name}.json', 'w'), separators=(',', ':'))
def rgb(src, dst): etc1.decode(f'{obb}/{src}.ETC').convert('RGB').save(f'{out}/{dst}', 'WEBP', quality=88)
mesh('Furniture/Dais/dais', 'dais', 'dais.webp'); rgb('Furniture/Dais/fan_furniture_dais', 'dais.webp')
mesh('Furniture/Crystals/crystal_01', 'crystal', 'crystal.webp')
# the stand crystals glow pink-white in the game (lit by their shine pass): bake that glow into the colour map
c = np.asarray(etc1.decode(f'{obb}/Furniture/Crystals/fan_furniture_crystals.ETC').convert('RGB')).astype(float)
lum = c.mean(2, keepdims=True) / 255
glow = np.clip(np.array([255, 150, 225]) * (0.55 + lum * 0.9) + lum * 120, 0, 255)
from PIL import Image
Image.fromarray(glow.astype('uint8')).save(f'{out}/crystal.webp', 'WEBP', quality=88)
mesh('Runes/rune_01', 'runestone', 'runes/blank.webp'); rgb('Runes/Rune_01_Blank', 'runes/blank.webp')
REF = os.path.join(os.path.dirname(__file__), '..', '..', 'reference', 'native-rules')
table = {r[0]: r[6] for r in list(csv.reader(open(f'{REF}/table-3acc48.txt', encoding='latin1')))[2:] if r and r[0].startswith('R_')}
cards = json.load(open('src/data/catalog-magic.json')) + json.load(open('src/data/cards.json'))
LEGACY = {'R01': 'R_MINORPOWER', 'R02': 'R_MINORARMOUR', 'R03': 'R_MINORMOJO', 'R04': 'R_EXTRACARD', 'R05': 'R_MINORHEALTH', 'R06': 'R_HASTE', 'R07': 'R_MAJORMOJO'}
n = 0
for c in cards:
    if c['type'] != 'rune': continue
    tex = table.get(c.get('nativeTag') or LEGACY.get(c['id'], ''))
    path = tex and next((f'{obb}/Runes/{f[:-4]}' for f in os.listdir(f'{obb}/Runes') if f.lower() == tex.lower() + '.etc'), None)
    if path: etc1.decode(path + '.ETC').convert('RGB').save(f'{out}/runes/{c["id"]}.webp', 'WEBP', quality=86); n += 1
print('rune stand exported; rune stones:', n)
