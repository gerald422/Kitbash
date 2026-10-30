import sys, json, numpy as np
sys.path.insert(0, '/home/claude/kits')
import geo, belt
REL = 'CaptainWithJumpPack/CaptainWithJumpPack/RawStl/'
Mtb = np.array(json.load(open('cap_torso.json'))['Mtorso_to_body']); M = np.linalg.inv(Mtb)      # body file -> torso coords
A = belt.belt_anchors(REL + '3-Legs.stl', M)
for k, K in A.items(): print('%-10s at %s (torso coords %s)' % (k, K[:3, 3].round(2), (M @ np.r_[K[:3, 3], 1])[:3].round(2)))
out = {'M': M.tolist(), 'anchors': {k: K.tolist() for k, K in A.items()}, 'fits': {}}
for f in ('8-WaistPlate-1', '9-WaistPlate-2', '10-WaistPlate-3', '11-Relic'):
    V, T = geo.load(REL + f + '.stl'); c = V.mean(0)
    d = {k: np.linalg.norm(K[:3, 3] - c) for k, K in A.items()}; s = min(d, key=d.get)
    F = np.linalg.inv(A[s]); loc = (F @ np.r_[c, 1])[:3]
    # the plate's closest point to the anchor: how far it sits off the belt surface
    gap = np.min(np.linalg.norm(V - A[s][:3, 3], axis=1))
    print('%-16s nearest anchor %-10s %.1f mm; centre in the anchor frame %s; nearest plate point %.2f mm from the anchor' % (f, s, d[s], loc.round(2), gap))
    out['fits'][f] = {'socket': s, 'fit': F.tolist()}
json.dump(out, open('cap_fits.json', 'w'), indent=1)
