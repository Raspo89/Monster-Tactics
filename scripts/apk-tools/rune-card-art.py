"""Turn an original rune texture (UV sheet: left oval = stone face with the carved glyph, right oval = back)
into card art like the game shows: the stone face on its own, glyph glowing white.
Usage: python3 rune-card-art.py <etc1-dir> <obb-dir> <texture-name> <out.webp>"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, sys.argv[1])
from etc1 import decode_alpha

def card_art(texture_path, picture=None):
    if picture is None: picture = 'Buff' in os.path.basename(texture_path)
    im = decode_alpha(texture_path + '.ETC', texture_path + '_a.A8').convert('RGB')
    w, h = im.size
    face = im.crop((0, 0, w // 2, h)).resize((256, 512), Image.LANCZOS)
    a = np.asarray(face).astype(float) / 255
    H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    e = np.hypot((xx - W / 2) / (W * .47), (yy - H / 2) / (H * .47))
    inside = e < .84                                   # inside the dark rim of the oval
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-6)
    stone = np.median(a[inside], axis=0)
    dist = np.linalg.norm(a - stone, axis=2)
    d = dist[inside]
    # Otsu threshold on the colour distance from the stone: the carved glyph is the far cluster
    hist, edges = np.histogram(d, 64); centres = (edges[:-1] + edges[1:]) / 2; best, thr = -1, .2
    for i in range(1, 64):
        w0, w1 = hist[:i].sum(), hist[i:].sum()
        if not w0 or not w1: continue
        m0, m1 = (hist[:i] * centres[:i]).sum() / w0, (hist[i:] * centres[i:]).sum() / w1
        v = w0 * w1 * (m0 - m1) ** 2
        if v > best: best, thr = v, centres[i]
    stone_sat = (stone.max() - stone.min()) / max(stone.max(), 1e-6)
    glyph = inside & (dist > max(thr, .14)) & (sat <= stone_sat + .12) & (e < .8)
    # Race-buff runes carry a painted face, not a carved glyph: show them as painted.
    if picture: glyph[:] = False
    g = Image.fromarray((glyph * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(7)).filter(ImageFilter.MaxFilter(3))
    core = np.asarray(g).astype(float) / 255
    glow = np.asarray(g.filter(ImageFilter.GaussianBlur(9))).astype(float) / 255
    # stone shading: darker towards the rim, like the lit 3D stone
    shade = np.clip(1.15 - .45 * e ** 2, .5, 1.15)[..., None]
    rgb = np.clip(a * shade, 0, 1)
    rgb = rgb * (1 - glow[..., None] * .55) + np.array([.9, .95, 1]) * glow[..., None] * .55
    rgb = rgb * (1 - core[..., None]) + core[..., None]
    alpha = np.clip((1 - e) * 18, 0, 1)
    out = Image.fromarray((np.dstack([rgb, alpha]) * 255).astype(np.uint8), 'RGBA')
    # the card shows the stone lying at an angle: squash it into a wide oval
    out = out.resize((320, 240), Image.LANCZOS)
    canvas = Image.new('RGBA', (320, 256), (0, 0, 0, 0)); canvas.alpha_composite(out, (0, 8))
    return canvas

if __name__ == '__main__':
    card_art(os.path.join(sys.argv[2], 'Runes', sys.argv[3])).save(sys.argv[4], 'WEBP', quality=90)
