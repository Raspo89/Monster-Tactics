# 7.8 — closer to the original: arenas, battle controls, menus

Compared against three recordings of the original game and rebuilt from the APK's own data and art.

## Arenas
- `scripts/import-native-maps.py` imports the original two-player battle layouts from `Layouts/multiplayer/2p/*.map` (108 maps; 2 files without start cells are skipped). Format worked out from the files and the `MCT_*` enum in `libapp.so`: 13×13 cells, "even-q" hex layout (checked: every map is exactly point-symmetric between the two starts in that layout, 100%, against 69–70% for the other three conventions).
- Each map has 91 playable cells, rocks, 4 rune stands per player and bonus tiles. Bonus values come from the native globals table: +2 / +3 power, +2 armour, regen, +1 / +2 Mojo, +1 card. The −2 power and −2 armour tiles use −2, the number printed on the original tile icons.
- New skirmishes default to "original arenas": a random original map in one of the four original arenas (lava, forest, mountain, desert). Floors are composed from each arena's own floor textures with lighting matched to the videos. The four older maps remain selectable.
- Bonus tiles and flame / trap / barrier tiles use the original pickup icons from the GUI atlas; grid lines are thin and white like the original.

## Battle controls
- Gear [Esc] bottom-left opens the pause options (log, rules, sound, settings, main menu); green check [Space] bottom-right ends the turn; a "دورك" (your turn) banner at the start of each turn.
- The camera fits the larger boards on phones (minimum zoom 0.3) and centres on the visible part of the screen.

## Menus
- Main menu right page is the original "Single Player — Click to Start" page with the original medallions: Daily Challenge (new), Solo Quests (still unavailable), Skirmish, Pass & Play; collection, shop, settings and rules are round icons below.
- Daily Challenge: the same opponent and original map for everyone on a given date; first win of the day pays 250 extra coins on top of the normal reward.
- End of battle shows the original WINNER / BAD LUCK logo over the blue screen.
- On narrow phones the book pages stack, play page first.

## Tests
232 tests pass, including tests/native-maps.test.ts (layout import, symmetry, start/stand/rock/tile placement, tile bonus amounts, AI games on original layouts staying on the board). Checked in headless Chrome at 1280×720, 390×844 and 844×390.

## 7.8.1 — zoom
- The mouse wheel zooms smoothly in proportion to the wheel movement (it used to jump a fixed 8% per event, which is very fast on mice and touchpads that send many events) and toward the point under the cursor; pinch zooms toward the point between the fingers.
- Zoom limits follow the fitted view of each board: 80% of it at the smallest, 2.4× at the largest. Zooming back out returns to the centred view.
