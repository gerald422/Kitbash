Kitbash Finalise 0.3.3
======================
0.3.3: parts that aren't manifold can be fixed from the dialog. Tick
"Make them manifold first (3D Print Toolbox)" (on by default): Finalise runs
the 3D Print Toolbox's Make Manifold on its own copies of those parts - your
originals aren't touched - and they then boolean with the Manifold solver.
Any part still not manifold after that goes in with Exact (the log says
which). Needs the 3D Print Toolbox extension enabled; without it the box is
greyed out and the old choice (fix by hand, or Use Exact) is there as before.
(0.3.2 was the bionic-leg version, on hold; this is 0.3.1 plus
the manifold option.)

0.3.1 (from the test in your Blender): a foot peg into a base that isn't
manifold was cut off by the base's carve (Exact booleans used to run last
on a piece); now each piece keeps its order - parts, carves, pegs, holes,
letters - and goes Exact from the first boolean that needs it. Feet sunk
into a scenic base get their peg pointing the right way (into the base).
Hard Ops' empty Cutters collection is removed after Apply / Discard.

Turns a model built with Part Sockets / TIOW Inbox into print pieces: every
part booleaned together in a fixed joint order, and, if you print in
sub-assemblies, a push-fit peg in the middle of every joint where a piece
comes off, and the model's ID letter on every piece.

New in 0.3:
  - Square pegs with one corner cut off: they only go in one way round,
    exactly as posed in Blender (Spike / Quad-Key / Bayonet still there).
  - Peg per piece, ticked in the dialog: legs (Waist / Flat Waist) start
    off - they sit on their flat face and adaptors - everything else on.
  - Bases: a base on the legs' Base socket is a separate piece by default,
    with the peg on the foot and the hole in the base.
  - A joint the chosen size won't fit (a small neck ball) drops to the
    next Part Sockets size down (M -> S) instead of a hole breaking out.
  - Fixed: in 0.2 a peg on the body (the torso's neck / waist pegs) was cut
    off again by the carve, leaving only the hole. Don't print 0.2 pieces.
0.2: pegs in the middle of the joint face, square to it (on the body
where the body is too thin for the hole); one letter per model.

Needs: Blender 5.1, Part Sockets enabled (sockets, peg sizes). Uses Hard
Ops' own boolean setup when Hard Ops is enabled (its Boolean modifier,
Cutters collection, boolshape display and modifier sort, no Hard Ops UI);
the solver is forced to Manifold for the build and Hard Ops' own settings
are put back afterwards. Without Hard Ops it makes the same Boolean
modifiers itself.

Install: Edit > Preferences > Add-ons > tick "Kitbash Finalise" (it is
already in your add-ons folder; or Install from Disk > kitbash_finalise.py).
Sidebar (N) > Finalise tab.

Use
---
1. Select any part of the model, click Finalise Model.
2. The dialog:
   - Parts that aren't manifold are listed in red. Leave "Make them manifold
     first (3D Print Toolbox)" ticked to have them fixed on the copies, fix
     them yourself, or tick "Use Exact for the parts above": only those parts'
     booleans use Exact, and they go last on their piece (Exact output can
     itself be non-manifold, which the Manifold solver can't take).
   - "Print as sub-assemblies": tick it, then tick each piece that prints
     separately. A piece takes everything on it (an arm takes its hand,
     weapon, pauldron, forearm plate) unless you tick that too. "Peg" next
     to each: a peg + hole where it plugs in, or none (it just sits on its
     face, still lettered). Legs start with Peg off, bases start ticked.
   - Carve overlaps: the piece's own shape is cut out of the body where the
     two overlap, so it seats back in.
   - ID letter + Letter: the model's letter (the next one not used by
     another finalised model in the file: A, then B, ...). See below.
3. You get a draft in a "Finalise - <model>" collection; your parts are only
   hidden, not changed. Booleans are switched off in the draft (a body with
   15 booleans is slow to redraw): the parts show as solids, the pegs,
   holes and letters as wires, and each joint has an arrow empty
   (FA_joint_1_...). Move or rotate an arrow to move its peg and hole
   together. Letters are their own wires (FA_letter_A_...), parented to
   their piece: move one if you put a peg on top of it.
