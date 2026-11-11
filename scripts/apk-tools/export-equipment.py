"""Export every original weapon, shield and armour (helmet) mesh used by the native tables as small
JSON meshes plus decoded textures, ready for render-equipment.py.
Usage: python3 export-equipment.py <obb-dir> <out-dir>"""
import re, csv, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import mda
from etc1 import decode_alpha
obb, out = sys.argv[1], sys.argv[2]
REF = os.path.join(os.path.dirname(__file__), '..', '..', 'reference', 'native-rules')

def find(folder, rel, ext):
    """Case-insensitive lookup of <obb>/<folder>/<rel>.<ext>."""
    path = os.path.join(obb, folder)
    for part in rel.replace('\\', '/').split('/'):
        hit = [n for n in os.listdir(path) if n.lower() in (part.lower(), (part + ext).lower())]
        if not hit: return None
        path = os.path.join(path, hit[0])
    return path if os.path.isfile(path) else None

_all = {}
for _root, _dirs, _files in os.walk(obb):
    for _f in _files:
        if _f.lower().endswith('.etc'): _all.setdefault(_f[:-4].lower(), os.path.join(_root, _f))
def anywhere(base): return _all.get(base.lower())

def rows(name, key):
    return [r for r in list(csv.DictReader(open(os.path.join(REF, name), encoding='latin1')))[1:] if r[key]]

def export(tag, folder, model, texture, kind):
    m = find(folder, model, '.MDA'); t = find(folder, texture, '.ETC')
    if not m or not t: print('missing', tag, model, texture); return None
    # Effect sheets (*_fx, glow) are additive overlays in the game: flagged so the renderer adds them as light
    # instead of drawing an opaque sheet over the item.
    parts = mda.read(m)
    fx = lambda p: bool(re.search(r'_fx|glow', p['texture'] or '', re.I))
    solid = [p for p in parts if not fx(p)] or parts
    P = np.concatenate([p['positions'] for p in solid]); N = np.concatenate([p['normals'] for p in solid])
    if kind != 'armour':  # align: longest axis up, second across, thinnest towards the camera
        c = P.mean(0); _, _, vt = np.linalg.svd(P - c, full_matrices=False)
        R = np.stack([vt[1], vt[0], vt[2]])
        if np.mean(N @ vt[2]) < 0: R[2] *= -1; R[0] *= -1
    groups = []
    for p in parts:
        pos, nrm = p['positions'], p['normals']
        if kind != 'armour': pos, nrm = (pos - c) @ R.T, nrm @ R.T
        tex = p['texture'].replace('\\', '/').split('/', 1)[-1] if p['texture'] else texture
        tf = (find(folder, tex, '.ETC') or anywhere(os.path.basename(tex))) if p['texture'] else t
        tf = tf or t
        name = os.path.basename(tf)[:-4] + '.png'
        if not os.path.isfile(os.path.join(out, name)):
            # the _a.A8 channel is a gloss mask, not transparency: keep colour only
            decode_alpha(tf, tf[:-4] + '_a.A8').convert('RGB').save(os.path.join(out, name))
        groups.append({'positions': pos.round(5).ravel().tolist(), 'normals': nrm.round(4).ravel().tolist(), 'uv': p['uv'].round(5).ravel().tolist(),
                       'indices': p['indices'].tolist(), 'texture': name, 'skinWeights': [], 'skinIndices': [], 'bonePalette': [], **({'additive': True} if fx(p) else {})})
    json.dump({'groups': groups, 'bones': []}, open(os.path.join(out, tag + '.json'), 'w'))
    return tag

os.makedirs(out, exist_ok=True)
done = []
for r in rows('table-3f05e0.txt', 'Tag Name'): done.append(export(r['Tag Name'], 'Weapons', r['Model Name'], r['Texture Name'], 'weapon'))
for r in rows('table-3c2fa0.txt', 'Tag Name'): done.append(export(r['Tag Name'], 'Shields', r['Model Name'], r['Texture Name'], 'shield'))
for r in rows('table-345730.txt', 'Card Tag'): done.append(export(r['Card Tag'], 'Armour/Helmets', r['Helmet Model'], r['Helmet Texture'], 'armour'))
print('exported', sum(1 for x in done if x), 'of', len(done))
