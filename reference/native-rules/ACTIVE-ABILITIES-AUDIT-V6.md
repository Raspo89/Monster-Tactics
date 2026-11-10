# Original monster active abilities — native evidence, version 6

Source: the user's original `libCombatMonsters.so`, decoded native `table-341b48.txt` (ability definitions), `table-3189a0.txt` (monster to ability assignment), `native-parameters.json`, and complete UTF-16 `Locale/eng.txt` from the user's OBB. No native executable was run. `src/data/abilities.json` contains all 57 non-empty, non-NONE table entries, including the four zero-cost basic attacks; 49 entries have a positive Mojo cost.

## Costs, use and attack budget

- The ability table's Mojo cost is the **activation cost**, independent of the monster table's Mojo summoning cost. Targets and min/max range also belong to the ability definition.
- A specialised skill is used **instead of the basic attack**. This is explicitly stated in native HELP_MONSTERCARDS_7.
- `CBattle::Process`, at 0x11a540–0x11a54c, treats only ability type 0x3A (Move) as movement. Other abilities call `SetHasAttackedThisTurn`, including zero-cost, self and support actions. Thus a zero Mojo cost does not permit unlimited activation.
- `CanDoAtLeastOneAbility` at 0x1326f4 requires alive, no Dazed/Ice Block and an unused attack token. It does not test summoning sickness. Newly summoned monsters can use their activated ability.
- Sprint and SuperSprint share `CAbility_Sprint`: target must have moved, clears its moved flag and summoning sickness. An artillery target that could not move retains/receives an attacked flag; this prevents attacking as well as recovering movement. The caster still spends its attack on casting Sprint/SuperSprint.

## Combat values and effects

- `DealCombatDamageTo`, 0x13464c, calls `GetPower` then adds its ability-power argument at 0x1346a0 and clamps nonnegative at 0x1346e4. All `AB_*_Power` values are **additive** to current power. E.g. Smash adds3, Savage adds1, Head Shot adds2, Meteor subtracts2. They do not replace printed/current power.
- Abilities with native power -999 (Zap, Death Mark, Disarm, Trick Shot) intentionally skip combat damage in their handlers; implement them as no direct damage, not a huge negative strike.
- Afflictions from attacks can apply even when defence/shield absorbed all damage, provided the target survives. Fireball calls `BecomeAfflicted(Flame)` after a nonlethal `DealCombatDamageTo` return; damage dealt need not be positive. Vampire life-leech separately requires actual positive health loss.
- Phalanx counts adjacent **other friendly monsters**, excluding hero. Blood Lust counts adjacent enemy monsters, excluding hero.
- Heroic Shout grants Mighty to all own alive creatures **including hero**, skipping already-Mighty creatures. Inspiring Strike gives2 health to own monsters, including caster, excluding hero.
- Meteor's affected area is the selected tile and all tiles within1, per override at 0xed97c. The targetable centre uses the ability table's range2.
- Explode targets self plus every adjacent creature. Primary and secondary use current power plus respective native deltas0. It need not kill its caster if health/defence are sufficient; don't implement unconditional suicide.
- Colossus Smash damages and pushes all adjacent creatures. Push attempts do nothing if the destination is obstructed/outside; the attack still resolves.

## Afflictions and upkeep

- Dazed, Snared and Ice Block have native duration2, decremented only during **their owner's upkeep**, before effects are processed (`ProcessTeamForUpkeep` 0x111634). They therefore survive the next own upkeep2→1 and expire at the following own upkeep1→0. HELP_AFF_12 calls this "next-but-one upkeep".
- Reapplying one of these statuses does not extend/stack it: `SetAfflictionTurns` 0x1319b4 returns for an existing status with Application0. Mighty and Berserk are also unique permanent afflictions, not stacking power grants. Take Aim/FirstAid directly grants permanent +2 power on each activation and can stack over separate turns.
- Dazed prevents attack/activated ability, Snared prevents movement. Ice Block prevents actions and targeting by attacks/other abilities, and prevents damage. Ice Block is classified as a **good** affliction in original help; Cure removes bad afflictions and must not remove it.
- Flame is permanent until cured, causing -1 health per own upkeep. Burning Imps instead gain3; native racial immunity for Robots rejects all afflictions, beneficial and harmful. Regen gives +1 per own upkeep, plus its ability's immediate2 health.
- Mighty is +2 power. Berserk is +5 own power and +2 incoming attack power. Death Mark adds1 incoming attack power. Vengeance loses5 health when the afflicted creature next attacks, then is removed. Magic Shield absorbs one incoming attack completely.
- Stepping onto the native regeneration tile removes **all bad afflictions immediately**, not only poison (HELP_AFF_1).

## Range and icons

Ability marking uses `CMap::RecurseRangeCalculator` (0x1609d0), not its separate `AvoidingObstacles` variant. It marks hex distance over existing cells and does not perform an intervening-rock line-of-sight test. Rune stands are excluded as normal highlighted creature targets.

Original icon fields are indices like `1*55` (Fireball), `1*3` (Heroic Shout), `1*19` (Heal), not direct image filenames. Original per-ability WAV files are available under `Sound/game/abilities/` in the OBB. No assumption about an atlas image filename was made here.

## Evidence files

- `active-ability-evidence-v6.txt`: bounded native disassembly supporting the above rules.
- `active-ability-help-v6.json`: complete selected original help strings, preserving bracket markup that the old locale extractor had truncated.
- Original table and parameters remain alongside this audit.

## Final trigger and movement checks

- Vengeance triggers after **every ability whose table `Is Offensive` flag is1**, including nondamaging Zap, Death Mark and Disarm. `CAIBattleState::DoAbilityOnTargetHex` 0xf7d2c–0xf7d40 loads ability-data field0x10 and passes it to `ProcessAbilityTriggerdAfflictions` 0xf7ac0. That function checks nonzero, applies5 healthloss, then removes Vengeance. Nonoffensive Heal/Cure/Rally do not trigger it. This does not depend on actual damage dealt.
- Trap's `TriggerAction` at0x20d5f8 has no owner/team check. It hits any stepping creature (except an IceBlocked one) for5 healthloss, then deactivates.
- Fire and Barrier durations decrement on their **creating owner's upkeep** (`CTileItem::Upkeep` 0x20995c compares stored owner to current upkeep team). They do not decrement at both players' upkeeps. Trap has lifetime-1 and waits for a trigger.
- Blink is an activated teleport. Its shared ability eligibility does not check summoning sickness or Snare; its handler at0xdcd88 directly sets the destination hex. Therefore Snared or newly summoned monsters can Blink if their attack token and Mojo are available. Being Snared also does not prevent being pushed.
- Fire tile entry at0x20b878 deals1 through defence-aware `DealDamageTo`, then inflicts Flame on survivors. It skips the initial fire-tile damage for Imps but still inflicts Flame; Imps gain3 at their upkeep. Robots can reject Flame but still take ordinary tile damage after armour. No fire-tile team check exists.
