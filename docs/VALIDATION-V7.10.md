# Validation — 7.10 Solo Quests

## Source data (APK / OBB)
- `Quests/{tut,easy,medium,hard,hard2,hard3}.txt`: rooms with number, position relative to an earlier room (N/E/S/W), enemy hero, enemy deck and board layout; `[LASTBATTLE]` ends a quest and `// Sub-Boss` marks mini bosses. The co-op and 1v2/2v4 quests are not included (they need more than two players).
- `Decks/*.bdk` (u32 version, u32 count, records of four u16): type 2 monster = race (1-based order of the monster table), class, index inside that race+class group; type 0 equipment = 1 weapon / 2 shield / 3 armour and its 1-based row; type 1 rune and type 3 spell = 1-based row of their tables. Checked on the themed decks (`50___Elves`, `Hrd_robots`, `Archer_Pack`, `Mage_Pack` ... contain exactly the expected race/class).
- `Layouts/quests/<quest>/<n>.txt`: cells named A0–I8. The board is the radius-4 hexagon around E4 — all 2270 cells named in the 109 layout files lie inside it — and `TEMPLATE,<name>` removes cells. The template tables live in `libapp.so` (`CLayoutMgr::FillValidCellsTemplate`); `scripts/apk-tools/extract-map-templates.py` follows that code with capstone → `reference/native-rules/map-templates.json`. No named cell falls inside a removed area, and every board is one connected piece with both starts on it.
- Heroes: `table-33ddc8` (stats, ability) joined row by row with `table-33fe88` (class, model). Dean, Tut, Grumsnik and Raeynor keep the existing playable leaders; the other 14 become `hero_*` opponents that use the monster ability of the same AT_ id. Models converted from `Archetypes/Bosses/*` by `scripts/apk-tools/convert-heroes.py`, portraits rendered like the leaders.
- Art: parchment maps, round frames, padlock and tick from `GUI/quests`, `GUI/ButtonBits2`, `GUI/ButtonBits4` (`scripts/apk-tools/quest-ui.py`).

## Import result (`scripts/import-native-quests.py`)
- 119 rooms, 109 boards, enemy decks of 24–63 cards. 238 card copies of 16 kinds are not in the game yet and are left out of those decks (listed in `reference/native-rules/quest-cards-not-imported.txt`, e.g. Mulligan, Mojo Turbo, Banker's Delight).

## Rules chosen where the files say nothing
- Prize on the first win of a room: 60 / 100 / 150 / 200 / 260 / 320 coins by quest; mini boss ×2 coins + a rare card; last battle ×3 coins + a legendary card. Every win also gives the usual victory reward.
- The tutorial and easy quests are open; each other quest opens when the one before it is finished.
- Enemy +1 Mojo each turn in Harder (stated by the original text) and Nightmare (assumed).
- AI level: tutorial/easy = easy, medium = normal, hard and above = hard.

## Checks
- `tests/quests.test.ts` (6 tests): all rooms, decks, heroes and boards resolve; boards connected; room unlocking; prizes once; quest unlock chain and save/reload; hero stats and Mojo bonus; AI finishes the last battle of every quest.
- AI vs AI over all 119 rooms with the starter deck: no errors; starter deck wins most easy rooms, loses most from medium on (the original expects a growing collection).
- Browser: quest list, map, room dialog and battle start on 1280×800 and 390×844.
