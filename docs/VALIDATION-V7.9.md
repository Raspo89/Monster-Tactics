# Validation — 7.9 equipment and rarity frames

## Equipment from the original game
- `scripts/import-native-equipment.py` reads the APK tables for weapons, shields and armour and writes `src/data/catalog-equipment.json`: 200 cards (`NE_<tag>`) after dropping cost-0 default items. Families: shield 41, bow 36, staff 33, armour 26, artillery ammo 24, axe 11, mace 11, dagger 9, sword 9.
- Class rules follow the original help text: warriors use swords, axes, maces and daggers; archers bows; mages staffs; artillery its ammo. Armour and shields go on any monster, and a monster can carry a weapon, an armour piece and a shield together. In the original there is no separate helmet card: armour is a helmet + chest set, shown with its helmet.
- Supported effects: attack, defence, health (added and removed when the item is replaced), Mojo per turn (original rules), on-hit afflictions with their chance (stun, death mark, ice, flame, snare) and protection from afflictions. Ability boosts and splash perks are listed in `reference/native-rules/equipment-notes.txt` and not applied yet.
- Art: `scripts/apk-tools/mda.py` parses the MDA meshes (all 171 used ones), `export-equipment.py` + `render-equipment.py` render them with three.js, `polish-equipment.py` adds a light rim so thin bows and staffs stay readable on small cards → `public/assets/original/equipment/*.webp` (205 images).

## Starter deck
- 20 monsters + 2 Mojo runes + 2 heals + 1 bolt + 1 shield + 4 weapons (2 cheapest common warrior weapons, 1 bow, 1 staff; items without drawbacks preferred). Old saves without weapons are moved to the new starter deck and receive the missing copies; coins and other cards are kept.

## Rarity frames
- Every card frame now follows rarity: common green, uncommon red, rare blue, legendary gold (heroes keep gold).

## Checks
- `tests/equipment.test.ts` (6 tests): catalogue families, class targeting, stacking and health removal, protection, starter weapons for each class, old-save migration.
- Full suite and difficulty tests pass; browser check on desktop (1280×800) and phone (390×844): deck builder, shop filters by type, battle start with a dagger in hand, no page errors.
