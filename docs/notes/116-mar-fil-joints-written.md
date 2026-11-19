# 116 - Mar Fil joints written to the library (Nov 19)

**The write step.** `kits/connectors/write_joints.py RESULTS.json [MORE ...] [--skip FILE] [--dry] [--yes]` (or
`Write joints.bat`) puts a proving run's joints into the sidecars, in file coordinates as `seat.py` does (fit in the
file = F @ back, socket = G @ S):
- children: the fit, sure or near; hosts: sockets, sure only; legs: Shin R / L from the ankle balls; torsos: Shoulder L
  mirrored from Shoulder R about the waist;
- near fits go in the sidecar's `check` list; the Squad Builder shows "near fit (Waist): check it" until corrected;
- copied / auto anchors on the written sockets are replaced (PLAN step 6); clicked anchors, `tiow_corrected`,
  `tiow_holds` and `exact` fits stay (the two hand-fixed Waist fits kept);
- mirror variants inside right sidecars are rewritten as the mirror of the new numbers, after checking one old pair
  follows that convention;
- the skip list (`kits/connectors/marfil_write_skip.txt`): Intercessor bolters (point every way), Bladeguard shields,
  near Bladeguard melee, Jump Chaplain Legs D's waist (176 deg round);
- backups in `_backups\connectors-joints-DATE\before`, `written.json` md5s, `_builder\index.json` refreshed; undo
  with `Write joints.bat restore` (seat.py restore).

**Left files.** `prove.py --left` searches the left-hand files (`side` L in the index, for arms, melee, pistols, hands,
shields, pads, knee pads) mirrored, and turns the result back (MX M MX, names R -> L). Checked on run 25: the left
files' joints turn as their right twins mirrored (0.1-0.3 deg); they differ by where each file's origin sits. Sheets
leave the left results out.

**Run 25** (reference: the 17:02 `Kitbash reference updated.blend` with one waist cut), all of Mar Fil, 859 parts
(279 left). Written: 723 sidecars, 713 fits, 350 sockets, 124 near (flagged), 177 mirror copies, 314 copied / auto
anchors replaced. Left as they were: 136 (most on the skip list; ~16 nothing found: Intercessor backpacks, Chaplain
on Bike knee / shoulder bits, two Veteran helmets). Arms 190, Melee 160, Shoulder Pads 78, Knee Pads 74, Heads 72,
Pistols 49, Legs 46, Backpacks 27, Hands 12, Chests 6, Jump Packs 6, Shields 3.

**Installed:** the page and `build_index.py` (near flag kept through Prepare), `kb.py install`; sidecars exported to
`library/` (it was also behind on the Nov 15-18 writes).

**Reference renames** (Josh, Nov 19): `another waist legs cut` -> `Intercessor Legs Waist`, the old `Assault Legs
Waist` -> `set aside old Waist` (not read). Backup: `Kitbash reference updated (before waist renames 2026-11-19).blend`.

**Cut-only page (Josh, Nov 19, after 20 random marines).** The write left 640 Mar Fil parts untouched (532 with old
fits: types with no cut yet, parts the search missed) and, on written parts, old sockets where no cut joint was sure:
58 arm wrists (13 of 23 weapons on the random marines sat on them, the ones that looked wrong), 26 pad spots, every
belt / hip / plate / buckle / trophy spot. So the page now shows only what the cuts made: `_builder\cut_only.json`
lists each written part's cut-made fits and sockets (and its mirror copies'); with `"on": true`, `build_index.py`
leaves out every other part and every other joint (fits Josh corrected by hand stay), and parts with no cut fit
for their step. Sidecars are not changed. 719 parts on the page (all Mar Fil: Arms 190, Melee 160, Shoulder Pads 78,
Knee Pads 74, Heads 72, Pistols 49, Legs 42, Backpacks 27, Hands 12, Chests 6, Jump Packs 6, Shields 3); weapons go
only on the 69 arms with a cut wrist. `write_joints.py` adds what it writes to the list and rebuilds the index while
it is on; restore puts the list back. `"on": false` and Prepare: everything again.
