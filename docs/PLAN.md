# Kitbash plan (agreed with Josh, Nov 24 2026)

**This is the plan; follow it, and only it.** Agreed with Josh on Nov 24 2026. It replaces the Nov 16 plan
(`docs/archive/PLAN-to-2026-11-24.md`). Change it only when Josh decides something new, and date the change, the same
day.

**Josh: "I do not want to redo this."** So the plan lists every connector, joint and maker before any work starts.
A seat Josh has approved is never redone.

## Goal

Every part in scope seated correctly, on any host, whatever its maker. Each joint is done once.

## Method

1. **Claude seats each part as well as possible.** By cuts, by fits, or one at a time by hand: whichever gets it right.
   The seating method is the skill `kitbash-seat-by-shape` (`.claude/skills/kitbash-seat-by-shape/SKILL.md`):
   same-shape transfer of Josh's placements, pads carried by the joint, legs on adapter 3, the buckle turn, and cuts
   taken from seats.
2. **In small batches:** one kit, or about 10 parts of one type. Each batch is a Blender file:
   - every part is on its host, which is locked,
   - each part pivots on its joint,
   - each part records where Claude put it.
3. **Josh fixes the batch by eye** and saves.
4. **Claude reads his changes.**
   - If he made the same change to every part (for example, the same depth or turn across a kit), Claude says so and
     applies it to the rest of the kit.
   - Parts corrected that way go to Josh in the next batch, marked "pre-set". They are never written unseen.
5. **Josh's fixed placements are written to the library** (backup first), and nothing else.
   - That part's old fits are removed in the same write (per batch).
   - Claude then rebuilds the batch from the library alone and checks it matches Josh's file.
6. **Every part goes through this,** including parts that already have fits from the cuts (Mar Fil torsos, legs,
   heads, packs), so all of them are checked.

## Rules that stop roll-backs

1. **A written fix is Josh's.** It is marked in the sidecar, and nothing ever changes it again: no search, no re-run.
   Hand fixes made later in the app are kept the same way.
2. **A batch file Josh has touched is never regenerated or overwritten.** A redo is a new file.
3. **A joint has two halves, and each batch fixes only one half:** the host's socket or the part's fit. For example,
   one known-good pad on many arms fixes the arms' sockets; one known-good arm with many pads fixes the pads' fits.
4. **Stages run in order and don't reopen.** If a later batch shows an earlier part is off, Josh fixes it there and
   that one part is rewritten, not the stage.
5. **Any change to scope, connectors or method goes into this plan, dated, before work continues.**

## Makers

| Maker | In | Out |
|---|---|---|
| Mar Fil | everything in the stages below (the base body) | Captain with Jump Pack |
| Springles (Heresy) | arms, pads, heads, hands, melee, forearm armour, backpacks, toppers, accessories | |
| Springles - Weapons | weapons that carry their hands (two-handed held, pistols, melee), backpacks, heavy weapon, heavy weapon cables (30) | weapons without a hand |
| Marta (Tacticus, and Marta - Weapons) | arms, all legs, pads, weapons with a hand, accessories | torsos, heads, backpacks |
| Turtle Ninja (Tacticus and Heresy) | straight torsos, arms, legs, pads, heads, packs, weapons, accessories | torsos that lean (posed copies), "Rigging Required" folders |
| BBoosty (Heresy) | everything but torsos, servo arms included | torsos, weapons without a hand |
| CyberBrush (Tacticus) | everything but torsos, cloaks included | torsos, weapons without a hand |
| Redwarden (Tacticus) | torso, heads, pads, backpacks, weapons | in the library now: the Techmarine kit (1 torso, 8 helmets, 12 pads). Josh adds the weapons before the wrist and two-armed stages; the backpacks before the backpack stage |
| WarGame Exclusive (WargamesPrint) | heads, pads, forearm armour, shin pads, and its 20 unsorted files (sorted first) | |
| Bits | chest inserts, melee, two-handed held, waist adapters, wings and wing mounts (7) | |
| Bases | the last stage | |
| Old Style Space Knight | | all of it, for now |

**Out everywhere:**
- Terminators, Gravis, Phobos.
- Weapons without a hand.
- Aquilas, purity seals and scrolls (renegade chapter, `_hidden.txt`).

**Mirroring:**
- Right parts are placed, and a left part is its right one mirrored.
- Every left-only arm sculpt gets a mirrored right version.
- Every two-armed weapon gets a mirrored version.

## Physical connectors (printed parts that sit between two parts)

| Connector | Between | Per part, only these vary | State |
|---|---|---|---|
| **Shoulder spacer** (one spacer, for every arm and two-armed weapon of every maker) | torso shoulder and arm | how deep the spacer goes into the arm, and the arm's turn | exists (the Springles spacer) |
| **Pauldron guide** (the pad connector) | arm and pad | where the guide sits on each arm; each pad's seat in the guide | exists |
| **Waist adapter 3** | torso waist and flat-topped legs (Marta, Turtle Ninja) | | exists |
| Neck, backpack, backpack topper | torso and head, torso and pack, pack and topper | **joints, not printed parts** (agreed Nov 24) | |
| Bionic hip connector | legs and a bionic leg | **parked: arrives next week, its own plan then** | |

