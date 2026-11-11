# Validation — 7.11 booster chests

## From the original
- Locale `NAME_BOOSTER*` / `DETAIL_BOOSTER*`: Mini (6 random, nothing guaranteed), Full (12, guaranteed one rare — slight chance of legendary — and three uncommons), Monster / Equipment / Rune / Spell (same guarantee, one card type), Mega (12: one legendary, three rares, eight uncommons), Epic (12 legendaries, cannot be bought), Mystery (cards, coins, chests or other bonuses), Black (one limited-edition black card — left out: the game has no black cards).
- Where they came from: daily challenge = coins + a mystery chest (`HELP_COTD_1`), quests = coins and sometimes chests (`HELP_BOOSTERS_2`), monthly leaderboards and clans (online only, not in this game), buying with coins (`HELP_BOOSTERS_6`).
- Art: `Furniture/Chest/chestanimated.MDA` with each `fan_furniture_chest_*` texture, mystery texture from `Furniture/Epicbooster` (`scripts/apk-tools/chest-art.py`).

## Our choices (the original values were on the server)
- Prices: Mini 300, Full / typed 900, Mega 2800 coins (single cards cost 60 / 180 / 600 / 1800).
- "Slight chance" of legendary = 10%. Other slots use the normal drop weights (70 / 23 / 6 / 1 %).
- Mystery: 35% 150–600 coins, 40% another chest (mini, full, a typed chest, 9% mega, 1% epic), 25% three random cards.
- Quest prizes: mini boss = Full chest, last battle = Mega chest (Nightmare: Epic chest), replacing the single rare/legendary card of 7.10.

## Checks
- `tests/chests.test.ts` (5): contents and guarantees of every type, typed pools, buying rules, opening, mystery outcomes, save/reload. Quest test updated for chest prizes. Full suite passing.
- Browser: chest page, opening a Full chest and a Mystery chest on 1280×800 and 390×844.
