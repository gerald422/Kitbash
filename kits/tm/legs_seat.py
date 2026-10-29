import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob
import legs_match as LM
O = "Techmarine (2)/Techmarine/"
LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
out = {}
for f in sorted(glob.glob(geo.U + O + 'Legs/Legs-Raw-STL/*.stl')):
    rel = f[len(geo.U):]; md, rref, Mnew, G = LM.match(rel)
    jt = LM.S_WAIST[:3, 3]; d_mm = np.linalg.norm((np.linalg.inv(Mnew) @ np.r_[jt, 1])[:3] - jt)
    out[rel] = dict(M=Mnew.tolist(), ref=rref, med=md)
    print('%-16s ref %-14s med %.3f | vs export: %.1f deg, %.2f mm at the waist' % (os.path.basename(rel), os.path.basename(rref)[:-4], md, geo.ang(Mnew[:3, :3]), d_mm), flush=True)
json.dump(out, open('/home/claude/kits/tm/legs_seat.json', 'w'), indent=1)
