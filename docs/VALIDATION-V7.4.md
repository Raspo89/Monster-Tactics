# 7.4 — art from the APK, original runes and spells

## Art restored from the APK (Combat_Monsters_5_6_0_00 XAPK)
- `scripts/apk-tools/etc1.py` decodes the game's `!ETC` textures. Checked against the 596 textures already in the project: all pixel-identical.
- 220 monster skins that the lite package had dropped were decoded from the OBB, so all 816 skins of the 64 monster models are now present (stored as WebP, 44 MB smaller than PNG).
- 22 cape, wing and eye textures were missing; the 3D board used to paint the body texture on those parts. They are restored and the board now uses each part's own texture.
- One portrait was rendered for each of the 768 model/skin pairs (three.js, same camera angle and framing as the original portraits; silhouette overlap 0.98). All 1,536 monsters now show their own colours; the 1,079 placeholder looks from 7.3 are gone.
- Rune and spell card art (98 images) decoded from the OBB.

## Original runes and spells
- `scripts/import-native-magic.py` turns tooltips from the native rune and spell tables into structured effects, with numbers from the native globals table. 74 runes and 361 spells imported (`src/data/catalog-magic.json`), each with an Arabic description.
- Spell effects: area damage, destroy, heal, permanent attack/armour change, health loss (with hero gain per death), cleanse good/bad afflictions, bounce to hand, afflictions, extra turn, draw, Mojo gain, hero heal/loss, destroy runes; targeted damage, buffs and afflictions.
- Rune effects: stat auras for your / enemy / all monsters filtered by race or class, hero auras, extra Mojo for you and/or opponents, extra draw, haste. The seven existing runes now run through the same code with identical results.
- 366 runes/spells are not imported yet (bombs, lava, rune trading, discard, equipment theft and other one-off effects). They are listed in reference/native-rules/magic-not-imported.txt.
- Starter, AI and format decks are unchanged (built only from pre-import cards).

## Tests
205 tests pass, including tests/magic.test.ts: targeted behaviour of each effect family, every imported card played in every legal way, and full AI games with decks full of imported magic. Difficulty ordering unchanged (hard > normal > easy).
