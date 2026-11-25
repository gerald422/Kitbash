# 136 - Stage 2: the cloaks on Torso 2 written (Nov 25)

Josh finished `02 Stage 2 - cloaks on Torso 2`: "all the capes we are keeping are now done. i removed a few. i also had
to scale 2".

**Written** (`batch.py write`, backup `D:\Kitbash Library\_backups\batch write 2026-11-25 0015`):
- **Torso 2's Cloak socket.** This is Torso 2's Back frame, written from column c1 as half "both".
- **Cloak fits for the 17 kept cloaks:**
  - CyberBrush Bug Hunters Cloaks 1-5;
  - Marta 49 March 2026 Cloaks 1-7;
  - Marta Deathwatch 2;
  - Marta Aug 2025 Cloaks 3, 4 and 5;
  - Marta Space Wolves Cloak 1.

  Every joint placed from the library (socket . fit) matched his file: 0.0000 mm, 0.000 deg.

**Removed by Josh (not written):**
- Marta Jul 2025 (the fur), Sharks, and Space Wolves Cloaks 2 and 3;
- earlier, Marta Aug 2025 Cloaks 1 and 2 (Terminator).

Their sidecars are unchanged, and they are not yet hidden in the library: asked.

**Scaled by Josh:** Marta Aug 2025 Cloak 4 at 95.58% and Cloak 5 at 91.28%, both evenly.
- A fit must stay rigid. So `write` now gives a part Josh scaled its own `scale`: the old scale times his. The fit is
  written unscaled, in the scaled file's coordinates.
- TIOW Inbox already scales a part's mesh by its sidecar `scale` (Springles 110%, Marta two-armed 0.9), and
  `batch.stl_tris` does too. So the next batches show these two cloaks at his size.
- `write` refuses a scaled part that is uneven or has a mirror fit.

**Also in `write`:** a part Josh deleted from the batch file is skipped and listed, instead of stopping the write.

Next: the Cloak socket on every other torso (Mar Fil, Redwarden, TN), carried by each torso's Back socket, in batches of
about 20-25.
