# Tools used to restore art from the original APK (7.4)

- `etc1.py` — decoder for the game's `!ETC` textures (10-byte header + ETC1 mip chain) and `LUM8` alpha files. Verified pixel-identical against all 596 textures that were already in the project.
- `decode_all2.py` — decodes every monster skin found in `Archetypes/*` of the extracted OBB into `public/original3d/models/*` and lists it in `model-manifest.json`.
- `../decode-magic-art.py` — decodes rune and spell card art.
- `render.html` + `rlib.py` + `gen_portraits.py` — render one portrait per model/skin with three.js in headless Chrome (camera yaw 153.4°, pitch 20°, flat ambient light; framed to the bounding box of the original portraits, IoU ≈ 0.98 against them). Serve the workspace root over HTTP on port 8765 and run with Playwright.

Paths inside these scripts point at the machine they were run on; adjust them before re-running.
