TIOW -> Blender bridge
======================

Send an STL from TIOW-FTRP and it is imported into whatever Blender scene is
open: selected, active, and ready for Part Sockets.

The two sides only share a folder:
  %LOCALAPPDATA%\TIOW-FTRP\local-data\blender-inbox
TIOW writes one small request file there per item. Blender checks the folder
twice a second, imports the STL and deletes the request.


1. Blender (once)
-----------------
Edit > Preferences > Add-ons > Install from Disk > tiow_inbox.py, then tick
it. Its panel is in the N sidebar, Sockets tab > TIOW Inbox (listening
on/off, placement, last import).


2. TIOW-FTRP (once, and again after any TIOW update)
----------------------------------------------------
Close TIOW-FTRP. Open a terminal in this folder and run:

    node apply-blender-bridge.mjs

Then start TIOW-FTRP again. The originals are kept beside each changed file as
*.pre-blender-bridge.

Do this BEFORE connecting your library folders in TIOW: part types are worked
out when TIOW first adds a file to a catalogue.

To use the part types from your library instead of the built-in list:

    node apply-blender-bridge.mjs --library "E:\Library\_library.json"

Re-run that whenever you change partTypes in _library.json.

    node apply-blender-bridge.mjs --check   shows what it would change
    node apply-blender-bridge.mjs --undo    puts the originals back

If TIOW's author changes those files, the patch stops with "anchor found 0x"
and changes nothing.


Part types
----------
A file's type (TIOW's Item type, and the Blender collection it lands in) comes
from the nearest folder named after a part type: Arms, Heads, Chests, Legs,
Backpacks, Jump Packs, Shoulder Pads, Knee Pads, Melee, Pistols, Heavy Weapons,
Two-Handed Guns, Two-Handed Melee, Shields, Accessories, Bases,
Mechadendrites, Servo Skulls, Trophies, Seals, Grenades, Hands, Hand-less
Weapons, Two-Handed Held, Backpack Toppers, Heavy Weapon Cables, Cables, Pack
Fins, Bikes, Bike Parts, Servo Arms, Adapters, Forearm Armour, Cloaks.

Creator spellings work too: Helmets, Torsos, Arms-RawStl-Mirrored,
KneePad-RawSTL, ShinPads-RawSTL and PuritySeals-RawSTL are all
recognised. Words like RawStl, Mirrored, Sergeant and Support at the end of
a folder name are ignored.

Files in no matching folder fall back to TIOW's own filename rules, so a
generic "Weapons" folder stays "Weapons" until you sort it.

Using it
--------
In TIOW, with the item's folder connected:
  - double-click a card, or
  - right-click a card > Send to Blender, or
  - use the Send to Blender button in the details panel.

The toast says "Sent to Blender" when Blender is listening. It says "Queued"
when Blender isn't open or the add-on is off.

In Blender, each part:
  - goes into a collection named after its part type (Arms, Pistols,
    Two-Handed Guns...). Cycle Variant uses that collection as its pool.
  - is centred on the 3D cursor. The origin stays where the STL had it;
    Part Sockets sets the real one.
  - comes in 1:1 (1 STL unit = 1 Blender unit), the same as importing by
    hand, so it matches the parts already in your files.
  - stores its source path in the custom property tiow_src.
  - can be removed again with Ctrl+Z (one undo step per import).

Requests wait while you are in Edit Mode, and import when you Tab back out.
Requests older than 5 minutes are dropped, so old clicks don't show up the
next time you open Blender.


Auto-snap (TIOW Inbox 1.2, needs Part Sockets)
----------------------------------------------
Select the model you are building, then send a part. It goes onto the free
socket of its joint in that model:

  Arms (power fists too)                         -> Shoulder R / L
  Two-Handed Guns, Two-Handed Melee, Heavy Weapons -> Shoulder R, and clear Shoulder L
  Pistols, Melee, Shields (Mar Fil's has a hand)  -> Hand R / L (on the arm)
  Legs -> Waist      Heads -> Neck      Backpacks, Jump Packs -> Back
  Pack Fins -> Pack Fin R / L (on the jump pack)   Bases -> Base (under the legs)
  Shoulder Pads -> Pad R / L (on the arm)   Knee Pads -> Shin R / L (on the legs)
  Backpack Toppers -> Back Top (on the backpack)
  Heavy Weapon Cables -> Cable (on the heavy weapon)
  Belt bits: see "Pads and belt bits" below

R or L comes from the part's name or folder (77-Arm-1-R-B, Arm_L_03,
LeftOrientated). With no side in the name it tries R, then L.

  - Select a part that is already on the model and send another of the same
    kind: the new one takes its place. Double-clicking through arms in TIOW
    swaps them on the model one after another.
  - Anything the outgoing part was holding (a pistol in its Hand socket) moves
    across to the new part.
  - The outgoing part is deleted if it came from TIOW (send it again to get it
    back), or sent to its Dressing Room home if it is one of your own parts.
    Preferences > TIOW Inbox > Swapped-out Part changes this.
  - Hidden parts on a socket (variants you have parked there) don't count as
    taking it.
  - Nothing selected: the part just lands at the cursor, as before.
  - Ctrl+Z undoes the whole import, snap and swap in one step.

The table lives in _library.json under "joints"; Blender reads it from the
Library folder the STL came from, so you can edit it without re-patching TIOW.
"jointAliases" lets library parts snap onto files set up with the old names
(arm__Torso_r counts as Shoulder R, and so on).

Settle: a "settle" entry slides the part along a socket axis after snapping
until it touches the model (the part the socket is on, the part that hangs
from, and anything else on that socket), then "sink" presses it in that
far (mm) so a bit printed with its host merges into it. The fit only has to
be roughly right - across the surface and the angle - because the distance
to the surface is measured each time.