4. Preview Booleans: select a piece (or nothing for all) to switch its
   booleans on and see the result; click again to switch them off.
5. Apply Booleans: applies everything one boolean at a time, deletes the
   cutters and part copies, names the pieces "<model> - Body [A]" and
   "<model> - <part> [A]", and says whether each piece is manifold.
   Discard Finalise throws the draft (or the baked pieces) away and shows
   your parts again.

Order
-----
Parts are unioned into their piece by the joint they sit on: Waist, Flat
Waist, Shoulder, Neck, Back, Hand, Grip, Shield, Forearm, Pad, Shin, Hip,
Belt, Back Top, Pack Fin, Wing, Cable, Servo Arm, Mechadendrite, Bike, Base
(add-on preferences to change it). Then the pegs, cavities, carves and
letters.

Pegs
----
Part Sockets' push-fit connector in its Long proportions (never the shallow
Disc), sized by the Part Sockets settings shown in the panel: scale
(Marine / Vehicle), size S / M / L or Custom, clearance, bottom gap, taper.
Square (keyed) is the default: square, as wide as the size, tapered with a
lead-in nose, one corner cut off so it only seats one way. It turns with
the joint's socket; rotate the joint arrow to turn it. Spike (round),
Quad-Key (round with 4 flats, seats every 90 degrees) and Bayonet are
still there. If neither side of a joint can take the chosen size, it uses
the next size down (logged); Custom doesn't step down.

Where it goes:
  - The piece's face where it plugs in is found first: the biggest smooth
    patch of the piece that looks at the body and is hidden by it (the
    legs' flat top, the arm's shoulder disc, the pack's back plate).
  - Flat face: the peg comes straight out of it, so it goes in the way the
    piece slides on (the legs' post into the torso's socket).
  - Curved face (a neck ball): along the socket, which sits on the ball
    with its Z through the ball's middle, as long as that's a way the
    piece can come off; else the way it pulls off where the two touch.
  - Always the middle of that face.
Bases: the peg goes on the foot (in the middle of the biggest sole patch
standing on the base, square to it) and the hole in the base; the hole may
go right through a hollow base's top.
Which side (everything else): Peg On = "Piece (body if thin)" (default)
puts the peg on the piece and the hole in the body, unless the body is too
thin in the middle of the face for the hole and the piece isn't: then the
peg goes on the body and the hole in the piece. "Always the piece" never flips (the peg is
shortened, and the log warns if the hole would break through).
Where the body is only a little short, the peg is shortened to fit
instead. The panel log says per joint how the peg was placed, its length,
which side it's on, and any gap it bridges.

ID letter
---------
One letter per model, the same on every piece of it, so a squad's pieces
don't get mixed up (A, B, C ... no I or O). It is debossed:
  - on every separate piece, on its face where it plugs in, as big as fits
    beside the peg / hole (up to Max Letter Size in the panel, default
    6 mm). Where that face has no room round the peg (a small shoulder
    disc), it goes on the biggest hidden face beside it, and only if there
    is none, on the peg's tip / the hole's floor;
  - once on the body: on the face the legs plug into (its base) if it fits
    1.5 mm there, else wherever on the body it fits biggest under a piece.
Only on faces that are hidden once assembled (the other piece within
3 mm), facing it, without steps, and thick enough behind for the depth.
Letters are draped over the face, so a gently curved one works too, and
read the right way round looking at the face.

Order on each piece: its parts, then the carves, then pegs, holes and
letters (so a carve never cuts a peg back off).

Tested on your Assault Marine (claude tests.blend): body + legs, both arms,
helmet and jump pack as six pieces; all six manifold after Apply and every
peg checked to be there. Legs: no peg, letter 5.1 mm on their top, body
letter 3.9 mm on its base. The torso is hollow under the neck (about
1.4 mm), so the neck takes an S peg on the torso into the helmet's ball.
That file has no base, so the foot peg was tested on a test model (legs on
a hollow 25 mm base). Your left bolt pistol (211-L) has 12 open edges, so
it needs Exact.