## What is made: sockets (on hosts) and fits (on the parts that hang on them)

| Host | Sockets it gets | Parts that fit on them |
|---|---|---|
| Torsos (Mar Fil, Redwarden, Turtle Ninja straight ones) | `Shoulder R` (`L` = mirror), for the spacer; `Neck`; `Back`; `Waist`; `Chest Insert` (some torsos); `Neck Guard`, the collar (some torsos); the cloak (new socket) | spacer; heads; backpacks and jump packs; legs or adapter 3; inserts; collars; cloaks |
| Shoulder spacer | the arm seat | every right arm and every mirrored right version of a left-only arm; every two-armed weapon and its mirrored version |
| Arms | `Pad R`, where the pauldron guide sits; `Hand R`; `Forearm R` (`L` = mirror) | pads, by their seat in the guide; weapons with a hand, hands, shields, two-handed held weapons; forearm armour |
| Weapon hilts (some) | `Weapon Head` | weapon heads |
| Backpacks | `Back Top`; `Servo Arm` (some backpacks only) | toppers; servo arms |
| Backpack toppers (some) | `Servo Arm` | servo arms |
| Jump packs | `Wing Mount R` / `L` | wing mounts, then wings on them |
| Heavy weapons | `Cable`, where the cable plugs in (its other end goes to the backpack) | heavy weapon cables |
| Waist adapter 3 | `Flat Waist` | Marta and Turtle Ninja legs |
| Legs (all) | `Shin R` / `Shin L`; `Buckle`; `Hip R` / `Hip L`; `Belt Back`; `Base`, where the legs stand | shin pads; buckles; accessories; accessories; bases |

**Accessories:** the parts that sit on the legs' and torsos' accessory sockets are stage 10, before bases (agreed
Nov 24). That means hip items, belt-back items, hip plates, holsters, buckles, loincloths, tabards and trophies.
Nothing hangs off them, so they can't cause rework.

## What is in each batch file (so every fix is judged against its neighbours)

Every batch shows the part being fixed **in place on a real marine**, never on its own:
- **Host:** the approved part it sits on, locked. For example, the approved torso and spacer under an arm.
- **Check pieces:** known-good parts on the other side of the joint, locked. For a **socket** batch, Josh moves the
  check piece to show where the socket should be. That move becomes the host's socket.
- **Neighbours:** the parts around it that the seat has to clear, such as the torso when seating pads.
  - Approved neighbours are shown solid and locked.
  - Neighbours not yet approved are shown faint, for context only, and are never edited.

The known-good parts come from **the reference marine**: Josh's own placements in the main reference file (Torso 2, Arm
2B R, its pad and weapon, head, backpack, legs, shin pads), plus the spacer and the pauldron guide he places in stage 1.

| Stage | Being fixed | Host (locked) | Check pieces and neighbours |
|---|---|---|---|
| 2. Torsos | the torso's sockets | the torso | the reference arm on the spacer (both sides), head, backpack, legs (or adapter 3 and a Marta legs), insert, collar, cloak, each on its socket |
| 3. Arms | the arm's depth and turn on the spacer | an approved torso and the spacer | the other arm (its mirror); faint: the reference pad in the guide, so the pad's clearance of the torso shows |
| 3. Two-armed weapons | depth and turn on the spacer | an approved torso and the spacer | faint: the head and the pads |
| 4. Arms' sockets | `Pad R`, `Hand R`, `Forearm R` on each arm | the approved arm on its torso | the reference pad in the guide, the reference weapon in the hand, reference forearm armour |
| 5. Pads, weapons, forearm armour, weapon heads | the part's fit | the reference arm on the torso (the hilt for heads) | the torso and head, solid |
| 6. Heads, packs, inserts, collars, cloaks | the part's fit | an approved torso | the reference arms and pads |
| 6. Packs' and toppers' sockets | `Back Top`, `Servo Arm` | the approved pack on its torso | a reference topper or servo arm on each socket |
| 6. Toppers, servo arms | the part's fit | the reference pack on the torso | the reference arms and pads |
| 7. Adapter 3 and the legs | the adapter's seat, then each legs' waist | an approved torso, then the torso and adapter | the reference legs beside it |
| 7. Legs' sockets | `Shin`, `Buckle`, `Hip`, `Belt Back`, `Base` | the approved legs on the torso | a reference shin pad, buckle, hip item, belt-back item and base |
| 8. Shin pads | the pad's fit | the reference legs | the other shin pad (its mirror) |
| 9. Wings; heavy weapon cables | the wing mount and wing; the cable | the approved jump pack; the heavy weapon on the reference arm | the torso; the backpack, where the cable ends |
| 10. Accessories | the accessory's fit | the reference legs or torso | the neighbouring accessories, faint |
| 11. Bases | the base's fit | the reference legs | |

