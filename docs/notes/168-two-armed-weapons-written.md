# 168 - Two-armed weapons written; long paths in the write (Nov 25)

Josh: "both good to write" (the CyberBrush b file and Marta).

**Written** (backups `batch write 2026-11-25 2256` and `2257`):
- CyberBrush: all 8, with his 0.45 mm move; he re-turned Spear Arm 1 (172 deg, 13 mm) in the b file.
- Marta: 35. He changed 4 more by eye (2H Arms For Hammer, And Arms With Handle R L, Jan 2026 Set Arms 3 With Katana,
  Sharks Arm 3) and placed the DW Frag Cannon (23 mm, 12 deg). He removed DW Weapon T Ua 1 from the file again, so it
  stays on `kits/seat/not_arms.txt` for the weapons stage (stage 5).

All 43 read back at 0.0000 mm. The batch files went to the Recycle Bin.

**Stage 3 two-armed is done:** 212 written (Mar Fil 169, Marta 35, CyberBrush 8). Out: Turtle Ninja's 28 (Josh, notes
167) and Gravis / Phobos / Terminator. Next in PLAN.md: stage 4, the arms' sockets.

**Long paths:** the first Marta write stopped at its backup. A Marta Combo Weapons sidecar's backup path
(`_backups\batch write ...\before\lib\Marta PunkGirl - Weapons\Primary Combo Weapons\...`) is over Windows' 260
characters. The write backs everything up before touching the library, so nothing had been written. `batch.py` now
uses `\?\` long paths (`lp()`) for the backup and for the library and repo copies. Without it, a too-long repo
path would also have been skipped quietly as "not the same".