Building a marine from scratch (TIOW Inbox 1.7)
-----------------------------------------------
The torso is the root. Send a torso with nothing selected, then select it and
send the rest; select an arm to give it a weapon, the jump pack for fins.

  Torso:  Shoulder R, Shoulder L, Neck, Back, Waist
  Legs:   Base (at the legs file's origin), Hip R, Hip L, Belt Front, Belt Back
          (on the belt, 1.11), Shin R / L (found on import)
  Arms:   Hand R or L, Forearm R or L (B arms), Pad R or L (copied on import)
  Jump packs: Pack Fin R, Pack Fin L

Every Mar Fil file of the Assault Marines kit (AssaultMarines-V2) has a
<part>.sockets.json beside it in D:\new cults with its sockets, its fit and its
part type. The type in that file wins over TIOW's, so a power fist arrives as an
arm and a two-handed axe as Two-Handed Melee whatever folder TIOW read.

Where the fits came from:
  - Torsos: your sockets on 23-Torso-2 (all six torsos share the joints).
  - Legs: your Chest-to-legs sockets from Legs donrrr ("posing for claude"):
    the torso's front lip on the stomach plating. 28 uses the average of the
    others. Mirrored legs are the mirror of their original.
  - Right arms: your origins and wrist sockets. Left arms are mirrors of the
    right B arm of the same number, so their sockets are your right ones
    mirrored.
  - Melee and pistols: your origins; the ones not in your file use Mar Fil's
    shared grip (your bolt pistol fit). LeftOrientated files are mirrors.
  - Two-handed weapons, jump packs and fins: Mar Fil's kit position.
  - Helmets and heads: your 1-Helmet-1 fit for the whole folder.

A two-handed weapon comes with both arms: it snaps to Shoulder R and sends
home whatever is on Shoulder L. An arm sent onto either shoulder later
replaces the two-hander.

The sockets file is merged, never replaced: anchors the add-on copied or you
clicked, and fits you saved, stay put.


Hands are hands (TIOW Inbox 1.8)
--------------------------------
Any hand-held part goes onto any arm, from any kit, with nothing set up for
that part or that arm. Both ends of the wrist are found from the shape:

  Arm with no Hand socket: the wrist face at the far end of the arm. Origin
    at its centre, Y up the forearm, and the roll from where the forearm's
    armour sits round the wrist (on your Assault Marine arms that matches
    your own wrist sockets to about 1 degree, except the round-wrist R-A arms,
    where it is within 10-30 degrees of yours).
    A Mar Fil '<name>-Mirrored' arm takes its roll from '<name>' mirrored:
    Mar Fil turned the forearm on some of those, so its armour points the
    wrong way for the hand.
  Hand-held part with no Hand fit: the wrist stump (a round flat cap on a
    short neck) with a fist behind it. Mar Fil's assault fist comes with the
    add-on and is fitted behind every stump on the part at every roll; the
    best is the hand, and the fist gives the roll, so a weapon held at a
    different angle in the fist still comes out the right way up. The stump
    sits 0.19 mm into the arm's wrist face, as in your placements.

Measured against your own placements of all 82 Assault Marine hand-held parts
on all 60 arms (rules only, nothing from your file): half come within 5 degrees
and 0.25 mm of where you put them, 9 in 10 within 8 degrees and 0.4 mm. The
worst (up to 30 degrees) are on the round-wrist arms named above.

R or L: from the name or folder as before ('-Mirrored' counts as left).
With neither, the fist decides (a left fist doesn't fit a right hand).

Both are worked out once (a second or a few per part) and saved in the part's
.sockets.json, marked "ruled", so the next import is instant. Sockets and fits
you made yourself always win. Not covered yet: power fists (they replace the
hand, so they snap as arms), and two-handed weapons (kit position as before).

Veteran Squad and Bladeguard (TIOW Inbox 1.9)
---------------------------------------------
Both kits are exported in the same frame as the Assault Marines, so:

  Chests: the Assault Marine torso's Shoulder R/L, Neck, Back and Waist.
  Legs (the Body folders): seated like your Assault Marine legs (the
    orange version you picked): the closest of your AM legs' waists is
    matched onto each legs piece and your torso placement carried over,
    with belt anchors (1.11). Each mirrored legs piece takes the exact
    mirror of its original's seat. Base at the legs file's origin.
  Arms, power fists, Bladeguard's sword arms (159/160) and the Vet gun arms
    (97/98): kit position, joint on the inner face of the shoulder (x 5.568,
    as on your Bladeguard arms). Hand R/L by the wrist rule.
  Melee, pistols, the Vet one-handed guns (Gun-5, Combi-4, 120) and the
    Bladeguard shields: no fit saved, the hand rule places them.
  Two-handed guns, heavy weapons, Bladeguard two-handed melee: kit position
    on Shoulder R, clearing Shoulder L.
  Heavy weapon cables (122/124/126/128 and their NewVersions): their own
    joint, Cable, on the heavy weapon (kit position).
  Backpacks: kit position on Back; each has a Back Top socket (your topper
    socket from Vet backpack 1). Toppers (BackPackUpdate-1 5-13): their own
    joint, Backpack Toppers -> Back Top.
  Helmets and heads: one Neck fit per folder (the Assault Marine helmet
    matched onto the kit's helmet 1).
  Vet shin pads: Shin R / Shin L fits from the Techmarine rig pad; Vet
    pauldrons: Pad R (R-A..M) and Pad L (L-A..M) from your 62-on-76 example.
    Bladeguard pads keep the 1.6 folder fits.

Pauldron anchors on Bladeguard arms: their shoulders are each sculpted
differently, so the copied anchor is rougher (0.19-0.41). The status line
says "rough match" above 0.25: check the pauldron, and if it sits wrong
click that arm's three points (other arms in the folder then copy yours).

All of this is in each file's .sockets.json in D:\new cults (merged, nothing
you saved is replaced).


Intercessors V2 (TIOW Inbox 1.10)
---------------------------------
D:\new cults\Intercessors-V2. The chests are the Assault Marine torso at
every joint (0.02 mm), so the same joints and the same ways of placing:

  Chests: the Assault Marine torso's Shoulder R/L, Neck, Back and Waist.
  Legs (and the Legs-Mirorred copies): seated like your Assault Marine
    legs, as for the Vets, with belt anchors; Base at the legs file's origin.
  Rocks: Bases on the legs' Base, where Mar Fil put them.
  Arms: joint on the inner face of the shoulder; Hand R/L by the wrist rule.
  Hands (new part type "Hands"): the bare hands go on the arm's Hand
    socket like anything held. Each hand has a Grip R or Grip L socket at
    its wrist.
  Hand-less weapons (new part type "Hand-less Weapons", Mar Fil's -NoHand
    files): go on a hand's Grip, held just as Mar Fil's own hand + weapon
    versions hold them. The hand-less bolters sit as in the held bolters.
    Select the hand first. A weapon goes in either hand as it is (not
    mirrored), as in Mar Fil's left-hand versions.
  Melee and pistols with a hand: the kit's wrist (the same as the hands).
  Hand 10 (a hand holding a shield): Shields, by the hand rule.
  Held bolters (Bolter-Individual 144-178): Pistols, on their own wrist
    (the hand is at the stock end).
  Arms with a bolter (Bolter-Individual 125-143) and the one-sided heavy
    weapon arms (right 188, 189, 191, 193, 201, 203, 205; left 189-L,
    201-L, 202, 204): Mar Fil exported these 2-5 mm off the shoulder and
    turned 6-25 degrees, so each is placed by its shoulder disc (the flat
    round inner face): centre on the joint, face flat on the chest. They
    come in right/left pairs exported together as one turned unit (125-R
    with 125-L, 131 with 131, 137 with 137, 188/189 with 189-L, 201 with
    201-L, 203 with 204), so both arms of a pair get the same correction
    and keep the pose Mar Fil gave them together; both discs land within
    0.1 mm of their joints. The right ones carry a Cable socket.
  Two-handed bolters (Bolter-Dual) and two-handed heavy weapons: kit
    position on Shoulder R, clearing Shoulder L; heavy ones have a Cable.
  Cables and belts: Heavy Weapon Cables on Cable (kit position).
  Helmets and heads: one Neck fit (your Assault Marine helmet matches the
    Intercessor helmet to 0.02 mm).
  Backpacks: kit position on Back.
  Shin pads: Shin R / Shin L from the Techmarine rig (same pads, 0.03-0.05).
  Pauldrons: Pad R from your 62-on-76 example; left by mirroring.
  Not placed: Desolator 213-218 (SuperFrag, Superkrak, Vengor launcher).

New in 1.10 for every kit: when you select a part and send something, that
part's own sockets come first (select the left arm and send a pauldron: it
goes on that arm).


Every kit fits every kit (TIOW Inbox 1.11)
------------------------------------------
Any kit's part goes on any other kit's body: an Intercessor V2 shin pad on
Assault or Vet legs, any torso on any legs, a Chaplain arm on an Assault
torso. Every kit is set up to the same joints:

  Torso: your Assault Marine torso's sockets (all 33 chests checked: the
    same at every joint).
  Legs on the Waist: seated like your Assault Marine legs.
  Arms on the Shoulder: the flat round inner face of the shoulder centred
    on the joint, flat on the chest (all 90 of your Assault arm fits are
    within 0.3 mm of that).
  Hands: the wrist rule on arms, the hand rule on anything held. Your own
    Assault wrist sockets and weapon fits agree with the rules to 0.5 mm;
    the roll about the wrist can differ by a few degrees (5-29 degrees on 8
    of your 60 Assault arms), so a weapon moved between kits may need its
    roll touched up.
  Heads on the Neck: your Assault helmet's seat (its neck ring matched onto
    each head). Packs on the Back: Mar Fil's export position, which is
    exactly your Assault jump pack fits.
  Pads: the shin and pauldron anchors, found on every kit's legs and arms.
  Belt: Hip R, Hip L, Belt Front, Belt Back on every legs piece.

