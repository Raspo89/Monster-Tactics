"""Import the original weapons, armour and shields from the recovered native tables:
table-3f05e0 (weapons), table-345730 (armour), table-3c2fa0 (shields) -> src/data/catalog-equipment.json.

Rules from the game's own help text (Locale/eng.txt, HELP_OTHERCARDS_2..4 and HELP_MONSTERCARDS_8):
mages may only use staffs, archers only bows, warriors all melee weapons (sword, axe, mace, dagger),
artillery the artillery ammunition; armour and shields go on any monster, and a monster may carry both.
Perks: BC_POWER/BC_ARMOUR/BC_HEALTH change the stat, BC_MANA gives Mojo each turn,
BC_AFFLICTION_* afflicts the target on a hit (value = chance in %), BC_PROT_ALL/BAD block afflictions.
Ability boosts and splash are not imported yet (listed in reference/native-rules/equipment-notes.txt).
Run from the project root: python3 scripts/import-native-equipment.py
"""
import csv, json
from pathlib import Path
REF = Path('reference/native-rules')
def rows(name, key):
    return [r for r in list(csv.reader(open(REF / name, encoding='latin1')))[2:] if r and r[0]]
WEAPON = {'BWT_SWORD': ('sword', 'warrior', 'سيف'), 'BWT_AXE': ('axe', 'warrior', 'فأس'), 'BWT_MACE': ('mace', 'warrior', 'مطرقة'),
          'BWT_DAGGER': ('dagger', 'warrior', 'خنجر'), 'BWT_BOW': ('bow', 'archer', 'قوس'), 'BWT_STAFF': ('staff', 'mage', 'عصا'),
          'BWT_ARTIL': ('artillery', 'artillery', 'ذخيرة مدفعية')}
FOR = {'warrior': 'للمحاربين', 'archer': 'للرماة', 'mage': 'للسحرة', 'artillery': 'للمدفعية'}
AFF = {'STUN': ('stun', 'الذهول'), 'DEATHMARK': ('deathmark', 'علامة الموت'), 'ICEBLOCK': ('ice', 'التجميد'), 'FLAME': ('flame', 'الاشتعال'), 'SNARED': ('snare', 'التقييد')}
notes = []
def perks(pairs, e, tag):
    for perk, value in pairs:
        v = int(float(value or 0))
        if perk in ('', 'BC_NONE'): continue
        if perk == 'BC_POWER': e['attack'] = e.get('attack', 0) + v
        elif perk == 'BC_ARMOUR': e['armor'] = e.get('armor', 0) + v
        elif perk == 'BC_HEALTH': e['health'] = e.get('health', 0) + v
        elif perk == 'BC_MANA': e['mojo'] = e.get('mojo', 0) + v
        elif perk.startswith('BC_AFFLICTION_') and perk[14:] in AFF: e['afflict'], e['chance'] = AFF[perk[14:]][0], v
        elif perk == 'BC_PROT_ALL': e['protect'] = ['all']
        elif perk == 'BC_PROT_BAD': e['protect'] = ['bad']
        elif perk.startswith('BC_PROT_') and perk[8:] in AFF: e.setdefault('protect', []).append(AFF[perk[8:]][0])
        else: notes.append(f'{tag}\tperk {perk} {v} not supported')
def sign(n): return f'+{n}' if n > 0 else str(n)
def text(e, who):
    parts = []
    if e.get('attack'): parts.append(f"{sign(e['attack'])} هجوم")
    if e.get('armor'): parts.append(f"{sign(e['armor'])} دفاع")
    if e.get('health'): parts.append(f"{sign(e['health'])} صحة")
    if e.get('mojo'): parts.append(f"{sign(e['mojo'])} موجو كل دور")
    if e.get('afflict'):
        name = next(a for k, a in AFF.values() if k == e['afflict'])
        parts.append(f"يصيب الهدف بـ{name}" + ('' if e['chance'] >= 100 else f" ({e['chance']}%)"))
    for p in e.get('protect', []):
        parts.append({'all': 'محمي من كل الحالات', 'bad': 'محمي من الحالات السيئة'}.get(p) or 'محمي من ' + next(a for k, a in AFF.values() if k == p))
    return ' • '.join(parts or ['بدون زيادة']) + f' • {who}'
out = []
# weapons: Tag,Rarity,Mojo,Name,Short,Type,Model,Texture,Power,Perk1,V,Perk2,V,...,Boosts Ability,Boost Value,Splash
for r in rows('table-3f05e0.txt', 0):
    kind, cls, ar = WEAPON[r[5]]
    e = {'attack': int(r[8] or 0)}; perks([(r[9], r[10]), (r[11], r[12])], e, r[0])
    if len(r) > 18 and r[17] not in ('', 'AT_NONE'): notes.append(f'{r[0]}\tboosts {r[17]} by {r[18]} not supported')
    if len(r) > 19 and r[19] not in ('', '0'): notes.append(f'{r[0]}\tsplash {r[19]} not supported')
    out.append({'id': 'NE_' + r[0], 'name': r[3].strip(), 'race': 'neutral', 'type': 'weapon', 'slot': 'weapon', 'kind': kind, 'forClass': cls,
                'cost': int(r[2]), 'rarity': r[1], 'text': text(e, ar + ' ' + FOR[cls]), 'keywords': [], 'nativeTag': r[0], 'equip': e})
# armour: Tag,Rarity,Mojo,Name,Short,Armour,Perk1,V,Perk2,V,...
for r in rows('table-345730.txt', 0):
    e = {'armor': int(r[5] or 0)}; perks([(r[6], r[7]), (r[8], r[9])], e, r[0])
    out.append({'id': 'NE_' + r[0], 'name': r[3].strip(), 'race': 'neutral', 'type': 'armor', 'slot': 'armor', 'kind': 'armour',
                'cost': int(r[2]), 'rarity': r[1], 'text': text(e, 'درع (خوذة وصدرية وأكتاف) لأي وحش'), 'keywords': [], 'nativeTag': r[0], 'equip': e})
# shields: Tag,Rarity,Mojo,Name,Short,Model,Texture,Armour,Perk1,V,Perk2,V,...
for r in rows('table-3c2fa0.txt', 0):
    e = {'armor': int(r[7] or 0)}; perks([(r[8], r[9]), (r[10], r[11])], e, r[0])
    out.append({'id': 'NE_' + r[0], 'name': r[3].strip(), 'race': 'neutral', 'type': 'armor', 'slot': 'shield', 'kind': 'shield',
                'cost': int(r[2]), 'rarity': r[1], 'text': text(e, 'ترس لأي وحش'), 'keywords': [], 'nativeTag': r[0], 'equip': e})
out = [c for c in out if c['cost'] or any(v for v in c['equip'].values())]  # default 'bare hands' weapons
for c in out:
    c['equip'] = {k: v for k, v in c['equip'].items() if v}
    if c['rarity'] not in ('C', 'U', 'R', 'L'): c['rarity'] = 'R'
Path('src/data/catalog-equipment.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
(REF / 'equipment-notes.txt').write_text('\n'.join(notes) + '\n')
from collections import Counter
print(Counter(c['kind'] for c in out), 'notes', len(notes))
