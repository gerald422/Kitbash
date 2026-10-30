"""The Captain with Jump Pack's waist plates are exported in place on his body (3-Legs = torso + legs in one).
Seat the body like any Mar Fil legs (AM waist matched, as legs_match.py), put the belt anchors on it with the
same rule every leg got (belt.py), and each plate's fit is the inverse of the anchor it sits on."""
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits')
import geo, legs_match, belt
REL = 'CaptainWithJumpPack/CaptainWithJumpPack/RawStl/'
md, rref, M, G = legs_match.match(REL + '3-Legs.stl')
print('body seated: waist match median %.3f mm (ref %s)' % (md, rref.split('/')[-1]))
A = belt.belt_anchors(REL + '3-Legs.stl', M)
for k, K in A.items(): print(k, K[:3, 3].round(2))
out = {'M': M.tolist(), 'anchors': {k: K.tolist() for k, K in A.items()}, 'fits': {}}
for f, sock in (('8-WaistPlate-1', 'Hip R'), ('9-WaistPlate-2', 'Hip R'), ('10-WaistPlate-3', 'Hip L'), ('11-Relic', None)):
    V, T = geo.load(REL + f + '.stl'); c = V.mean(0)
    # which anchor is nearest (the relic: wherever it hangs)
    near = min(A, key=lambda k: np.linalg.norm(A[k][:3, 3] - c))
    s = sock or near
    F = np.linalg.inv(A[s])
    loc = (F @ np.r_[c, 1])[:3]
    print('%-16s on %-10s centre in the anchor frame %s  (nearest anchor %s, %.1f mm)' % (f, s, loc.round(2), near, np.linalg.norm(A[near][:3, 3] - c)))
    out['fits'][f] = {'socket': s, 'fit': F.tolist()}
json.dump(out, open('cap_fits.json', 'w'), indent=1)
