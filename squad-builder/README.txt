Squad Builder
=============
A page you open in Chrome or Edge to build one model or a whole squad step
by step (torso, legs, arms, head, back, shoulder pads, weapons, shin pads,
base), seeing each part where it will go, then send the lot to Blender in one
go. TIOW stays as it is for browsing and tagging the collection.

Files (keep them together)
  Squad Builder.html           the page (works offline: nothing is uploaded)
  Prepare Squad Builder.bat    gets the library ready (below)
  prepare_builder.py           what the .bat runs, inside Blender
  build_index.py               used by prepare_builder.py

Getting the library ready (once, then after adding parts)
  1. Blender 5.1 with Part Sockets and TIOW Inbox 1.17.5 enabled.
  2. Double-click Prepare Squad Builder.bat. It runs Blender in the
     background (your open Blender isn't touched) and:
       - works out the anchors some parts only get on their first import
         (wrist sockets, pauldron points, shin anchors, weapon grips) and
         saves them in each part's .sockets.json, so the page shows those
         parts exactly where Blender puts them;
       - makes a light copy of every part's mesh (about 6,000 triangles)
         and an index, in D:\Kitbash Library\_builder.
     The first run takes a while (roughly an hour or two for the whole
     library). After that it only does new or changed parts. If you stop it,
     run it again: it carries on where it left off.
  If the library isn't at D:\Kitbash Library or Blender isn't in
  C:\Program Files\Blender Foundation\Blender 5.1, edit the two lines at the
  top of the .bat.

Using it
  1. Open Squad Builder.html in Chrome, Edge or Opera. The first time, click
     Folders... and choose the Kitbash Library folder; allow the browser to
     view and save changes there. Parts are sent by writing them into the
     library's _builder\inbox folder, which TIOW Inbox watches (browsers
     won't let a page write into AppData, where TIOW's own inbox is). The dot
     at the top says "Blender listening" while Blender is open.
     Next time, one click on the page reconnects it (the browser asks).
  2. Set Squad to how many models you want.
  3. Work down the steps: Base, Legs, Torso, then arms, head, back, wings,
     pads, weapons, shin pads, loincloth and belt. The legs stand on the base as soon as you pick
     them, so you see the pose before the torso. Hover a card to see that
     part in place (blue outline); click it to take it - it stays on that
     step so you can try others - and press Next when you're happy. Next
     with nothing picked leaves the slot empty; Remove clears it. Right and
     Left are separate slots for arms, pads, weapons and shins: a right part
     with a maker's left copy appears in both, and pads and shin pads can
     always be mirrored. An arm with its weapon built in skips its hand.
  4. With more than one model, "Same part for every model" (on by default)
     puts each pick on every model. Untick it to pick for each model in
     turn: five torsos, one after another, then five legs, and so on. A
     model's tab takes you to that model to change just its part.
  5. Send to Blender. Blender must be open with TIOW Inbox listening. The
     whole squad arrives side by side, each part on its own model, whatever
     is selected in Blender. When a base arrives the model is stood on it;
     a base whose top is lower than the feet rises until the lowest foot
     touches it (the page shows the same). A base you've placed by hand and
     saved with Fix the Part doesn't rise: it sits where you put it.

Notes
  - "no fit yet" on a card: that part has no fit saved for this slot, so the
    page can't show where it goes and Blender parks it beside the model for
    you to place by eye. Place one, use Save Correction > Fix the Part with
    Whole Folder ticked, and the rest of its folder follows (the page picks
    that up next time Prepare runs).
  - Something slightly off? Fix it in Blender with Save Correction (TIOW
    Inbox panel), then run Prepare Squad Builder again so the page matches:
    it only redoes what changed.
    Prepare lists every such part in _builder\no_fit.txt.
  - Flat legs (Marta, Turtle Ninja) on a Mar Fil torso bring the body
    adaptor, as in Blender.
  - Hiding parts: tick "Hide parts" (by the search box) and each card gets
    a Hide button, with the parts already hidden shown dimmed with Unhide.
    Untick it and hidden parts are left out of the builder. Nothing is
    deleted; sidecars stay as they are. The list is _hidden.txt in the
    library folder: one library path per hidden part, "word: aquila" to hide
    every part with that in its name, "type: Seals" for a whole type. It
    starts with aquilas, purity seals and scrolls; for a word or type line,
    edit _hidden.txt.
  - Weapons held in both hands with no arms of their own (Two-Handed Held:
    the toothed two-handed chainglaives, Springles' guns, Turtle Ninja's
    bolter poses) are in Weapons on the right hand and take the left hand's
    slot too. In Blender the weapon turns about the right wrist so its other
    hand meets the left arm's wrist - on arms posed to hold one (Springles'
    duel melee arms, say). On other arms it stays as gripped.
  - Wings (step 7): Right and Left, on a back with wing mounts (the TN Mk6
    Universal jump pack). Each wing brings its connector (the Techmarine
    kit's Arm 2 Joint) onto the pack's Wing Mount and hangs from the
    connector, as in base_jumpack.blend; the page shows both, and
    Blender adds the connector itself. Backs without wing mounts skip the
    step. The six Malal3D Bladecrow wings come at x1.3, lefts mirrored.
  - Loincloth (step 11): the front of the belt is the loincloth's alone.
    Loincloths are their own type (Marta's and CyberBrush's), in Blender
    tilted to sit flush and settled onto the belt like belt bits. On legs
    striding forward, the bottom of a loincloth can pass through the raised
    thigh: a rigid cloth can't follow the knee.
  - Belt (step 12): Right hip, Left hip and Back - the anchors on every pair
    of legs. A part shows on the tabs it has a fit for. In Blender it is
    tilted to sit flush and settled onto the legs, so it can sit a little
    differently from the page.
  - Arms have three tabs: Right, Left and Two-handed. Two-handed holds the
    pieces with both arms and the weapon in one (two-handed guns, two-handed
    melee, heavy weapons); they go on the right shoulder and take both.
    Picking one replaces the arms, and picking an arm replaces it. A model
    with one skips the hands (its weapon is built in) and the pads (TIOW
    Inbox finds pad spots on single arms only); those picks aren't sent.
