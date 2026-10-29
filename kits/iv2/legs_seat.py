"""Intercessors V2 legs seated like Josh's AM-V2 legs (same method as Vet/Bladeguard); mirrored legs = mirror of their original."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob
from scipy.spatial import cKDTree
import legs_match as LM
MX = np.diag([-1.0, 1, 1, 1])
LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
def mirror_move(lrel, rrel):
    V, T = geo.load(rrel); W, U = geo.load(lrel)
    S = geo.surf(np.asarray(V, float) * [-1, 1, 1], T[:, ::-1], 150000); P = geo.surf(W, U, 3000)
    R, t, d = geo.icp(P, cKDTree(S), S, np.eye(3), np.zeros(3), 60)
    return np.linalg.inv(geo.M4(R, t)), float(np.median(d))
out = {}
origs = sorted(IV + 'Legs-Raw/' + os.path.basename(f) for f in glob.glob(geo.U + IV + 'Legs-Raw/*.stl'))
for rel in origs:
    md, rref, Mnew, G = LM.match(rel)
    hips = {k: (G @ np.array(v)).tolist() for k, v in LJ[rref]['hips'].items() if k in ('Hip R', 'Hip L')}
    out[rel] = dict(M=Mnew.tolist(), ref=rref, med=md, hips=hips)
    print('%-30s ref %-14s %.3f' % (os.path.basename(rel), os.path.basename(rref)[:-4], md), flush=True)
for f in sorted(glob.glob(geo.U + IV + 'Legs-Raw/Legs-Mirorred/*.stl')):
    mrel = IV + 'Legs-Raw/Legs-Mirorred/' + os.path.basename(f)
    o = IV + 'Legs-Raw/' + os.path.basename(f).replace('-(mirrored)', '')
    A, md = mirror_move(mrel, o); Mo = np.array(out[o]['M'])
    out[mrel] = dict(M=(MX @ Mo @ MX @ np.linalg.inv(A)).tolist(), ref='mirror of ' + o, med=md,
                     hips={('Hip R' if k == 'Hip L' else 'Hip L'): (A @ MX @ np.array(H) @ MX).tolist() for k, H in out[o]['hips'].items()})
    print('%-30s = mirror of %s (fit %.3f)' % (os.path.basename(f), os.path.basename(o), md), flush=True)
json.dump(out, open('/home/claude/kits/iv2/legs_seat.json', 'w'), indent=1)
