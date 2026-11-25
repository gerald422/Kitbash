# 141 - The TN legs turn, flat bottoms and the mirrored arms (Nov 25)

Josh, on the flat-bottomed torsos: "they have all been rotated to fit onto the legs. whilst that is correct it now
means that the base for those torsos is not flat like the marfil torsos". Then: "ive noticed that the mirroring is off
on the arms".

## What was measured

TIOW Inbox stands a TN or Redwarden torso by its sidecar `upright`. The torso is symmetric about that: its written
Shoulder L is Shoulder R mirrored across the upright's YZ plane to 0.00 mm.

The TN Waist socket carries Josh's legs change (notes 130-132). So Legs 1A on a TN torso is turned **18.5 deg**
against the upright, where on Torso 2 it is turned 0 deg. Split into Torso 2's waist axes:
- 5.1 deg forward;
- 9.7 deg sideways;
- 14.5 deg twist about the vertical.

The same holds on all 54 TN torsos. Redwarden is turned 19.0 deg. The legs' up axis leans 11 deg (Redwarden 10 deg),
so the base is not flat. Mar Fil torsos are within 1.3 deg.

## The mirrored arms: a fault in my files, now fixed

`make_cloak_socket_batch.py` and `make_check_marines.py` stood each written torso on its Waist socket. They also took
the live mirror plane from it. For TN torsos that turns the torso 18.5 deg, and the left arm was mirrored across a
turned plane.

This was only in how those files showed it. The library's Shoulder L sockets are right.

Both generators now use `make_torso_batch.upright` (stand the torso as TIOW does) and `upright_mirror` (the upright's
plane through the shoulders' midpoint). Rebuilt with the same seed (`Check - 5 random marines (2026-11-25 b)`), a TN
torso is square with symmetric arms, and the legs show the turn.

## The base: Josh decides

Josh's legs fix is his, and nothing here changes it (Rule 1). A flat bottom only fixes the legs' tilt, though. The
14.5 deg twist and the 9.7 deg sideways part are what make the base uneven. Asked whether he meant it, or wants the TN
legs re-fixed once and carried across, as before.
