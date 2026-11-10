# 7.5 — four spell fixes

- Timed afflictions now default to the recovered native durations: Stun, Ice Block and Snare use AF_Stun_Turns, AF_IceBlock_Turns and AF_Snare_Turns. Explicit ability durations are preserved. On load, upgradeState repairs negative durations for these three timed effects in existing battles, starting a fresh finite duration; other permanent afflictions and positive countdowns are preserved. The upgrade is idempotent.
- The native spell importer retains the original “cannot attack this turn” clause as blockAttackThisTurn, including hero Berserk. Successful application consumes the attack action; reapplying an existing Berserk affliction also blocks the attack. Robot immunity is preserved. The original restriction is printed in the Arabic card text.
- Vengeance is classified as harmful in the importer and its targeted spell now offers enemy monsters, rejecting allies. Its native five-health loss still occurs on the victim's next attack.
- Second Wind clears abilityUsed along with attack and movement usage. Class-specific refresh spells affect only their own class. Afflictions remain in force, and reused special abilities must still pass their normal cost/target/status checks.

The fixes live in both the importer and generated data. Regeneration still yields exactly 74 runes and 361 spells, with the same 366 unsupported cards; only four imported card records change (Berserk metadata/text and Vengeance targeting/text). No asset files, economic settings, storage keys or deck presets change.

tests/magic-regressions.test.ts adds twelve behavioral regressions: finite targeted/hero afflictions, saved-battle migration/idempotence, Berserk's attack block/next-turn release/reapplication/robot immunity, hostile Vengeance targeting and its five-health consequence, reuse of a special ability after Second Wind, and class-limited refresh preserving afflictions.

Validation: all 217 standard tests pass (the retained 205 plus 12 new regressions), including the difficulty matchup checks; production TypeScript/Vite build passes. Tournament stress suites are separate from npm test and were not re-run. The offline HTML embeds the unchanged runtime assets once, and the ZIP includes the source plus asset restoration script. ZIP CRC and source/offline registry consistency are checked during packaging.
