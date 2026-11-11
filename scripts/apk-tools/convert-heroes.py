"""Convert the original quest heroes (Archetypes/Bosses/*) to the game's skinned-model JSON.

Same pipeline as reference/conversion/batch.py used for the four playable leaders: decode the MDA mesh and
its texture, bake the original idle pose as a fallback, write webp textures, and add hero_<key> entries to
public/original3d/model-manifest.json.
usage: python3 scripts/apk-tools/convert-heroes.py <extracted-obb-dir>     (pip install texture2ddecoder)
"""
import sys, json, re, io
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0, 'reference/conversion')
from convert import parse_mda, convert

class Dir:
    """Read files of the extracted OBB like the original zip (case preserved, '/' separators)."""
    def __init__(self, root):
        self.root = Path(root); self.names = [str(p.relative_to(self.root)) for p in self.root.rglob('*') if p.is_file()]
    def namelist(self): return self.names
    def read(self, n): return (self.root / n).read_bytes()

z = Dir(sys.argv[1])
heroes = json.load(open(sys.argv[2] if len(sys.argv)>2 else 'src/data/native-quests.json'))['heroes']
out_root = Path('public/original3d')
manifest = json.load(open(out_root / 'model-manifest.json'))
animation = parse_mda(z.read('Animation/character_anims.MDA'))
for key, h in heroes.items():
    if not key.startswith('hero_'): continue
    source = next(n for n in z.names if n.lower() == h['model'].lower())
    dst = out_root / 'models' / key; dst.mkdir(parents=True, exist_ok=True)
    model = convert(z, source, dst)
    if not model['defaultTexture']:
        # Some .mtl files name their texture without the folder prefix: match the folder's .ETC files by name.
        from convert import decode_texture
        folder = source.rsplit('/', 1)[0]
        etcs = sorted((n for n in z.names if n.rsplit('/', 1)[0] == folder and n.endswith('.ETC')), key=len)
        for n in etcs: decode_texture(z, n, dst / (Path(n).stem + '.png'))
        pick = lambda m: next((Path(n).stem + '.png' for n in reversed(etcs) if Path(n).stem.lower().split('_skin')[-1] and Path(n).stem.lower().split('_skin')[-1] in m.lower()), Path(etcs[0]).stem + '.png')
        model['defaultTexture'] = Path(etcs[0]).stem + '.png'
        for g in model['groups']: g['texture'] = pick(g['material'])
    poses = []
    for bone in model['bones']:
        an = next((b for b in animation['bones'] if b['name'] == bone['name']), None)
        v = an['frames'][4] if an else [0, 0, 0, 30000, 0, 0, 0]
        q = np.array(v[:4], dtype=float) / 30000; q /= np.linalg.norm(q); x, y, zz, w = q
        R = np.array([[1-2*(y*y+zz*zz), 2*(x*y-zz*w), 2*(x*zz+y*w)], [2*(x*y+zz*w), 1-2*(x*x+zz*zz), 2*(y*zz-x*w)], [2*(x*zz-y*w), 2*(y*zz+x*w), 1-2*(x*x+y*y)]])
        M = np.eye(4); M[:3, :3] = R; M[:3, 3] = np.array(v[4:]) / 10000; poses.append(M)
    for g in model['groups']:
        p = np.array(g['positions']).reshape(-1, 3); normals = np.array(g['normals'], dtype=float).reshape(-1, 3) / 127
        lens = np.linalg.norm(normals, axis=1); normals /= np.where(lens > 0, lens, 1)[:, None]; g['normals'] = np.round(normals, 6).reshape(-1).tolist()
        if g['skinWeights'] and poses:
            ww = np.array(g['skinWeights']).reshape(-1, 4); jj = np.array(g['skinIndices']).reshape(-1, 4); out = np.zeros_like(p); nn = np.zeros_like(normals)
            for vi in range(len(p)):
                for k in range(4):
                    if ww[vi, k]:
                        bone = g['bonePalette'][jj[vi, k]]; out[vi] += ww[vi, k] * (poses[bone] @ np.r_[p[vi], 1])[:3]; nn[vi] += ww[vi, k] * (poses[bone][:3, :3] @ normals[vi])
            g['idlePositions'] = np.round(out, 6).reshape(-1).tolist(); g['idleNormals'] = np.round(nn, 6).reshape(-1).tolist()
    # png -> webp, like the shipped leaders
    for png in dst.glob('*.png'):
        Image.open(png).save(png.with_suffix('.webp'), 'WEBP', quality=88, method=6); png.unlink()
    web = lambda t: t[:-4] + '.webp' if t and t.endswith('.png') else t
    model['defaultTexture'] = web(model['defaultTexture']); model['materials'] = {k: web(v) for k, v in model['materials'].items()}
    for g in model['groups']: g['texture'] = web(g['texture'])
    filename = Path(source).stem + '.json'
    (dst / filename).write_text(json.dumps(model, separators=(',', ':')))
    manifest[key] = {'source': source, 'json': f'models/{key}/{filename}', 'skins': [], 'defaultTexture': model['defaultTexture'],
                     'vertices': sum(len(g['positions']) // 3 for g in model['groups']), 'triangles': sum(len(g['indices']) // 3 for g in model['groups']), 'bones': len(model['bones'])}
    print(key, manifest[key]['vertices'], model['defaultTexture'], flush=True)
(out_root / 'model-manifest.json').write_text(json.dumps(manifest, indent=2))