Tested in Blender with 6 marines built from mixed kits; every joint meets
as closely as within one kit. Two things changed for parts you already have:

  Belt anchors. The hip sockets the legs had came from your Assault scene
    and sit inside the waist pointing up or down, so a belt bit sent there
    came in turned and slid about 10 mm. Every legs piece (Assault, Vet,
    Bladeguard, Intercessor, Chaplain, Outrider, Techmarine) now has all
    four belt anchors on the belt, made the way a clicked anchor is (out of
    the surface, up). Anchors you clicked yourself are kept.
  The Chaplain head sits on your helmet seat (Mar Fil's export is 4.5
    degrees off it).

Also new in 1.11:
  Pads, hands and hand-less weapons go on the side you pick: select a left
    shin anchor (or a left arm, or a left hand) and send a right-only pad or
    a hand-less weapon from a "(Right)" folder - it goes on the left
    (mirrored if it's a pad).
  The wrist rule looks past a flat bit that isn't round when a wrist-sized
    round face sits just behind it (the Chaplain's rosary cross hid his
    left wrist). On all 254 kit arms nothing else changed.
  New part types: Bikes, Bike Parts, Cables, Servo Arms, Mechadendrites.


Chaplain with Jump Pack (TIOW Inbox 1.11)
-----------------------------------------
All Mar All the time\ChaplainWithJumpPack (1). The four poses (A-D) were
each exported on a turned torso; the turn of each is worked out from its two
arms' shoulder faces (they agree to 0.01 mm), so:

  Chest: the Assault torso sockets. Legs A-D: seated like your Assault legs;
    Base = its rock (Bases, as exported). Arms 13-20: on the shoulder as
    posed for their legs (right A goes with left A, and so on), Hand R/L by
    the wrist rule. Crozius (Melee, right) and Absolvor pistol (Pistols,
    left): the hand rule. Head: your helmet seat. Jump pack: Back, export
    position; exhaust: Backpack Toppers on its Back Top.
  Book, badge, holster, grenade: the legs carry an anchor at each of Mar
    Fil's spots (book and grenade Belt Back, badge Belt Front, holster Hip
    L); send them with the legs selected and each lands exactly where Mar
    Fil put it. On other legs they go on the belt anchors like any belt bit.
  Pads: shin pads and pauldrons by the shared anchors (0.03-0.05).


