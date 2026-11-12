"""Export the equipment meshes in their original (unaligned) space, to be worn by the 3D units.

The original attaches these rigid meshes to the creature skeleton (Bip01 bones): weapons to the right hand,
shields to the left forearm, helmet / shoulder / chest pieces of an armour set to head, upper arms and chest.
Writes public/original3d/equip/<TAG>.json ({parts:[{piece, positions, uv, indices, texture, additive?}]}) and the
textures (colour only: the _a.A8 channel is a gloss mask) to public/original3d/equip/tex/.
usage: export-worn-equipment.py OBB_DIR
"""
import re, csv, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import mda
from etc1 import decode_alpha
obb = sys.argv[1]; out = 'public/original3d/equip'; os.makedirs(out + '/tex', exist_ok=True)
REF = os.path.join(os.path.dirname(__file__), '..', '..', 'reference', 'native-rules')
def find(folder, rel, ext):
    path = os.path.join(obb, folder)
    for part in rel.replace('\\', '/').split('/'):
        hit = [n for n in os.listdir(path) if n.lower() in (part.lower(), (part + ext).lower())]
        if not hit: return None
        path = os.path.join(path, hit[0])
    return path if os.path.isfile(path) else None
_all = {}
for r_, d_, f_ in os.walk(obb):
    for f in f_:
        if f.lower().endswith('.etc'): _all.setdefault(f[:-4].lower(), os.path.join(r_, f))
def rows(name, key): return [r for r in list(csv.DictReader(open(os.path.join(REF, name), encoding='latin1')))[1:] if r[key]]
def texture(tf):
    name = os.path.basename(tf)[:-4] + '.webp'
    if not os.path.isfile(f'{out}/tex/{name}'):
        decode_alpha(tf, tf[:-4] + '_a.A8').convert('RGB').save(f'{out}/tex/{name}', 'WEBP', quality=85)
    return name
def parts_of(folder, model, tex, piece):
    m = find(folder, model, '.MDA'); t = find(folder, tex, '.ETC')
    if not m or not t: return []
    res = []
    for p in mda.read(m):
        tx = p['texture'].replace('\\', '/').split('/', 1)[-1] if p['texture'] else ''
        tf = (find(folder, tx, '.ETC') or _all.get(os.path.basename(tx).lower())) if tx else t
        tf = tf or t
        part = {'piece': piece, 'positions': p['positions'].round(4).ravel().tolist(), 'uv': p['uv'].round(4).ravel().tolist(),
                'indices': p['indices'].tolist(), 'texture': texture(tf)}
        if re.search(r'_fx|glow', os.path.basename(tf), re.I): part['additive'] = True
        res.append(part)
    return res
count = 0
def save(tag, parts):
    global count
    if parts: json.dump({'parts': parts}, open(f'{out}/{tag}.json', 'w'), separators=(',', ':')); count += 1
for r in rows('table-3f05e0.txt', 'Tag Name'): save(r['Tag Name'], parts_of('Weapons', r['Model Name'], r['Texture Name'], 'weapon'))
for r in rows('table-3c2fa0.txt', 'Tag Name'): save(r['Tag Name'], parts_of('Shields', r['Model Name'], r['Texture Name'], 'shield'))
for r in rows('table-345730.txt', 'Card Tag'):
    save(r['Card Tag'], parts_of('Armour/Helmets', r['Helmet Model'], r['Helmet Texture'], 'helmet') + parts_of('Armour/Shoulders', r['Shoulder Model'], r['Shoulder Texture'], 'shoulder') + parts_of('Armour/Chests', r['Chest Model'], r['Chest Texture'], 'chest'))
print('worn equipment exported:', count)
