# 143 - The Redwarden torso stood at the TN height (Nov 25)

Josh, in the legs redo file (notes 142): the Redwarden column "sits so much lower ... it should align with the TN one".

**Why it was lower:** each TN torso's `upright` (how TIOW stands it in the Mar Fil frame) both turns it and lifts
it, so its Waist stands at 29.50 mm, close to Torso 2's 29.31. Redwarden's `upright`, from `kits/rw_spr/sidecars.py`,
only turns it 180 deg to face +Y. With no lift, its Waist stood at 11.45 mm and the whole torso sat 18 mm lower.
This affects where TIOW drops the torso when it imports it (placement "FILE") and how the batch files show it. It
never affected how parts seat on it.

**Fixed:**
- The Redwarden torso's `upright` is lifted 18.05 mm, so its Waist stands at the TN height.
- Its sockets and fits are unchanged.
- Backup: `_backups\redwarden height 2026-11-25 1234`.
- The builder index doesn't carry `upright`, so it needs no rebuild.

The legs file was rebuilt as `02 Stage 2 - TN and Redwarden legs redo (2026-11-25 b).blend`. The three floors now sit
within 1.4 mm of each other (-0.58, 0.78, 0.62). The first build (unsaved by Josh) went to the Recycle Bin.
