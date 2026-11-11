# Validation — 7.12 stronger computer opponent

Player report after 5 games: the opponent was far too easy. The default level was "normal" (one-step greedy) with the starter deck, the tutorial/easy quests used "easy" (random top-half moves, 15% early end of turn), and the computer never got better cards than the starter deck while the player's collection grows.

## Changes
- Default difficulty is now hard (turn planner that checks the opponent's reply) and the last choice is saved.
- `aiDeck(race, difficulty)`: easy/normal = starter deck; hard = veteran deck (best commons–rares of the race up to 5 Mojo, weapon per class, armour); expert = champion deck (rares and legendaries up to 6 Mojo). Scored by (power×1.6 + health + armour×1.5 + 2 for an active ability) / cost.
- New level expert = hard planner + champion deck + 1 extra Mojo a turn (shown in the menu).
- Quests: tutorial normal, every other quest hard (the decks and enemy Mojo bonuses stay the original ones). Campaign stages: normal, normal, hard, hard, expert.

## What was tried and not kept
- A threat map in the evaluation (what the opponent can hit next turn) and guessing the opponent's hand from its unplayed cards: in AI-vs-AI matches (16–40 games each) none of the variants beat the existing hard AI clearly (37–62%, within noise), and the threat map made thinking 2–3× slower. Both are left as optional weights (`threat`, `guessHand`), off by default.

## Checks
- Own decks, paired seats: hard vs normal 10/12, expert vs hard 12/12 (`tests/ai-decks.test.ts` keeps a smaller version; also checks deck legality and that rarity rises with the level).
- Existing difficulty tests unchanged and passing (easy < normal < hard on equal starter decks). Full suite: 258 tests.
- Browser (390×844): new menu option, saved choice, expert match starts.