Outriders (TIOW Inbox 1.11)
---------------------------
All Mar All the time\Outriders (1). Rider, arms and bike were exported
together in the bike's frame:

  Torsos (13): the Assault torso sockets.
  Legs A-F and the mirrored B-F: seated like your Assault legs, with a Bike
    socket and a Base socket at the bike's origin.
  Bike: 19-Body-1 (new type Bikes) goes on the legs' Bike socket, as
    exported under the rider. It carries one socket per bike part (new type
    Bike Parts: 21 front body, front wing, both wheels, both exhausts, both
    handlebar ends, and the bolter or plasma twin guns), each saved for that
    part, so a bike part finds its own place whatever you select.
  Base 90x52: under the bike, wheels on it.
  Arms: each handlebar arm and free arm goes with one legs pose (as Mar
    Fil's ReadMe says: 7-ArmWithHandle-Right-A with 1-Legs-A, the left
    handlebar arms with the mirrored legs, the free arms with the other
    side). They go on the shoulder exactly as Mar Fil assembled them on the
    bike, so the hand is on the handlebar. Arms he exported to one side
    (7-29 mm) are moved back. The -B / -2 versions (no cross) fit the same.
  Weapons with a hand: the hand rule (right ones R, mirrored ones L).
    Hand-less weapons (36, 39, 42, 45): on a hand's Grip, held as in the
    A version - an Intercessor V2 hand takes them.
  Belt bits (holsters, pouches, purity seals - new type Seals): flat back on
    the belt, up the right way, on any belt anchor; the -Mirrored holsters
    try the left hip first.
  Pads: 19 right shin pads (+ 8 left copies; the others mirror), 24
    pauldrons - 1-R and DW-1 are rights, the chapter pads are lefts.


