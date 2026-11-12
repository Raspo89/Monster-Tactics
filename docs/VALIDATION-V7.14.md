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
