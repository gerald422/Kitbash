**Revised 17 Oct 2026: flat discs, not Shape Match.** Arm, leg and chest joints are flat discs for every creator (Mar Fil's legs and chest are the exception). Shape Match can't locate or roll a flat disc. The Set Origin at Flat engine can, run automatically.

Tested on `Operation Marine\3rd attempt finalising.blend` (24 Sep):

| Part | Rule | Found | Area | Distance from Josh's hand-set origins |
|---|---|---|---|---|
| Arms | largest flat patch facing −X | 33/33 | 16.1 every time | 0.02–0.11, one at 0.27 |
| Legs | largest flat patch facing +Z | 21/22 | ≈36.8 | 0.1–0.28 |

- The one leg miss (32-Legs-5) picked a 21.6 patch, so an area check would flag it for review.
- All arms keep their imported rotation (rot = 0). Josh's convention is: origin at the disc centre, axes as imported, identity offsets.

**Revised master:** disc direction in that creator's import axes, disc area (±10%), and a fixed creator correction. To apply one, find the matching patch, put the origin at its centre, and set rotation to the import axes × the correction. Fall back to a roll sweep only for creators whose export orientation varies.

**Cross-creator example in that file:** torso `23-Torso-2.001` carries `arm__Torso_r` and `HeresyArms_r`. The second is the first rotated 91.7° about Z, shifted −0.17 along X and −0.73 along Z in socket space. That is that creator's correction. Recommended: bake corrections in at import so each torso needs one socket per joint.

**Units:** that file is `scale_length` 1.0 (metres) with parts at 1 STL unit = 1 BU. The inbox add-on now defaults to 1:1. Bake for Print exports ×1000 in such a scene, so set Unit Scale to 0.001.
