# 7.1 asset and download cleanup

Removed 688 conversion-only files: 649 unused PNG textures, 14 unused world/prop JSON files, 24 superseded single-direction sheets and one animation-source dump. Removed two unimported card-plan JSON files. The detailed paths and sizes are in reference/ASSET-CLEANUP-V7.1.json. Model manifests now list only retained skins; unused visual sheet metadata was removed.

All 72 meshes preserve every runtime-consumed numeric array exactly against v7, including original positions, normals, UVs, indices, skin weights, skin indices, bone palettes and idle bounds geometry. All 260 card/hero visual references resolve to existing textures, portraits and both generations of directional fallback sheets. Bone names and first fallback frames are identical. The four runtime clips (idle, walk, attack, death) preserve every original frame exactly. Unused clips, extra per-bone frames and conversion metadata were removed. No image resampling or quality reduction was applied.

Production TypeScript check and Vite build passed. The previous 183 rule/economy tests remain relevant: no battle, card, progression or storage logic changed. This pass uses exact asset equivalence and existence checks; WebGL rendering was not re-tested.

The download stores assets once in PLAY-OFFLINE.html. SOURCE includes the code, tests and conversion references but excludes a second public asset tree. Run node scripts/restore-offline-assets.mjs from SOURCE to reconstruct the runtime assets from the sibling offline HTML before npm install/build. Restored assets are compared byte-for-byte with the production public tree during packaging; ZIP CRC is checked. Prior full conversion source remains in git history.