Techmarine (TIOW Inbox 1.11)
----------------------------
All Mar All the time\Techmarine (2). The chest matches the Assault torso
(waist, shoulders and neck 0.03 mm; back 2 degrees), so:

  Legs 1-4: seated like your Assault legs; Base = the tactical rock.
  Arms: exported in four sets on a turned torso (18 + 12/14, 19 + 16, and
    the two axe double arms), worked out from each set's shoulder faces
    (0.08 mm). Each arm goes on the shoulder as posed; arms 12/14/16 carry
    their cable (new type Cables) and a Hand L (their wrists are a little
    out of round, so it's saved with them).
  Double arms 20/22: Two-Handed Melee on Shoulder R (clearing Shoulder L),
    with their cables.
  Hand 38: Hands, goes on arm 12's wrist (as exported), with a Grip L.
  Cog axes, grav pistol: the hand rule.
  Backpack: Back, export position, with
    Back Top - the forge bolter / forge plasma (Backpack Toppers),
    Servo Arm - the servo arms (new type Servo Arms): each arm's shoulder
      ball (all r 2.47) goes in the seat Mar Fil uses in his build file,
      the arm otherwise as exported (some were 2-14 mm off it),
    Mechadendrite - the mechadendrites (new type), as exported.
  Holsters and pouch: anchors at Mar Fil's spots on the legs they were
    exported on (holster: legs 1 and 4; pouch: all four).
  Helmet: your helmet seat. Pads: the shared anchors.


Helmet updates and BackPackUpdate-1
-----------------------------------
Mar Fil's two helmet update sets (10 + 11 helmets) are in three places each:
All Mar All the time\HelmetsUpdate, the Outriders' Helmets-1 / Helmets-2
(unzipped), and HelmetsUpdate / HelmetsUpdates-1 at the top of D:\new cults -
the same files, so all copies have sidecars. They go on the Neck like your
Assault helmets (update helmet 1 is the same sculpt as your 1-Helmet-1 and
sits exactly where it does; all 21 share that seat).
BackPackUpdate-1 (4 backpacks, 9 toppers) is the same in the Vet, Bladeguard
and Outrider (unzipped BackPacks) folders and at the top of D:\new cults;
every copy now has the Vet kit's sidecars.


Turtle Ninja and the body adaptor (TIOW Inbox 1.12, 1.12.1)
----------------------------------------------------------
D:\new cults\Turtle Ninja. Everything is set up by rules matched to the Mar Fil
Assault torso, so Turtle Ninja and Mar Fil parts swap freely.

Waists: Mar Fil's waist is a plug with stomach plating on the legs ("Waist").
Turtle Ninja and Marta legs are flat on top ("Flat Waist").
  - Flat legs on a Mar Fil torso bring a body adaptor (D:\new cults\body
    adaptor) onto the torso's Waist and stand on its flat ring. The top of
    all six adaptors is a copy of the Mar Fil legs' waist (0.1 mm), so the
    adaptor sits in the torso exactly like Mar Fil legs do.
  - Adaptor 3 is the default. Next Adaptor (TIOW Inbox panel) swaps the one
    on the selected model for the next and the legs stay on; the number next
    to it is the one flat legs bring. Preferences > Body Adaptors sets the
    folder.
  - Mar Fil legs sent to that torso replace the adaptor and the flat legs.
  - A Turtle Ninja torso takes both kinds: flat legs on its flat bottom, Mar
    Fil legs with its flat bottom sitting on top of their belt (front belt
    line). Legs on one replace legs on the other.

Torsos: each design comes in nine poses; the flat one (square shoulders and
neck) is the one set up - 54 designs. They import standing up in the Mar Fil
frame (Z up, facing +Y). Shoulders: the shoulder disc matched to the Mar Fil
torso's shoulder face. Neck: the head sits where it does on the Mar Fil torso
relative to the shoulder joints (height, front-back, tilt). Back: the pack
plate matched to the Mar Fil torso's back.

Legs (465): Flat Waist from the top face (Turtle Ninja exports facing -X or
+Z by kit; both handled). Belt anchors 1 mm under the top, Base under the
feet. No shin anchors (shin pads are for Mar Fil legs).

Arms (159): the shoulder disc on the socket, face flat, as the Mar Fil arms.
Wrists are found by the wrist rule on import; Turtle Ninja hand weapons (48)
go in by the hand rule. The Mk10 power fists are exported turned: check
their swing.
Bolter poses (Mk4 Tactical A-D, Mk6 Addon A-C): the right arm of a pose has
a Hand R at its lettered wrist; the bolter held in both hands ("Two-Handed
Held", new joint) goes in it and meets the left arm of the same pose. The
merged bolter + both arms pieces are Two-Handed Guns on Shoulder R.

Helmets (197): the neck ball in the torso's neck cup, upright and facing
front, on a reference torso of the same mark; on any other torso the same
relative to the shoulder joints.

Packs (53, and the five Mk10 Hellblaster packs in the Intercessors V2
BackPacks-Raw folder, which are Turtle Ninja's): the mount plate flat on the
torso's back plate, centred, upright.

Accessories, grenades and seals (75): lying on their backs as exported;
they go on the belt anchors and rock and settle like Mar Fil's.

_library.json: a library with its own _library.json uses its "joints"
instead of the add-on's table, so copy the new Legs, Adapters and Two-Handed
Held entries from the one here into it (D:\new cults has none, so it uses the
add-on's).

Pack toppers (1.12.1): every Turtle Ninja powerpack has a Back Top on the
top centre of the pack (Z up, Y forward, like Mar Fil's). The banners and vox
casters go there pole first, 1.1 mm into the pack top; the Mk4 vox caster
lands exactly where Turtle Ninja exported it on the Mk4 packs. Mar Fil
toppers go on Turtle Ninja packs and Turtle Ninja toppers on Mar Fil packs.
Hellblaster packs have no Back Top. "Powerpack 1" (Mk6, the pack with a vox
caster built in, exported standing and smaller) sits like Mk6 Powerpack 1.

Mk7 power fists: left arms (their names carry no side; the add-on now takes
the side from the fit the part has). Upper arm hanging as straight down as
each arm allows.

Mk4 lightning claws: they slide over the open hand of
Mk4_Lightning_Powerfist_A exactly as in Turtle Ninja's merged claw arm (the
arm has a Hand R for them).

Jump-pack terrain (Mk10 Jumppack Intercessor): every jump legs piece has a
second Base anchor held for the terrain, so a terrain piece lands where it
was exported with the legs and a round base still goes on the usual Base.

One-off kits exported as one assembled model (Librarian, Legion Moritat):
every part sent onto the kit body lands where Turtle Ninja put it, through
the same joints as everything else (Mar Fil arms, helmets, packs and other
legs fit the kit bodies too). The Librarian's torso is the file called
Full_Model_Decimated. The Moritat body is torso and legs in one piece. Their
pauldrons and belt bits have anchors held for them on the kit arms and legs.
Mk4 Tactical bodies (torso and legs in one piece): torso joints by the flat
torso rule, Base under the feet, belt anchors, standing upright on import.

Not set up yet: pauldrons on Turtle Ninja arms (waiting for a reference
placement), Primus Medicae and WGBL (their parts are not exported in one
frame). The Mk6 "Rigging Required" files are skipped.


Marta (TIOW Inbox 1.12.2)
-------------------------
D:\new cults\Marta. Torsos and heads are not set up (Josh), so male and
female kits are the same here. Presupported files are skipped.
  - Legs (220): flat on top like Turtle Ninja's (Flat Waist; Marta exports
    them facing +Z), belt anchors and Base by the same rules. On a Mar Fil
    torso they bring the body adaptor.
  - Bases (42 round ones): the disc centre on the rim top goes under the
    feet.
  - Two-armed weapon sets (32): the right arm's shoulder face on Shoulder R
    like any arm, the left arm follows (Two-Handed Guns / Melee). Marta's
    shoulder joints are 12.3 mm apart: on Turtle Ninja and Marta-width torsos
    the left arm lands on Shoulder L, on a Mar Fil torso it sits about
    1.4 mm in.
  - Loincloths (21): hang from Belt Front, then rock and settle onto the
    belt. Belt bits now go to the anchors they have a fit for first.
  - Chin pads (31 more): Mar Fil legs only for now (Josh), fitted to Mar
    Fil's shin pad like the earlier Marta pads. Most of Marta's newer pads
    are left-only files: they go on the left shin. The thicc / heavy pads
    made for her bigger legs did not match Mar Fil's shin and are not set up.
  - Pauldrons (86): Josh's 62-on-76 placement, 62 matched onto each pad (the
    same way as the Turtle Ninja Mk10 pads), on the arm's Pad anchor; lefts
    are mirrored. 16 that matched poorly (thicc ones, some spiky or feathered
    ones) are left for Save Fit for Folder.

Springles (TIOW Inbox 1.13)
---------------------------
D:\new cults\Springles. Springles' heresy parts are smaller than Mar Fil's;
your working file scales them up by 1.1, so their .sockets.json now carries a
"scale" (1.1002 for the pattern C arms, 1.1 for the rest, exactly what your
file used) and the add-on scales the mesh on import.
  - Arms (144: patterns C, P and S, right and left): the shoulder disc's
    centre on your HeresyArms_r point (0.75 mm in and down from Shoulder R,
    1.6 degrees turned), file axes - this is your placement of the 74 arms in
    "3rd attempt finalising actual.blend", to within 0.05 mm for most. Two
    exceptions: your pattern P and S arms there are turned 90 degrees (their
    shoulder disc faces forward), and 16 arms' origins sit 0.2-1.2 mm off the
    disc centre; both follow the disc rule here. Left arms are the mirror
    rule. The helmet-hold arm is a left arm (you mirrored it onto the right).
  - Wrists: Springles hands end in a shallow dome that sits in a cup at the
    end of the forearm. Hand R/L = the centre of the cup's rim, Y up the
    forearm, the hand's top towards up-and-forward. Pattern P cups the shape
    search missed were carried from the same pose in pattern C (the forearms
    are the same mesh). "slung arm+hand" has its hand built in.
  - Pauldrons: every arm has a Pad R/L anchor, from your 62 placed by
    hand on patternC heavy Rarm 4 (working file, 20 Oct - reproduced
    exactly). Every other arm gets it turned with its own shoulder (its
    shoulder shape matched to that arm's, within 0.2 mm), pushed out only
    where its armour would otherwise cut into the pad, so a pad tilts with
    a raised arm as yours does. Any pauldron with a
    Pad fit (Mar Fil, Marta, Turtle Ninja) goes on them; lefts are mirrored.
  - Hand-held weapons: the two-hand and off-trigger versions of the guns
    ("Two-Handed Held": the trigger hand goes in the right hand), the
    with-hand pistols, axes and tabars. The dome's tip sits on the cup floor,
    the hand's wrist axis along the forearm, the weapon's top up. They also
    go in Mar Fil hands (dome 0.55 mm into the wrist face), and Mar Fil
    weapons go in Springles cups.
  - Two hands on ball wrists: after a two-hand gun goes in the right hand
    it is turned about that wrist so its other hand reaches the left wrist
    as nearly as it can (the status line says how far it turned and how
    close it got). Springles' ranged and heavy arm pairs come within about
    1-2 mm on a Mar Fil torso (their own torso is a little wider); the las
    cannon, plasma cannon and rocket launcher (not underslung) are held
    level that way on the ranged arms (a big turn, within 1 mm). If the hands can't get within
    3 mm (melee arms, say) the gun stays upright in the right hand.
  - Heavy weapon backpacks and the assault cannon ammo pack: the mount plate
    on Back.
  - Not set up: the 1-hand, no-hands and plastic versions, the mk6
    uparmoured cybernetics legs, the ammo belts and the backpack camera
    (later, Josh).

BBoosty and CyberBrush (TIOW Inbox 1.14)
----------------------------------------
Both makers export their parts in the model's own axes (front -Y), only
moved apart for printing, so one rule places most of them. In the Kitbash
Library they are "BBoosty - Heresy" and "CyberBrush - Tacticus".

  - Arms: the round flat shoulder face goes on the heresy shoulder point,
    as Springles' arms do (on Mar Fil, Turtle Ninja and the CyberBrush
    torso). Arms printed turned take the pose of a sibling with the same
    arm. Wrist sockets sit in the wrist cup like Springles'. BBoosty arms
    with a pad built in ("...Shoulder...") get no pauldron anchor; every
    other arm gets a Pad R/L anchor on its shoulder dome.
  - Arms with the hand built in (CyberBrush weapon, fist and claw arms,
    BBoosty's shield-grip left arms) say so in their sidecar ("noHand"):
    no wrist socket is looked for and the status line stays quiet.
  - Hands, and weapons with a hand (Consul, Chaplain, Iron Father, Praetor):
    the wrist ball goes in the wrist socket. Hands go in either hand.
  - Paragon blade held in two hands: the upper hand in the right wrist, the
    sword turns about it to bring the lower hand to the left wrist (as
    Springles' two-handed guns).
  - Pauldrons (BBoosty Medusas Mortals, Paragon, Consul, Chaplain, Iron
    Father and Iron Hands sets; CyberBrush sets 1-2): their inner shell on
    the arm's shoulder dome. Right pads; lefts are mirrored.
  - Heads: the neck ball in the neck cup. Backpacks: centred on the back
    plate (Medusas Mortals packs as your Backpack2).
  - CyberBrush torso: a Chests part with Shoulder, Neck, Back, Waist and
    Flat Waist sockets where Mar Fil's torso has them.
  - CyberBrush two-armed guns and two-handed swords and axes go on the
    right shoulder and bring the left arm with them.
  - Bases (BBoosty): the round base rule.

Forearm armour (new type "Forearm Armour"): CyberBrush's Space Bug Hunter
forearms sit on a Forearm R / Forearm L socket where your Forearm 3 sat on
77-Arm-1-R-B. Mar Fil's assault arms have that socket already (your
Wrist_Armout_r); any other arm with a wrist socket gets one when forearm
armour arrives, the same step from its wrist. Lefts are mirrored. Select the
arm (or its Forearm socket) before sending. Arms with the hand built in have
no wrist socket, so no Forearm socket either (yet).

Not placed yet: BBoosty separated weapons, shields without a hand,
holsters / grenades / pouch / melta bomb, servo arms and modules, Iron Father
claw / flamer / melta, base topper, backpack cams; CyberBrush equipment 1-7,
cloaks, loincloths, belt decorations, shields without an arm, the Free
weapons. They are in the library under their type (Hand-less Weapons,
Shields, Accessories, Grenades, Servo Arms, Backpack Toppers, Cloaks) and park
on that type's socket when the model has one (place by eye, Save Fit for
Folder), otherwise they land at the cursor.

Standing on the base (TIOW Inbox 1.15)
--------------------------------------
Everything hangs off the torso, so the torso keeps its file angle and the
legs and base end up however the waist fit tilts them (Mar Fil legs seat
about 14 degrees forward). When a base - or terrain - snaps onto the legs'
Base socket, the whole model is now turned so the base sits flat on the
grid: the socket's Z straight up (the smallest turn, so the model keeps
facing the way it did) and the base's underside dropped onto the grid
where it stands (models side by side stay side by side). Only the model's
root moves: every joint stays exactly as it was, and Kitbash Finalise works
the same either way. The status line says how much tilt it took out.
  - Stand on Base (TIOW Inbox panel) switches it off; Level Now does it
    any time on the selected model (after swapping legs, say) - with no
    base on yet, it stands the model on the legs' Base socket.

One file, both sides (TIOW Inbox 1.16)
--------------------------------------
Mar Fil ship many left parts as exact mirror copies of the right ones (the
'-Mirrored' and LeftOrientated files, '...-L-A' arms). Those copies are
folded into the right part's .sockets.json as a "variant" (its own sockets
and fits, and where its mesh sits) and the copy's STL is moved out of the
library to "Kitbash Library - mirror copies" beside it (nothing deleted;
_mirror_copies.csv in the library lists every one). TIOW then shows one
card per part.
  - Send it and it goes on the side it should: the side you picked (select
    the left arm, or the Shoulder L socket, or the arm whose hand it goes
    in) or else the free side, its own side first. On the left it arrives
    exactly as the old left copy did: same shape, same place, same anchors.
  - Mirror (TIOW Inbox panel) flips the selected part. An arm, a hand-held
    part, a pauldron or a hip pouch moves to the other side as its mirror
    image, with what it holds, and the part already there swaps over.
    Legs, a head or a torso flip where they stand and keep what's on them
    (the pads stay on the same shins, the base re-levels). It uses the
    maker's copy when there is one; any other part gets a plain mirror,
    saved in its sockets file so anchors clicked on it are kept.
  - Mirroring flips any lettering, purity-seal script, chapter icon or
    one-sided gun detail, the same as the maker's own copies do.
  - A copy only goes if it matches its twin everywhere (median 0.05 mm,
    95% within 0.15 mm). Copies Mar Fil changed after mirroring (a turned
    forearm, a re-posed leg) stay as their own files.
  - The add-on reads a part's maker name from its sockets file, so files
    can be renamed without changing any side or pairing rule.

