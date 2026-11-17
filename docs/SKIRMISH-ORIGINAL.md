# Skirmish like the original (7.25)

## What the original did

The game's own help page for Skirmish ("It's Not Fair", `HELP_QUICKBATTLE_2/3` in `Locale/eng.txt`) says the computer
gets, depending on the difficulty chosen: some extra cards at the start, some extra Mojo every turn, and a deck picked at
random from "its large and nasty library", matched with the best hero to play it.

- **The amounts are not in the app.** `CUserAccount::GetBonusesForSkirmish(eDifficulty, eOnlineGameType, int&, int&)`
  (0x292ad4) only looks the two numbers up in a map filled from account data sent by Rubicon's servers, which are gone.
- **The library is.** `CEnemyDeckMgr::Init` (0x1a451c) reads an embedded list of 227 deck names
  (`reference/native-rules/table-349a00.txt`), skips any containing "starter", loads each `Decks/<name>.bdk`, records the
  deck rules it is legal under, which hero classes may lead it, and its average Mojo cost.
- **The pick.** `CEnemyDeckMgr::GetRandomDeck` (0x1a3dcc) takes a random legal deck, then a random hero of an allowed class
  whose starting Mojo is at least the deck's (average cost − 0.5, truncated, at most 5). Heroes by class (eHeroType =
  row of the hero table): fighter 1,2,3,4,13,16 · ranger 5,6,7,8,14,17 · mage 9,10,11,12,15,18 · artillery 19,20,21.
  Allowed classes: the class of a weapon in the deck that none of its monsters can hold (fighter, ranger, mage,
  artillery in that order), otherwise the classes of every weapon in the deck, otherwise any.

## The port

- `scripts/import-skirmish-decks.py` decodes all 227 decks into `src/data/skirmish-decks.json` (record format as in
  `import-native-quests.py`; the high byte of the type field is the foil flag). 583 cards across 108 decks are spells
  and runes this game never imported, so they are dropped.
- `originalSkirmishDeck()` (`src/engine/progression.ts`) is `GetRandomDeck`, with three departures:
  decks that lost more than a fifth of their cards are skipped; the one deck with no monsters ("boss": a lone hero with
  big weapons and Carnage) is skipped because our computer cannot play it; the four heroes this game has no model for
  (Minotrix, Booga, Ocularus, Kargadan) are skipped. That leaves 211 decks for standard rules, 118 of them untouched,
  and 17 heroes.
- Setup → «تشكيلة الخصم» → «🎲 مكتبة اللعبة الأصلية» is the new default for Skirmish; a toast names the deck and hero.
  Choosing a race still works as before.
- Setup → «أفضلية الخصم» level N now gives +N Mojo every turn **and** N extra cards in the opening hand
  (`dealExtraCards`). Only in Skirmish; quests keep their own bonus, other modes keep expert's +1 Mojo.

## How strong the library is in our engine

Original-style AI at 2,500 nodes on both sides, 100 games each, every pairing from both seats:

| library deck (random each game) against | result |
| --- | --- |
| zombie deck, hard tier | 55 / 100 |
| human deck, old builder, hard tier | 16 / 100 |
| human deck, new builder, expert tier | 5 / 100 |
| best of all races (robots), expert tier | 1 / 100 |

So the library is an average opponent in our engine, well below the decks our builder makes since 7.23. Several of its
heroes are fragile (Alphedia 15 health, Boneyard/Ernold/Hyssta 20) and the original AI walks them forward. The original
leaned on the extra cards and Mojo to make it hard; the handicap dial is that lever here.
