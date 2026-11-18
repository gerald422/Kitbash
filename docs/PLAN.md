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
- **Bladeguard arms out for now** (Josh, Nov 17: a bad example of a normal fit, Arm 10 especially). Mar Fil arms are
  the Assault and Intercessor ones; the reader leaves Bladeguard arms out (`reference.EXCLUDE`).
- **Bike parts later, with their own cuts** (Josh, Nov 16): bike torsos (Bike Chaplain body), riding legs (Outriders)
  and bike parts are left out of the Mar Fil searches until they have their own torso / legs cuts.

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
   - **It looks for the shape of the cut, never the geometry** (Josh, Nov 13 and Nov 17; this has slipped back
     several times). The only thing compared is the cut's mating surface against the part's surface. Never triangle
     counts, never the part's whole mesh compared with another, never "what touches", never sculpt detail. The mesh
     around the joint doesn't matter; only the mating surface and the roll do.
   - **Where to look** (Nov 17): a spot on a host (arm wrist, arm pad spot, legs shin spot, legs buckle) is looked
     for only within a shell round the joint that placed that host (its shoulder, its waist), at the distance it has
     on the reference part, a few mm either way. That only narrows where the shape is searched; what is compared
     doesn't change. It keeps answers in the right place (no axe on a shoulder). It does not make a different sculpt
     match: tried Nov 17, the Intercessor arm's near pad spot inside the shell sat flipped, so hosts stay sure only.
   - **Legs' turn** (Nov 17): the waist gives the place and tilt and its notch the turn; the belt buckle, which sits
     forward of the waist, then sets the turn about the waist (a longer lever). A buckle that disagrees with the
     notch by more than 3 deg is written and flagged; no buckle found, the notch alone.
     A near buckle can't set the turn, but it still says which way the legs face: legs whose round waist kept a file
     turn facing backwards (12 Intercessor legs are saved that way round) are turned round by it, flagged.
   - **Shins from the ankle balls** (Josh, Nov 17-18): the shin spot alone slides on the smooth shin (0.2-4 mm, up to
     30 deg, while still "sure"). The two balls on each ankle are one sculpt and fit themselves at any turn, so they
     are found as balls: a ball the size of his cut (the vote of every surface point facing out of a ball that size),
     the pair the reference's spacing apart (4.44 mm, within 0.04), near where the shin spot puts it. Their middle and
     the line through them set the shin; the shin spot then sets only the lean, the one turn left about that line.
     The reference's balls are found by the same search, so both are measured alike. Outer = the ball the shin spot
     points to.
   - sure: written;
   - near (look): written, flagged, shown flagged in the Squad Builder;
   - none: listed by cut (= the cut to make next).
   - **Hosts (torsos, arms, legs) take a sure match only** (Josh, Nov 16: a near match put an axe on a shoulder); a near
     host match is listed as a cut to make. Child parts keep "near = written and flagged".
6. **Hosts** (parts others hang off): the cuts write their anchors, **replacing** any old socket.
7. **Joints stored as numbers.** Each part's joint is stored as data; TIOW Inbox and the Squad Builder put the origin
   on the joint when the part comes in. Library STLs are not rewritten any more (the ~1,100 Mar Fil files moved on
   Nov 15 stay as they are: their sidecars record where they came from).
8. **Left = right mirrored** (notes 106).
9. **Hand fixes survive re-runs** (Save fit / `exact`), and are the only per-part placement data kept.
10. **Sharing:** the scripts, the per-maker recipes and the cuts (cut surfaces + anchor numbers), never the makers'
    STLs. Anyone runs them on their own downloads; nothing depends on folder structure. Josh's hand fixes, if shared,
    are keyed by the original file's checksum, not its path. (Check each maker's licence before sharing cuts.)

## The reference file (agreed Nov 16)

