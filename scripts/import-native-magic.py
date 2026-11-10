"""Import original runes and spells whose effects the engine supports, from the recovered native tables.

Reads reference/native-rules/table-3acc48.json (runes), table-3c7f50.json (spells) and the numeric globals
in table-34b638.txt, turns each tooltip into a structured effect and writes src/data/catalog-magic.json.
Cards whose effect is not supported yet are listed in reference/native-rules/magic-not-imported.txt.
Run from the project root: python3 scripts/import-native-magic.py
"""
import json, re
from pathlib import Path

REF = Path('reference/native-rules')
G = {}
for line in open(REF / 'table-34b638.txt', encoding='latin1'):
    m = re.match(r'\s*([-+]?[\d.]+)\s*//\s*(\w+)', line)
    if m: G[m.group(2).lower()] = float(m.group(1))

def param(name):
    """Value and stat of a tooltip parameter such as RU_MajorPower_Power or SP_JustMinus3_Health."""
    low = name.lower(); stat = low.rsplit('_', 1)[1]
    if low in G: v = G[low]
    else:
        m = re.search(r'(just|mojo|herohealth|attack|armour|health)(minus)?(\d+)_', low)
        if not m: raise KeyError(name)
        v = -int(m.group(3)) if m.group(2) else int(m.group(3))
    stat = {'power': 'attack', 'attack': 'attack', 'armour': 'armor', 'health': 'health', 'abshealth': 'health', 'damage': 'damage', 'mojo': 'mojo'}[stat]
    return int(v), stat

RACES = {'humans': 'human', 'elves': 'elf', 'orcs': 'orc', 'zombies': 'zombie', 'lizards': 'lizard', 'dwarves': 'dwarf', 'minotaurs': 'minotaur',
         'werewolves': 'werewolf', 'golem': 'golem', 'golems': 'golem', 'elementals': 'elemental', 'cyclops': 'cyclops', 'skeletons': 'skeleton',
         'robots': 'robot', 'imps': 'imp', 'spectres': 'spectre', 'vampires': 'vampire'}
CLASSES = {'warriors': 'warrior', 'archers': 'archer', 'mages': 'mage', 'artillery': 'artillery', 'monsters': None, 'creatures': None}
WHO = r"(?:(your|friendly|enemy|other players'|of your)\s+)?"
NOUN = r"(" + '|'.join(list(RACES) + list(CLASSES)) + r")"
P = r"((?:RU|SP)_\w+)"

def group(who, noun):
    g = {'who': {'your': 'mine', 'friendly': 'mine', 'of your': 'mine', 'enemy': 'enemy', "other players'": 'enemy'}.get(who or '', 'all')}
    if noun in RACES: g['race'] = RACES[noun]
    elif CLASSES.get(noun): g['cls'] = CLASSES[noun]
    return g

AFFLICT = {'Dazed': 'stun', 'Mighty': 'mighty', 'Berserk': 'berserk', 'Snared': 'snare', 'Regen': 'regen', 'Death Mark': 'deathmark',
           'Ice Block': 'ice', 'Flame': 'flame', 'Vengeance': 'vengeance', 'Magic shield': 'shield'}

