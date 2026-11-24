# 129 - Stage 2: Josh's legs change applied across Redwarden / Turtle Ninja batch 1 (Nov 24)

Josh fixed two pieces on the Redwarden Prime Techmarine torso in batch 1 (notes 128):
- the helmet: 2.27 mm, no turn;
- **Legs 1A: 1.97 mm and 19.0 deg in its Waist socket's frame.**

He asked for the same legs change on the other legs in the file. PLAN Method step 4 is "a repeated fix, applied
across the batch for him to check".

**How.** The change is taken in the frame the legs sit on, their Waist socket: `D = inv(start) . now`. Every torso
stands on that same socket (stood on its waist as Torso 2, notes 128), so `D` means the same thing on each, and each
of the other 21 legs gets `own(torso) . start . D`.

Josh's file is never overwritten. The result is a new file beside it:
`02 Stage 2 - Redwarden and Turtle Ninja torsos 1 (2026-11-24 b).blend`.
- His helmet change stays as he made it, on the Redwarden only.
- The applied legs are tagged `kb_applied`.
- `read` lists his two changes plus the 21 applied legs, all the same change.
- `write` takes the applied legs like his own once he has checked them.

New command: `batch.py apply BATCH.blend FROM_ID OUT.blend`. It puts FROM_ID's change on every piece with the same id
suffix (the reference column is left alone), and refuses to overwrite. It was tested by rebuilding the "b" file from
Josh's file: every piece matches (0.000).

Renders `02t b check - ...png` beside the batch: on each torso tried (Mk2 A1, Mk6, Mk10 and the Redwarden) the legs
take the same turned stance under the waist.
