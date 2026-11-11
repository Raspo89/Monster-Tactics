"""Import the original single-player quests from the OBB.

Quests/<id>.txt   rooms: number, position relative to an earlier room (N/E/S/W), enemy hero, enemy deck,
                  board layout number; "[LASTBATTLE]" ends the quest, "// Sub-Boss" marks a mini boss.
Decks/<name>.bdk  u32 version, u32 count, then count records of 4 x u16 (a, b, c, type):
                  type 2 monster: race (1-based RT_ order), class (CT_ order), index inside that race+class
                  type 0 equipment: 1 weapon / 2 shield / 3 armour, 1-based row of that table
                  type 1 rune, type 3 spell: 1-based row of the rune / spell table
Layouts/quests/<id>/<n>.txt  hexagonal board of radius 4 named on a 9x9 grid (letters A-I = rows, digits 0-8 = columns), optional TEMPLATE
                  that removes cells (reference/native-rules/map-templates.json), bonus cells, rocks,
                  [2PLAYER] starts and rune daises.  P1 (the player) sits on the high letters.
Writes src/data/native-quests.json and src/data/quest-maps.json.
usage: python3 scripts/import-native-quests.py <extracted-obb-dir>
"""
import json, sys, re, struct, csv
from pathlib import Path

obb = Path(sys.argv[1])
REF = Path('reference/native-rules')
QUESTS = [('tut', 'مهمة التدريب', 'Tutorial Quest', 'تعرّف على اللعبة واحصل على بطاقات مجانية في الطريق.', 'easy'),
          ('easy', 'المهمة السهلة', 'Easy Quest', 'أول تحدٍّ حقيقي لك، مهمة تمهيدية تعطيك طعم القتال.', 'easy'),
          ('medium', 'المهمة المتوسطة', 'Medium Quest', 'المهمات صعبة لكن الجوائز كثيرة. هل عندك اللي يلزم؟', 'normal'),
          ('hard', 'المهمة الصعبة', 'Hard Quest', 'حاول تهزم هجمة من التشكيلات القوية المليانة بطاقات نادرة وأسطورية.', 'hard'),
          ('hard2', 'المهمة الأصعب', 'Harder Quest', 'الساحات موزونة ضدك، وأبطال العدو يكسبون نقطة موجو إضافية كل دور.', 'hard'),
          ('hard3', 'مهمة الكابوس', 'Nightmare Quest', 'مجموعة شريرة من المكائد، هذه المهمات غير عادلة أبدًا. الأفضل لا تحاول أصلًا!', 'hard')]
AR = {'Blart': 'بلارت', 'Doc Pain': 'دوك بين', 'Ouranus': 'أورانوس', 'Lavalem': 'لافاليم', 'Dean': 'دين', 'Noigle': 'نويغل',
      'Shaq': 'شاك', 'Boneyard': 'بونيارد', 'Silvanus': 'سيلفانوس', 'Alphedia': 'ألفيديا', 'Raeynor': 'راينور', 'Hyssta': 'هيستا',
      'Clank': 'كلانك', 'Ernold': 'إرنولد', 'Mambo': 'مامبو', 'Machli': 'ماتشلي', 'Minotrix': 'مينوتريكس', 'Booga': 'بوغا',
      'Tut': 'توت', 'Ocularus': 'أوكيولاروس', 'Kargadan': 'كارغادان', 'Grumsnik': 'غرومسنيك'}
# Heroes the game already has as the four playable leaders keep those keys.
LEGACY = {'Dean': 'human', 'Tut': 'zombie', 'Grumsnik': 'orc', 'Raeynor': 'elf'}
CLASS = {'CT_FIGHTER': 'warrior', 'CT_RANGER': 'archer', 'CT_MAGE': 'mage', 'CT_ARTIL': 'artillery'}

def table(name):
    return [r for r in list(csv.reader(open(REF / name, encoding='latin1')))[2:] if r and r[0]]
