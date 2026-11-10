"""Make rendered equipment art readable on small cards.

Thin weapons (bows, staffs) almost vanish at card size, so every render gets a
soft light rim and dark textures are lifted.  The few meshes that render to
almost nothing borrow the image of the closest item of the same family.
usage: polish-equipment.py RAW_DIR OUT_DIR
"""
import sys, os, glob, re
import numpy as np
from PIL import Image, ImageFilter

raw, out = sys.argv[1:3]
files = sorted(glob.glob(os.path.join(raw, '*.webp')))
stats = {}
for f in files:
    a = np.asarray(Image.open(f).convert('RGBA')).astype(float)
    stats[os.path.basename(f)] = (a[..., 3] > 40).mean()

def family(name):
    return re.sub(r'\d*M?\.webp$', '', name).rsplit('_', 1)[0]

for f in files:
    name = os.path.basename(f)
    src = f
    if stats[name] < 0.003:
        same = [n for n in stats if family(n) == family(name) and stats[n] >= 0.01]
        if same:
            src = os.path.join(raw, max(same, key=lambda n: stats[n]))
    im = Image.open(src).convert('RGBA')
    a = np.asarray(im).astype(float)
    alpha = a[..., 3] / 255
    m = alpha > 0.15
    if m.any():
        lum = a[..., :3].mean(-1)[m].mean()
        if lum < 110:
            gain = min(2.2, 110 / max(lum, 20))
            a[..., :3] = np.clip(255 * (a[..., :3] / 255) ** (1 / gain), 0, 255)
    item = Image.fromarray(a.astype('uint8'), 'RGBA')
    mask = item.split()[3].point(lambda v: 255 if v > 30 else 0)
    rim = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(2.5))
    glow = Image.new('RGBA', item.size, (255, 236, 190, 0))
    glow.putalpha(rim.point(lambda v: int(v * 0.55)))
    base = Image.new('RGBA', item.size, (0, 0, 0, 0))
    base.alpha_composite(glow)
    base.alpha_composite(item)
    base.save(os.path.join(out, name), 'WEBP', quality=88, method=6)
print('polished', len(files))
