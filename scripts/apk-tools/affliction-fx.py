"""Export the original affliction effects for the 3D board.

Models (Particles/*): Death Mark skull, Vengeance dagger, Ice Block — normalised to height 1, standing on y=0.
Particle textures (Common/*) used by the original affliction particles (.mtl): flames, stars, stun ring,
snare ring, sparkles, smoke, streak, rage. Written to public/original3d/fx/.
usage: affliction-fx.py OBB_DIR
"""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import mda, etc1
from PIL import Image
obb = sys.argv[1]; out = 'public/original3d/fx'; os.makedirs(out, exist_ok=True)
def tex(src, name, keep_alpha):
    a = f'{obb}/{src}_a.A8'
    if keep_alpha and os.path.exists(a): im = etc1.decode_alpha(f'{obb}/{src}.ETC', a)
    else:
        im = etc1.decode(f'{obb}/{src}.ETC').convert('RGB')
        if keep_alpha:  # additive particle on black: the browser overlay canvas is transparent, so turn brightness into alpha
            rgb = np.asarray(im).astype(float); lum = rgb.max(2)
            alpha = np.clip(lum * 1.15, 0, 255); colour = np.where(lum[..., None] > 0, rgb * 255 / np.maximum(lum[..., None], 1), 0)
            im = Image.fromarray(np.dstack([colour, alpha]).astype('uint8'), 'RGBA')
    im.save(f'{out}/{name}.webp', 'WEBP', quality=90)
for name, src, texture in [('skull', 'Particles/Deathmark/deathmark', 'Particles/Deathmark/Fan_deathmark'),
                           ('dagger', 'Particles/Vengeance/Vengeance', 'Particles/Vengeance/Fan_vengance'),
                           ('ice', 'Particles/IceBlock/iceblock', 'Particles/IceBlock/Fan_iceblock')]:
    parts = mda.read(f'{obb}/{src}.MDA')
    P = np.concatenate([p['positions'] for p in parts]); lo, hi = P.min(0), P.max(0); h = max(hi[1] - lo[1], 1e-6)
    off = np.array([(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2])
    groups = [{'positions': ((p['positions'] - off) / h).round(5).ravel().tolist(), 'uv': p['uv'].round(5).ravel().tolist(), 'indices': p['indices'].tolist()} for p in parts]
    json.dump({'texture': f'{name}.webp', 'size': ((hi - lo) / h).round(4).tolist(), 'groups': groups}, open(f'{out}/{name}.json', 'w'))
    tex(texture, name, name == 'ice')   # ice keeps its alpha (frosted panes); skull/dagger alpha is a gloss mask
for name, src in [('flame', 'Common/particle_explosion'), ('star', 'Common/Particle_star'), ('stun', 'Common/Particle_stun'), ('snare', 'Common/Particle_snare'),
                  ('sparkle', 'Common/GLWG_poof_sparkles'), ('smoke', 'Common/Fan_smoke'), ('streak', 'Common/StreakHard'), ('rage', 'Common/Particle_rage'), ('dust', 'Common/particle_dust')]:
    tex(src, name, True)
print('fx exported:', sorted(os.listdir(out)))
