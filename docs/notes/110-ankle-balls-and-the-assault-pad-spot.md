# 110: Ankle balls place the shins; the Assault pad spot (Nov 17-18)

Proving runs 6-14 (`~\Desktop\mar fil connectors\proving 6` ... `proving 14 legs`, `proving 8 arms`) on Josh's
reference file. New `prove.py` options: `--types`, `--all <type>` (every part of the type), `--kits`.
Veteran and Bladeguard legs are left out (`NOT_LEGS`, Josh Nov 17).

## The shin spot slides

Josh: the shin pads were off, and the balls at the ankles should give the fit. His cuts: `legs ankle ball outer right`,
`inner right`, `outer left`, `inner left` (the exposed dome of each ball, under the shin pad).

Run 6 searched each ball near where the shin spot put the socket. Balls were sure (0.0013 mm), but 0.2-4 mm from where
the "sure" shin spot predicted them, and the ankle axis up to 19 deg out. A smooth shin fits as well slid or rolled.

## Balls are found as balls

- A ball fits itself at any turn, and the outer and inner balls are one sculpt (4.44 mm apart). The cut search
  returned 6-100 tied poses; even on Legs 1A, the leg the cuts were made on, it put the inner cut on the outer ball,
  turned 180 deg (runs 7-11, `ball_check.py`).
- A ball fitted to the leg's own surface wasn't steady either: only a cap shows, so radius and centre trade off
  (1.9-2.25 mm).
- What works (run 12 on, `prove.balls_near` / `ankle_pair`): one ball size for all (the smallest cut's, 2.049 mm).
  Every surface point facing out of a ball that size votes for the centre behind it, and the centre is refined on
  the points of that ball. Then take the pair 4.44 mm apart (within 0.04) nearest where the shin spot puts it.
  - The reference's balls come from the same search on Legs 1A, so both are measured alike.
  - Outer is the ball the shin spot points to; that only needs it right within 90 deg.
- The ball middle and the line through the two balls set the shin. The shin spot then sets only the lean: the one turn
  left about that line, searched alone, so it can't slide. On clean sides it fits to a median 0.005 mm (max 0.03).
  The shin spot alone had been a median 0.45 mm / 17 deg out.

## Legs facing backwards

Run 13: 12 Intercessor legs (2, 3, 4, 7, 8, 11, 13, 16, 18, 19, 22, 24) came out turned about 175 deg from their
library fits. They are saved facing back in their files, and the round waist kept the file's turn. Left and right then
swapped, so the right shin spot fitted the left leg to 0.30-0.35 mm, which looked like a different sculpt. A near
buckle now turns such legs round (more than 90 deg out only), flagged.

## Run 14: legs

87 of 94 sides clean:

| Kit | Clean sides |
|---|---|
| Assault | 25 of 26 |
| Intercessor | 46 of 50 |
| Jump Chaplain | 8 of 8 |
| Techmarine | 8 of 8 |

Still open:

- Assault Legs 4A left: the lean fits 2.9 mm.
- Intercessor Legs 7: no buckle, still backwards.
- Intercessor Legs 22 left: lean 0.40 mm.
- Intercessor Legs 21 right: no ball pair.
- Captain legs: no shin spot found at all.

Where a near buckle turned legs round, the turn is only as good as that buckle: 20-35 deg from the library on a few
legs.

## Assault pad spot (run 8)

Josh cut a bigger `arm pad spot` on the shape the Assault arms share (one cut per arm type; Intercessor arms will need
their own).

- Sure on 35 of 37 Assault arms (0.0015-0.0027 mm, 98-100% cover), all 15 power fists included. Arm 12A and 12B are
  near (0.006).
- A/B pairs (one upper arm) put the pad within 0.06 mm / 0.1 deg of each other.
- The pads are 0.05-0.45 mm from the old library fits.
- Also sure on most Outrider and Veteran arms and Jump Chaplain Arm C. Intercessor and Techmarine arms: none.
