**Adjust on the page (Nov 12): move / turn / snap / seat a placed part and save it as its fit.**

Why: Josh wants consistent placement without Claude running anything when parts are added, and correcting by eye in
Blender is slow (snapping against millions of faces). The page already draws parts where Blender puts them and can
write to the library, so corrections are made there. Every correction is logged, which also shows which joints keep
needing fixes.

- **What it does** (`squad-builder/src/app.js`, section "Adjust"; three.js TransformControls r147 vendored): click a
  placed part, a handle sits on the socket it hangs from (socket x gap); Move / Turn change the fit in that frame
  (F' = Sw^-1 . handle . F0); Snap = click a spot on the part, then where it should go (translation); Seat = slide
  the part toward its host (direction: part centroid to the host's nearest point) until first contact, 0.1 mm in,
  rays both ways on the ~6,000-triangle previews. While trying out, the fit applies to every model showing the part
  and to its plain mirror on the other side.
- **Save fit**: writes `fits[<socket>]` + `exact` into the part's `.sockets.json` (a maker's left copy: its
  `variants[i].sidecar`; a part shown plain-mirrored: the fit it mirrors, conjugated by MX, so both sides move). The
  file is read and written losslessly (only the changed fit's lines differ; floats written as Python's json does), so
  `kb.sidecar` re-saves it byte-identically and `merge` keeps it (`exact`). TIOW Inbox already places `exact` fits
  without rock / settle / base rise, so no add-on change.
- **Log**: `_builder/corrections.jsonl`, one line per save: at, part, v, sock, host, before, after, mm, deg. Replayed
  over the index when the page loads (an entry applies while the index still has its `before` or `after`), so
  Prepare isn't needed after a correction. With no library folder (test, demo, shared page) a save lasts the visit.
- **Not adjustable**: the torso (root) and brought parts (body adaptor, wing connector).
- **Tests**: `squad-builder/test/t_adjust.js` (26 checks): all 6,895 repo sidecars round-trip byte for byte through
  the page's reader/writer; a written fit changes only that fit and `exact`; turn about the wrist, reset, save;
  mirrored pad saves the right-side fit; maker's left arm saves its own entry; Seat brings a pack pulled 4 mm off the
  back onto it again; Snap; a real click selects; Send unchanged; real file writes (the browser's private folder
  standing in for the library); log replay. Not run: a squad sent to Blender after a page correction (the `exact`
  path itself was tested with Save Correction in 1.17.2).
- **Arms prototype, same night** (PC, `Desktop\kitbash-calib\arm3.py`, not in the repo): finding anchors from the
  mesh alone on the 48 Assault arms against Josh's hand-set values: shoulder disc centre 0.06 mm median (0.27 max);
  wrist face centre 0.19 mm, axis 1 deg; roll carried from a reference cuff 0.3 deg on oval-wrist B arms, 2-40 deg off
  on round-wrist A arms (nothing near a round wrist fixes roll; his were set by eye). Hence: his placements win, the
  finder fills unplaced parts, round wrists get corrected on the page.
- `tools/kb.py install TASK [--check]`: on a repo clone on the PC, copies the repo's version of installed files that
  differ, backing the old ones up.