Squads from the Squad Builder page (TIOW Inbox 1.17)
----------------------------------------------------
The Squad Builder page (its own folder, with its own README) sends a whole
squad at once. Each request names its model and the socket the part goes
on, so every part lands on its own model whatever is selected in Blender,
and each model's torso is placed where the page showed it (side by side,
80 mm apart). Everything else is the normal snap: maker's left copies,
mirrored pads, flat legs bringing the body adaptor, standing on the base.
Parts sent from TIOW itself work exactly as before.

1.17.1: browsers won't let a web page write into AppData, where TIOW's inbox
is, so the page writes its requests into the library's own _builder\inbox
folder instead. TIOW Inbox watches that folder too: Preferences > Squad
Builder Inbox (default D:\Kitbash Library\_builder\inbox; used only when
that _builder folder exists, which Prepare Squad Builder.bat makes; empty =
off). It also touches a .listening file there, so the page can show
"Blender listening".

Save Correction (TIOW Inbox 1.17.2)
-----------------------------------
For a part that's slightly off: move it where it should be, keep it
selected, and in the TIOW Inbox panel press one of:

  Fix the Part    this part is off wherever it goes (a pistol a little
                  forward in every hand). Its fit is saved in its own
                  .sockets.json, so it lands like this on every model.
  Fix the Socket  everything is off on this host (every head sits low on
                  this torso; pads dig into this torso). The socket on the
                  torso / arm / legs it sits on moves instead, so every part
                  lands right on it. The part stays where you put it.

  Whole Folder    the same move for every part in that folder (a kit's
                  pistols, its arms, its torsos) - not just this file.
  Both Sides      (on) the other side gets the mirror image: the left hand,
                  the left pad, the left shoulder, a maker's left copy.

