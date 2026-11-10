"""Blank stat badges from the original GUI/MonsterStats atlas.

The atlas only has badges with the numbers baked in (0-99), so the digit of
the "1" badge is painted out and the game writes any value (+2, 12...) on top.
usage: stat-badges.py OBB_DIR OUT_DIR
"""
import sys, os
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import etc1

obb, out = sys.argv[1:3]
atlas = etc1.decode_alpha(os.path.join(obb, 'GUI/MonsterStats.ETC'), os.path.join(obb, 'GUI/MonsterStats_a.A8'))
rows = {'attack': 38, 'mojo': 190, 'health': 342, 'armour': 494}
for name, y in rows.items():
    cell = np.asarray(atlas.crop((38, y, 76, y + 38))).copy()   # the "1" badge
    rgb, alpha = cell[..., :3].copy(), cell[..., 3]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    digit = (hsv[..., 1] < 70) & (hsv[..., 2] > 150)           # white glyph
    digit = cv2.dilate(digit.astype('uint8'), np.ones((3, 3), 'uint8'), iterations=4)
    inner = cv2.erode((alpha > 200).astype('uint8'), np.ones((3, 3), 'uint8'), iterations=3)
    mask = (digit & inner) * 255
    rgb = cv2.inpaint(rgb, mask.astype('uint8'), 7, cv2.INPAINT_TELEA)
    rgb = np.where(mask[..., None] > 0, cv2.GaussianBlur(rgb, (7, 7), 0), rgb)
    im = Image.fromarray(np.dstack([rgb, alpha]), 'RGBA').resize((114, 114), Image.LANCZOS)
    im.save(os.path.join(out, f'badge-{name}.webp'), 'WEBP', quality=92)
print('badges', list(rows))
