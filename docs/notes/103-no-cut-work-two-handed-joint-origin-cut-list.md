**No-cut work, Nov 15: Mar Fil two-handed and heavy weapons seated by the shoulder disc and moved; "origin is the
joint" read as the fit (TIOW Inbox 1.17.9, page index, kb); the share server refuses cross-site posts; the list of
connectors still to cut (`docs/cuts-needed.md`).**

- **Josh, Nov 15:** "do the work that doesn't need a cut. Give me a list across all of the makers that will need a
  cut".
- **Two-handed guns / melee and heavy weapons (Mar Fil)** carry their own arms, so the shoulder disc covers them
  (`marfil.json`: the disc entry under each type). Search (`connectors-2026-11-15-10`, 169 parts, 3 min): 165 sure,
  4 look, 0 none. **44 sure ones were the LEFT arm's disc**: the piece has a disc on both arms, both match exactly,
  and the left won (13-20 mm, 131-177 deg from the library fit): Intercessor bolters / plasma incinerators /
  pyreblaster, Veteran guns and combi weapons, one Bladeguard sword. `seat.py write --near 2` (new) writes only
  fits within 2 mm and 10 deg of the old one and lists the rest (`left_far.txt`): 121 written (match <= 0.0049 mm,
  most moved 1.5 mm / 7.9 deg on Assault two-handed melee). The 44 keep their library fits. **To do:** make
  `find_all` prefer the disc nearest the part's own Shoulder R fit when a connector fits twice (or search only the
  right arm's half); then they need no cut.
- **Moved** (`origins-2026-11-15-3`): all 169 by their Shoulder R fit (the 44 by their library fit), origin 32 mm.
  14 extra test models (10 written, 4 of the 44, each on a Mar Fil torso) with the 340 before: 354 of 354 where
  they were.
- **(d) "no fit = origin is the joint"**: a sidecar's `origin.joint` (set by `Move origins.bat`) now stands for an
  identity fit for that joint where none is stored: TIOW Inbox 1.17.9 (`01_import.py`, when it reads a sidecar's
  fits), `build_index.part_data` (the page index), `kb.origin.with_joint_fit` (used by `maker_view` and `move`, so
  `seat.py`, `kb.carry`, `origins.py` agree). Checked: 37 test models on a scratch copy, then every moved part's
  joint fit deleted (83 sidecars): 173 of 173 parts where they were; `tests/kb/t_kb.py` (+3). Installed (TIOW Inbox
  to addons and bridge, `build_index.py`). **The identity fits are still in the sidecars**: nothing reads them as
  missing now, but leaving them costs nothing and keeps old tools working; dropping them is a one-line option in
  `origins.py` if Josh wants the sidecars smaller.
- **Share server** (item 7, Nov 13 review): `/send` and `/correct` refuse a body that isn't JSON (another site's
  form can't send JSON without a CORS preflight, which this server never answers) and a request with
  `Sec-Fetch-Site: cross-site`; nothing else checked, so it works the same through the tunnel. Test
  `squad-builder/test/t_share_correct.py` (+2, all pass). Installed; takes effect at `Restart share server.bat`.
- **The cut list** (`kits/connectors/cuts_needed.py` -> `docs/cuts-needed.md`, no Blender): one row per maker
  folder and joint, with the parts waiting, their kits and a part to cut it on; Mar Fil rows are only what its
  search hasn't covered. A part is covered when a written seat.py run found its connector sure (or wrote a look), or
  it is a connector's reference. "No cut, a search to run" lists types whose connector exists but weren't searched.
  Left out: torsos, accessories / belt bits (last), bases and other types, Marta heads, TN Rigging Required, hidden
  parts. Nov 15: 89 cuts or placements over 15 maker folders. Re-run after each cut.