**Order this needs:** stage 1 must give the reference marine, including the spacer and the guide placed by Josh.
Stage 2 can't check a torso's shoulder without it.

## Order of stages

Each stage is only possible once the one before it is fixed.

0. **Tools:** the seat-by-shape scripts move into the repo (`kits/seat/`, local paths removed), and the batch file
   builder and reader are made. Then one trial batch.
1. **The reference marine:** Josh places the spacer on the reference Torso 2 and Arm 2B R on it, and checks the guide
   and pad on that arm. With the rest of his reference placements, this gives the known-good check pieces for every
   batch (the section above).
2. **Torsos:** all their sockets.
3. **Arms** on the spacer: depth and turn. Then two-armed weapons.
4. **Arms' sockets:** `Pad R`, `Hand R`, `Forearm R`.
5. **Pads, weapons with a hand, forearm armour, weapon heads.**
6. **Heads, backpacks, jump packs, toppers, servo arms, inserts, collars, cloaks.**
7. **Legs:** adapter 3, the waists, then the legs' sockets.
8. **Shin pads.**
9. **Jump pack wings, and heavy weapon cables.**
10. **Accessories.**
11. **Bases.**

## Before this plan: history, and the issues the old method caused

The old documents stay for reference only. Never follow them:
- the previous plan (Nov 16): `docs/archive/PLAN-to-2026-11-24.md`;
- older plans and open lists: `docs/archive/`;
- every piece of work so far, one note each: `docs/notes/INDEX.md`;
- the review written before this plan: `docs/archive/REVIEW-2026-11-24.md`.

**What the old method (search-only runs written straight to the library) caused:**

1. **"Sure" was taken as "right".** It only meant the cut's shape matched. Marta shoulders were "all sure" with the
   arms turned wrong.
2. **Nothing checked the search against Josh's own placements.** On Nov 24 the reader was found to read the seat file
   30-250 mm out. Every pad joint from Josh's seats was wrong, and the checks hadn't caught it, because they used the
   pipeline's own output.
3. **Partial methods were written to the library before the chain was proven.** For example:
   - the Nov 15 no-cut fits are still in the library;
   - Mar Fil run 25 (Nov 19) had to be redone as run 26 the next day;
   - the Nov 20 pad joints were left in an old frame when the guide replaced it.
4. **Old and new fits are mixed in the library,** from at least four methods, so a fit can look fine and come from a
   dropped method.
5. **Round joints took their turn from the file,** and the per-maker conversion the plan called for was never built.
   So every Marta and Turtle Ninja arm was turned wrong.
6. **The pad search used the whole pad inside,** close to a bowl, which matches itself at any turn: 9-13° off, or not
   found.
7. **Plan steps were skipped silently.** The spacer joint and the frame conversion were in the plan and never built,
   and nothing said so.
8. **The plan wasn't updated as the method and scope changed.** Turtle Ninja went out and back in, Marta arms went out
   and back in, and the guide arrived. Decisions made in chat were lost between sessions.
9. **Inputs were spread over 7+ blend files,** and only two were read.
10. **Long overnight runs went on for hours on a bug** before anyone looked at a result.

How this plan prevents them: Josh's eye on every part before it is written, small batches, approved seats never
redone, one plan updated the same day.

## Status

| Stage | State |
|---|---|
| 0. Tools | done Nov 24 (notes 121): `kits/seat/`, the batch builder and reader; the trial batch is the stage 1 file |
| 1. The reference marine | done Nov 24 (notes 122): Josh's fix (spacer 2.085 mm into the torso) written: Torso 2 Shoulder R/L, Arm 2B R on it and its Pad R/L (the guide), Shoulder Pad 1 in the guide. Other pads and arms stay in the old pad frame until stages 4-5 |
| 2. Torsos | every Mar Fil torso but the Bike Chaplain, the Redwarden torso and all 55 Turtle Ninja straight torsos written (notes 123-132). Batches of about 20-25 parts (Josh); once written, a batch's files go to the Recycle Bin (his standing OK; never his reference or working files). Chest Insert and Neck Guard: later, certain torsos only (Josh). The Bike Chaplain chest written (notes 133, 134). The 17 kept cloaks and Torso 2's Cloak socket written (notes 134-136; the Mar Fil cape and 6 cloaks removed by Josh, 2 scaled by him). With Josh: the Cloak socket on every other torso, batch files dated 2026-11-25 (TN 1-3, Mar Fil; each starts on its Back; notes 137); the 27 Mar Fil torsos hidden in the builder written as built (notes 137). The unused cloaks and the cape are hidden |
| 3. Arms | with Josh: the first batch, `03 Stage 3 - Mar Fil Assault right arms (2026-11-25).blend` (23 arms, each from its old seat; notes 137) |
| 4-11 | not started |
