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

Against the original-style AI at 15,000 nodes, both sides on hard decks, each pairing played from both seats:

| advanced AI | result |
| --- | --- |
| evaluation only, no reply (= the original) | 5 / 12 |
| reply lookahead, 8,000 nodes, 8 candidates, ghost hand | **16 / 24** |
| the same without the ghost hand | 15 / 24 |
| two passes, 20,000 nodes, 24 candidates shortlisted to 6, replies at 6,000 | 15 / 24 |
| plus a third half-move (our follow-up turn), weights 0.5 and 1.0 | 7 / 12, 7 / 12 |
| blending the turn's own value into the decision, 0.3 and 0.5 | 15 / 24, 15 / 24 |

So the reply lookahead is worth about +25 percentage points, and nothing beyond it moved the number.

## Why more search does not help

Measured over three games (`/home/claude/work/diag.ts`): the value predicted for the chosen turn versus the value that
actually came out of the opponent's real turn differs by roughly ±100 points (10th–90th percentile −83 … +177) on
evaluations of about 200, with a mean of +78 — the simulated opponent is weaker than the real one, so reality is usually
a little better than feared. The spread between the candidate turns is smaller than that error, so deeper search is
measuring its own noise. The way past this is a better opponent model or a less noisy evaluation, not more nodes.
