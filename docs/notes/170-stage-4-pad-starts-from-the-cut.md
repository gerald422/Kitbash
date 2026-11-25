# 170 - Stage 4: pad starts from Josh's pad spot cut; wrist cut starts shown to compare (Nov 25)

Josh, on batch 1 (notes 169): "the pauldrons dont work" ... "the guide is failing to find a match a lot of the time so
its being placed incorrectly", then "the wrists are mostly fine. its the pauldrons that have the issue", and "I am
happy to view the new hand fits aswell". He floated a guide per pad type. My reply: that suits a pad-side problem, and
the guides should then share one crown frame, so each arm keeps one Pad R socket. This file tests the arm side.

**`make_socket_batch.py` now starts from his cuts (same-shape transfer, skill `kitbash-seat-by-shape`):**
- **Pad R:** `Assault Arm Pad spot` (his cut on Arm 2B R) fitted onto each arm by trimmed ICP of the cut's points only,
  from two starts (the file frame and the torso place). His Pad R on 2B R is carried by that fit. Grades by trimmed
  rms: under 0.06 mm "same shape", under 0.15 mm "near", else the torso place, for him by eye.
- **Hand R:** the old Hand R, as he asked. `Assault arm wrist a` (2A R) and `wrist b` (2B R, whose Hand R comes from his
  Shield R there: 0.02 mm / 5.3 deg from its library one) are fitted too. Where one lands (under 0.15 mm) a faint
  Chain Sword 1 R shows that start beside the real one, to compare.
- Each column's note lists its grades.

**`04 Stage 4 - Mar Fil Assault arm sockets (2026-11-25 b).blend`** (spec `04-marfil-assault-sockets-b.json`):
- Pad spot: 11 arms same shape (0.027-0.056 mm), 8 near (4A/B, 5A/B, 6A/B 0.066-0.089, 11A/B 0.13). 3A R and 3B R
  don't match (0.29 mm): his 3A R example, a different shoulder; placed by the torso, by eye.
- Wrist cut: lands on 7A, 7B, 8A, 9A, 9B (0.08-0.14 mm), 21-131 deg from the old sockets; no match elsewhere. Faint
  swords on those five.

The first file (notes 169) is replaced by this one.
