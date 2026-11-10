# 7.3 — the full original monster catalogue

- `scripts/import-native-monsters.py` reads the recovered native monster table (reference/native-rules/table-3189a0.json) and writes `src/data/catalog-cards.json`.
- All 1,536 collectible original monsters are now in the game (16 races × 100 rows, minus the 64 boss "King" rows). 220 were already present and keep their ids; 1,316 are new (`NM_<race>_<row>`), 848 of them with an active ability. Cost, power, health, rarity, class and ability are copied exactly; every ability in the table was already implemented by the engine.
- Art: 237 of the new monsters use their own model and texture. 1,079 use the same model with the closest texture that is in this package (marked `fallback` in visual-manifest.json): the lite package only kept 229 of the 768 model/texture pairs the table needs. Supplying the missing textures from the APK would fix their colours without code changes.
- Starter decks, AI decks and format decks are still built from the pre-import cards, so matches and the difficulty tests are unchanged.
- The collection and the shop show 60 cards at a time with a "show more" button so phones stay responsive.
- tests/catalogue.test.ts checks every table row is present exactly once with its printed stats, every monster has a portrait and texture that exist, and starter/AI decks contain no new cards. 191 tests pass.

Not yet imported: the 266 original runes, 542 spells and the weapon/armour/shield tables. Each has its own effect that the engine must implement first.
