"""Import the original two-player battle layouts from the OBB (Layouts/multiplayer/2p/*.map).

File format: byte0 version, byte1 player count, uint16 width, uint16 height, then width*height cell codes,
row by row, in an "even-q" hex layout (columns vertical, even columns shifted down half a cell).
Cell codes follow the MCT_* enum in libapp.so: 0 void, 1 floor, 2 +2 power, 3 +3 power, 4 power penalty,
5 +2 armour, 6 armour penalty, 7 regen, 8 +1 Mojo, 9 +2 Mojo, 10 extra card, 0x40-0x43 rocks,
0x30+p rune dais of player p, 0x64+p start of player p.
Usage: python3 scripts/import-native-maps.py <extracted-obb-dir>
"""
import json, sys, glob, os
from pathlib import Path

obb = Path(sys.argv[1])
BONUS = {2: ('token', 'star'), 3: ('token', 'star3'), 4: ('token', 'curse'), 5: ('token', 'shield'), 6: ('token', 'rust'),
         7: ('token', 'heart'), 8: ('tile', 'altar1'), 9: ('tile', 'altar'), 10: ('token', 'card')}

def engine(x, y):
    """Engine axial coordinates (q, r) for original cell (x, y); r is the screen column."""
    return 12 - y - x // 2, x - 3

maps = []
for f in sorted(glob.glob(str(obb / 'Layouts/multiplayer/2p/*.map')), key=lambda p: int(Path(p).stem)):
    d = open(f, 'rb').read()
    w, h = d[2], d[4]
    cells = d[6:6 + w * h]
    out = {'id': 'N2P_' + Path(f).stem, 'cells': [], 'tiles': [], 'tokens': [], 'starts': [None, None], 'daises': [[], []]}
    for y in range(h):
        for x in range(w):
            v = cells[y * w + x]
            if not v: continue
            q, r = engine(x, y)
            k = f'{q},{r}'
            out['cells'].append(k)
            # Original player 1 starts at the top; the engine's player 0 sits at the bottom of its own view.
            if 0x64 <= v <= 0x65: out['starts'][1 if v == 0x64 else 0] = k
            elif 0x30 <= v <= 0x31: out['daises'][1 if v == 0x30 else 0].append(k)
            elif v >= 0x40 or 0x0b <= v <= 0x0e: out['tiles'].append([k, 'rock'])
            elif v in BONUS:
                kind, name = BONUS[v]
                out['tiles' if kind == 'tile' else 'tokens'].append([k, name])
    if None in out['starts']: continue
    maps.append(out)
Path('src/data/native-maps.json').write_text(json.dumps(maps, separators=(',', ':')) + '\n')
print('maps', len(maps), 'cells per map', min(len(m['cells']) for m in maps), '-', max(len(m['cells']) for m in maps),
      'daises per player', sorted({len(m['daises'][0]) for m in maps}))
