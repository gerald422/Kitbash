**Origins moved for real (Nov 15, item 5 c): 478 Mar Fil arms, legs, shoulder pads and shin pads rewritten so the
file's origin is the joint and the fit for that joint is none; `Move origins.bat`, no Claude. Parts land where they
did (268 of 272 test parts exactly; the 4 others are hip plates on moved legs, 0.1-2.2 mm).**

- **Josh, Nov 15:** the connector run (notes 100) "looked good", go ahead; files being adjusted in the Kitbash Library
  may be updated there (no STL backup for now, he can get them again from MMF / Discord). Accessories still need
  work and are left till last on purpose.
- **What a move is** (`kb/origin.py`): a fit says part = socket x gap x fit. The file is moved by its own fit for
  its joint (new point = fit x old point), so it lies in that socket's frame: joint on the origin, the socket's own
  axes, and the fit becomes identity. The same G goes through everything the sidecar holds in file coordinates:
  sockets and an anchor's three points (G x), other fits (x inverse G), each maker's copy by ITS own fit Gv
  (`align` = Gv x align x inverse G; its sockets and fits with Gv). G is the stored fit made exactly orthonormal
  (Newton steps), so the mesh is never skewed; the fit is then written as exact identity. Not just a slide: the
  socket's turn is baked in too (Mar Fil arms: under 1 deg for 122 of 228, the torso's shoulder sockets lie along
  the kit's axes; legs 11-19 deg, the lean of the waist seat; pads 90-140 deg, they lie in the pad spot's frame).
- **The fit is kept in the sidecar as identity**, so TIOW Inbox 1.17.8 and the page work unchanged. Dropping it
  ("no fit = origin is the joint") is item 5 (d), not done.
- **`origin` in the sidecar** (and in a copy's own `sidecar`): `{"from_file": [16], "joint": fit name, "by": ...}`.
  from_file takes the maker's file coordinates to the file as it is now and adds up over runs. It is what keeps
  everything else lined up: a fresh download can be moved the same way, `kb.origin.maker_view(sc)` gives the
  sidecar back in the maker's coordinates.
- **What reads it:** `kits/connectors/seat.py` searches every part in the maker's coordinates (Josh's blends are cut
  there; a kit's parts share one frame there, which the round connectors' turn leans on) and converts the fit /
  sockets it finds to the file as it is now; a connector cut later on a moved file is recognised (it sits on the
  file as it is) and converted. `kb.carry.Ref` reads a moved folder-mate back in the maker's frame, so a new part
  (unmoved) is still compared like with like. `tests/golden/run.py` compares places in the maker's frame, so
  `golden.json` stays good whichever way a file lies (also: a part mirrored on the spot, `tiow_mirrored`).
- **Left alone, listed:** a part with no fit for its joint; a `scale`; any key not known to be safe (`upright`,
  `offHand`, `pivot`, `types`, an unknown one: `kb.origin.TOP` / `SOCK` / `VAR` / `VSC`); an ASCII STL. Heads,
  packs, hands and weapons need their config (and for some those keys handled) before they can move.
- **`kits/connectors/origins.py`** (`Move origins.bat`; config = the maker's connector file: maker, types, and the
  `fit` entries name each type's joint): list, report, Y; per part: sidecar, STL and page preview copied to
  `_backups\origins-DATE\before`, the STL written beside the old one and its corners checked against the old ones
  moved (2e-4 mm) before it replaces it, sidecar saved (not merged: everything in it moves, nothing is dropped; the
  move is worked out again from the file as it is at that moment), preview moved (after the STL, so Prepare doesn't
  remake it), index entry refreshed (`kb.index.update_part` now refreshes a part's copies too), `journal.jsonl`.
  A part that fails half way is put back at once. `restore`: sidecar + STL + preview back where both still have
  the run's md5 (a part saved since stays moved: file and sidecar still agree). Run again any time: only parts
  whose joint is off the origin move (after Seat connectors or a Save fit).
- **Rehearsal** (scratch copy of 109 parts, 12 models built with TIOW before / after): 129 of 132 where they were;
  restore = every file byte-identical. What it found:
  - the 3 others: `Jump Captain - Hip Plate With Pouch / Holster` on moved legs, 0.8-2.2 mm, 1.4-5.5 deg. The legs'
    sockets are right (shin pads on the same legs: 0.00). A 0.00001 mm slide of the same legs changes nothing, so it
    is not plain rounding; believed to be rock / settle (`inner_side`'s ray grid, `settle_onto`'s random 4,000 of the
    host's corners) taking other samples once the legs' file is turned. Not proven. Accessories are last (Josh).
  - the golden run's turn came from acos of the trace: a last-place rounding of the 4-place matrices read as
    0.6-0.9 deg. Now from the skew part (atan2). `--squads` / `--golden` for a one-off before / after.
  - the golden run writes anchors TIOW works out at import into the library's sidecars (as any import does).
- **The run** (`_backups\origins-2026-11-15`, 4.7 GB of originals): 478 moved, none failed, 5 left (no fit: Captain
  with Jump Pack Arm 3 L and Legs, Bike Chaplain Shoulder Pad 1 R / 2 R / L). Arms 228 (origin 32.4 mm median),
  legs 90 (29.2), shoulder pads 80 (3.3), shin pads 80 (4.0); 115 copies. After: 26 models (the 14 golden + the 12)
  on the real library against a snapshot taken just before: 268 of 272 where they were (the 4: those hip plates,
  0.12-2.19 mm). All 478: fit identity, index = sidecar (copies too), preview box within 0.1 mm of the STL's and
  newer than it. `seat.py` dry on 13 moved parts: same connectors, sure, 0.0 mm from the new fits.
- **Share server**: previews went out with `max-age=86400`, so a browser kept yesterday's preview under today's
  index (a moved part then sits wrong on the shared page for up to a day). Now `no-cache` + ETag (304 when
  unchanged); installed (`kb.py install origins-2026-11-15`), takes effect at `Restart share server.bat`. Previews
  fetched before that restart stay cached up to a day: clear the browser's cache for the shared page if moved parts
  look scattered. The page on the PC itself reads files directly (no cache).
- **The page's corrections log** needs nothing: a line is replayed only where the index's fit is still the line's
  `before` or `after`.
- **Not touched:** `golden.json` (still Nov 13's, before the connector run: `Run checks.bat` lists Mar Fil parts by
  those fractions of a mm until Josh records again), TIOW Inbox, the page.
