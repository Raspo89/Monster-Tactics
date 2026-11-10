# Native monster races and passive triggers

Source: recovered `table-340bb0.txt`, numeric parameters in `native-parameters.json`, original `Locale/eng.txt` from `main.obb` (UTF-16), and read-only ARM disassembly from `libCombatMonsters.so`. The first 16 rows are monster races. RT_HEROES1–4 and RT_DUNGEONMASTER are hero/model categories rather than additional monster races.

`src/data/races.json` contains their Arabic labels, native identifiers and real numeric values.

## Trigger mapping

- Human: dynamic power, +1 per adjacent friendly creature, including hero.
- Elf: dynamic health, +4 while all owned monsters are elves. Hero race is ignored. Must remove aura on impurity and restore on purity.
- Orc: dynamic power, +1 per other owned orc; no arbitrary cap.
- Zombie: every surviving zombie on both teams gains +1 permanent health on any creature death.
- Lizard: killer gets +2 permanent power and +2 permanent health when credited with a creature kill. Unlike werewolf, its native credited-kill path does not check opposing team.
- Dwarf: survive a combat attack, gain +2 permanent power. The native survivor-credit function is called even if the attack deals no health damage.
- Minotaur: equip/re-equip gains +1 permanent power and +3 permanent health. This is an event bonus; re-equipping a slot triggers it again.
- Werewolf: killing an enemy creature grants +3 permanent health. Native `CreditMeWithAKill` checks victim and killer teams specifically for this bonus.
- Golem: when owner plays a rune, every owned golem gains +3 permanent health. The `RB_GOLEM_BONUS` / Rune Worship text (+2 when anyone plays rune) exists in locale but is NOT the race table's assigned bonus. Golems use `RB_RUNEHEALTH_BONUS`.
- Elemental: owner plays a spell, all owned elementals gain +1 permanent power and +1 permanent health.
- Cyclops: each other friendly monster death grants +2 permanent power. The race uses `RB_FREINDLY_DEATH_GAINS_POWER`, not the unused locale's adjacent-empty-tile armour bonus.
- Skeleton: +3 native racial armour less 1 per currently equipped item. Count weapon, body armour and shield separately. Replacement changes no slot count.
- Robot: prevent ALL afflictions, including beneficial ones; this is broader than just poison immunity. Native `BecomeAfflicted` checks race bonus 0xD then returns without applying the affliction.
- Imp: flame-afflicted upkeep grants +3 permanent health in place of normal -1 flame health. Poison or other status is not flame and must not be mistaken for it.
- Spectre: no equipment; basic attacks with default weapons cannot target/damage it. Equipped weapons and activated abilities/spells can affect it.
- Vampire: causing positive health loss in combat grants a fixed +2 permanent health once per damaging attack/ability. No gain when only armour/shield was removed, no per-point multiplication, and no health threshold. Each own upkeep also loses 3 health, ignoring armour.

## Vampire and Imp markup recovery

The earlier `locale.json` had cut bracket markup after `@X` and `@C`. Full UTF-16 `Locale/eng.txt` says:

`RAB_BLOODSUCKER_BONUS`: `%PRACE% permanently gain RB_BloodSuckerUp_Health when they take @X[19], but suffer RB_BloodSuckerDown_Health every upkeep.`

`@X[19]` is the health icon. Native `CCharacterMin::CreditMeWithCausingLifeLoss(int)` at **0x13456c**, reached from `DealCombatDamageTo` with positive post-armour health loss, checks race bonus **0x10** and calls `AddHealth` with global field **0x454** (+2). The amount of damage is only checked `>0`; it is not used as a multiplier. `CBattle::ProcessTeamForUpkeep` at **0x1114b8**, instruction **0x1116c8**, checks the same bonus and schedules the global field **0x458** (-3) as upkeep health loss.

`RAB_BURN_BONUS` ends `if afflicted with @C[1]Flame@C[0].` Native `CUpkeepMgr::StartActiveUpkeep` at **0x210938**, branch **0x2109ac**, checks bonus **0xE**, choosing global **0x450** (+3 health) instead of flame's global **0x1C** (-1 health).

`CCharacterMin::DealCombatDamageTo` at **0x13464c**, branch **0x1347fc**, checks a default-weapon basic attack and defender bonus **0xF** to set the damage to zero.

No speculative vampire threshold is needed. No unconfirmed mechanics were added to the descriptions.
