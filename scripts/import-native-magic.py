"""Import original runes and spells whose effects the engine supports, from the recovered native tables.

Reads reference/native-rules/table-3acc48.json (runes), table-3c7f50.json (spells) and the numeric globals
in table-34b638.txt, turns each tooltip into a structured effect and writes src/data/catalog-magic.json.
7.28 added parse_more for the remaining families. Cards whose effect is not supported yet are listed in reference/native-rules/magic-not-imported.txt.
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
    m = re.fullmatch(r'Target monster becomes afflicted with ([A-Za-z ]+?)( and cannot attack this turn)?\.', t)
    if m and m.group(1) in AFFLICT:
        name = AFFLICT[m.group(1)]
        good = name in ('mighty', 'regen', 'shield', 'berserk')
        return {'target': 'mine' if good else 'enemy', 'ops': [{'op': 'afflict', 'g': {'who': 'target'}, 'name': name, **({'blockAttackThisTurn': True} if m.group(2) else {})}]}
    m = re.fullmatch(r'All ' + WHO + r'heroes become afflicted with ([A-Za-z ]+?)( and cannot attack this turn)?\.', t)
    if m and m.group(2) in AFFLICT: return {'ops': [{'op': 'afflict', 'g': {'who': {'enemy': 'enemy', 'your': 'mine'}.get(m.group(1) or '', 'all'), 'heroes': True}, 'name': AFFLICT[m.group(2)], **({'blockAttackThisTurn': True} if m.group(3) else {})}]}
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
    if t == 'All enemy creatures lose all weapon upgrades.': return {'ops': [{'op': 'unequip', 'g': {'who': 'enemy'}, 'which': 'weapon'}]}
    if t == 'All creatures lose all defensive equipment (shields & armour).': return {'ops': [{'op': 'unequip', 'g': {'who': 'all'}, 'which': 'defence'}]}
    m = re.fullmatch(r'Lava erupts from (SP_\w+_Count) random tiles, dealing (SP_\w+_Damage) damage to any creature stood there\.', t)
    if m: return {'ops': [{'op': 'eruption', 'n': int(G[m.group(1).lower()]), 'dmg': int(G[m.group(2).lower()])}]}
    m = re.fullmatch(r'Move one enemy hero to a random position up to (SP_Hurricane_MaxRange) spaces away\.', t)
    if m: return {'ops': [{'op': 'tornado', 'min': int(G['sp_hurricane_minrange']), 'max': int(G[m.group(1).lower()])}]}
    m = re.fullmatch(r'Receive (SP_MojoBoost_Mojo) for each of your runes in play\.', t)
    if m: return {'ops': [{'op': 'mojoPerRune', 'n': int(G[m.group(1).lower()]), 'who': 'mine'}]}
    m = re.fullmatch(r'Receive (SP_MojoTurbo_Mojo) for every rune in play\.', t)
    if m: return {'ops': [{'op': 'mojoPerRune', 'n': int(G[m.group(1).lower()]), 'who': 'all'}]}
    m = re.fullmatch(r'Discard your hand, then draw (\d+) new cards\.', t)
    if m: return {'ops': [{'op': 'burnHand', 'n': int(m.group(1))}]}
    m = re.fullmatch(r'For every rune each enemy has in play, each of their monsters receives (SP_runeBane_Damage) damage\.', t)
    if m: return {'ops': [{'op': 'runeDamage', 'n': int(G[m.group(1).lower()]), 'per': 'enemy'}]}
    m = re.fullmatch(r'For every rune in play, each enemy monster receives (SP_runePain_Damage) damage\.', t)
    if m: return {'ops': [{'op': 'runeDamage', 'n': int(G[m.group(1).lower()]), 'per': 'all'}]}
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
    m = re.fullmatch(r'All your monster abilities cost (RU_Accounting_Mojo) to activate\.', t)
    if m: return {'abilityDiscount': -int(G[m.group(1).lower()])}
    m = re.fullmatch(r"Your opponent's cards cost an extra (RU_BankersDelight_Mojo) to play from hand\.", t)
    if m: return {'tax': int(G[m.group(1).lower()])}
    m = re.fullmatch(r'All your monsters receive (RU_\w+HeroBash_Power) against heroes\.', t, re.I)
    if m: return {'heroBash': int(G[m.group(1).lower()])}
    m = re.fullmatch(r'Receive (RU_Reaper_Mojo) whenever a monster dies\.', t)
    if m: return {'reaper': int(G[m.group(1).lower()])}
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
        if k in NEW_OPS or any(x in g for x in ('both', 'aff', 'tile', 'minHealth', 'maxHealth', 'notRace')) or g.get('who') == 'target' and e.get('target') in TARGET_AR or k == 'unequip' and (o['which'] == 'all' or g.get('both') or g.get('heroes')) or k == 'destroyRunes' and o['who'] == 'mine':
            parts.append(op_more(o, e)); continue
        if k == 'damage': parts.append(f"{who_ar(g)}: {o['n']} ضرر")
        elif k == 'destroy': parts.append(f"دمّر {who_ar(g)}")
        elif k == 'heal': parts.append(f"{who_ar(g)}: علاج {o['n']}")
        elif k == 'stat': parts.append(f"{who_ar(g)}: {sign(o['n'])} {AR_STAT[o['stat']]}")
        elif k == 'lose': parts.append(f"{who_ar(g)} تخسر {o['n']} صحة" + (f"، وقائدك يكسب {o['heroPerDeath']} صحة عن كل وحش يموت" if o.get('heroPerDeath') else ''))
        elif k == 'cleanse': parts.append(f"{who_ar(g)} تتخلص من " + {'bad': 'كل الحالات السيئة', 'good': 'كل الحالات الجيدة', 'all': 'كل الحالات'}[o['which']])
        elif k == 'bounce': parts.append(f"{who_ar(g)} ترجع ليد صاحبها مع عتادها" + (f"، وقائد صاحبها يكسب {o['heroPerBounce']} صحة عن كل وحش" if o.get('heroPerBounce') else ''))
        elif k == 'afflict':
            parts.append(f"{who_ar(g)}: " + ('يكسب ' if o['name'] in ('mighty', 'regen', 'shield', 'berserk') else 'يصيبه ') + AR_AFF[o['name']])
            if o.get('blockAttackThisTurn'): parts[-1] += '، ولا يستطيع الهجوم هذا الدور'
        elif k == 'refresh': parts.append(f"{who_ar(g)} تتحرك وتهاجم مرة ثانية هالدور")
        elif k == 'draw': parts.append(f"اسحب {o['n']} " + ('بطاقة' if o['n'] == 1 else 'بطاقات'))
        elif k == 'mojo': parts.append(f"اكسب {o['n']} موجو" if 'max' not in o else f"اكسب من {o['n']} إلى {o['max']} موجو عشوائيًا")
        elif k == 'heroLose': parts.append(f"قائدك يخسر {o['n']} صحة")
        elif k == 'heroHeal': parts.append(f"قائدك يكسب {o['n']} صحة")
        elif k == 'unequip': parts.append(('كل وحوش الخصم تفقد أسلحتها' if o['which'] == 'weapon' else 'كل الوحوش تفقد دروعها وتروسها'))
        elif k == 'eruption': parts.append(f"تنفجر الحمم من {o['n']} خانة عشوائية، وكل من يقف عليها ياخذ {o['dmg']} ضرر")
        elif k == 'tornado': parts.append(f"انقل قائد الخصم لمكان عشوائي يبعد {o['max']} خانات")
        elif k == 'mojoPerRune': parts.append(f"اكسب {o['n']} موجو عن كل " + ('رون لك في الساحة' if o['who'] == 'mine' else 'رون في الساحة (لك وللخصم)'))
        elif k == 'burnHand': parts.append(f"ارمِ يدك كلها واسحب {o['n']} بطاقات جديدة")
        elif k == 'runeDamage': parts.append(f"كل وحش للخصم ياخذ {o['n']} ضرر عن كل " + ('رون يملكه الخصم' if o['per'] == 'enemy' else 'رون في الساحة'))
        elif k == 'destroyRunes': parts.append('دمّر ' + ('كل رونات الخصم' if o['who'] == 'enemy' else 'كل الرونات'))
    groups = []
    for a in e.get('auras', []):
        if groups and groups[-1][0] == a['g']: groups[-1][1].append(a)
        else: groups.append((a['g'], [a]))
    for g, items in groups:
        parts.append(f"{who_more(g)}: " + ' و'.join(f"{sign(a['n'])} {AR_STAT[a['stat']]}" for a in items))
    if 'mojo' in e:
        m = e['mojo']
        if m.get('mine'): parts.append(f"قائدك يولد {m['mine']} موجو إضافي كل دور")
        if m.get('enemy'): parts.append(f"الخصم يولد {m['enemy']} موجو إضافي كل دور")
    if e.get('draw'): parts.append('اسحب بطاقة إضافية في بداية كل دور' if e['draw'] == 1 else f"اسحب {e['draw']} بطاقات إضافية في بداية كل دور")
    parts += rune_more(e)
    if e.get('haste'): parts.append('وحوشك تتحرك في دور استدعائها')
    if e.get('abilityDiscount'): parts.append(f"قدرات وحوشك تكلف {e['abilityDiscount']} موجو أقل")
    if e.get('tax'): parts.append(f"بطاقات الخصم تكلفه {e['tax']} موجو زيادة")
    if e.get('heroBash'): parts.append(f"وحوشك +{e['heroBash']} هجوم ضد القادة")
    if e.get('reaper'): parts.append(f"اكسب {e['reaper']} موجو كل ما يموت وحش")
    s = '، '.join(parts)
    return s + (' ما دام الرون قائمًا' if 'auras' in e else '')


# ---------------------------------------------------------------------------------------------------------------
# 7.28: the rest of the original runes and spells. Each family below maps the original tooltip onto engine effects.
HERO_KEYS = {h['name'].split(' • ')[0]: k for k, h in json.load(open('src/data/native-quests.json'))['heroes'].items()}
AFF_TAG = {'STUN': 'stun', 'MIGHTY': 'mighty', 'BERSERK': 'berserk', 'SNARED': 'snare', 'SNARE': 'snare', 'REGEN': 'regen', 'DEATHMARK': 'deathmark',
           'DM': 'deathmark', 'ICEBLOCK': 'ice', 'ICE': 'ice', 'FLAME': 'flame', 'FIRE': 'flame', 'VENGEANCE': 'vengeance', 'MAGICSHIELD': 'shield', 'SHIELD': 'shield'}
GOOD = ('mighty', 'regen', 'shield', 'berserk', 'vengeance')
KIND = {'monster': 'unit', 'monsters': 'unit', 'spell': 'spell', 'spells': 'spell', 'rune': 'rune', 'runes': 'rune', 'equip': 'equip', 'equipment': 'equip', 'some equipment': 'equip'}
RACE_TAG = {'HUMAN': 'human', 'ELF': 'elf', 'ORC': 'orc', 'ZOMBIE': 'zombie', 'UNDEAD': 'zombie', 'LIZARD': 'lizard', 'DWARF': 'dwarf', 'MINOTAUR': 'minotaur',
            'WEREWOLF': 'werewolf', 'GOLEM': 'golem', 'ELEMENTAL': 'elemental', 'CYCLOPS': 'cyclops', 'SKELETON': 'skeleton', 'ROBOT': 'robot', 'IMP': 'imp',
            'SPECTRE': 'spectre', 'VAMPIRE': 'vampire'}
def P_(name): return param(name)[0]

def parse_more(kind, tag, t, use_on):
    t = re.sub(r'@C\[\d+\]', '', t).replace('#', ',').strip()
    t = re.sub(r'@X\[\d+\]', '', t)
    if kind == 'rune':
        if tag == 'R_BLANK': return {'blank': True}
        m = re.fullmatch(r'All your monsters come into play afflicted with ([A-Za-z ]+)\.', t)
        if m and (m.group(1) in AFFLICT or m.group(1) == 'Shield'): return {'enterAfflict': [AFFLICT.get(m.group(1), 'shield')]}
        m = re.fullmatch(r'Whenever an opponent plays (?:a |an )?(spell|rune|monster|equip), their hero suffers (?:(RU_\w+)|(-?\d+))\.', t)
        if m: return {'punish': [{'kind': KIND[m.group(1)], 'n': -(P_(m.group(2)) if m.group(2) else int(m.group(3)))}]}
        m = re.fullmatch(r'Each time you play (?:a |some )?(spell|rune|monster|equipment), draw a card and your hero suffers (RU_\w+) and opponent heroes gain \+?(\d+)\.', t)
        if m: return {'onPlay': [{'kind': KIND[m.group(1)], 'draw': 1, 'heroLose': -P_(m.group(2)), 'enemyHeroGain': int(m.group(3))}]}
        m = re.fullmatch(r'Each time you play (?:a |some )?(spell|rune|monster|equipment), your hero generates (RU_\w+) but suffers (RU_\w+)(?: damage)?\.', t)
        if m: return {'onPlay': [{'kind': KIND[m.group(1)], 'mojo': P_(m.group(2)), 'heroLose': -P_(m.group(3))}]}
        m = re.fullmatch(r'All (spells|runes|monsters|equipment) costs? an extra (RU_\w+) to play\.', t)
        if m: return {'hunt': [{'kind': KIND[m.group(1)], 'n': P_(m.group(2))}]}
        if tag == 'R_CARD_HUNT': return {'hunt': [{'kind': 'all', 'n': int(G['ru_bankersdelight_mojo'])}]}
        if tag == 'R_NOMOVE': return {'noMove': True}
        if tag == 'R_NOATTACKS': return {'noAttack': True}
        if tag == 'R_NOSPECIALABILITY': return {'noAbility': True}
        m = re.fullmatch(r'All your monsters receive (RU_\w+) but cannot move\.', t)
        if m: n, st = param(m.group(1)); return {'auras': [{'g': {'who': 'mine'}, 'stat': st, 'n': n}], 'noMove': True}
        m = re.fullmatch(r'All monsters suffer (RU_\w+) for each piece of equipment on them\.', t)
        if m: return {'gravity': P_(m.group(1))}
        if tag == 'R_CARD_MAESTRO': return {'killDraw': 1}
        if tag == 'R_GRIMREAPER': return {'killDraw': 1, 'killMojo': int(G['ru_reaper_mojo']), 'killHeal': int(G['ru_healthreaper_health'])}
        if tag == 'R_HEALTH_REAPER': return {'deathHeal': {'who': 'all', 'n': int(G['ru_healthreaper_health'])}}
        if tag == 'R_MY_HEALTH_REAPER': return {'deathHeal': {'who': 'mine', 'n': int(G['ru_myhealthreaper_health'])}}
        if tag == 'R_LONE_HERO': return {'upkeep': [{'op': 'loneHero', 'when': 'mine', 'who': 'mine', 'n': int(G['ru_lonehero_health'])}]}
        if tag == 'R_WAR_HERO': return {'warHero': int(G['ru_warhero_power'])}
        if tag == 'R_HERO_SPIKE': return {'upkeep': [{'op': 'heroSpike', 'when': 'mine', 'who': 'enemy', 'n': int(G['ru_herospike_damage'])}]}
        if tag == 'R_HEALTHCARDS': return {'upkeep': [{'op': 'healthCards', 'when': 'mine', 'who': 'mine', 'n': int(G['ru_health1_health']), 'max': 8}]}
        if tag == 'R_TOOMANYCARDS': return {'upkeep': [{'op': 'tooMany', 'when': 'mine', 'who': 'enemy', 'n': 1}]}
        if tag == 'R_TOOFEWCARDS': return {'upkeep': [{'op': 'tooFew', 'when': 'mine', 'who': 'enemy', 'n': 1, 'max': 5}]}
        if tag == 'R_NEGLECT': return {'neglect': 'all'}
        if tag == 'R_SLYNEGLECT': return {'neglect': 'enemy'}
        if tag == 'R_ACCOUNTING2': return {'abilityDiscount': -int(G['ru_accounting2_mojo'])}
        if tag in ('R_ABUNDANCE', 'R_OVERABUNDANCE'): return {'drawAll': 1 if tag == 'R_ABUNDANCE' else 2}
        if tag in ('R_EXTRA2CARDS', 'R_EXTRA3CARDS'): return {'draw': int(tag[7])}
        if tag in ('R_TILEDOUBLER', 'R_SLYTILEDOUBLER'): return {'tileDouble': 'all' if tag == 'R_TILEDOUBLER' else 'mine'}
        if tag == 'R_OPENSEASON': return {'openSeason': True}
        if tag == 'R_GETORFMYLAND': return {'guardDais': True}
        if tag in ('R_NOSMASH', 'R_MY_NOSMASH'): return {'noSmash': 'all' if tag == 'R_NOSMASH' else 'mine'}
        if tag.startswith('R_DEBOUNCE_'): return {'debounce': {'ALL': 'all', 'THIERS': 'enemy', 'MINE': 'mine'}[tag[11:]]}
        if tag == 'R_DISCARD_PENALTY': return {'discardPenalty': -int(G['ru_discardpenalty_health'])}
        m = re.fullmatch(r'Your creatures do not become afflicted with ([A-Za-z ]+)\.', t)
        if m and m.group(1) in AFFLICT: return {'noAff': {'who': 'mine', 'names': [AFFLICT[m.group(1)]]}}
        m = re.fullmatch(r'All monsters do not become afflicted with ([A-Za-z ]+)\.', t)
        if m and m.group(1) in AFFLICT: return {'noAff': {'who': 'all', 'names': [AFFLICT[m.group(1)]], 'monstersOnly': True}}
        m = re.fullmatch(r'Your (.+?) hero is protected from all (bad )?afflictions\.', t)
        if m and m.group(1) in HERO_KEYS: return {'noAff': {'who': 'mine', 'names': ['bad' if m.group(2) else 'all'], 'hero': HERO_KEYS[m.group(1)]}}
        # race words: Word (all of a race +2, other races -1), Rune (yours +2, all others -1/-1), My (yours +1/+1/+1)
        m = re.fullmatch(r'R_(WBUFF|RBUFF|MYBUFF)_(\w+)', tag)
        if m and m.group(2) in RACE_TAG:
            r = RACE_TAG[m.group(2)]
            if m.group(1) == 'WBUFF': return {'auras': [{'g': {'who': 'all', 'race': r}, 'stat': 'attack', 'n': 2}, {'g': {'who': 'all', 'notRace': r}, 'stat': 'attack', 'n': -1}]}
            if m.group(1) == 'RBUFF': return {'auras': [{'g': {'who': 'mine', 'race': r}, 'stat': 'attack', 'n': 2}, {'g': {'who': 'all', 'notRace': r}, 'stat': 'attack', 'n': -1}, {'g': {'who': 'all', 'notRace': r}, 'stat': 'health', 'n': -1},
                                                {'g': {'who': 'enemy', 'race': r}, 'stat': 'attack', 'n': -1}, {'g': {'who': 'enemy', 'race': r}, 'stat': 'health', 'n': -1}]}
            return {'auras': [{'g': {'who': 'mine', 'race': r}, 'stat': s, 'n': 1} for s in ('attack', 'armor', 'health')]}
        # upkeep hexes, curses and healing
        m = re.fullmatch(r'(All monsters|Enemy monsters|Heroes|Enemy heroes|Monsters) (suffer|gain) (SP_\w+)(?: damage)? on their controller\'s upkeep(?:, and your hero suffers (SP_\w+)(?: damage)? on yours)?\.', t)
        if m:
            who = 'enemy' if m.group(1).startswith('Enemy') else 'all'; heroes = 'eroes' in m.group(1)
            n, st = param(m.group(3)); op = 'heal' if m.group(2) == 'gain' else ('damage' if st == 'damage' else 'lose')
            fx = [{'op': op, 'when': 'any', 'who': who, 'heroes': heroes, 'n': abs(n)}]
            if m.group(4): n2, st2 = param(m.group(4)); fx.append({'op': 'damage' if st2 == 'damage' else 'lose', 'when': 'mine', 'who': 'mine', 'heroes': True, 'n': abs(n2)})
            return {'upkeep': fx}
        m = re.fullmatch(r'Your (monsters|hero) gains? (SP_\w+) on your upkeep\.', t)
        if m: return {'upkeep': [{'op': 'heal', 'when': 'mine', 'who': 'mine', 'heroes': m.group(1) == 'hero', 'n': P_(m.group(2))}]}
        # bombs: effect for whoever destroys them
        if tag.startswith('R_BOMB_'):
            b = None
            m = re.fullmatch(r"Whoever destroys this bomb, all their enemys' monsters suffer (SP_\w+)( damage)?\.", t)
            if m: n, st = param(m.group(1)); b = {'ops': [{'op': 'damage', 'g': {'who': 'enemy'}, 'n': n}] if st == 'damage' else [{'op': 'lose', 'g': {'who': 'enemy'}, 'n': -n}]}
            m = re.fullmatch(r'Whoever destroys this bomb, all their creatures gain (SP_\w+)\.', t)
            if m: n, st = param(m.group(1)); b = {'ops': [{'op': 'heal', 'g': {'who': 'mine', 'both': True}, 'n': n}] if st == 'health' else [{'op': 'stat', 'g': {'who': 'mine', 'both': True}, 'stat': st, 'n': n}]}
            m = re.fullmatch(r'Whoever destroys this bomb gains (SP_\w+)', t)
            if m: b = {'ops': [{'op': 'mojo', 'n': P_(m.group(1))}]}
            m = re.fullmatch(r'Whoever destroys this bomb draws (three|five|seven) cards\.', t)
            if m: b = {'ops': [{'op': 'draw', 'n': {'three': 3, 'five': 5, 'seven': 7}[m.group(1)]}]}
            if tag == 'R_BOMB_SWINDLE': b = {'ops': [{'op': 'unequip', 'g': {'who': 'enemy', 'both': True}, 'which': 'all'}]}
            if tag == 'R_BOMB_GOODNEWS': b = {'ops': [{'op': 'afflict', 'g': {'who': 'mine', 'both': True}, 'name': a} for a in ('mighty', 'regen', 'shield')]}
            if tag == 'R_BOMB_BADNEWS': b = {'ops': [{'op': 'afflict', 'g': {'who': 'enemy', 'both': True}, 'name': a} for a in ('stun', 'snare', 'deathmark')]}
            if tag == 'R_BOMB_REVENGE': b = {'ops': [{'op': 'damage', 'g': {'who': 'mine', 'both': True}, 'n': 5}]}
            return {'bomb': b} if b else None
        return None
    # ---- spells
    if tag == 'SP_FIZZLE': return {'ops': [], 'blank': True}
    if tag == 'SP_WISHRAND_WEAPON_ART': return None  # artillery weapons left the game in 7.26
    m = re.fullmatch(r'SP_NEXT(MONSTER|RUNE|SPELL|WEAPON|ARMOUR|SHIELD)', tag)
    if m: return {'ops': [{'op': 'drawKind', 'which': {'MONSTER': 'unit', 'RUNE': 'rune', 'SPELL': 'spell', 'WEAPON': 'weapon', 'ARMOUR': 'armor', 'SHIELD': 'shield'}[m.group(1)]}]}
    m = re.fullmatch(r'SP_WISH(?:RAND)?_(MONSTER|RUNE|SPELL|ARMOUR|SHIELD|WEAPON(?:_(ANY|WARRIOR|ARCHER|MAGE))?)', tag)
    if m:
        w = m.group(1).split('_')[0]; cls = {'WARRIOR': 'warrior', 'ARCHER': 'archer', 'MAGE': 'mage'}.get(m.group(2) or '')
        return {'ops': [{'op': 'wish', 'which': {'MONSTER': 'unit', 'RUNE': 'rune', 'SPELL': 'spell', 'ARMOUR': 'armor', 'SHIELD': 'shield', 'WEAPON': 'weapon'}[w], **({'name': cls} if cls else {})}]}
    m = re.fullmatch(r'SP_(ALLDISC|SLYDISC)_(ALL|SPELLS|RUNES|MONSTERS|EQUIPMENT)', tag)
    if m: return {'ops': [{'op': 'discard', 'who': 'all' if m.group(1) == 'ALLDISC' else 'enemy', 'which': {'ALL': 'all', 'SPELLS': 'spell', 'RUNES': 'rune', 'MONSTERS': 'unit', 'EQUIPMENT': 'equip'}[m.group(2)], **({'selfPer': 1} if m.group(1) == 'SLYDISC' else {})}]}
    m = re.fullmatch(r'SP_(SLY)?DISCARD(\d)', tag)
    if m: return {'ops': [{'op': 'discard', 'who': 'enemy' if m.group(1) else 'all', 'which': 'random', 'n': int(m.group(2)), **({'selfPer': 1} if m.group(1) else {})}]}
    if tag in ('SP_MOJO_DOUBLER', 'SP_MOJO_TRIPLER'): return {'ops': [{'op': 'mojoMult', 'n': 2 if tag == 'SP_MOJO_DOUBLER' else 3}]}
    if tag == 'SP_SWINDLE': return {'ops': [{'op': 'unequip', 'g': {'who': 'enemy', 'heroes': True}, 'which': 'all'}]}
    if tag == 'SP_SEPARATE': return {'ops': [{'op': 'unequip', 'g': {'who': 'enemy', 'both': True}, 'which': 'defence'}]}
    if tag == 'SP_CORROSION': return {'ops': [{'op': 'unequip', 'g': {'who': 'all', 'both': True}, 'which': 'weapon'}]}
    m = re.fullmatch(r'SP_(M|SM)_AFF_(\w+)', tag)
    if m and m.group(2) in AFF_TAG: return {'ops': [{'op': 'afflict', 'g': {'who': 'all' if m.group(1) == 'M' else 'enemy'}, 'name': AFF_TAG[m.group(2)]}]}
    m = re.fullmatch(r'SP_(KILL|SLYKILL)_AFF_(\w+)', tag)
    if m and (m.group(2) in AFF_TAG or m.group(2) == 'ALL'): return {'ops': [{'op': 'destroy', 'g': {'who': 'all' if m.group(1) == 'KILL' else 'enemy', 'aff': AFF_TAG.get(m.group(2), 'any')}}]}
    m = re.fullmatch(r'SP_(BOUNCEALL|BOUNCESLY)_(\w+)', tag)
    if m and m.group(2) in AFF_TAG:
        hb = re.search(r'gains (SP_\w+) for each bounce', t)
        return {'ops': [{'op': 'bounce', 'g': {'who': 'all' if m.group(1) == 'BOUNCEALL' else 'enemy', 'aff': AFF_TAG[m.group(2)]}, **({'heroPerBounce': P_(hb.group(1))} if hb else {})}]}
    m = re.fullmatch(r'SP_BOUNCE_YOU_(\w+)', tag)
    if m and m.group(1) in RACE_TAG: return {'ops': [{'op': 'bounce', 'g': {'who': 'mine', 'race': RACE_TAG[m.group(1)]}}]}
    m = re.fullmatch(r'SPT_(HAFF|CAFF)_(\w+)', tag)
    if m and m.group(2) in AFF_TAG:
        a = AFF_TAG[m.group(2)]; good = a in GOOD
        tgt = ('mineHero' if good else 'enemyHero') if m.group(1) == 'HAFF' else ('mineAny' if good else 'enemyAny')
        return {'target': tgt, 'ops': [{'op': 'afflict', 'g': {'who': 'target'}, 'name': a}]}
    if tag == 'SPT_TERMINATE': return {'target': 'enemy', 'ops': [{'op': 'destroy', 'g': {'who': 'target'}}]}
    if tag == 'SPT_BOUNCE': return {'target': 'enemy', 'ops': [{'op': 'bounce', 'g': {'who': 'target'}}]}
    if tag == 'SPT_DISMANTLE': return {'target': 'enemy', 'ops': [{'op': 'unequip', 'g': {'who': 'target'}, 'which': 'defence'}]}
    if tag == 'SPT_CORROSION': return {'target': 'enemy', 'ops': [{'op': 'unequip', 'g': {'who': 'target'}, 'which': 'weapon'}]}
    if tag == 'SPT_DENUDE': return {'target': 'enemy', 'ops': [{'op': 'unequip', 'g': {'who': 'target'}, 'which': 'all'}]}
    if tag == 'SPT_SMASH': return {'target': 'rune', 'ops': [{'op': 'smashRune'}]}
    if tag == 'SPT_2NDWIND': return {'target': 'mine', 'ops': [{'op': 'refresh', 'g': {'who': 'target'}}]}
    if tag == 'SPT_SLYCURE': return {'target': 'mineAny', 'ops': [{'op': 'cleanse', 'g': {'who': 'target'}, 'which': 'bad'}]}
    if tag == 'SPT_UNCURE': return {'target': 'enemyAny', 'ops': [{'op': 'cleanse', 'g': {'who': 'target'}, 'which': 'good'}]}
    if tag == 'SPT_SHATTER': return {'target': 'any', 'ops': [{'op': 'cleanse', 'g': {'who': 'target'}, 'which': 'all'}]}
    if tag == 'SPT_ABSORB': return {'target': 'mine', 'ops': [{'op': 'absorb', 'g': {'who': 'target'}}]}
    m = re.fullmatch(r'Target monster drains (SP_\w+) from your hero to gain (SP_\w+)\.', t)
    if m: return {'target': 'mine', 'ops': [{'op': 'spike', 'g': {'who': 'target'}, 'n': -P_(m.group(1)), 'gain': P_(m.group(2))}]}
    m = re.fullmatch(r'Each of your monsters drains (SP_\w+) from your hero to gain (SP_\w+)\.', t)
    if m: return {'ops': [{'op': 'spike', 'g': {'who': 'mine'}, 'n': -P_(m.group(1)), 'gain': P_(m.group(2))}]}
    m = re.fullmatch(r'Your hero absorbs (?:up to )?(SP_\w+) from each of your monsters\.', t)
    if m: return {'ops': [{'op': 'absorb', 'g': {'who': 'mine'}, 'n': P_(m.group(1))}]}
    m = re.fullmatch(r'Your hero receives (SP_\w+) for each Mojo remaining\. \(Capped at (\d+)\)', t)
    if m: return {'ops': [{'op': 'heroPerMojo', 'n': P_(m.group(1)), 'max': int(m.group(2))}]}
    m = re.fullmatch(r'Target player draws (\d) cards?\. \(Target their hero\.\)', t)
    if m: return {'target': 'anyHero', 'ops': [{'op': 'drawFor', 'n': int(m.group(1))}]}
    m = re.fullmatch(r'All (enemy )?runes set to (\d+)\.', t)
    if m: return {'ops': [{'op': 'runeSet', 'who': 'enemy' if m.group(1) else 'all', 'n': int(m.group(2))}]}
    m = re.fullmatch(r'(Your|All) runes get (SP_\w+)\.', t)
    if m: return {'ops': [{'op': 'runeSet', 'who': 'mine' if m.group(1) == 'Your' else 'all', 'which': 'add', 'n': P_(m.group(2))}]}
    if tag == 'SP_MYRUNESMASH': return {'ops': [{'op': 'destroyRunes', 'who': 'mine'}]}
    if tag in ('SP_RUNESLEFT', 'SP_RUNESRIGHT', 'SP_RUNEFULLRAND'): return {'ops': [{'op': 'runeOwners', 'which': 'random' if tag == 'SP_RUNEFULLRAND' else 'swap'}]}
    m = re.fullmatch(r'Destroy all monsters with (SP_\w+) or (more|less)\.', t)
    if m: n = P_(m.group(1)); return {'ops': [{'op': 'destroy', 'g': {'who': 'all', **({'minHealth': n} if m.group(2) == 'more' else {'maxHealth': n})}}]}
    m = re.fullmatch(r'SP_EXPUNGE_(ALL|MOJO|PWR|ARM|DRAW|REGEN)', tag)
    if m: return {'ops': [{'op': 'destroy', 'g': {'who': 'all', 'tile': {'ALL': 'any', 'MOJO': 'mojo', 'PWR': 'power', 'ARM': 'armour', 'DRAW': 'draw', 'REGEN': 'regen'}[m.group(1)]}}]}
    m = re.fullmatch(r'SP_SHATTER_HERO_(ALL|ENEMYGOOD|MYBAD)', tag)
    if m: return {'ops': [{'op': 'cleanse', 'g': {'who': {'ALL': 'all', 'ENEMYGOOD': 'enemy', 'MYBAD': 'mine'}[m.group(1)], 'heroes': True}, 'which': {'ALL': 'all', 'ENEMYGOOD': 'good', 'MYBAD': 'bad'}[m.group(1)]}]}
    if tag == 'SP_TORNADO': return {'ops': [{'op': 'moveMonster', 'min': int(G['sp_hurricane_minrange']), 'max': int(G['sp_hurricane_maxrange'])}]}
    return None

AR_KIND = {'unit': 'وحش', 'rune': 'رون', 'spell': 'تعويذة', 'equip': 'عتاد', 'weapon': 'سلاح', 'armor': 'درع', 'shield': 'ترس', 'all': 'بطاقة'}
AR_KINDS = {'unit': 'الوحوش', 'rune': 'الرونات', 'spell': 'التعاويذ', 'equip': 'العتاد', 'all': 'البطاقات'}
AR_TILE = {'any': 'أي خانة مميزة', 'mojo': 'خانة موجو', 'power': 'خانة قوة', 'armour': 'خانة درع', 'draw': 'خانة سحب بطاقة', 'regen': 'خانة علاج'}
HERO_AR = {k: h['name'] for k, h in json.load(open('src/data/native-quests.json'))['heroes'].items()}

def who_more(g):
    """Arabic for groups that use the 7.28 keys; falls back to who_ar for the old ones."""
    if g.get('who') == 'target': return 'الهدف'
    if not any(k in g for k in ('both', 'aff', 'tile', 'minHealth', 'maxHealth', 'notRace')): return who_ar(g)
    noun = 'المخلوقات (وحوش وقادة)' if g.get('both') else ('القادة' if g.get('heroes') else (AR_RACE.get(g.get('race')) or AR_CLS.get(g.get('cls')) or 'الوحوش'))
    if g.get('notRace'): noun = f"الوحوش من غير {AR_RACE[g['notRace']]}"
    base = {'mine': f'كل {noun} اللي لك', 'enemy': f'كل {noun} اللي للخصم', 'all': f'كل {noun}'}[g['who']]
    if g.get('aff'): base += ' المصابة بأي حالة' if g['aff'] == 'any' else f" اللي عليها {AR_AFF[g['aff']]}"
    if g.get('tile'): base += f" الواقفة على {AR_TILE[g['tile']]}"
    if 'minHealth' in g: base += f" اللي صحتها {g['minHealth']} أو أكثر"
    if 'maxHealth' in g: base += f" اللي صحتها {g['maxHealth']} أو أقل"
    return base

TARGET_AR = {'enemyHero': 'قائد الخصم', 'mineHero': 'قائدك', 'anyHero': 'قائد تختاره', 'enemyAny': 'مخلوق للخصم', 'mineAny': 'مخلوق لك', 'any': 'أي مخلوق', 'rune': 'رون للخصم'}

def op_more(o, e):
    g = o.get('g', {}); k = o['op']; w = who_more(g) if g else ''
    if g.get('who') == 'target' and e.get('target') in TARGET_AR: w = 'الهدف (' + TARGET_AR[e['target']] + ')'
    if k == 'drawKind': return f"اسحب أول {AR_KIND[o['which']]} في مجموعتك (إذا فيه)"
    if k == 'wish': return f"خذ {AR_KIND[o['which']]} عشوائي" + (f" لـ{AR_CLS[o['name']]}" if o.get('name') else '') + ' من كل بطاقات اللعبة لليد'
    if k == 'discard':
        who = 'كل اللاعبين' if o['who'] == 'all' else 'الخصم'
        what = f"{o['n']} " + ('بطاقة' if o['n'] == 1 else 'بطاقات') + ' عشوائية' if o['which'] == 'random' else ('يده كاملة' if o['which'] == 'all' else f"كل {AR_KINDS[o['which']]} من يده")
        return f"{who} يرمي {what}" + ('، وقائدك يخسر 1 صحة عن كل بطاقة' if o.get('selfPer') else '')
    if k == 'mojoMult': return ('ضاعف' if o['n'] == 2 else 'ثلّث') + ' الموجو اللي باقي معك، وقائدك يخسر صحة بقدر الموجو المكتسب'
    if k == 'unequip': return f"{w} تفقد " + {'all': 'كل عتادها', 'weapon': 'أسلحتها', 'defence': 'دروعها وتروسها'}[o['which']]
    if k == 'smashRune': return 'دمّر الرون المستهدف'
    if k == 'runeSet': return {'all': 'كل الرونات', 'enemy': 'كل رونات الخصم', 'mine': 'كل روناتك'}[o['who']] + (f": +{o['n']} صحة" if o.get('which') == 'add' else f" صحتها تصير {o['n']}")
    if k == 'runeOwners': return 'وزّع الرونات بين اللاعبين عشوائيًا' if o['which'] == 'random' else 'بدّل الرونات بينك وبين الخصم'
    if k == 'absorb': return (f"قائدك يمتص {o['n']} صحة من كل وحش لك" if 'n' in o else 'قائدك يكسب صحة بقدر صحة الهدف')
    if k == 'spike': return ('الهدف' if g.get('who') == 'target' else 'كل وحش لك') + f" يسحب {o['n']} صحة من قائدك ويكسب +{o['gain']} هجوم"
    if k == 'heroPerMojo': return f"قائدك يكسب {o['n']} صحة عن كل موجو باقي (حدها {o['max']} موجو)"
    if k == 'drawFor': return f"القائد المستهدف يسحب {o['n']} " + ('بطاقة' if o['n'] == 1 else 'بطاقات')
    if k == 'moveMonster': return f"انقل وحش عشوائي للخصم لمكان عشوائي يبعد {o['max']} خانات"
    if k == 'destroy': return f"دمّر {w}"
    if k == 'afflict': return f"{w}: " + ('يكسب ' if o['name'] in GOOD else 'يصيبه ') + AR_AFF[o['name']]
    if k == 'refresh': return f"{w} يتحرك ويهاجم مرة ثانية هالدور"
    if k == 'cleanse': return f"{w} يتخلص من " + {'bad': 'كل الحالات السيئة', 'good': 'كل الحالات الجيدة', 'all': 'كل الحالات'}[o['which']]
    if k == 'bounce': return f"{w} يرجع ليد صاحبه مع عتاده" + (f"، وقائد صاحبه يكسب {o['heroPerBounce']} صحة عن كل وحش" if o.get('heroPerBounce') else '')
    if k == 'damage': return f"{w}: {o['n']} ضرر"
    if k == 'lose': return f"{w} تخسر {o['n']} صحة"
    if k == 'heal': return f"{w}: علاج {o['n']}"
    if k == 'stat': return f"{w}: {sign(o['n'])} {AR_STAT[o['stat']]}"
    if k == 'mojo': return f"اكسب {o['n']} موجو"
    if k == 'draw': return f"اسحب {o['n']} " + ('بطاقة' if o['n'] == 1 else 'بطاقات')
    if k == 'destroyRunes' and o['who'] == 'mine': return 'دمّر كل روناتك'
    return ''

def rune_more(e):
    parts = []
    if e.get('blank'): parts.append('ما يسوي شي')
    for a in e.get('enterAfflict', []): parts.append(f"وحوشك تدخل الساحة وعليها {AR_AFF[a]}")
    for p in e.get('punish', []): parts.append(f"كل ما الخصم يلعب {AR_KIND[p['kind']]} قائده يخسر {p['n']} صحة")
    for o in e.get('onPlay', []):
        bits = []
        if o.get('draw'): bits.append('تسحب بطاقة')
        if o.get('mojo'): bits.append(f"تكسب {o['mojo']} موجو")
        if o.get('heroLose'): bits.append(f"قائدك يخسر {o['heroLose']} صحة")
        if o.get('enemyHeroGain'): bits.append(f"قائد الخصم يكسب {o['enemyHeroGain']} صحة")
        parts.append(f"كل ما تلعب {AR_KIND[o['kind']]}: " + ' و'.join(bits))
    for h in e.get('hunt', []): parts.append(f"كل {AR_KINDS[h['kind']]} تكلف الجميع {h['n']} موجو زيادة")
    if e.get('noMove'): parts.append('وحوشك ما تقدر تتحرك')
    if e.get('noAttack'): parts.append('وحوشك ما تقدر تهاجم هجومها العادي')
    if e.get('noAbility'): parts.append('وحوشك ما تقدر تستخدم قدراتها')
    if e.get('gravity'): parts.append(f"كل وحش يخسر {-e['gravity']} صحة عن كل قطعة عتاد عليه")
    if e.get('killDraw') or e.get('killMojo') or e.get('killHeal'):
        bits = (['تسحب بطاقة'] if e.get('killDraw') else []) + ([f"تكسب {e['killMojo']} موجو"] if e.get('killMojo') else []) + ([f"قائدك يكسب {e['killHeal']} صحة"] if e.get('killHeal') else [])
        parts.append('كل ما تقتل وحش: ' + ' و'.join(bits))
    if e.get('deathHeal'): parts.append(f"قائدك يكسب {e['deathHeal']['n']} صحة كل ما يموت " + ('أي وحش' if e['deathHeal']['who'] == 'all' else 'وحش من وحوشك'))
    for f in e.get('upkeep', []):
        if f['op'] == 'loneHero': parts.append(f"في بداية دورك: قائدك يكسب {f['n']} صحة إذا ما حوله أحد")
        elif f['op'] == 'heroSpike': parts.append(f"في بداية دورك: كل مخلوق للخصم جنب قائدك ياخذ {f['n']} ضرر")
        elif f['op'] == 'healthCards': parts.append(f"في بداية دورك: قائدك يكسب {f['n']} صحة عن كل بطاقة فوق 5 في يدك (حدها {f['max']})")
        elif f['op'] == 'tooMany': parts.append('في بداية دورك: قائد الخصم يخسر (4 ناقص عدد بطاقات يده) صحة')
        elif f['op'] == 'tooFew': parts.append(f"في بداية دورك: قائد الخصم يخسر (عدد بطاقات يده ناقص 10) صحة، حدها {f['max']}")
        else:
            noun = ('القادة' if f.get('heroes') else 'الوحوش'); who = {'all': f'كل {noun}', 'enemy': f'{noun} اللي للخصم', 'mine': ('قائدك' if f.get('heroes') else 'وحوشك')}[f['who']]
            verb = {'heal': f"تكسب {f['n']} صحة", 'damage': f"تاخذ {f['n']} ضرر", 'lose': f"تخسر {f['n']} صحة"}[f['op']]
            parts.append((f"{who} {verb} في بداية دور صاحبها" if f['when'] == 'any' else f"{who} {verb} في بداية دورك"))
    if e.get('drawAll'): parts.append(f"كل اللاعبين يسحبون {e['drawAll']} " + ('بطاقة إضافية' if e['drawAll'] == 1 else 'بطاقات إضافية') + ' كل دور')
    if e.get('neglect'): parts.append(('دروع الكل' if e['neglect'] == 'all' else 'دروع الخصم') + ' ما تتجدد في بداية الدور')
    if e.get('warHero'): parts.append(f"قائدك +{e['warHero']} هجوم عن كل عدو جنبه")
    if e.get('noAff'):
        a = e['noAff']; what = 'كل الحالات' if 'all' in a['names'] else 'الحالات السيئة' if 'bad' in a['names'] else ' و'.join(AR_AFF[n] for n in a['names'])
        if a.get('hero'): parts.append(f"قائدك إذا كان {HERO_AR[a['hero']]} محمي من {what}")
        else: parts.append(('مخلوقاتك' if a['who'] == 'mine' else 'كل الوحوش') + f" محمية من {what}")
    if e.get('tileDouble'): parts.append('الخانات المميزة تعطي ضعف الفايدة' + (' لك بس' if e['tileDouble'] == 'mine' else ' للكل'))
    if e.get('openSeason'): parts.append('تقدر تحط رونات على قواعد الخصم (تشتغل كأنها له)')
    if e.get('guardDais'): parts.append('ما أحد يقدر يحط رون على قواعدك')
    if e.get('noSmash'): parts.append(('روناتك' if e['noSmash'] == 'mine' else 'كل الرونات') + ' ما تتأثر بتعاويذ تدمير الرونات')
    if e.get('debounce'): parts.append({'all': 'كل الوحوش', 'enemy': 'وحوش الخصم', 'mine': 'وحوشك'}[e['debounce']] + ' ما ترجع لليد بالتعاويذ')
    if e.get('discardPenalty'): parts.append(f"كل ما أحد يخليك ترمي بطاقة، قائده يخسر {e['discardPenalty']} صحة")
    if e.get('bomb'): parts.append('قنبلة — اللي يدمّرها ينفّذ: ' + '، '.join(op_more(o, e['bomb']).replace('اللي لك', 'اللي له').replace('اللي للخصم', 'اللي لأعدائه') for o in e['bomb']['ops']))
    return parts

NEW_OPS = {'drawKind', 'wish', 'discard', 'mojoMult', 'smashRune', 'runeSet', 'runeOwners', 'absorb', 'spike', 'heroPerMojo', 'drawFor', 'moveMonster'}

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
        if not e:
            e = parse_more(kind, r['Tag Name'], tip, r.get('Use On'))
        if r['Tag Name'] in already: continue
        if not e or not text(e):
            skipped.append(f"{kind}\t{r['Tag Name']}\t{tip}"); continue
        out.append({'id': ('NR_' if kind == 'rune' else 'NS_') + r['Tag Name'], 'name': r['Name'], 'race': 'neutral', 'type': kind,
                    'cost': int(r['Mojo']), 'text': text(e), 'keywords': [], 'rarity': r['Rarity'], 'nativeTag': r['Tag Name'],
                    'art': r['Texture Name'], 'effect': e})
Path('src/data/catalog-magic.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
(REF / 'magic-not-imported.txt').write_text('\n'.join(skipped) + '\n')
print(json.dumps({'runes': sum(c['type'] == 'rune' for c in out), 'spells': sum(c['type'] == 'spell' for c in out), 'notYet': len(skipped)}))
