# Validation — 2026-11-08

51 engine rule tests passed. They cover hex geometry, seeded setup, all 36 unit summons, movement, summoning sickness, charge, guard, line of sight, stealth, melee retaliation, ranged attacks, shields, poison, healing, splash, hunger, equipment replacement, runes, faction auras, resurrection, teleport, leader abilities, simultaneous leader deaths, fatigue, deterministic full matches and resource/occupancy invariants.

The final normal/easy run passed all 59 tests (51 rule tests plus eight benchmark partitions). A separate hard/normal run passed all eight benchmark partitions. The easy chooser was subsequently changed to select from the best half of all legal actions as specified; the normal and hard code paths were unchanged by that final easy-only adjustment.

| Comparison | Games | Higher-level wins | Losses | Draws |
| --- | ---: | ---: | ---: | ---: |
| Normal vs easy | 100 | 81 | 19 | 0 |
| Hard vs normal | 100 | 82 | 18 | 0 |

Each comparison uses 50 seeded setups (800–849), with each setup played twice and the higher difficulty swapped between sides. Decks, races, starting player and map remain identical within each pair. All four factions and all three maps are represented. No difficulty gets additional resources, stronger cards or access to opposing hands/deck order. These are regression benchmarks for these specific starter decks and seeds, not a universal win-rate guarantee. Maximum observed decision time under parallel test load: normal 159 ms, hard 274 ms.

Browser QA: menu and setup, mulligan, summoning with energy/token consumption, movement, melee kill and log, opponent play, saved-match continuation, deck editing/validation/save, local-player handoff and hidden hand. A production build passes TypeScript checks. The standalone HTML embeds all 49 image assets and the JS/CSS without external runtime requests. Direct file:// launch cannot be exercised in the cloud browser; the same interface and engine were tested over the local web preview.

The project uses original generated sprite artwork, not the original game's 3D models. The tutorial is one three-step practice match, and the campaign is five progressive encounters rather than the proposed later 20-stage story expansion.
