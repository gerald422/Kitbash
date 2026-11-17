# 109: Proving runs on the reference file (Nov 16-17)

Josh's reference file (`~\Desktop\mar fil connectors\Kitbash reference.blend`, PLAN.md "The reference file"), read by
`kits/connectors/reference.py`, searched by `kits/connectors/prove.py` on 48 Mar Fil parts (3 per type, spread over
kits), with 4 test marines assembled from the numbers alone. Nothing written to the library.

## Rules that came out of it (all in PLAN.md)

- **Shape, never geometry.** The search compares only the cut's mating surface with the part's surface. Josh had to
  repeat this (Nov 13, Nov 17), so it's now in PLAN.md Method 5, CLAUDE.md and the head of `kb/connect.py`.
- Hosts take a sure match only: a near arm-wrist match put an axe on a shoulder (run 1).
- Bike torsos and riding legs are left out until they get their own cuts.
- Shins: each side is searched on its own, with sides taken from the waist frame (Outrider legs are turned 90 deg in
  their file). The left is the mirror.
- Legs' turn: the belt buckle (`Legs Buckle`) sets the turn about the waist. It sits forward of the waist, so it's a
  long lever. It's flagged when it disagrees with the waist's own turn by more than 3 deg. The waist cut counts as
  round even with its notch: the round test uses the median distance, and a small notch doesn't move the median. So
  without a buckle, the turn is the file's.

## Region search (Nov 17): kept as a guard, not as a match

Josh asked why more cuts were needed if the search matches shape. My answer: sure means the same sculpt to within
0.005 mm, and Intercessor and Bladeguard arms are different sculpts. To try to avoid new cuts, a spot on a host (wrist,
pad spot, shin spot, buckle) is now searched only in a shell around the joint that placed the host, at its
reference distance ± a few mm (`kb.connect.find(region=)`). Run 3 (`proving 3`):

- Intercessor arm wrist: none, 0.0315 mm.
- Bladeguard arm pad spot: none.
- Intercessor pad spot: near. Written as a trial, it sat flipped behind the shoulder.

So narrowing where to look doesn't make a different sculpt match. `HOST_NEAR_IN_REGION = False`: hosts are sure only
again. The region stays, to keep answers in the right place.

## Run 3 results

- Sure on every Assault chain joint.
- Torso shoulder, neck and waist are sure on all 4 torsos.
- Shins are sure on all 4 legs, both sides, jump legs included, so the inner-circle recut isn't needed.
- Buckle: sure on Legs 1A (turned -0.1 deg) and Assault Legs 1 (turned -12.3 deg, flagged). None on the Jump Chaplain
  legs (its own belt), near on Intercessor Legs 1.
- Still needing a cut (one per kit sculpt):
  - Intercessor arm wrist and pad spot.
  - Bladeguard arm wrist and pad spot.
  - The Intercessor shoulder pad placed on its arm.
  - Bladeguard / Veteran axes and the Veteran combi weapon: near on `weapon wrist 3`, but 8-18 mm from where the
    library has them, so most likely wrong.
  - Shields: near, 12-31 mm off. A shield is held differently; it needs its own grip cut.
  - Captain jump pack mount.
  - Jump Chaplain and Techmarine torso backs.