# Both hero tables list the 22 heroes in the same order (the stats table calls Shaq HT_KORMA, the model table HT_SHAQ).
arche = table('table-33fe88.txt')
heroes = {}
for r, a in zip(table('table-33ddc8.txt'), arche, strict=True):
    tag, name = r[0], r[1]
    key = LEGACY.get(name, 'hero_' + tag[3:].lower())
    heroes[name] = {'key': key, 'name': f'{name} • {AR[name]}', 'attack': int(r[2]), 'health': int(r[3]), 'armor': int(r[4]),
                    'mojo': int(r[5]), 'combatClass': CLASS[a[1]], 'abilityId': None if r[6] == 'AT_NONE' else r[6],
                    'model': f'Archetypes/{a[4].replace("bosses", "Bosses")}/{a[5]}.MDA', 'tag': tag}

# card lookup tables
cards = []
for f in ['cards', 'native-cards', 'ability-cards', 'catalog-cards', 'catalog-magic', 'catalog-equipment']:
    cards += json.load(open(f'src/data/{f}.json'))
by_tag = {c['nativeTag']: c['id'] for c in cards if c.get('nativeTag')}
monsters = [r for r in json.load(open(REF / 'table-3189a0.json'))[1:] if r['Race']]
RACES = []
for r in monsters:
    if r['Race'] not in RACES: RACES.append(r['Race'])
CLASSES = ['CT_FIGHTER', 'CT_RANGER', 'CT_MAGE', 'CT_ARTIL']
group = {}
for r in monsters:
    group.setdefault((r['Race'], r['Class']), []).append(r)
runes = json.load(open(REF / 'table-3acc48.json'))
spells = json.load(open(REF / 'table-3c7f50.json'))
equip = {1: table('table-3f05e0.txt'), 2: table('table-3c2fa0.txt'), 3: table('table-345730.txt')}
missing = {}
def deck(name):
    d = (obb / 'Decks' / f'{name}.bdk').read_bytes()
    n = struct.unpack_from('<I', d, 4)[0]
    out = []
    for i in range(n):
        a, b, c, t = struct.unpack_from('<4H', d, 8 + i * 8)
        if t == 2:
            r = group[(RACES[a - 1], CLASSES[b])][c]; tag = f"{r['Race']}:{r['Name']}"
        elif t == 0: tag = equip[a][b - 1][0]
        elif t == 1: tag = runes[a + 1]['Tag Name']
        else: tag = spells[a + 1]['Tag Name']
        if tag in by_tag: out.append(by_tag[tag])
        else: missing[tag] = missing.get(tag, 0) + 1
    return out

templates = {k.upper(): set(v) for k, v in json.load(open(REF / 'map-templates.json')).items()}
BONUS = {'MCT_BONUS_MOJO2': ('tile', 'altar'), 'MCT_BONUS_PWR2': ('token', 'star'), 'MCT_BONUS_ARM': ('token', 'shield'),
         'MCT_BONUS_REGEN': ('token', 'heart'), 'MCT_BONUS_CARD': ('token', 'card')}
def cell(name):
    """Engine axial key of quest cell 'G4' (same even-q placement as the 13x13 multiplayer boards)."""
    y, x = ord(name[0]) - 65 + 2, int(name[1:]) + 2
    return f'{12 - y - x // 2},{x - 3}'
