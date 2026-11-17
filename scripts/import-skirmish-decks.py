"""Import the original game's Skirmish deck library.

The original keeps a list of 227 enemy decks (reference/native-rules/table-349a00.txt, the list CEnemyDeckMgr::Init
loads; names containing "starter" are skipped). For each deck it records:
  - the deck rules it is legal under (CUserAccount::ValidateDeck for each of the 5 rules),
  - which hero classes may lead it: the class of the first weapon in the deck that none of the deck's monsters can use
    (fighter, ranger, mage, then artillery), otherwise the classes of every weapon in the deck, otherwise any class,
  - its average Mojo cost (CPanel_DeckLoadSave::GetMojoAvg), truncated after subtracting 0.5 and capped at 5.
CEnemyDeckMgr::GetRandomDeck then picks a random legal deck and a random hero of an allowed class whose starting Mojo
is at least that value. Heroes by class (eHeroType): fighter 1,2,3,4,13,16 - ranger 5,6,7,8,14,17 -
mage 9,10,11,12,15,18 - artillery 19,20,21.

Decks/<name>.bdk  u32 version, u32 count, then count records of 4 x u16 (a, b, c, type); see import-native-quests.py.
Cards this game has not imported are dropped; a deck is kept for a rule only if what is left still passes that rule.

Writes src/data/skirmish-decks.json.
usage: python3 scripts/import-skirmish-decks.py <extracted-obb-dir>
"""
import json, sys, struct, csv
from pathlib import Path

obb = Path(sys.argv[1])
REF = Path('reference/native-rules')

def table(name):
    return [r for r in list(csv.reader(open(REF / name, encoding='latin1')))[2:] if r and r[0]]

cards = []
for f in ['cards', 'native-cards', 'ability-cards', 'catalog-cards', 'catalog-magic', 'catalog-equipment']:
    cards += json.load(open(f'src/data/{f}.json'))
by_tag = {c['nativeTag']: c for c in cards if c.get('nativeTag')}
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

# Heroes the Skirmish picker uses, by class, in eHeroType order (row of the hero table).
heroes_table = table('table-33ddc8.txt')
HERO_GROUPS = {'warrior': [1, 2, 3, 4, 13, 16], 'archer': [5, 6, 7, 8, 14, 17], 'mage': [9, 10, 11, 12, 15, 18],
               'artillery': [19, 20, 21]}
LEGACY = {'Dean': 'human', 'Tut': 'zombie', 'Grumsnik': 'orc', 'Raeynor': 'elf'}
def hero_key(row):
    return LEGACY.get(row[1], 'hero_' + row[0][3:].lower())
heroes = {cls: [{'key': hero_key(heroes_table[i]), 'name': heroes_table[i][1], 'mojo': int(heroes_table[i][5])} for i in ids]
          for cls, ids in HERO_GROUPS.items()}

CLASS_OF = {0: 'warrior', 1: 'archer', 2: 'mage', 3: 'artillery'}
missing_total = {}
def decode(name):
    d = (obb / 'Decks' / f'{name}.bdk').read_bytes()
    n = struct.unpack_from('<I', d, 4)[0]
    out, monster_classes, weapon_classes, costs, missing = [], set(), [], [], 0
    for i in range(n):
        a, b, c, t = struct.unpack_from('<4H', d, 8 + i * 8)
        t &= 0xff                                           # the high byte is the foil flag
        if t == 2:
            r = group[(RACES[a - 1], CLASSES[b])][c]; tag = f"{r['Race']}:{r['Name']}"; monster_classes.add(CLASS_OF[b])
        elif t == 0: tag = equip[a][b - 1][0]
        elif t == 1: tag = runes[a + 1]['Tag Name']
        else: tag = spells[a + 1]['Tag Name']
        card = by_tag.get(tag)
        if card:
            out.append(card['id']); costs.append(card.get('cost', 0))
            if t == 0 and a == 1 and card.get('forClass'): weapon_classes.append(card['forClass'])
        else:
            missing += 1; missing_total[tag] = missing_total.get(tag, 0) + 1
    return out, monster_classes, weapon_classes, costs, missing, n

def hero_classes(monster_classes, weapon_classes):
    for cls in ['warrior', 'archer', 'mage', 'artillery']:   # a weapon nobody in the deck can hold is the hero's
        if cls in weapon_classes and cls not in monster_classes: return [cls]
    present = [cls for cls in ['warrior', 'archer', 'mage', 'artillery'] if cls in weapon_classes]
    return present or ['warrior', 'archer', 'mage', 'artillery']

names = [l.strip() for l in open(REF / 'table-349a00.txt', encoding='latin1') if l.strip() and 'starter' not in l.lower()]
decks = []
for name in names:
    ids, mc, wc, costs, missing, original = decode(name)
    avg = sum(costs) / len(costs) if costs else 0
    decks.append({'name': name, 'cards': ids, 'originalCount': original, 'missing': missing,
                  'heroClasses': hero_classes(mc, wc), 'mojoNeeded': min(5, int(avg - 0.5)) if avg >= .5 else 0})
json.dump({'heroes': heroes, 'decks': decks}, open('src/data/skirmish-decks.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(decks), 'decks;', sum(d['missing'] for d in decks), 'cards not in this game across',
      sum(1 for d in decks if d['missing']), 'decks')
print('most common missing:', sorted(missing_total.items(), key=lambda x: -x[1])[:12])
