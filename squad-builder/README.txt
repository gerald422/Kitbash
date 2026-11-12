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
  share_server.py              shares the page with people you choose (below)
  Share Squad Builder*.bat     start sharing / add people
  Build received models.bat    builds what they send

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
  2. Pick the Armour at the top: Tacticus (all power armour - Tacticus,
     Heresy and Phobos kits), Terminator or Gravis. Only parts for that
     armour are listed; bases, belt bits and Bits show for all. Switching
     takes off picks that don't fit the new armour. (No Terminator or
     Gravis torso has attachment spots yet, so those models are put
     together in Blender.) Then set Squad to how many models you want.
  3. Work down the steps: Base, Legs, Torso, then arms, head, neck guard,
     chest equipment, chest insert, back, wings, pads, weapons, shin pads, hip plates,
     holsters, buckle, tabard, loincloth and belt. The legs stand on the base as soon as you pick
     them, so you see the pose before the torso. Hover a card to see that
     part in place (blue outline); click it to take it - it stays on that
     step so you can try others - and press Next when you're happy. Next
     with nothing picked leaves the slot empty; Remove clears it. Right and
     Left are separate slots for arms, pads, weapons and shins: a right part
     with a maker's left copy appears in both, and pads and shin pads can
     always be mirrored. An arm with its weapon built in skips its hand.
     Swapping the torso, legs or arms takes off anything that no longer has
     a spot (chest equipment on a torso without the spots, shin pads on
     legs without shin spots...), and such parts are never sent.
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

Adjust: fixing where a part sits
--------------------------------
Adjust (top left of the view) lets you correct a placed part on the page:

  1. Click the part. A handle appears on the joint it hangs from.
  2. Move: drag the arrows. Turn: drag the rings (the part turns about its joint).
     Snap: click a spot on the part, then the spot on the model it should meet.
     Seat: slides the part onto what it hangs from until they touch.
  3. Save fit. Reset puts it back as it was saved; Done leaves Adjust.

"Handle at" chooses what the part turns about: Joint (the joint it hangs
from) or Middle (the part's own middle, for small twists in place).
Clicking the torso turns it on the legs, about the waist; the arms, head and
pack go with it. That is saved as the legs' fit.

Save changes where that part sits on that kind of joint everywhere it is used:
on every model here, and in Blender, which places it exactly as you left it
(no rocking or settling). A part shown mirrored shares its fit with the other
side, so both move. A maker's own left copy keeps its own fit.

It writes the fit into the part's .sockets.json in the library and adds a
line to _builder\corrections.jsonl (what was moved, on what, and how far).
That log is replayed when the page loads, so there is no need to run Prepare
after a correction. The page works on the light preview meshes, so it is good
to about 0.15 mm: for a flush contact, finish in Blender with Save Correction.
Parts that are brought along (the adaptor, a wing's connector) can't be
adjusted here.

On the shared page (below) Save fit is written on your PC only for the
owner's sign-in; for anyone else it lasts their visit. The owner is the first
person you added, or whoever you name:
    python share_server.py --owner NAME

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
  - Neck guard (step 6) and Chest equipment (step 7): torsos with the spots
    (the Old Style Space Knight MK8 torsos) take a neck guard - one of the
    eight turtlenecks or the Collar, the back collar these torsos were made
    without - and a chest piece each side, the right one mirrored. Both sit
    exactly where the maker's builder has them. Other torsos skip both steps.
  - Chest insert (step 8): a torso with the spot (so far only MarFil
    Assault - Torso 2 Insert, Josh's cut of Torso 2) takes one of the 44
    chest inserts, where Josh placed his. Other torsos skip the step.
  - Wings (step 10): Right and Left, on a back with wing mounts (the TN Mk6
    Universal jump pack). Each wing brings its connector (the Techmarine
    kit's Arm 2 Joint) onto the pack's Wing Mount and hangs from the
    connector, as in base_jumpack.blend; the page shows both, and
    Blender adds the connector itself. Backs without wing mounts skip the
    step. The six Malal3D Bladecrow wings come at x1.3, lefts mirrored.
  - Hip plates (step 14) and Holsters (step 15): legs with plate spots (so far
    Mar Fil Assault, Intercessor and Techmarine, and Turtle Ninja) take a hip plate on each side, the right one
    mirrored. Holsters and sheaths hang from the plate on their side (the
    right ones mirrored). Other legs skip both steps.
  - Buckle (step 16) and Tabard (step 17): the buckle sits on the sculpted
    one (on Turtle Ninja legs, Mar Fil's buckle over their belt front) and
    prints on its own; tabards hang from it, so they follow its turn
    and tilt. Legs without a buckle spot skip both.
  - Loincloth (step 18): the front of the belt is the loincloth's alone.
    Loincloths are their own type (Marta's and CyberBrush's), in Blender
    tilted to sit flush and settled onto the belt like belt bits. On legs
    striding forward, the bottom of a loincloth can pass through the raised
    thigh: a rigid cloth can't follow the knee.
  - Belt (step 19): Trophy R and Trophy L (either side of the buckle, on
    legs that have them), then Right hip, Left hip and Back - the anchors on
    every pair of legs. A part shows on the tabs it has a fit for. In Blender it is
    tilted to sit flush and settled onto the legs, so it can sit a little
    differently from the page.
  - Arms have three tabs: Right, Left and Two-handed. Two-handed holds the
    pieces with both arms and the weapon in one (two-handed guns, two-handed
    melee, heavy weapons); they go on the right shoulder and take both.
    Picking one replaces the arms, and picking an arm replaces it. A model
    with one skips the hands (its weapon is built in) and the pads (TIOW
    Inbox finds pad spots on single arms only); those picks aren't sent.

Sharing (a username and password per person)
  Lets a few people build models on this page from their own browser, so you
  can print them. They see the page and the light preview copies only, never
  an STL, and what they send is saved on this PC for you to build.
  1. Once: install cloudflared (in a Command Prompt:
       winget install --id Cloudflare.cloudflared).
  2. Once per person: double-click "Share Squad Builder - people.bat", type
     their name and a password (at least 10 characters). Add yourself too.
     The same file changes a password, and takes someone off if you type
     -NAME. Restart sharing after a change.
  3. Double-click "Share Squad Builder.bat". Two windows open; the second
     prints an address like https://some-words.trycloudflare.com. Send that
     to them with their name and password. The address is new each time.
  4. They build, then press "Send for printing". Each send lands in
     D:\Kitbash Library\_builder\received\<name>\<date-time>\.
  5. To build one: open Blender (TIOW Inbox on), then double-click
     "Build received models.bat". It moves the newest set into the inbox
     and Blender builds it as if you'd pressed Send to Blender. Run it again
     for the next set.
  6. Close both windows to stop sharing. Nothing is reachable then.
  Light on the PC: the server and cloudflared use a few tens of MB and
  next to no CPU while idle. It only answers people who sign in; eight wrong
  passwords lock that address out for 15 minutes. Your hidden parts stay
  hidden for them, and they can't change the hidden list.