def parse_spell(t, use_on):
    t = re.sub(r'@C\[\d+\]', '', t).replace('#', ',').strip()
    m = re.fullmatch(r'Target (?:monster|creature) suffers ' + P + r' damage\.', t)
    if m and use_on == 'UO_MONSTER': return {'target': 'enemy', 'ops': [{'op': 'damage', 'g': {'who': 'target'}, 'n': param(m.group(1))[0]}]}
    m = re.fullmatch(r'Target (?:monster|creature) gains ' + P + r'\.', t)
    if m:
        n, stat = param(m.group(1))
        return {'target': 'mine' if n > 0 else 'enemy', 'ops': [{'op': 'heal' if stat == 'health' else 'stat', 'g': {'who': 'target'}, 'stat': stat, 'n': n}]}
    m = re.fullmatch(r'Target monster becomes afflicted with ([A-Za-z ]+?)(?: and cannot attack this turn)?\.', t)
    if m and m.group(1) in AFFLICT:
        name = AFFLICT[m.group(1)]
        good = name in ('mighty', 'regen', 'vengeance', 'shield', 'berserk')
        return {'target': 'mine' if good else 'enemy', 'ops': [{'op': 'afflict', 'g': {'who': 'target'}, 'name': name}]}
    m = re.fullmatch(r'All ' + WHO + r'heroes become afflicted with ([A-Za-z ]+?)(?: and cannot attack this turn)?\.', t)
    if m and m.group(2) in AFFLICT: return {'ops': [{'op': 'afflict', 'g': {'who': {'enemy': 'enemy', 'your': 'mine'}.get(m.group(1) or '', 'all'), 'heroes': True}, 'name': AFFLICT[m.group(2)]}]}
    m = re.fullmatch(r'All ' + WHO + NOUN + r' suffers? ' + P + r' damage\.', t)
    if m: return {'ops': [{'op': 'damage', 'g': group(m.group(1), m.group(2)), 'n': param(m.group(3))[0]}]}
    m = re.fullmatch(r'All ' + WHO + r'heroes suffer ' + P + r' damage\.', t)
    if m: return {'ops': [{'op': 'damage', 'g': {'who': 'enemy' if m.group(1) else 'all', 'heroes': True}, 'n': param(m.group(2))[0]}]}
    m = re.fullmatch(r'Destroy all ' + WHO + NOUN + r'\.', t)
    if m: return {'ops': [{'op': 'destroy', 'g': group(m.group(1), m.group(2))}]}
    m = re.fullmatch(r'Destroy all (enemy )?runes\.', t)
    if m: return {'ops': [{'op': 'destroyRunes', 'who': 'enemy' if m.group(1) else 'all'}]}
    m = re.fullmatch(r'All ' + WHO + NOUN + r' (?:receives?|suffers?) ' + P + r'\.', t)
    if m:
        n, stat = param(m.group(3)); g = group(m.group(1), m.group(2))
        if stat == 'health' and n > 0: return {'ops': [{'op': 'heal', 'g': g, 'n': n}]}
        if stat == 'health': return {'ops': [{'op': 'lose', 'g': g, 'n': -n}]}
        if stat in ('attack', 'armor'): return {'ops': [{'op': 'stat', 'g': g, 'stat': stat, 'n': n}]}
    m = re.fullmatch(r'All ' + WHO + NOUN + r' suffer ' + P + r'\. Your hero gains ' + P + r' for each death\.', t)
    if m: return {'ops': [{'op': 'lose', 'g': group(m.group(1), m.group(2)), 'n': -param(m.group(3))[0], 'heroPerDeath': param(m.group(4))[0]}]}
    m = re.fullmatch(r'All ' + WHO + NOUN + r' lose all (bad |good )?afflictions\.', t)
    if m: return {'ops': [{'op': 'cleanse', 'g': group(m.group(1), m.group(2)), 'which': (m.group(3) or 'all').strip()}]}
    m = re.fullmatch(r'All ' + WHO + NOUN + r' (?:are|is) returned to (?:their owners hands|your hand)\.(?: Their owner\'s hero gains ' + P + r' for each bounce\.)?\s*\(Includes carried equipment\.\)', t)
    if m: return {'ops': [{'op': 'bounce', 'g': group(m.group(1), m.group(2)), **({'heroPerBounce': param(m.group(3))[0]} if m.group(3) else {})}]}
    m = re.fullmatch(r'All (?:of )?your ' + NOUN + r' take another turn\.', t)
    if m: return {'ops': [{'op': 'refresh', 'g': group('your', m.group(1))}]}
    m = re.fullmatch(r'Draw (\d+) additional cards?\.', t)
    if m: return {'ops': [{'op': 'draw', 'n': int(m.group(1))}]}
    m = re.fullmatch(r'Get ' + P + r'\. Your hero suffers ' + P + r'\.', t)
    if m: return {'ops': [{'op': 'mojo', 'n': param(m.group(1))[0]}, {'op': 'heroLose', 'n': -param(m.group(2))[0]}]}
    m = re.fullmatch(r'Get between ' + P + r' and ' + P + r' at random\. Your hero suffers ' + P + r'\.', t)
    if m: return {'ops': [{'op': 'mojo', 'n': param(m.group(1))[0], 'max': param(m.group(2))[0]}, {'op': 'heroLose', 'n': -param(m.group(3))[0]}]}
    m = re.fullmatch(r'Your hero receives ' + P + r'\.', t)
    if m: return {'ops': [{'op': 'heroHeal', 'n': param(m.group(1))[0]}]}
    return None

