"""Cut the original Solo Quest artwork out of the GUI atlases.

GUI/quests        six parchment maps, one per quest page   -> ui-v7/quest-map-1..6.webp
GUI/ButtonBits2   green and fiery round frames, padlock     -> ui-v7/quest-orb-green/red.webp, quest-lock.webp
GUI/ButtonBits4   green tick                                -> ui-v7/quest-check.webp
usage: quest-ui.py OBB_DIR OUT_DIR
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import etc1

obb, out = sys.argv[1:3]
def atlas(n): return etc1.decode_alpha(f'{obb}/GUI/{n}.ETC', f'{obb}/GUI/{n}_a.A8')
q = atlas('quests')
for i, box in enumerate([(0, 0, 336, 504), (344, 0, 680, 504), (688, 0, 1024, 504), (0, 512, 336, 1016), (344, 512, 680, 1016), (688, 512, 1024, 1016)], 1):
    q.crop(box).save(f'{out}/quest-map-{i}.webp', 'WEBP', quality=86)
b2 = atlas('ButtonBits2')
b2.crop((0, 0, 320, 320)).resize((160, 160)).save(f'{out}/quest-orb-green.webp', 'WEBP', quality=88)
b2.crop((324, 0, 644, 320)).resize((160, 160)).save(f'{out}/quest-orb-red.webp', 'WEBP', quality=88)
b2.crop((675, 113, 739, 177)).save(f'{out}/quest-lock.webp', 'WEBP', quality=90)
atlas('ButtonBits4').crop((513, 65, 651, 203)).resize((96, 96)).save(f'{out}/quest-check.webp', 'WEBP', quality=90)
print('quest ui done')
