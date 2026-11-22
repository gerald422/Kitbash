# 118 - Pauldrons: one shared inside shape, and the print fix in Finalise 0.3.4 (Nov 22)

**Josh's idea.** Instead of a fit per arm and pad, one pauldron "adapter" across every Tacticus maker: placement comes
from the fit, and a separate, per arm + pad piece fixes the print ("placement comes from this, printing fix comes from
a different adaptor"), worked out when placed so the union is manifold and the pad doesn't move.

**Shared inside shape.** A placement blend (Mar Fil Torso 2 + Assault Arm 2B R with the seated Mar Fil pads, plus one
pad per Mar Fil kit and per maker, loose) was built; Josh placed all 15 on Arm 2B R
(`~\Desktop\mar fil connectors\Pauldron adapter - place the pads (2026-11-22).blend`). Each pad's inside was read as a
height map along the Mar Fil Assault pad's axis (ray casts from below, faces looking down only). One shape fits inside
all 15 (footprint 64 mm^2); Mar Fil Veteran is the tightest, Bladeguard has the most room. Draft in
`Pauldron adapter - shared shape draft (2026-11-22).blend`.

**Print fix (the plug).** On Arm 2B R, 12 of the 15 pads already make one solid with the arm. Marta Apothecary and TN
Pauldron A 1 touch it all round the rim and leave a sealed pocket under them (filled, they're one solid). CyberBrush
(5 shells, 67 open edges) and WargamesPrint (13 shells, 48 open edges) are broken in their own STLs; the union repairs
them. Only Bladeguard doesn't touch the arm (14 mm pad on its own): it needs a plug.
- A filler over the whole gap made tiny sealed pockets; a plug at the smallest gap sat at the pad's side and showed
  as a 7 mm strip under the rim (renders). What works: within 2.5 mm of the pad's axis (under the crown), round the
  point where the arm comes closest, 0.5 mm in from the inside edge, columns no taller than 1.5 mm, sunk 0.35 mm into
  both, voxel remeshed (0.06). Bladeguard: gap 0.4-0.6 mm, ~3 mm^3, hidden from every side (six-view render).
- Order matters with Exact: (pad + plug) then the arm closes; arm + plug + pad left 13-17 non-manifold edges.

**Finalise 0.3.4** (`addons/kitbash_finalise.py`):
- `pad_plug`: for a part on a `Pad` socket printed in the same piece as its arm, whose BVH doesn't overlap the arm's,
  the plug is made before any boolean and put on the pad's copy as a live union (Manifold, Exact if the pad isn't
  manifold); the pad then goes onto the arm in the usual order. Dialog option "Plug shoulder pads that don't touch
  their arm" (on). A gap over 1.5 mm at the crown is logged, not filled.
- `merge_shells`: a part copy with several shells is unioned into one first (Manifold). Found on TN Pauldron A 1
  (6 overlapping shells): the Manifold solver left the shells that only overlap the pad (not the arm) separate.
- `fill_pockets` on Apply: shells sealed inside a piece (ray parity, 3 directions) are deleted (filled), slivers under
  0.15 mm dropped, a piece left in several shells reported as a problem.
- Tests: `finalise/tests/t_padplug.py` (synthetic dome arm + pad: floating, touching with a stud shell, plug off);
  t_base / t_exact / t_place still pass (47 checks). On the PC (Blender 5.1, Manifold): Bladeguard, Apothecary,
  Pauldron A 1, Mar Fil Assault each one manifold solid.

**Not done.** Josh's 15 placements are not written to the library yet, and the plug was only proved on Arm 2B R; a
steeper or slimmer shoulder could push the plug toward the rim (only the six-view render shows that, not the checks).
