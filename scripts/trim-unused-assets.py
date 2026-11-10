"""Remove conversion-only payloads; preserve every runtime model/skin field.
Run from the project root. Git history retains the full conversion source.
"""
from pathlib import Path
import json

root = Path('public/original3d')
manifest = json.loads((root/'model-manifest.json').read_text())
portraits = json.loads(Path('src/data/visual-manifest.json').read_text())['portraits']
report = {'removed': [], 'compacted': []}
needed = set()
for card_id, portrait in portraits.items():
    entry = manifest[portrait['model']]
    mesh = json.loads((root/entry['json']).read_text())
    skin = next(f for f in entry['skins'] if int(f.split('.')[0]) == portrait['skin'])
    for group in mesh['groups']:
        texture = skin if skin in entry['skins'] and group['texture'][0].isdigit() else group['texture']  # capes, wings and eyes keep their own texture
        path = root/Path(entry['json']).parent/texture
        assert path.is_file(), (card_id, path)
        needed.add(path)

def remove(path):
    report['removed'].append({'path': str(path), 'bytes': path.stat().st_size})
    path.unlink()

for path in (root/'models').rglob('*.png'):
    if path not in needed:
        remove(path)
for folder in [root/'world', root/'props', Path('public/assets/original/sheets')]:
    if folder.exists():
        for path in folder.rglob('*'):
            if path.is_file(): remove(path)
        for path in sorted(folder.rglob('*'), reverse=True):
            if path.is_dir(): path.rmdir()
        folder.rmdir()
for name in ['world-manifest.json', 'animation-source.txt']:
    path = root/name
    if path.exists(): remove(path)

def rewrite(path, value):
    before = path.stat().st_size
    path.write_text(json.dumps(value, separators=(',', ':')))
    report['compacted'].append({'path': str(path), 'before': before, 'after': path.stat().st_size})

fields = ['positions', 'uv', 'normals', 'indices', 'skinWeights', 'skinIndices', 'bonePalette', 'texture', 'idlePositions']
for entry in manifest.values():
    path = root/entry['json']
    mesh = json.loads(path.read_text())
    rewrite(path, {'groups': [{k: group.get(k, []) for k in fields} for group in mesh['groups']],
                   'bones': [{'name': bone['name'], 'frames': bone['frames'][:1]} for bone in mesh['bones']]})
path = root/'animations.json'
animations = json.loads(path.read_text())
animations['clips'] = {k: animations['clips'][k] for k in ['idle', 'walk', 'attack', 'death']}
rewrite(path, animations)
report['removedBytes'] = sum(x['bytes'] for x in report['removed'])
report['compactedBytes'] = sum(x['before']-x['after'] for x in report['compacted'])
Path('reference/ASSET-CLEANUP-V7.1.json').write_text(json.dumps(report, indent=2))
print({k: v for k, v in report.items() if not isinstance(v, list)})
