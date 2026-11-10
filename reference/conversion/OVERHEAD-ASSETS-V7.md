# V7 overhead fallback animation assets

Source: the existing decoded original Combat Monsters character models and common animation clips in public/original3d. No new artwork or executable code from the APK was run.

Camera elevation: atan2(15,6) = 68.1985905 degrees, matching the new shared camera position (0,15,6). Front/back face directions are retained. Output: 144 directional WebP sheets, covering all 72 existing model entries. Each sheet is 1280x540, with 160x180 frames; 8 samples each for idle, walk and attack.

Files are under public/assets/original/pov-v7/. Ground-anchor, projection scale and model-height metadata are in src/data/pov-sprites-v7.json, keyed identically to the older fallback manifest. The prior pov files and metadata are unchanged for older match compatibility. Reproducer: reference/conversion/bake-overhead-v7.py.

Validation: all 144 sheets reopened; all 3,456 frames have nonempty alpha; all metadata values finite with positive height and pixels-per-unit. A single initial zero-byte neutral_dragon-front encode was detected, re-baked and validated. The reproducer now encodes to a nonempty in-memory buffer, verifies the image and atomically replaces the target. A six-model contact sheet was reviewed for direction, full character coverage and higher overhead appearance.

Like the previous raster fallbacks, these use each archetype default texture. Exact individual card colours remain available in portraits and the GPU 3D path.
