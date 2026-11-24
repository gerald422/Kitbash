# 120 - Reader fix, the review, and the new plan (Nov 24)

**Reader bug found and fixed.** Test marines built only from the overnight proving numbers had wrong pauldrons. A
round-trip check against Josh's own guide seats showed the cause:
- When the seat file was loaded on top of the main reference, Blender had not yet updated the loaded objects'
  `matrix_world`, so every arm and guide from the seat file was read 30-250 mm out.
- Every pad joint from the guide seats was wrong (Arm 2B R by 36 mm). This was also the "torso copies 11.8-30 mm off"
  of notes 119.
- Fix: `bpy.context.view_layer.update()` after the extra files are loaded (`kits/connectors/reference.py`).
- All 11 seated arms that were checked then read back exactly (0.00 mm).
- The overnight runs were stopped. Their numbers are void.

**Also found:**
- The pad search turns pads 9-13° or misses them. The whole pad inside is close to a bowl.
- Marta and Turtle Ninja arms come out turned wrong. They are matched with the Mar Fil disc, and the turn is taken
  from their own files' frame.
- Nothing was written to the library.

**Code:**
- `prove.py --sources` picks parts from `_sources.csv`, so other makers' arms are found.
- `write_joints.py --drop-old MAKERS` replaces `--convert-pad`. Josh decided that arms and pads keep only new-method
  joints. Dry-run only.

**Review and new plan.** `docs/archive/REVIEW-2026-11-24.md` listed where things stood, the issues, and why progress
kept rolling back:
- "sure" taken as "right";
- no check against Josh's placements;
- partial methods written to the library;
- old and new fits mixed;
- plan steps skipped silently;
- the plan not updated.

Josh then set a new method, and the new `docs/PLAN.md` (agreed Nov 24) is built on it:
- Claude seats parts in small batches, on a real marine, with locked hosts and known-good check pieces.
- Josh fixes them by eye.
- Repeated fixes are applied across a kit, for him to check.
- Only his fixed placements are written, and never changed again.

The plan's scope, connectors and joints:
- Every shoulder goes through the one spacer, every pad through the pauldron guide.
- Neck, backpack and topper are joints.
- In: Redwarden, WarGame Exclusive, CyberBrush and BBoosty (no torsos), Bladeguard and Techmarine arms, all Marta
  Tacticus legs, the Turtle Ninja Heresy kits, Springles - Weapons, Bits.
- Old Style Space Knight is out for now. The bionic hip is parked.

The old plan is `docs/archive/PLAN-to-2026-11-24.md`.

**Skill.** Nov 23's seat-by-shape method is `.claude/skills/kitbash-seat-by-shape/SKILL.md`. Its scripts are kept in
`~\Desktop\mar fil connectors\_method scripts (2026-11-23)\` until stage 0 moves them into `kits/seat/`.
