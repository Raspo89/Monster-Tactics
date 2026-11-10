# Monster Tactics v2 — 2026-11-09

The user-supplied Combat Monsters 5.6 XAPK contains 7,004 OBB entries. Read-only conversion of the original MDA meshes, packed textures, animation clips, GUI sprites and selected sounds supplies this personal recreation.

## Implemented
- 24 converted model archetypes; 40 character portraits; 24 animated sprite sheets (576 frames); seven original sound effects; source-native card frames and four floor textures.
- Original mesh renderer for WebGL 2 devices. Animated pre-rendered native models remain available without WebGL. Human hero uses a humanoid fighter instead of the default Dean asset.
- Optional source-oriented rules: six-card opening hands, no opening-player first draw, regenerating expendable defence, class minimum/maximum attack ranges, summon-turn attacks, two warrior moves in lieu of attacking, artillery movement/attack exclusion, persistent +2 standing bonuses, equipment on heroes.
- Existing matches retain the previous rules. New games default to the source-oriented option.

## Verification
- 63 focused rule tests passed: 32 engine, 19 abilities, 12 source rules, including complete deterministic AI matches across all four races.
- TypeScript and production build passed. Browser QA checks local match creation, six-card opening, original character rendering, original card frames, card deployment, movement, turn switching and original sound file loading.
- Cloud browser has no WebGL support. The sprite fallback is visually verified; GPU rendering is not visually verified here. Three.js bone transforms are directly based on the same absolute, identity-inverse-bind conversion used for sprite baking.
- Standalone HTML embeds all referenced art/audio/model files, CSS and bundled code. Desktop file-opening behavior cannot be verified in this cloud browser.

## Remaining differences
This is a playable reconstruction, not a recovered original client or complete clone. The 47 card names and stats, leaders and abilities are prototype content. Human/zombie racial numerical bonuses are provisional; orc scaling/cap are provisional; elf purity is not restored. Fixed 7 Mojo, attack cost, retaliation, movement distance, healing timing/value and portions of terrain remain prototype choices. Four source floor textures do not reproduce all original arena geometry. The current dragon slot uses an original lizard model. Only four playable races are included. Source card stats and server logic were not recovered. Not all playlist videos have been reviewed in this revision.

Conversion scripts and source text evidence are in reference/. Do not describe unverified values as original values.
