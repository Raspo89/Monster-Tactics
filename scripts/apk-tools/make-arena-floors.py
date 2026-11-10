"""Compose a battle floor per original arena from its floor textures (floor_02 tiled, floor_01 overlay with alpha)
and a light tint taken from the battle videos. Usage: python3 make-arena-floors.py <obb-dir> <out-dir>"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from etc1 import decode_alpha
obb, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
ARENAS = {  # folder, file prefix, light colour (centre), light colour (edge), overlay scale
    'lava': ('Arena_01', 'CM_lava', (255, 214, 120), (150, 92, 40), 1.0),
    'forest': ('Arena_02', 'CM_forest', (255, 255, 150), (130, 150, 60), 1.0),
    'mountain': ('Arena_03', 'CM_mountain', (205, 190, 255), (120, 80, 190), 1.0),
    'desert': ('Arena_04', 'CM_desert', (255, 232, 170), (170, 120, 60), 1.0),
}
S = 2048
T = 341  # base tile size: about 200 px on screen, close to the texture scale in the battle videos
for name, (folder, prefix, inner, outer, scale) in ARENAS.items():
    d = f'{obb}/Arenas/{folder}/{prefix}'
    base = decode_alpha(d + '_floor_02.ETC').convert('RGB').resize((T, T), Image.LANCZOS)
    canvas = Image.new('RGB', (S, S))
    for y in range(0, S, T):
        for x in range(0, S, T): canvas.paste(base, (x, y))
    over = decode_alpha(d + '_floor_01.ETC', d + '_floor_01_a.A8').resize((int(1250 * scale),) * 2, Image.LANCZOS)
    n = over.width; yy, xx = np.mgrid[0:n, 0:n]; fade = np.clip((n * .5 - np.hypot(xx - n / 2, yy - n / 2)) / (n * .14), 0, 1)
    over.putalpha(Image.fromarray((np.asarray(over.getchannel('A')).astype(float) * fade).astype(np.uint8)))
    canvas = canvas.convert('RGBA'); canvas.alpha_composite(over, ((S - over.width) // 2, (S - over.height) // 2))
    a = np.asarray(canvas.convert('RGB')).astype(float) / 255
    yy, xx = np.mgrid[0:S, 0:S]; r = np.clip(np.hypot(xx - S / 2, yy - S / 2) / (S * .62), 0, 1)[..., None]
    light = (np.array(inner) * (1 - r) + np.array(outer) * r) / 255
    img = np.clip(a * light * (1.7 if name == 'forest' else 1.25), 0, 1)
    Image.fromarray((img * 255).astype(np.uint8)).save(f'{out}/{name}.webp', 'WEBP', quality=86, method=6)
    print(name)