One blend holds every cut and every reference placement: **`~\Desktop\mar fil connectors\Kitbash reference.blend`**,
started by `kits/connectors/make_reference.py` (Mar Fil Torso 2 at the centre; Arm 2B R, Legs 1A, Bladeguard Helmet
3A, Jump Pack 1, Chain Sword 1 R, Shoulder Pad 1, Shin Pad 1 and Intercessor Back Pack 1, each
straight from the library at the library's position of Nov 16, no cuts). Josh redoes the cuts there from scratch;
the older cut blends (`arms a`, `wrist a`, `legs`, `marfil nck`, `mar back pack`, `mostof a marine`, and the
`marfil reference.blend` Claude built from them on Nov 16) are superseded once it is done. Rules, so a script reads it
without guessing:

1. **Parts are imported from the library as they are** (`D:\Kitbash Library`): no applied transforms, no edits to the
   mesh, the file name as the object name. So
   which file, and which frame, every part is, is known.
2. **Mar Fil Torso 2 stays at the centre, unmoved.** Every other part is sat where it should be by eye: that pose
   is the anchor.
3. **Each cut is its own object**, faces duplicated off the part (Shift+D, P), only the mating surface, in the
   maker's cuts collection, with exactly one of these names (which part it was cut on is read from where it lies):
   `torso shoulder`, `torso neck`, `torso waist`, `torso back`, `arm shoulder disc`, `arm pad spot`, `arm wrist`,
   `legs waist`, `legs shin spot`, `legs buckle`, `legs ankle ball` (`legs ankle ball outer right` / `inner right` /
   `outer left` / `inner left`: the exposed dome of each ankle ball, under the shin pad), `head neck`, `jump pack mount`, `backpack mount`, `weapon wrist`;
   optional `pad inside`, `shin pad inside`; also `arm wrist armour`, `legs back plate` (`legs backplate` reads the same). Case doesn't matter. A second cut of the same joint takes a label after the name (`arm wrist a`, `weapon wrist 2`): the fixed part names the joint, the rest is only a label. A `.001` Blender adds is ignored. Parts may also carry the maker's original file name (`81-Arm-2-R-A`): the reader keeps the library file whose mesh lines up with the object.
4. **Both sides of each joint are cut:**

   | Joint | host side | part side |
   |---|---|---|
   | shoulder | torso shoulder | arm's shoulder disc |
   | neck | torso neck | head's neck |
   | waist | torso waist | legs' waist |
   | back | torso back | backpack mount; jump pack mount |
   | wrist | arm wrist (so the anchor is found on other arms) | the hand's wrist on a weapon (or just the weapon placed in the hand: its wrist is what rests on the arm wrist cut; Josh, Nov 17: the axe, combi weapon and shield fitted as placed, no new cuts) |
   | pad | arm pad spot: one per arm type, a bigger section of the shape that type shares (Josh, Nov 18; the Assault one is sure on 35 of 37 Assault arms, Intercessor arms need their own) | the pad's inside (or just the pad placed: its inside is taken from where it rests) |
   | shin | legs ankle ball outer / inner, each side (they place the shin); legs shin spot (right shin), and one on the left shin under a mirrored shin pad placed by eye (Nov 17; the side is read from where it lies): it says where to look and sets the lean | the shin pad's inside (or just the shin pad placed) |   | buckle | belt buckle on the legs | |

5. **Two collections per maker and armour mark**: parts in `<Maker>` or `<Maker> <mark>` (`Mar Fil`, `Turtle Ninja
   Mk7`, `Springles`), their cuts in the same name + ` cuts` (`Mar Fil cuts`). Parts keep their library file name.
   Each other maker's part sits **against Mar Fil parts**: their arm on the Mar Fil torso, their weapon on a Mar Fil
   wrist, their torso (set to one side, anywhere: only relative poses are read) with Mar Fil arms, head, pack and
   legs on it.
6. **Each cut takes its joint from the reference part sat on it** (Nov 17): a host cut from the child placed on it
   (Chain Sword 1 R in an Intercessor arm's hand, Shoulder Pad 1 on it), a child cut from the host it sits on (the
   Captain's pack on a Torso 2 copy). So a new part can be set anywhere in the file, as long as a part whose joint
   is already known sits against it. An arm group also gets a Torso 2 copy with the arm on its shoulder, so that its
   spots are searched round the shoulder. `kits/connectors/add_reference_parts.py` adds such groups (backup first).

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

- For Mar Fil: the cuts in the reference file (see "The reference file"; it replaces the reference pairs asked for
  before: legs, an arm, a head and a jump pack on a torso, a back cut, a hand-wrist cut on a Mar Fil weapon on a
  Mar Fil wrist).
- Then per maker, against Mar Fil parts: the cuts in the table.
- Answers when a search lists parts it couldn't match.
