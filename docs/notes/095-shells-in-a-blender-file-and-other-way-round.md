**Shells for five part types in one Blender file, and "Other way round" on the page (Nov 14). Josh's decision the same day: origins are to be moved for real, so a part needs no fit of its own.**

- **Josh (Nov 14, after notes 094's shells):** "I want to move the origins for real as that should remove the need for
  sidecars and simplify this massively ... move this part to world centre and adjust the origin by the mating process
  rather than keeping thousands of references ... if I wanted to share the mechanism I just need to share the shells
  and a script." He asked for shells for pads, heads, backpacks, arms and hands in a Blender file, where he does one
  example a part type a creator; and for direction "a button in the web app similar to hidden that says this should
  be the other way around. On save it would then adjust the orientation."
- **`kits/nofit/shells.py make`**: one shell a maker folder (maker + armour type) and type, 42 in all (pads 12, heads
  7, backpacks 6, arms 11, hands 6), each the mating faces of ONE fitted part moved by that part's fit, so it lies
  where the part sits on its joint: the scene's centre is the socket (Pad R, Neck, Back, Shoulder R, Hand R; lefts
  mirrored), 1 unit = 1 mm. Which part: pads, the master of notes 094; Mar Fil heads and arms, Josh's reference
  helmet 1 and arm 1A R; otherwise the fitted right-hand part with the folder's most ordinary box. Which faces: pads,
  the inside (`kb.carry.inner`); arms and backpacks, the flat face at the joint (the level with most area among faces
  within 6 / 8 mm looking back into the joint); heads and hands, faces within 4 / 3 mm looking back into it.
  `shells.json` lists what each came from. Files: `~\Desktop\TIOW Blender bridge\shells\` (not in the library, not in
  the repo).
- **`shells.py blend`**: `shells.blend`, one scene a type with its shells at the centre and Mar Fil's torso / arm
  round that joint as an unselectable wire guide (object names = the shells; each carries `from` and `socket`).
- **How good they are (check pictures looked at):** pads are clean insides, lying together over the arm's shoulder
  (TN Moritat's turned, as in 094). Arms and backpacks are thin flat faces for most makers; where no flat face was
  found the fallback took everything near (Marta Gravis arm, TN backpack: cluttered). **Heads and hands are rough**:
  a ball or ring with bits of helmet rim and fingers round it. Those want the mating faces chosen by hand in Blender
  (select, separate) or a rule a joint design; nothing reads them yet.
- **No shell (nothing fitted to take it from):** Marta heads, backpacks and jump packs; Springles hands; knee / shin
  pads and jump packs were not asked for. His first example for those is mated to another maker's shell or the guide.
- **The page: "Other way round"** in the Adjust panel (`squad-builder/src/app.js` `adjAround`, `shell.html`): half a
  turn of the selected part about its joint's own axis (the socket's Z) through the part's middle, as a pending
  change; **Save fit** keeps it (sockets file + corrections log, as any adjustment), Reset drops it. Page rebuilt
  and installed (`kb.py install page-around-2026-11-14`, old page in `_backups\page-around-2026-11-14\before`).
  Checked: `node --check`, `build_page.py --check`, the page loaded from a local server (button there, disabled with
  no part, no console errors). **Not checked: the turn itself on a model** (no library connected in that browser).
- **Moving origins for real: not started.** What it needs first, said to Josh:
  - the STLs have no backup, so re-origined files go to a new folder (or wait for his backup), never over the
    originals in place;
  - only parts that hang off something lose their fit (pads, heads, packs, hands, weapons: origin at the joint, fit
    = none). Parts things hang off still have to say where: a torso's five sockets, an arm's pad and hand spots,
    legs' base and belt, plus mirrored copies, scale and type. Those stay in a sidecar, or become shells of their
    own later;
  - TIOW Inbox and the page read fits today: "no fit = origin is the joint" has to be added to both.
- **Next:** Josh places one example a type a creator in `shells.blend` (import the library STL, its name is kept;
  move it onto the shell; save); the placements are then read from the file and the rest of each folder mated to
  the shell (`masters.py one` does pads; the same seating for the other types is to build).