Which to use: wrong on one host only -> Fix the Socket; wrong everywhere ->
Fix the Part. The move is kept in the socket's own frame, so parts in the
folder with slightly different fits each move by the same amount. Copies
already in the scene move too. A part you corrected lands exactly there
next time (no rocking or settling). Run Prepare Squad Builder afterwards so
the page matches (it only redoes what changed).

1.17.3: a socket you corrected is trusted as well. Belt bits on it aren't
rocked to a new tilt any more (that undid the angle you'd set); they only
settle in until they touch, so the bit you placed comes back where you put
it, pushed out to just touching if it was sunk into the belt.

Bases settle onto the feet (1.17.2): a base snapped on the legs' Base socket
rises along the socket until the lowest foot touches it (and 0.2 mm in, for
printing). A base is only ever raised: feet already on or in a scenic base
stay as they are.

Pads and belt bits (TIOW Inbox 1.6.1)
-------------------------------------
Shin pads and shoulder pads sit on three-point ANCHORS, so they land exactly
where the fit says - no tilting or sliding. Belt bits still settle (below).

Shin anchors (Mar Fil legs) are found by themselves when the legs arrive:
the two circles at the ends of each ankle and the top of the hole in the
front of each shin. The status line says "Shin anchors found" (or why
not). The anchors are drawn in front of the mesh so you can see them in the
holes. If one side was clicked by hand, only the other side is found.
Anchors > Find Shin Anchors starts again on the selected legs: it replaces
both shin anchors, clicked ones too, and forgets any saved clicks. Other
makers' legs get none - shin pads only go on Mar Fil legs.

Pad anchors (arms) are copied when an arm arrives: its mini shoulder pad is
matched to Mar Fil's 76-Arm-1-R-A (the arm in your pauldron example, built
into the add-on) or to any arm you have clicked in the same kit, and the
three points are carried across. When the arm's shoulder joint is known (it
has a Shoulder fit) the reference is swung about that joint through every
angle up to 120 degrees, so arms raised far forward or out (Mar Fil's arm 3,
power fists 166-174) are found too (1.8.1: all 90 Assault Marine arms and
power fists, and the Veteran Squad arms). That takes about 5 seconds the first
time; the anchor is then saved in the arm's .sockets.json beside the STL, so
it is instant afterwards. An arm whose shoulder doesn't match (another kit) says
so on the status line: Anchors > Pad R / Pad L, then three clicks on the
arm's mini shoulder pad - its front corner, its back corner, and its top at
the inner edge by the shoulder joint. That is saved with the arm too, and
other arms in the same folder (or the folder beside it) copy from it.

