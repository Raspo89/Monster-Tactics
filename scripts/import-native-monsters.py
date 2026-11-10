"""Import every original monster from the recovered native table (reference/native-rules/table-3189a0.json).

Cards already in native-cards.json / ability-cards.json keep their ids; the rest become NM_<race>_<row>.
Stats, rarity, class, Mojo cost and ability are copied exactly. Art: each monster uses the portrait
rendered from its own model + texture (all textures were decoded from the APK in 7.4).
Run from the project root: python3 scripts/import-native-monsters.py
"""
import json
from pathlib import Path

table = [r for r in json.loads(Path('reference/native-rules/table-3189a0.json').read_text())[1:] if r['Race']]
existing = json.loads(Path('src/data/native-cards.json').read_text()) + json.loads(Path('src/data/ability-cards.json').read_text())
have = {c['nativeTag'] for c in existing}
abilities = json.loads(Path('src/data/abilities.json').read_text())
manifest_path = Path('src/data/visual-manifest.json')
visual = json.loads(manifest_path.read_text())
portraits = {k: v for k, v in visual['portraits'].items() if not k.startswith('NM_')}

CLASS = {'CT_FIGHTER': ('warrior', 1, 'fighter', 'محارب'), 'CT_RANGER': ('archer', 3, 'rogue', 'رامي'),
         'CT_MAGE': ('mage', 2, 'spellcaster', 'ساحر'), 'CT_ARTIL': ('artillery', 3, 'artillery', 'مدفعية')}
RACE = {'RT_UNDEAD': 'zombie'}

# Every original monster uses the portrait rendered for its own model + texture (scripts/render-portraits/).
PORTRAITS = Path('public/assets/original/portraits')
def portrait(model, skin):
    path = f'portraits/m_{model}_{skin}.webp'
    assert (PORTRAITS / f'm_{model}_{skin}.webp').is_file(), path
    return path

out, rows_by_race, exact, fallback = [], {}, 0, 0
for r in table:
    if r['Rarity'] == 'B':  # boss "King" placeholders, never collectible
        continue
    race_key = r['Race']
    rows_by_race[race_key] = rows_by_race.get(race_key, 0) + 1
    tag = f"{race_key}:{r['Name']}"
    if tag in have:
        continue
    race = RACE.get(race_key, race_key[3:].lower())
    combat, rng, model_cls, label = CLASS[r['Class']]
    model = f"{race_key[3:].lower()}_{model_cls}"
    ability = r['Ability'] if r['Ability'] != 'AT_NONE' else None
    assert ability is None or ability in abilities, ability
    cid = f"NM_{race}_{rows_by_race[race_key]:03d}"
    card = {'id': cid, 'name': r['Name'], 'race': race, 'type': 'unit', 'cost': int(r['Mojo']),
            'attack': int(r['Power']), 'health': int(r['Health']), 'armor': 0, 'speed': 1, 'range': rng,
            'text': 'وحش أصلي بقدرة نشطة' if ability else f'وحش أصلي • {label}', 'keywords': [],
            'rarity': r['Rarity'], 'combatClass': combat, 'nativeTag': tag}
    if ability:
        card['abilityId'] = ability
    out.append(card)
    portraits[cid] = {'model': model, 'skin': int(r['Texture Name']), 'path': portrait(model, int(r['Texture Name']))}
    exact += 1

# Monsters imported before 7.3 (native-cards.json / ability-cards.json) switch to the same rendered portraits.
by_tag = {f"{r['Race']}:{r['Name']}": r for r in table}
for c in existing:
    r = by_tag[c['nativeTag']]
    model = f"{r['Race'][3:].lower()}_{CLASS[r['Class']][2]}"
    portraits[c['id']] = {'model': model, 'skin': int(r['Texture Name']), 'path': portrait(model, int(r['Texture Name']))}

Path('src/data/catalog-cards.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
visual['portraits'] = portraits
manifest_path.write_text(json.dumps(visual, ensure_ascii=False, indent=1) + '\n')
print(json.dumps({'added': len(out), 'exactArt': exact, 'fallbackArt': fallback, 'withAbility': sum(1 for c in out if 'abilityId' in c)}))