def parse_rune(t):
    t = re.sub(r'@C\[\d+\]', '', t).replace('#', ',').strip()
    m = re.fullmatch(r'All ' + WHO + NOUN + r' (?:receive|suffer)s? (?:a )?' + P + r'(?: boost)?\.', t)
    if m:
        n, stat = param(m.group(3))
        if stat in ('attack', 'armor', 'health'): return {'auras': [{'g': group(m.group(1), m.group(2)), 'stat': stat, 'n': n}]}
    m = re.fullmatch(r'All ' + WHO + NOUN + r' gain ' + P + r' but suffer ' + P + r'\.', t)
    if m: return {'auras': [{'g': group(m.group(1), m.group(2)), 'stat': param(p)[1], 'n': param(p)[0]} for p in m.group(3, 4)]}
    m = re.fullmatch(r'All ' + WHO + NOUN + r' gain ' + P + r' and ' + P + r' and ' + P + r'\.', t)
    if m: return {'auras': [{'g': group(m.group(1), m.group(2)), 'stat': param(p)[1], 'n': param(p)[0]} for p in m.group(3, 4, 5)]}
    m = re.fullmatch(r'Your hero gains ' + P + r' and ' + P + r' and ' + P + r'\.', t)
    if m: return {'auras': [{'g': {'who': 'mine', 'heroes': True}, 'stat': param(p)[1], 'n': param(p)[0]} for p in m.group(1, 2, 3)]}
    m = re.fullmatch(r'Your hero generates ' + P + r' each upkeep\.', t)
    if m: return {'mojo': {'mine': param(m.group(1))[0]}}
    m = re.fullmatch(r'All players get ' + P + r' each upkeep\.', t)
    if m: return {'mojo': {'mine': param(m.group(1))[0], 'enemy': param(m.group(1))[0]}}
    m = re.fullmatch(r'Other players get ' + P + r' on their upkeep, whilst you get ' + P + r' on yours\.', t)
    if m: return {'mojo': {'enemy': param(m.group(1))[0], 'mine': param(m.group(2))[0]}}
    if t == 'Draw an additional card during your upkeep.': return {'draw': 1}
    if t == "Your monsters can move on the turn they're played.": return {'haste': True}
    return None

AR_RACE = {'human': 'البشر', 'elf': 'الجان', 'orc': 'الأورك', 'zombie': 'الزومبي', 'lizard': 'السحالي', 'dwarf': 'الأقزام', 'minotaur': 'المينوتور',
           'werewolf': 'المستذئبين', 'golem': 'الغولم', 'elemental': 'العناصر', 'cyclops': 'السايكلوب', 'skeleton': 'الهياكل', 'robot': 'الروبوتات',
           'imp': 'العفاريت', 'spectre': 'الأطياف', 'vampire': 'مصاصي الدماء'}
AR_CLS = {'warrior': 'المحاربين', 'archer': 'الرماة', 'mage': 'السحرة', 'artillery': 'المدفعية'}
AR_STAT = {'attack': 'هجوم', 'armor': 'درع', 'health': 'صحة'}
AR_AFF = {'stun': 'الذهول', 'mighty': 'القوة', 'berserk': 'الهياج', 'snare': 'التقييد', 'regen': 'التجدد', 'deathmark': 'علامة الموت', 'ice': 'التجميد',
          'flame': 'الاشتعال', 'vengeance': 'الانتقام', 'shield': 'الحاجز السحري'}

def who_ar(g):
    if g.get('who') == 'target': return 'الهدف'
    if g.get('heroes'): return {'mine': 'قائدك', 'enemy': 'قائد الخصم', 'all': 'كل القادة'}[g['who']]
    noun = AR_RACE.get(g.get('race')) or AR_CLS.get(g.get('cls')) or 'الوحوش'
    return {'mine': f'كل {noun} اللي لك', 'enemy': f'كل {noun} اللي للخصم', 'all': f'كل {noun}'}[g['who']]

def sign(n): return f'+{n}' if n > 0 else str(n)

