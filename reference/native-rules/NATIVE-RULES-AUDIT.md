# Native Combat Monsters rules audit (2026-11-09)

Scope: read-only static analysis of user-supplied ARM ELF `apk-review/libCombatMonsters.so`, native text help and embedded data. No APK or native executable code was run. Instructions were decoded using Capstone; tables were recovered with a Python transcription of the game's own data decoder.

## Recovered data

`CGame::DecodeData` at 0x14ecd8 allocates N bytes and XORs source[i] with source[N+i]. `extract_all.py` finds constant source addresses/lengths at native call sites and reproduces that transformation. `table-index.json` records addresses, lengths, native loader symbols and call sites. All 14 readable tables were recovered: monster stats, hero stats, ability metadata, armor, weapons, shields, spells, runes, race data, model data, enemy deck labels and globals. Raw CSV/TXT tables are authoritative extracted content; JSON mirrors are convenience copies. Numeric globals from comment-labelled rows are also in `native-parameters.json`.

Examples:
- Rune table source 0x3acc48, length 0xa174, loader CRuneMgr::LoadRuneStats at 0x1d6554.
- Globals source 0x34b638, length 0x453f, loader CGame::LoadGlobalVariables at 0x14ef54.
- Ability table source 0x341b48, length 0x1725, loader CArchetypeMgr::PermanentInit.
- Monster table source 0x3189a0; hero table source 0x33ddc8.

## High-confidence core rules

1. **Basic attacks cost zero Mojo.** Ability CSV `AT_ATTACK`, `AT_BLAST`, `AT_SHOOT` and `AT_LOB` all have Mojo=0. Their ranges are respectively 0..1, 0..2, 2..3 and 3..3; actual target cannot be the attacker. Special abilities have individual explicit costs. Native `GetCanUseAbility` at 0x1341ec loads the cost from that exact ability metadata.
2. **Move after attacking is permitted when movement remains.** `GetCanMoveThisTurn` at 0x134450 checks exhausted flag bit4. Nonwarriors and heroes then only test the moved flag bit1, not attacked flag bit2. Warrior nonheroes may take their additional movement only while attacked flag bit2 is clear. `SetHasMovedThisTurn` at 0x1343f8 sets moved bit1 and also attacked bit2 for class3 artillery. `SetHasAttackedThisTurn` at 0x134424 sets attacked bit2 and also moved bit1 for artillery. Therefore heroes/ordinary units can attack then take one otherwise-unused movement; warriors may alternatively take two moves and forfeit attacking; artillery is mutually exclusive.
3. **No general automatic retaliation in the native normal attack chain.** `CAbility_Attack::DoAbilityToPrimaryTarget` at 0xd75bc calls attacker.DealCombatDamageTo(defender), then defender.ApplyAnyAfflictionsFromProtagonist(attacker). `DealCombatDamageTo` at 0x13464c computes outgoing power, target damage and attacker/defender kill/survive credits. `DealDamageTo` at 0x134028 consumes the defender's armor and then damages defender health. There is no mirrored basic attack call. Specific afflictions/abilities such as Vengeance may still hurt the attacker; those are separate effects.
4. **Hand draw implementation supports 200 cards.** `CHand::DrawCards` at 0x1576f0 checks count<=0xc7, draws and increments; it stops at 200. There is no seven-card burn in this routine. Note: another optional gameplay cap was not identified, so this statement describes the native draw implementation.
5. **Health gain is not capped to printed starting health.** `CCharacterMin::AddHealth` at 0x13194c adds directly to its signed accumulated health adjustment at +0x2b. `TakeDamage` at 0x133bb4 subtracts from the same field. Source health gains can exceed the printed starting value. Regen tile global value is +2, agreeing with Help/FACT text describing a permanent health gain; a globals comment calls it accrued damage healing.
6. **Elf purity is +4 Health.** `RB_ElfBonus_Health=4`; `GetTallyBasedBonuses_Health` at 0x134a44 compares CountFriendlyMonsters with CountFriendlyRaceMonsters and only grants this bonus when counts match. Heroes are excluded from those counts. Native fact text warns an Elf with <=4 current Health can die when another race enters play and removes the bonus.
7. **Human cohesion is +1 Power for each adjacent friendly creature**, with Health bonus0; **Zombie health gain1 when anything dies**; **Orc Power1 for each friendly Orc**. Exact parameters are in globals; the Orc metadata says each *other* friendly Orc. No cap of three was recovered.

## Four native runes ready to implement

All are persistent and target the owner's rune stands as described in native Help. Repeated copies cost base Mojo plus GO_AdditionalRuneCost2 for each matching active copy.

| Tag | Native name | Cost | Rarity | Effect |
| --- | --- | --- | --- | --- |
| R_MINORPOWER | Rune of Minor Power | 3 | C | +1 Power to all your monsters |
| R_MINORARMOUR | Rune of Minor Armour | 3 | C | +1 Armour to all your monsters |
| R_MINORMOJO | Rune of Minor Mojo | 3 | C | +1 Mojo each upkeep |
| R_EXTRACARD | Rune of Draw Mastery | 3 | R | Draw one additional card each upkeep |

The rune table contains additional upgrade tiers and many other original runes with their exact names, costs, filters, textures and parameterized tooltips. This audit does not implement them.

## Still uncertain / not recovered in this bounded task

- Rune starting health15 is directly visible in the user video but was not tied to a native static constant here. The locale uses RUNICSTARTHEALTH as a formatted placeholder.
- No source spell/ability/rune tooltip with spawn/summon/resurrection wording was found in the recovered tables. This is absence of evidence, not a proof that every special exception is impossible. The base native Help explicitly restricts normal summoning to an empty adjacent hero cell.
- The rune Help says any creatures may attack runes while adjacent; exact friendly-rune attack restrictions were not exhaustively traced.
- Global card stats were recovered, but mapping every entry to the current prototype roster and implementing every activated ability remains separate work.
