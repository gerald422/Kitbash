**On hold (Josh, Oct 29: "Hold on all the bionic legs bits as we will fix the plug first").** Not delivered: 1.18 and Finalise 0.3.2 stay in `/home/claude/tiow_blender/` and `/home/claude/finalise/`. Josh will send an example of where he wants the plug. State reached after his reviews (Oct 26–27, "nearly perfect" / "almost there"):
- **Cup fix:** the true LEG_HIGH hip cup is at (−0.91, −0.163, 9.801), r 2.762, opening (−0.482, 0, 0.876) (sphere votes; the first fit was ~1 mm off, which put the plug into the thigh). The kit files are a left leg; the right leg uses the mirrored meshes and points (`_bio_mirrored`, `bio_kit_side`).
- **Sloped cut like the ribbed hip it replaces:** `bio_belt_cut` tilts the cut 30° (`BIO_BALL_TILT`) plus a swing iterated from a seated pre-pose; the ball sits on the leg's line through the middle of the leg section; the pivot puts the plug section's high edge on the glue point. Pose solve (`bio_pose`, LM over rotation + knee) keeps the cup within 15° (`BIO_CUP_MAX`) of the ball.
- **Kit scale:** k = mean leg width / ball diameter, within 0.8–1.4, stored per model so both legs match; the panel has "Slope N° ◀▶" and "Kit size N% ◀▶".
- **Stump:** the plug is cut just under its neck step and sunk 0.15 into the leg, so only the lip shows; where the leg is narrower than the plug a skirt is lofted from ray-cast leg sections and joined by Boolean.
- Tests on that state: `test/v118/t_bionic.py` 179 checks, `t_bionic_fa` 9, `t_bionic_click` 3. Renders: `bionic_hip_v6.jpg`, `bionic_hip_v6_closeups.jpg`.

**Open:**
- Josh's plug-position example.
- Find where the kit lives on Josh's PC (not on D: or the Desktop); the add-on looks for LINK_LEG.stl in the library.
- Armour places, which Josh sets once.
- Springles legs need setting up as legs first (waist, upright, base); their shins are then clicked.
- Springles' own bionic legs as donor legs is a possible later mode.
