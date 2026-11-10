# POV revision — v3, 2026-11-09

Reference: user-supplied ScreenRecording_11-09-2026 10-00-15_1.mp4, duration 120.2 seconds. The recording is sideways; review frames were rotated to upright landscape. Gameplay at 12, 35 and 105 seconds establishes a bottom-to-top battlefield, elevated camera behind the player, compact corner status, small cards along the bottom and unobtrusive battlefield hexes.

Changes:
- Replaced side-by-side screen layout with a shared perspective camera. Player starts in the foreground looking away; opponent starts in the distance facing the camera. Depth changes projected cell and model size. Local two-player mode swaps viewpoint to the active owner.
- One camera projects unit models, hex corners, hover tests, targeting and effects. Wheel and +/- buttons zoom; right/middle drag or Shift+left drag pans; home resets. Projection tests cover both owners, all 63 cells, zoom bounds and pan offsets.
- Removed sidebars and footer panels from the battlefield. Compact HUDs occupy the corners; the hand stays visible when a unit is selected. Details use a small independent inspector.
- Added 48 directional native-model animated sheets: front and back views of 24 models, each with idle, walking and attack rows. GPU and non-GPU paths use the same elevated camera direction. Native arena geometry and textures supply four pre-rendered perspective backgrounds, with the missing terrain base layer composited from the original floor texture. This remains a baked environment rather than a fully interactive 3D arena. Zoom/pan use a 2D camera transform for this environment. Fixed a previously truncated mountain atlas in the world export.

Verification:
- 67 tests passed: prior 63 rules/AI tests plus four projection tests. TypeScript and production build passed.
- Browser QA: initial hand, summoning via projected cells, unit selection while retaining cards, camera zoom/reset and saved-match restore. Fallback characters display facing the correct sides. Cloud browser has no WebGL; native GPU rendering remains visually unverified here.
- Self-contained HTML embeds required art/audio/models and the new POV sheets/backgrounds. Direct local-file opening is not available in the cloud browser; desktop file behavior remains unverified.

Remaining: v2's 47 prototype cards, names/stats/hero abilities and provisional numerical rules are retained. Arena tile arrangement and camera values are approximations, not a claim of exact original game data. Not every playlist episode has been reviewed. See VALIDATION-V2.md for rule limitations.
