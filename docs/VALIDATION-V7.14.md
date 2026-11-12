# Validation — 7.14 affliction visuals

Problem: afflictions were drawn by the 2D board (Phaser) as small text labels and an ellipse, but the 3D unit models are a separate WebGL canvas on top, so the labels were tiny, collided, or hid behind the models; nothing showed fire, ice, stun etc.

## Assets (`scripts/apk-tools/affliction-fx.py` → `public/original3d/fx/`)
- Models from `Particles/`: Death Mark skull (`Deathmark/deathmark.MDA`), Vengeance dagger (`Vengeance/Vengeance.MDA`), Ice Block (`IceBlock/iceblock.MDA`) with their textures; normalised to height 1.
- Particle textures named by the original affliction `.mtl` files: `particle_explosion` (flame), `Particle_star` and `Particle_stun` (stun), `Particle_snare` (snare), `GLWG_poof_sparkles` (regen, berserk), `Fan_smoke`, `Particle_rage`, `StreakHard`. Black-background additive textures get alpha from brightness because the 3D canvas is transparent over the board.

## Drawing (`src/ui/models.ts`)
- Each unit model gets an effect group rebuilt when its afflictions change and animated every frame: flames rising, skull and dagger bobbing above the head, four stars orbiting the head, snare ring spinning on the ground, translucent ice block, pulsing magic-shield sphere, green sparkles + ring for regen, gold ring + sparkles for mighty, red ring + smoke for berserk.
- The text labels are now only drawn for units without a 3D model (fallback); the hover panel still lists the statuses.

## Checks
- Battle injected with one affliction per unit, screenshots at 1280×800 (2×) and 390×844: every effect visible; no page errors. Full test suite passing.

## 7.15 — worn equipment and attack visuals
- `scripts/apk-tools/export-worn-equipment.py` writes all 205 weapons / shields / armour sets in their original mesh space (`public/original3d/equip`, 7 MB, textures colour-only). Armour sets include helmet, shoulder and chest pieces from `table-345730`.
- Pieces ride on the skeleton bones (`Bip01 R Hand`, `Bip01 L Forearm`, `Bip01 Head`, both `UpperArm`s, `Spine1`). The original skin matrices are pose deltas, so each piece is placed at its joint in the bind pose (estimated from the vertices that bone moves) and then follows the bone. Orientation checked on front/side renders of the human fighter; helmet scale per race/class from `table-33e4f8`. Units without a weapon hold their class default (Wooden Sword / Bow / Staff / Rock, the cost-0 rows of the weapon table).
- The yellow line drawn for every attack (it looked like an arrow even for mages) is replaced, in the 3D layer so it shows in front of the models: warriors and adjacent hits = slash arc at the target, archers = arrow with a slight arc, mages = violet magic bolt with a sparkle trail and burst, artillery = tumbling rock on a high arc with a dust burst. The 2D version stays as fallback for units without a 3D model.
- Checked in the browser with equipped units of every class and slowed time; full test suite passing.

## 7.16 — original rune stands
- `scripts/apk-tools/rune-stand-fx.py`: `Furniture/Dais/dais.MDA` (grey stone texture, tinted by owner colour), `Furniture/Crystals/crystal_01.MDA` (colour map baked to the pink-white glow seen in the original videos), `Runes/rune_01.MDA` with each rune card's own `Rune_01_*` texture (86 runes, legacy R01–R07 mapped to the matching originals).
- Drawn in the 3D layer: empty stand = dais + slowly turning crystal + glow; filled stand = dais + the rune stone tilted to face the camera, swaying, with a glow; the 2D board keeps only a thin hex outline in the owner colour and the stand's health under it. Checked at 1280×800 and 390×844.
