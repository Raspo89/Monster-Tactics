# The advanced opponent (7.22)

Settings → «أسلوب الكمبيوتر» → «مطوّر». Code: `src/engine/smart-ai.ts`.

## Method

It keeps the original game's evaluation (`docs/AI-NATIVE.md`) and adds the one thing the original never does — it plays
the opponent's answer before committing to a turn.

1. Build the original's influence maps once for the position (`buildMaps`).
2. Search its own turn with the original's search (`nativeSearch`), asking for the best turn **per opening action**
   (`perFirst`), not just the best turn overall. That is what makes the candidates genuinely different turns rather than
   variations of the one the evaluation already likes.
3. For each candidate turn: end the turn, let the opponent take their best turn in reply (the same search run for the
   other side), then score the board that comes out of it with `nativeEvaluate` **using the root maps**, so every
   candidate is measured with the same yardstick.
4. Play the turn with the best board after the reply. Doing nothing is always one of the candidates.

Hidden information: the reply is played with the opponent's hand replaced. With `ghost` (the shipped setting) they get a
hand of the right size drawn from the cards they have not played yet, so the answer includes summons and spells; the
identity of the cards actually held is never read. `tests/smart-ai.test.ts` checks this: moving a card between the
opponent's hand and deck does not change the plan.

Shipped levels (`SMART_LEVEL` in `src/main.ts`), budget / time cap / candidates / reply budget:
normal `2500/2s/5/1200`, hard `8000/4.5s/8/2500`, expert `14000/7s/10/3500`. It runs in the same Web Worker as the
original AI, so the board keeps animating.

## Measured strength

**100 games at the shipped hard settings (advanced 8,000 nodes / 8 candidates / replies at 2,500 / ghost hand, against
the original-style AI at 15,000 nodes), both sides on hard decks, every pairing played from both seats: 50 / 100.**
The two halves of that run came out 29/50 and 21/50, which is the spread to expect from 50 games around an even result.

In other words the reply lookahead does **not** make it stronger. The short runs below were measured first and read as a
large gain; at 12–24 games the standard error is 7–10 percentage points, so every one of them is consistent with 50%.
They are kept here as a record of what was tried and of how misleading a 24-game sample is.

| advanced AI | result | games |
| --- | --- | --- |
| shipped settings | **50 / 100** | 100 |
| evaluation only, no reply (= the original) | 5 / 12 | 12 |
| reply lookahead, 8,000 nodes, 8 candidates, ghost hand | 16 / 24 | 24 |
| the same without the ghost hand | 15 / 24 | 24 |
| two passes, 20,000 nodes, 24 candidates shortlisted to 6, replies at 6,000 | 15 / 24 | 24 |
| plus a third half-move (our follow-up turn), weights 0.5 and 1.0 | 7 / 12, 7 / 12 | 12 each |
| blending the turn's own value into the decision, 0.3 and 0.5 | 15 / 24, 15 / 24 | 24 each |

Measuring an AI change in this game needs at least 100 games per configuration; at the shipped budgets that is about
25 minutes of machine time, or about 5 minutes with both sides searching 2,500 nodes.

## Why more search does not help

Measured over three games (`/home/claude/work/diag.ts`): the value predicted for the chosen turn versus the value that
actually came out of the opponent's real turn differs by roughly ±100 points (10th–90th percentile −83 … +177) on
evaluations of about 200, with a mean of +78 — the simulated opponent is weaker than the real one, so reality is usually
a little better than feared. The spread between the candidate turns is smaller than that error, so deeper search is
measuring its own noise. The way past this is a better opponent model or a less noisy evaluation, not more nodes.

# Where the strength actually came from: decks (7.23)

Three things were measured at 100 games each, every pairing played from both seats, both sides on the original-style AI
at 2,500 nodes (`/home/claude/work/deckbench.ts`).

**1. Making the evaluation aggressive does not work.** Against the unmodified evaluation (knobs in `AGGR`,
`native-ai.ts`): hurting the enemy hero worth double 46/100; attack over armour 51/100; march on the hero and ignore the
altars 50/100; all of them together 41/100. The original's weights are already at a local optimum.

**2. Race ranking** — each race's five best monsters (hard tier, human hero) against the human deck:
human 50 (the baseline, so exactly even), spectre 43, elf 25, cyclops/skeleton/werewolf 21, orc/vampire 19,
dwarf/minotaur/zombie 18, lizard 14, imp 9, golem 6. Lizards do badly in the AI's hands because the evaluation scores a
monster by what it is now, and a lizard's worth is what it *becomes* after a kill (+2/+2).

**3. The deck builder was leaving the best cards on the shelf.** `raceDeck` filtered out every card costing 1 Mojo, and
ranked cards with a formula that undervalued cheap bodies and happily picked monsters with 0 attack. The robot race is
made entirely of 1-Mojo legendaries that are immune to every affliction — the builder could never pick them. With that
fixed (`tempoScore`: value per Mojo, never a 0-attack monster, cost-1 cards allowed):

| deck | against the old builder's human deck |
| --- | --- |
| robots, expert tier | 75 / 100 |
| robots vs spectres, expert tier | 85 / 100 |
| best monsters across all 16 races, expert tier | **85 / 100** |
| humans, expert tier | **72 / 100** |
| humans, hard tier | 51 / 100 (no cost-1 cards at that tier, so nothing changes) |

The new ranking is now the default, and skirmish has an enemy-deck option «⚡ الأفضل من كل الأعراق» that builds from
every race at once. This single change is worth far more than everything tried on the search and the evaluation.

# Handicap, not intelligence (7.24)

A strong human player beats the computer easily whatever deck it holds, and nothing in the search or the evaluation
closed that gap. What does close it is material. Setup → «أفضلية الخصم» gives the computer extra Mojo every turn
(expert still defaults to +1). Mirror match, the same deck on both sides, 100 games each:

| extra Mojo per turn | win rate against the same deck with none |
| --- | --- |
| +1 | 59 / 100 |
| +2 | 71 / 100 |
| +3 | 79 / 100 |

Roughly ten percentage points per Mojo. Deck matchups for reference, both sides played by the original-style AI at
2,500 nodes, expert tier, 100 games: robots beat lizards 85/100 and humans 66/100 — so the robot deck is strong against
*the computer*; against a good human its 2–5 health bodies die one per turn.
