# 151 - Marta arms batch 1 written; the not-arms list (Nov 25)

Josh, on `03 Stage 3 - Marta right arms 1 (2026-11-25 b).blend`: "i removed one item which wasnt an arm. Can that be
logged so it can be picked up with weapons later. Aside from that good to go".

**Written:**
- The Shoulder R fit of 27 Marta right arms, each with his 0.32 mm change (notes 150).
- Each fit is 0.32-0.34 mm / 0.04 deg from the old one.
- 28 sidecars, with Torso 2 unchanged.
- Every joint read back at 0.0000 mm.
- Backup: `_backups\batch write 2026-11-25 1347`.
- Both files (his and the b) and their .blend1 went to the Recycle Bin.

**The removed item:** Marta Deathwatch `DW Weapon T Ua 1` (Bits Death Watch/Arms). It is a weapon filed as an arm,
with category Arms and a Shoulder R fit. Nothing was written for it.

**Logged:** `kits/seat/not_arms.txt` lists parts filed as arms that Josh says aren't arms.
- `make_arm_batch.py` leaves them out and says so.
- The weapons stage picks them up from there (also in `docs/OPEN.md`).

**Worth checking:** the same folder has `DW Weapon T Ua 2` and `DW Weapon T Ua 3`, also filed as Arms with a
Shoulder R fit (Ua 3 also has a Pad R socket). Josh hasn't seen them yet. They will come up in the next Marta batch,
where he can remove them the same way.

**Next:** the other Marta arms with the 0.32 mm pre-set: 79 right (minus any on the list) and 60 left, the left
ones fixed as their mirror image (notes 147).