def layout(qid, n):
    lines = [l.split('//')[0].strip() for l in open(obb / 'Layouts/quests' / qid / f'{n}.txt', encoding='latin1')]
    removed, section = set(), None
    m = {'id': f'Q_{qid}_{n}', 'cells': [], 'tiles': [], 'tokens': [], 'starts': [None, None], 'daises': [[], []]}
    specials = []
    for l in lines:
        if not l: continue
        if l.startswith('['): section = l; continue
        a, b = [x.strip() for x in l.split(',')[:2]]
        a = a.upper(); b = b.upper() if re.fullmatch(r'[a-iA-I]\d', b) else b
        if a == 'TEMPLATE': removed = templates[b.upper()]; continue
        if section == '[2PLAYER]' and re.fullmatch(r'[A-I]\d', b):
            m['starts'] = [cell(a), cell(b)]; continue
        specials.append((a, b))
    # The quest board is the classic hexagon of radius 4 around E4 (all 2270 cells named in the layout files
    # lie inside it); templates then cut cells out of it.
    cq, cr = map(int, cell('E4').split(','))
    for y in 'ABCDEFGHI':
        for x in range(9):
            q, r = map(int, cell(f'{y}{x}').split(','))
            if max(abs(q - cq), abs(r - cr), abs(q - cq + r - cr)) <= 4 and f'{y}{x}' not in removed:
                m['cells'].append(cell(f'{y}{x}'))
    for a, b in specials:
        k = cell(a)
        if b.startswith('MCT_ROCK'): m['tiles'].append([k, 'rock'])
        elif b == 'MCT_RUNEDAIS_P1': m['daises'][0].append(k)
        elif b == 'MCT_RUNEDAIS_P2': m['daises'][1].append(k)
        elif b in BONUS:
            kind, v = BONUS[b]; m['tiles' if kind == 'tile' else 'tokens'].append([k, v])
        else: raise ValueError((qid, n, b))
    assert None not in m['starts'] and all(s in m['cells'] for s in m['starts']), (qid, n)
    return m

quests, maps, used_heroes = [], {}, set()
STEP = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}
for qid, title, english, body, ai in QUESTS:
    text = (obb / 'Quests' / f'{qid}.txt').read_text(encoding='latin1')
    rooms = []
    for block in re.split(r'(?=\[(?:LAST)?BATTLE\])', text):
        if not block.strip().startswith('['): continue
        head, *rest = block.splitlines()
        vals = [l.split('//')[0].strip() for l in rest]
        vals = [v for v in vals if v]
        n, rel, hero, deck_name, lay = vals[:5]
        if rel == 'X,X': parent, x, y = None, 0, 0
        else:
            d, p = rel.split(',');p = int(p); base = next(r for r in rooms if r['n'] == p)
            parent, x, y = p, base['x'] + STEP[d][0], base['y'] + STEP[d][1]
        hero = next(k for k in heroes if k.lower() == hero.lower()); h = heroes[hero]; used_heroes.add(hero)
        key = f'Q_{qid}_{lay}'
        if key not in maps: maps[key] = layout(qid, int(lay))
        room = {'n': int(n), 'parent': parent, 'x': x, 'y': y, 'hero': h['key'], 'deckName': deck_name, 'deck': deck(deck_name), 'map': key}
        if 'LASTBATTLE' in head: room['boss'] = 'last'
        elif 'sub-boss' in head.lower(): room['boss'] = 'sub'
        rooms.append(room)
    assert len({(r['x'], r['y']) for r in rooms}) == len(rooms), qid
    quests.append({'id': qid, 'title': title, 'english': english, 'text': body, 'ai': ai, 'enemyBonusMojo': 1 if qid in ('hard2', 'hard3') else 0, 'rooms': rooms})

hero_out = {h['key']: {k: v for k, v in h.items() if k != 'key'} for n, h in heroes.items() if n in used_heroes or h['key'] in LEGACY.values()}
Path('src/data/native-quests.json').write_text(json.dumps({'heroes': hero_out, 'quests': quests}, ensure_ascii=False, separators=(',', ':')) + '\n')
Path('src/data/quest-maps.json').write_text(json.dumps(list(maps.values()), separators=(',', ':')) + '\n')
Path(REF / 'quest-cards-not-imported.txt').write_text('Cards referenced by quest decks that the game has not imported (left out of those decks):\n' + ''.join(f'{k} x{v}\n' for k, v in sorted(missing.items())))
print(json.dumps({'quests': {q['id']: len(q['rooms']) for q in quests}, 'maps': len(maps), 'heroes': sorted(hero_out),
                  'deckSizes': sorted({len(r['deck']) for q in quests for r in q['rooms']}), 'missingCards': sum(missing.values()), 'missingKinds': len(missing)}, ensure_ascii=False))
