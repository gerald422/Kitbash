# The placement plan

**Agreed with Josh, Nov 16 2026. This is the plan; follow it.** It replaces the earlier connector work order (item 5
of the old open list), which is in `docs/archive/` as history only: don't pick anything up from there. Where this file
and an older note disagree, this file wins. Change it only when Josh decides something new, and date the change.
Open items that are not part of the plan: `docs/OPEN.md`. How the plan was reached: `docs/notes/108`.

## Aims

1. **Easy to add parts.** New STLs go in through a `.bat` / Blender script with no Claude: sorted, matched, placed.
   About 80% right on their own is accepted; Josh moves the rest by hand.
2. **Consistent placement across makers and parts.** Any part of any maker sits right on any host.

## Scope for now

- **In:** Mar Fil is the base body. Plain arms: **Mar Fil and Springles (Heresy)** (Springles' arms were already
  moved by Josh; the originals are set in `~\Desktop\Operation Marine\3rd attempt finalising actual.blend`).
  Weapons with a hand, two-armed weapons and customisation from every maker. Marta legs (unique poses).
- **Out for now:** Terminators and Gravis (they would need their own base fits; when they come, the same method),
  Marta Phobos, Springles' guns (they carry the hands; "not yet"), Marta heads, plain arms of Marta, Turtle Ninja,
  BBoosty and CyberBrush. Weapons without a hand are not used. Turtle Ninja: only the straight pose of each torso,
  nothing from "Rigging Required" folders.
- **Later:** accessories, including the legs' rear belt plate.

## The method

1. **Intake.** A recipe per maker (`add_creator.py` style) sorts each new file by type. If a maker's files don't
   share one frame, Josh moves them to the same centre spot on import (as he did for the Springles arms).
2. **Cuts.** Josh cuts **only the mating surface** of each joint, once, on a reference part. The rest of the mesh
   doesn't matter: never take "whatever touches" or sculpt detail as a connector.
3. **The Mar Fil reference.** Every reference part is sat **against a Mar Fil part** in its cut blend: a Turtle Ninja
   torso with a Mar Fil arm, head, pack and legs on it; a Springles arm with a Mar Fil weapon in its hand and a Mar
   Fil pad on it; a Marta weapon on a Mar Fil wrist. One ruler for every maker: it sets the joint, the maker's frame
   against Mar Fil's (so the roll from the file converts) and the maker's scale. A cut blend template with the Mar Fil
   host parts laid out makes this import, sit, cut, save.
4. **Anchor = Josh's placement** of the reference part on its host in the cut blend. No library fit is used.
5. **Search.** Every part of the type is searched for the cut. The shape gives the place and tilt; **the roll comes
   from the file** (the maker's own frame, converted by the Mar Fil reference). Never from a part's old fit.
   - sure: written;
   - near (look): written, flagged, shown flagged in the Squad Builder;
   - none: listed by cut (= the cut to make next).
6. **Hosts** (parts others hang off): the cuts write their anchors, **replacing** any old socket.
7. **Joints stored as numbers.** Each part's joint is stored as data; TIOW Inbox and the Squad Builder put the origin
   on the joint when the part comes in. Library STLs are not rewritten any more (the ~1,100 Mar Fil files moved on
   Nov 15 stay as they are: their sidecars record where they came from).
8. **Left = right mirrored** (notes 106).
9. **Hand fixes survive re-runs** (Save fit / `exact`), and are the only per-part placement data kept.
10. **Sharing:** the scripts, the per-maker recipes and the cuts (cut surfaces + anchor numbers), never the makers'
    STLs. Anyone runs them on their own downloads; nothing depends on folder structure. Josh's hand fixes, if shared,
    are keyed by the original file's checksum, not its path. (Check each maker's licence before sharing cuts.)

## The cuts

| Host / part | Cut | How many |
|---|---|---|
| Torso (host) | shoulder (left = mirror), neck, back, waist | per armour mark per maker (torso shapes differ by mark) |
| Arms (Mar Fil, Springles) | shoulder disc places the arm; pad spot, wrist anchor, armour spots found on the arm | per maker |
| Legs | waist places the legs; shin spot and belt buckle found on the legs | per maker (legs don't differ by mark) |
| Shoulder pads | the pad's inside | per maker |
| Shin pads | the pad's inside | per maker |
| Weapons with a hand | the wrist on the hand (the arm only has the anchor point) | per maker |
| Two-armed weapons | shoulder disc | per maker |
| Heads | neck | per maker |
| Jump packs | mount | per maker |
| Backpacks | the torso's back | per maker |
| Hip plates, trophies | spots set once relative to the buckle, which a cut finds on the legs | per armour type per maker |
| (later) belt-back accessories | the legs' rear belt plate | per maker |

If a search shows a kit that doesn't match (Mar Fil's Veteran / Bladeguard neck, Captain with Jump Pack legs), that
kit gets its own cut: the search's "none" list says so.

## Order

1. **Mar Fil first, proved on a small set before any library run.**
   - The proving set: one full Mar Fil chain (torso, legs, arm, shoulder pad, weapon, backpack, shin pad, head, jump
     pack) and one cross-maker chain (a Turtle Ninja torso, a Springles arm, a Marta weapon), right by the numbers
     and by Josh's eye.
   - Only then is a maker's whole library run, **once**.
2. Then the other makers.
3. Then the single drop-in `Add parts.bat`: sort, seat, store joints, refresh the page index, report what was
   flagged and what matched nothing. Per-maker configs, not Mar Fil's file hardcoded.

## What has to change from what exists (Nov 16)

- `kits/connectors/seat.py`: anchor from Josh's placement in the blend (not the reference part's library fit); roll
  from the file (not the part's old fit, the `near` turn); host-side cuts (pad spot, wrist, shin spot) **replace** old
  sockets (today they are only added where a part had none, and the shin spot is never written); the Mar Fil
  reference read from each cut blend; per-maker configs; joints written as numbers instead of moving STLs.
- TIOW Inbox, the Squad Builder (and Finalise): origin on the joint at import, from the stored joint.
- `kits/connectors/cuts_needed.py` / `docs/cuts-needed.md`: regenerate to this plan (torso cuts per mark, Springles
  arms in, the hand's wrist per maker, the Mar Fil reference).
- Two-armed weapons with a disc on both arms: prefer the disc on the side the file says (44 Mar Fil ones took the
  left disc).
- Every fit written on Nov 15 from old-fit examples or library anchors is redone from the cuts: Mar Fil weapon hands
  289, backpacks 29; BBoosty 22, Turtle Ninja 10, Marta Weapons 2, Bits 34 hand fits; the 44 two-armed weapons.
- **Retired, don't use for placement:** `kits/connectors/hands.py` and seat.py's "placed" connectors (an example
  placed by its library fit, its side = what touches the host), the per-hand-sculpt "designs" (notes 104-108).

## What Josh provides

- For Mar Fil: the reference pairs sat on their host in blends (legs, an arm, a head and a jump pack on a torso; his
  pad and shin pad blends are done), a back cut on a pack sat on a torso, one hand-wrist cut on a Mar Fil weapon sat
  on a Mar Fil wrist.
- Then per maker, against Mar Fil parts: the cuts in the table.
- Answers when a search lists parts it couldn't match.
