# Pad fix (Nov 8 2026)

Every arm's Pad socket in Josh's 62 convention (his pad 62 on arm 76, and his Springles seats), and the BBoosty /
CyberBrush pad fits moved off the old 'dome' sockets onto it.

Data the scripts read (staged from the PC, not in the repo): `_builder/index.json` and the previews of every arm
with a Pad socket, every pad and every chest (`/home/claude/work/pads/lib/_builder/previews`, from
`_backups\pads-2026-11-06\previews.tgz`), and the sidecars before the change (`/home/claude/work/pads/before`, from
`_backups\pads-2026-11-06\sidecars_before.tgz`).

- `arms_audit.py` - first audit (62's seat on every arm vs on arm 76); `arms_audit.json` is read by `seatrule.py`.
- `cupcheck.py`, `spin.py` - pad 56's spherical cup sits over the shoulder joint on every arm (position was fine);
  the spin about the cup axis is what was wrong (Springles 0 +-25, Mar Fil Assault -11, Marta all over).
- `fixseats.py` - the check (spin within 45 deg, out-from-side 50-110, lift 30-85 - the range of Josh's Springles
  seats and the Mar Fil Assault seats he uses) and the prediction (the passing arm in the nearest pose, same family
  first, turned about the shoulder joint by the pose difference; leave-one-out on passing arms 0.3-8 deg median).
- `padfam.py` - K: old dome seat -> Josh's Springles seat in the same pose (BBoosty Medusas Arm 4 R <-> Springles P
  Melee Arm 1 R, 0.85 deg apart). BBoosty/CyberBrush pad fits = K^-1 @ old fit.
- `padfix.py` - which arms change: BBoosty/CyberBrush (Springles pool), all Marta, and any other arm failing the check;
  Josh's corrected socket (BBoosty Arm 2 Bionic R) kept. `write_fix.py` writes sidecars + the index in place.
- `t_after.py`, `t_one.py`, `t_exba.py` - check sheets. TIOW test: `tests/pads/t_pads.py`.
