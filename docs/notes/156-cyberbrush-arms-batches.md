# 156 - Stage 3: CyberBrush arms (Nov 25)

Josh: "CyberBrush arms".

**In scope (CyberBrush - Tacticus, Space Bugs Hunters):** 38 right and 35 left plain arms without an exact fit. One
was already exact. The 7 two-handed parts wait for the two-armed stage. The "2 Hand Sword" and "2H Axe" folders' four
right arms are filed as single arms (category Arms), so they are in. If Josh removes one as half of a weapon, it goes
on `not_arms.txt`.

**Two files, with the 0.32 mm pre-set** (`--shift 0.32,0,0`, as Josh asked for TN, notes 153):
- `03 Stage 3 - CyberBrush right arms (2026-11-25).blend`: 38.
- `03 Stage 3 - CyberBrush left arms (2026-11-25).blend`: 35, each shown as its mirror image on the right spacer.

**Dry runs:**
- Right fits are 0.298-0.355 mm from the old ones.
- Left fits are 0.118-0.412 mm. That's the same 0.06 deg socket rounding as every left arm. CyberBrush files sit far
  from their own origin, so it shows up as up to about 0.1 mm either way at the fit.

**Renders:** 12 of the right arms sit at the shoulder.

**The first render stalled:** all 38 columns, run in the background after the dry runs. It wrote nothing after 17:22.
- The background task was stopped with TaskStop.
- Its Blender (found by command line and start time, started 17:21, `-b` on the right file) had already exited.
- Josh's own Blender (the left file, opened 18:02) was left alone.
- The renders were redone at 12 columns with a time limit.
