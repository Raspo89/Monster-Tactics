# 7.2 — phone play, smarter difficulty levels, rune fix

## Difficulty levels
Measured with real games under the rules the app uses (original rules, round arena, the four starter decks). Every seed is played twice with the two levels swapping seats, so race and first-player luck cancel out. Seeds below were not used while tuning.

| Match-up | Games | Win rate of the stronger level |
|---|---|---|
| Hard vs Normal, mixed races | 128 | 74% (was 59% before 7.2) |
| Hard vs Normal, same race | 64 | 75% |
| Normal vs Easy, mixed races | 128 | 94% |
| Normal vs Easy, same race | 64 | 86% |

- Easy: its "random" pick never actually varied (it copied the state, so the random number never advanced). It now varies properly and sometimes ends its turn early.
- Normal: unchanged — one greedy action at a time.
- Hard: plans its whole turn (beam search over action sequences), then tests each candidate plan against the opponent's likely reply and its own follow-up next turn. It only uses public information: the opponent's hand is emptied in every simulation. Its evaluation no longer over-values over-healing its own leader, values cards with diminishing returns and avoids drawing itself out of cards. A fixed work budget caps thinking time (typically under 0.1 s, rarely about 0.5 s on a desktop).
- `npm test` now includes tests/difficulty.test.ts (normal > easy, hard > normal mixed and mirror, hard > easy). `npm run bench:ai -- hard normal 1000 64` reproduces the table. The slow legacy-rule tournaments moved to `npm run test:tournament`.

## Rune fix
A creature could attack its own side's rune. Only enemy runes can be attacked now; the rune tutorial text says so, and a test covers it.

## Phone
- One finger drags the camera, two fingers pinch to zoom, a tap selects (the mouse controls are unchanged).
- The camera fits the whole arena into the space between the top HUD and the hand, in portrait and landscape, and refits after rotating; ⌂ returns to that view.
- Page pinch-zoom is disabled during play so gestures reach the board; card previews shrink to the corner and close when you tap the arena; landscape uses a shorter hand.
- Darker labels on the parchment setup page.

Inferno and the Elf hero heal were deliberately left unchanged.
Checked in headless Chrome at 390×844, 844×390 and 1280×720 (tap-to-summon, drag, pinch, a full match against Hard). Not tested on a physical phone.
