# 111: Armour types in cut names; the Intercessor pad spot and buckle (Nov 18)

Proving run 15 (`~\Desktop\mar fil connectors\proving 15`): every Assault, Intercessor, Techmarine and Jump Chaplain
arm and legs file (123 parts).

## Cut names carry the armour type

Josh's new cuts: `intercessor arm pad spot`, `Intercessor Legs belt buckle`. He means to put the type in front from
now on. `reference.cut_name` reads `<type> <fixed name> <label>` -> (fixed name, type); `belt buckle` reads as
`buckle`. Every cut of a joint is tried on each part and the best fit is kept (as before for several cuts); the
result records the type (`kind`), so the search says which armour a part is. `prove.py` now takes every buckle cut
(`dump["buckles"]`), not only the first.

Also: Captain with Jump Pack is left out altogether (`NOT_KITS`, Josh). The reference's "Forearm 2 a" / "Forearm 2.b"
are CyberBrush Forearm 2 (forearm armour, on Arm 2A / 2B over the `arm wrist armour` cuts): a copy lettered by hand
is now known by its name. No joint places forearm armour yet.

## Run 15

- Pads: Assault arms sure 37 of 39 (12A / 12B near, 0.006), all on the Assault cut. Intercessor arms sure 27 of 32,
  all on the Intercessor cut; the 5 not found are Bolter A3, A / B / C Grenade 3 and C Grenade 1, whose shoulder is
  also only near (no region). Techmarine Arm 4 and 5: sure on the Intercessor cut, 4.8 / 5.2 mm from the old library
  fits; Arm 4 looks right, Arm 5's pad looks tipped back (for Josh). Jump Chaplain arms: Arm C sure, A / B / D near
  (0.006) on the Assault cut.
- Shins: 90 of 92 sides clean (Assault 25/26, Intercessor 49/50, Jump Chaplain 8/8, Techmarine 8/8). Left: Assault
  Legs 4A left (lean 2.9 mm), Intercessor Legs 21 right (no ball pair).
- Buckle: the Intercessor buckle is sure only on Legs 1, the legs it was cut on; on the other Intercessor legs it is
  near (0.005-0.02 mm), so it says which way they face but doesn't set the turn. Legs 7 is now found and turned round
  (13 backwards legs turned). The Intercessor belts differ between legs files. The Assault buckle is sure on the
  Assault and Techmarine legs (turns of 10-34 deg from the file's; Assault Legs 4A and 5, Techmarine Legs 4 turned
  round). No buckle found on the Jump Chaplain legs; Intercessor Legs 10: no waist found.
