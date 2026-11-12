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

**Later the same day (Josh: rotating is hard because of the origins; saves must work from the shared page).**

- **Handle at Joint / Middle.** Middle puts the handle at the part's bounding-box centre (socket axes), so it turns in
  place. General form: handle delta U = P.P0^-1 in the world, fit delta L = Sw^-1.D.Sw, D = U (or U^-1, below).
- **The torso can be turned**: everything hangs off the torso, so it is saved as the legs' fit the other way round
  (D = U^-1), about the waist socket. Snap and Seat are off for it.
- **Shared page saves** (`share_server.py`): `POST /correct`, owner's sign-in only (403 otherwise; the page then keeps
  it for the visit). Owner = the user marked by `--owner NAME`, else the first added. The server checks the part is in
  the index, the fit is rigid, and that the file still has the page's `before` (409 if not); rewrites the sockets file
  exactly but for that fit and `exact`; backs the old file up once a day in `_backups\page-corrections\<date>\`;
  appends `corrections.jsonl` (with `by`). It also serves that log so the shared page replays it.
- Tests: `t_adjust.js` 30 checks; `test/t_share_correct.py` (22, runs the server on a throwaway library and drives the
  shared page as owner and as someone else).
- **What Josh has been asking for since the start (origins):** in Blender every imported part keeps the maker's file
  origin, which for kit-frame makers is the middle of the scene, so turning a part there swings it about a far point.
  The page's handle already sits on the joint; Blender needs the same: TIOW Inbox to put each part's origin on its
  joint at import. Not done: it changes how every placement is read back (Save Correction, anchors, variants), so it
  needs the golden run in Blender. See OPEN.md.
- **View lock (Josh: the camera moved while he was placing).** A drag that missed the handle went to OrbitControls. While
  a part is selected in Adjust: left button / one finger does nothing off the handle, right-drag / two fingers turns
  the view, wheel / pinch zooms, damping off. "View locked" toggles it. `t_adjust.js` 33 checks.
