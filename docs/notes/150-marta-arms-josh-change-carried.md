# 150 - Marta arms: Josh's change carried across the batch (Nov 25)

Josh, in `03 Stage 3 - Marta right arms 1 (2026-11-25).blend`: "ive made one change so far can that be applied across
all of the other marta arms please".

**His change** (`batch.py read`, saved 13:43): Jan 2026 Arm 4 R moved 0.32 mm along Torso 2's X (outward, the depth
on the spacer), with no turn.

**Carrying it:**
- `batch.py apply` sets every piece to the source piece's pose in its frame. That is right for one piece on many
  torsos (the legs, the cloaks), but wrong for 28 different arms.
- So `apply` gained `--delta`. It takes only his move, from where the arm was built (`kb_seated`) to where he put it,
  in the frame it sits on: C = (now in frame) . (as built in frame)^-1.
- It puts C on every other piece of the same kind, keeping each one's own seat: new = on . C . on^-1 . old.

**Result:** `03 Stage 3 - Marta right arms 1 (2026-11-25 b).blend`, a new file. His file is untouched (never rebuild
or overwrite a file Josh has, notes 148). `batch.py read` on it: 28 of 28 arms changed, "the SAME change", each
0.32 mm in X with no turn.

He carries on in the b file.
