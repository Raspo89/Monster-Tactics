# Original race assets, v5

Read-only conversion from the supplied original main.obb and recovered native catalogue. No generated replacement art.

- 128 native AT_NONE cards: 8 selected valid, named cards per each of the 16 monster races. Only positive-attack cards selected; two per class where that many valid positive-attack AT_NONE cards exist. Native stats and texture indices retained in src/data/race-card-plan.json.
- 43 additional original archetype models converted, making 67 model entries including earlier leaders and neutrals.
- 128 original portraits baked with the exact native texture index.
- 86 additional front/back animated sprite sheets, making 134 directional sheets total; each has 8 idle, 8 walk, 8 attack frames.
- Original camera angle 54.25 degrees; origin and height metadata computed from the complete clip bounds.
- All 128 portraits checked nonblank; every plan entry has its model, skin PNG, front/back sheet, and metadata present. Contact sheet of one card per race reviewed.

Current native subset deliberately selects cards without active card abilities. Vampire subset is artillery; Elemental subset has warriors and artillery. This does not include the complete original card catalogue. In 3D, card skin indices are exact; raster fallback sheets use one default skin per archetype.