def text(e):
    parts = []
    for o in e.get('ops', []):
        g = o.get('g', {})
        k = o['op']
        if k == 'damage': parts.append(f"{who_ar(g)}: {o['n']} ضرر")
        elif k == 'destroy': parts.append(f"دمّر {who_ar(g)}")
        elif k == 'heal': parts.append(f"{who_ar(g)}: علاج {o['n']}")
        elif k == 'stat': parts.append(f"{who_ar(g)}: {sign(o['n'])} {AR_STAT[o['stat']]}")
        elif k == 'lose': parts.append(f"{who_ar(g)} تخسر {o['n']} صحة" + (f"، وقائدك يكسب {o['heroPerDeath']} صحة عن كل وحش يموت" if o.get('heroPerDeath') else ''))
        elif k == 'cleanse': parts.append(f"{who_ar(g)} تتخلص من " + {'bad': 'كل الحالات السيئة', 'good': 'كل الحالات الجيدة', 'all': 'كل الحالات'}[o['which']])
        elif k == 'bounce': parts.append(f"{who_ar(g)} ترجع ليد صاحبها مع عتادها" + (f"، وقائد صاحبها يكسب {o['heroPerBounce']} صحة عن كل وحش" if o.get('heroPerBounce') else ''))
        elif k == 'afflict': parts.append(f"{who_ar(g)}: " + ('يكسب ' if o['name'] in ('mighty', 'regen', 'vengeance', 'shield', 'berserk') else 'يصيبه ') + AR_AFF[o['name']])
        elif k == 'refresh': parts.append(f"{who_ar(g)} تتحرك وتهاجم مرة ثانية هالدور")
        elif k == 'draw': parts.append(f"اسحب {o['n']} " + ('بطاقة' if o['n'] == 1 else 'بطاقات'))
        elif k == 'mojo': parts.append(f"اكسب {o['n']} موجو" if 'max' not in o else f"اكسب من {o['n']} إلى {o['max']} موجو عشوائيًا")
        elif k == 'heroLose': parts.append(f"قائدك يخسر {o['n']} صحة")
        elif k == 'heroHeal': parts.append(f"قائدك يكسب {o['n']} صحة")
        elif k == 'destroyRunes': parts.append('دمّر ' + ('كل رونات الخصم' if o['who'] == 'enemy' else 'كل الرونات'))
    groups = []
    for a in e.get('auras', []):
        if groups and groups[-1][0] == a['g']: groups[-1][1].append(a)
        else: groups.append((a['g'], [a]))
    for g, items in groups:
        parts.append(f"{who_ar(g)}: " + ' و'.join(f"{sign(a['n'])} {AR_STAT[a['stat']]}" for a in items))
    if 'mojo' in e:
        m = e['mojo']
        if m.get('mine'): parts.append(f"قائدك يولد {m['mine']} موجو إضافي كل دور")
        if m.get('enemy'): parts.append(f"الخصم يولد {m['enemy']} موجو إضافي كل دور")
    if e.get('draw'): parts.append('اسحب بطاقة إضافية في بداية كل دور')
    if e.get('haste'): parts.append('وحوشك تتحرك في دور استدعائها')
    s = '، '.join(parts)
    return s + (' ما دام الرون قائمًا' if 'auras' in e else '')

already = {c.get('nativeTag') for c in json.loads(Path('src/data/cards.json').read_text())}
out, skipped = [], []
for kind, table in (('rune', 'table-3acc48.json'), ('spell', 'table-3c7f50.json')):
    for r in json.loads((REF / table).read_text())[2:]:
        if not r['Tag Name'] or r['Tag Name'] == 'x': continue
        tip = r['Tooltip'].replace('\\n', ' ').replace('\n', ' ')
        tip = re.sub(r'\s+', ' ', tip)
        try:
            e = parse_rune(tip) if kind == 'rune' else parse_spell(tip, r['Use On'])
        except KeyError:
            e = None
        if r['Tag Name'] in already: continue
        if not e or not text(e):
            skipped.append(f"{kind}\t{r['Tag Name']}\t{tip}"); continue
        out.append({'id': ('NR_' if kind == 'rune' else 'NS_') + r['Tag Name'], 'name': r['Name'], 'race': 'neutral', 'type': kind,
                    'cost': int(r['Mojo']), 'text': text(e), 'keywords': [], 'rarity': r['Rarity'], 'nativeTag': r['Tag Name'],
                    'art': r['Texture Name'], 'effect': e})
Path('src/data/catalog-magic.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
(REF / 'magic-not-imported.txt').write_text('\n'.join(skipped) + '\n')
print(json.dumps({'runes': sum(c['type'] == 'rune' for c in out), 'spells': sum(c['type'] == 'spell' for c in out), 'notYet': len(skipped)}))
