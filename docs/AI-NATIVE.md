# The original computer opponent (7.18)

Source: read-only static analysis of the original `libCombatMonsters.so` (ARM, 2016) with Capstone and the angr
decompiler. Function names come from the library's own symbol table. The port is `src/engine/native-ai.ts`.

## Search — `CAIWorker_BruteForce::Start` (0x156f40)

- Root state = the battle (`CAIBattleState::InitFromBattle`), scored once.
- Breadth-first over the AI's own turn only. Each node is expanded in this order: equipment (`ExpandNode_SpawnEquipment`),
  fighting (moves one hex at a time, every ability on every valid target, attacks on runes), summons next to the hero,
  equipment again, spells, runes.
- Children of a level are sorted by score (`SortNodeValues`, QSort) and expanded best first; identical consecutive nodes are
  freed. Up to 12 levels; node pool of 40,000 (`[worker+0x214] = 0x9c40`).
- The best node found anywhere becomes the plan if it beats the root; otherwise the AI ends its turn. The plan is a chain
  of up to 11 actions (`SetResult`, `tAI_FULLRESULT` 0x10c bytes).
- There is no simulation of the opponent's reply.

Per action, before `Evaluate`:
- move: bonus −0.0001; afterwards, if the threat on the destination exceeds health + armour by x:
  −(15 + 5x), or −(20 + 20x) if the creature has already attacked (`ExpandNode_Fighting`, 0x156b18).
- abilities: bonus −0.0001 (−1.0001 for a free special); killing an enemy that was already "considered dead": −37.5.
- every node: −0.001 × depth.

## Score — `CAIBattleState::Evaluate` (0x151ef8)

For every creature: `GetMonsterExcellence`
- hero: 2H, minus (15−H)³ when H ≤ 15; vampire 0 if it attacked this turn else −20; imp +30 with Flame else −20.
- + H + Power/2; own creatures + 2·Armour + Power; enemy creatures + 0.3·Armour.
- + 5 · (Mojo its equipment produces, `GetAutomaticMojo(1)` 0x191bf4 — not the tile it stands on) · H · (2·dominance)².
- + affliction score (`GetAIScoreForAfflictions`, 0x1918d8): Regen +max(20−H,5); Vengeance −5 (+2H if H ≤ 5);
  Flame −max(30−H,10); Infect −15; Stun −Power; Mighty +3; Berserk +(H−3); Snare −⌈Power/2⌉;
  Death Mark −max(10−H,5); Magic Shield +max(10−H,3); Cripple −10 for a creature with a special ability.
  Bad afflictions do not count on a regen cell.
- infected neighbours: −30 each (hero −50); an infected creature −20 per neighbour (hero −40).
- spectre ×2.5, king ×5.

Own creatures add their influence-map value; enemy monsters add a tile value (armour 1, regen 5, Mojo+2 7, card 9,
Mojo+1 3.5, negative tiles −1). Own total adds, enemy total subtracts.
Then + 0.1 · unspent Mojo, − 100 · monsters · ((dominance − 0.5)·2)⁵ when dominance > 0.6 with more than 4 monsters,
+ value of own runes (reduced by the threat on them), − enemy rune count − 0.75 · enemy rune value.

Rune values (`ValueThisRune`, jump table at 0x14fab0): Mojo runes 10/20/30 · A², card runes depend on the deck,
Bankers' Delight 40/A, all others 3.

## Influence maps (built once per AI turn)

`CTeam::PrepareForAIThink` (0x282498):
- dominance D = (own power / (own power + enemy monsters' health+2·armour) + own health+2·armour / (that + enemy power)) / 2
- spending drive A = average hand cost · min(hand, 3) / Mojo; from round 2, if D > 0.5, A ·= 1 − 2(D − 0.5).

`ProduceInfluenceMap_Threats` (0x1536fc): each enemy adds max(power,1) to cells within its attack range, half one step beyond.

`ProduceInfluenceMap_Monsters` (0x1539a0), per class:
- while the deck has more than 3 cards: Mojo+2 altars A²/(d+1) + 7, Mojo+1 altars A²/(d+1) + 3.5, card tiles 36/(hand+1)/(d+1);
- enemy hero: 75/(d+1) · 3D from round 2 (archers stay ≥ 2 away, artillery ≥ 3); with 2 cards or fewer left: 250 + 50 · 75/(d+1).

`ProduceInfluenceMap_Hero` (0x154264), per class:
- while the deck has more than 8 cards: Mojo+2 altars A³/(d+1) + 7, card tiles as above; a hero under 15 health is pushed
  away from every enemy by (3 or 4 − d) · (power/H)² · 300;
- enemy hero pull as for monsters (archer heroes keep 2 away), threshold 8 cards.

## Differences in the port

- Our moves are whole walks, not single steps; the threat charge is applied to the destination.
- Node budget (7.19): normal 4,000 / 2 s, hard 15,000 / 4 s, expert 40,000 (the original's pool) / 7 s.
  The search runs in a Web Worker (`src/engine/ai-worker.ts`), so the board keeps animating and a «الخصم يفكر…» badge shows.
- 7.19 speed-up: applyAction copies states with a flat copy instead of structuredClone (72 → 38 µs per node);
  `tests/clone-state.test.ts` checks it plays identical games and never touches the old state.
- Measured (16 games each, both sides on hard decks, vs our look-ahead hard AI): 8,000 nodes 5/16, 15,000 nodes 10/16,
  40,000 nodes 10/16. Above ~15,000 the turn's search is usually exhausted, so strength comes from the evaluation, not depth.
- Card-specific spell values (`ValueThisSpell`) are not ported; spells are judged by the board they leave.
- Settings → «أسلوب الكمبيوتر» can switch back to our look-ahead AI (7.12). Easy keeps its loose play.
