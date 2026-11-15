**`Seat connectors.bat` (Nov 15): Mar Fil arms, legs, shoulder pads and shin pads seated by Josh's connectors, no
Claude. Search (~22 min, 12 Blender workers), report, Y to write (backups first), `restore`, `write`. A full dry run
is ready to write (`_backups\connectors-2026-11-15-8`); nothing has been written to the library yet.**

- **Files**: `Seat connectors.bat` (repo root), `kits/connectors/seat.py` (run / search worker / write / restore),
  `kits/connectors/marfil.json` (which object in which of Josh's blends is which connector, its reference part, and
  the fit or socket it stands for; pad insides from his placed pad + spot shell, notes 099).
- **What it does**: reads the connectors from `~\Desktop\mar fil connectors\` and stops if one no longer sits on its
  reference part (moved in the blend); searches every part of the maker in those types (`kb.connect.find_all`);
  writes `_backups\connectors-DATE[-N]\report.txt` (opened) and `plan.json`; on Y backs up each sidecar and
  `_builder\index.json` to `before\`, merges the fit (`kb.sidecar.merge`: `exact` fits stay; a sidecar the merge would
  make invalid is skipped, existing faults such as 32 pads without `schemaVersion` don't count), adds sockets a part
  has none of (sure only), refreshes the page index for those parts (`kb.index.update_part`), writes `written.json`.
  sure = written; look = written with a note in the sidecar's `notes` ("LOOK, check by eye") and listed; none =
  untouched, listed by kit (= what to cut next). Reference parts, variants and both-sided connectors (shin spot) are
  searched, not written.
- **restore**: puts back each sidecar whose md5 is still what the run wrote (one saved since is left, and listed);
  the index file itself if untouched since, else its entries refreshed. Round trip tested on a copy of 10 parts +
  the index (scratch): write then restore = every file byte-identical. **write**: writes the last searched, unwritten
  run without searching again.
- **Search fixes found on the full run** (`kb/connect.py`):
  - `near` (find / find_all / choose / prefer_file_turn): the pose the part's own fit or socket gives the connector.
    Ties go to it instead of the file frame; a **round connector takes its turn from it** (the swing is the pose:
    Intercessor bolter arms hold the gun 82 deg round from where the disc's little extra fits). No fit: file frame.
  - **Round is the connector's own property** (`Connector.round`: within 0.02 mm of itself turned 30 deg; only the
    disc, 0.012); on a part the disc could look keyed and its turn was left to the shape (55-80 deg off).
  - **find_all**: a connector at its own joint (within 1 mm of `near`) goes first and keeps its place even when a
    neighbour's claim overlaps it (the pad spot touches the disc and pushed it 59 deg round on Power Fist A2).
  - seat.py: a look match keeps the old place (settled from it) when that fits within 0.01 mm: no legs flipped.
- **Full dry run** (478 Mar Fil parts): 440 fits (304 sure, 136 look), 11 sockets (Forearm on Assault Arm 8B / 8C and
  Jump Chaplain Arm A-D), 7 parts get their first fit (Captain with Jump Pack arms 1 / 2 / 4, Bike Chaplain arms and
  legs); left: 36 none (Intercessor / Bladeguard / Techmarine / Bike Chaplain pads, 5 bolter arms, Captain legs,
  Intercessor Legs 10, Veteran Body F, Veteran Shin Pad M, 4 Bike Chaplain weapons filed as knee pads), 3 exact.
  Moves from the old fits: arms median 0.06 mm (8 over 1 mm), legs 0.45 mm (heading kept, 4 over 1 mm), shoulder
  pads 0.05 (max 0.4), shin pads 0.02 (max 0.7). So the library mostly stays; it gains a fit where shape decides.
- After a write: `Run checks.bat` (the golden squads with Mar Fil parts will differ by those fractions of a mm:
  record again only if they look right); export sidecars to the repo (`library-tools/sync_sidecars.py export`).
- Dry-run folders `_backups\connectors-2026-11-15` .. `-7` are Claude's test runs (unwritten): Josh's to delete.