Fits: one per library folder, in _fits.json. Already written for:
  All Mar All the time\AssaultMarines-V2\...\RawSTL\ShinPads
      and ShinPads\LeftOrientated
  VeteranBladeSquad ...\Shin-Pads\Shin-Pads-RawSTL and Shin-Pads-Mirrored
  All Mar All the time\AssaultMarines-V2\...\RawSTL\ShoulderPads
      (66 and 67 face the other way in their files, so each has its own fit
      in a .sockets.json)
  VeteranBladeSquad ...\ShoulderPads\ShoulderPads-RawSTL and -Mirrored
      (Death-ShoulderPad has its own fit: it sits like 62 in its file)
  TurtleNinja's Mk10 ...\Pauldrons
  51 May 2026 ...\legs-chin pads and base (Marta: each pad has its own fit,
      because her pads sit in different places in their files)
  ChaplainOnBike-Bits ...\ChaplainRawSTL (5-ShinPad-R right, 6-ShinPad-L
      left as it is - from the Chaplain rig)
The shin fits come from Mar Fil's Techmarine rig, the pauldron fits from
your example (62 on 76), carried to the other pads by matching shapes.

Pads are recognised by their file name (ShinPad, Shin-Pad, Chin_pad,
KneePad, ShoulderPad, Pauldron), whatever type TIOW gives them.

Left side: a pad with no left fit is mirrored (its mesh is flipped and
"(mirrored)" is added to its name). Mar Fil's "...-Mirrored" and
LeftOrientated files and Marta's _L pads go on as they are.

A new folder works as before: the first pad from it is parked on the
anchor; place it by eye, keep it selected and click Save Fit for Folder.
Pads no longer settle, so every pad from that folder then sits exactly
where you put that one, on any legs or arm with the same anchor.

Fits saved for Knee Pads or Shoulder Pads with 1.5 or earlier were measured
from the old anchors: save them again. Arms already in a scene keep their
old Pad anchor until they are sent again.

Belt bits (Accessories, Grenades, Seals, Trophies) go on Hip R, Hip L,
Belt Front or Belt Back. Since 1.11 every Mar Fil legs piece comes with all
four, on the belt (see "Every kit fits every kit"); one click on the part
places your own instead. Select the anchor you want before sending,
otherwise the first free one is used (a '...-Mirrored' bit tries the left
hip first). They tilt up to 8 degrees to sit flush ("rock"), slide in until
they touch ("settle") and press in 0.1 mm ("sink"), all set in the "joints"
table in _library.json. An anchor saved where the kit's maker put one
particular bit (the Chaplain's book, the Techmarine's holster) takes that
bit exactly there, with no tilting or sliding, and is used first for it.


Lifting parts out of an existing kitbash file
---------------------------------------------
lift_parts_to_library.py takes the parts out of a .blend you've already
worked on (written for "3rd attempt finalising.blend") and files them into
the Library folders:

  Library\<Creator - Mark>\<Kit>\<Type>\<part>.stl
  Library\<Creator - Mark>\<Kit>\<Type>\<part>.sockets.json   (if it has sockets)

Each STL is saved in the part's own coordinates, so its origin is the one
you set. Sockets, Store Per-Part Fit offsets and the fit types they use go
in the .sockets.json next to it; the TIOW Inbox add-on rebuilds them when
the part is imported. All captured fit types are also saved to Part Sockets'
Joint Library as "Kitbash master". The .blend itself is not changed.

Fit types are renamed to joint names on the way out (RENAME at the top of
the script): arm__Torso_r -> Shoulder R, Wrist_socket_r -> Hand R,
Wrist_Armout_r -> Forearm R, Shield_to_hand_r -> Shield R, Head -> Neck,
Backpack -> Back, both backpack toppers -> Back Top, fins and wings -> Pack
Fin R/L and Wing R/L, Right/Left Hip -> Hip R/L, Tabard -> Belt Front,
Legs 1-5 -> Base Pose 1-5, Jump legs 1-8 -> Base Jump 1-8. The waist types
(Legs, Legs to chest, Chest to legs, Adaptor) keep their names for now.

HeresyArms_r becomes Shoulder R too. Your torso 23-Torso-2.001 has both an
arm__Torso_r and a HeresyArms_r socket, and the difference between them
(0.75 mm and a 91.6 degree turn) is moved into the heresy arms' STL origins,
so every arm fits the one Shoulder R socket and lands exactly where your
HeresyArms_r socket put it.

  1. Install the updated tiow_inbox.py (Install from Disk again).
  2. Open the .blend. If you nudged any part by hand after snapping and want
     to keep that fit, select it, shift-select its socket, and run
     Store Per-Part Fit first.
  3. Scripting tab > Open > lift_parts_to_library.py. Set LIBRARY at the
     top to your Library folder. Run Script.
  4. That first run is a dry run: check Library\_lift_report_<file>.csv.
  5. Set DRY_RUN = False and run it again.

Existing STLs are never overwritten unless you set OVERWRITE = True.
Parts the script can't trace to a creator's file go in
Library\_Unsorted\From <file name>\<Type>\ for you to move.
