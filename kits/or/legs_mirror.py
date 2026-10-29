import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob
from scipy.spatial import cKDTree
MX = np.diag([-1.0, 1, 1, 1]); MY = np.diag([1.0, -1, 1, 1])
O = "Outriders (1)/Outriders/"
out = json.load(open('/home/claude/kits/or/legs_seat.json'))
def mirror_move(lrel, rrel):
    """A: original-legs coords -> mirrored-legs coords, with the original mirrored across Y (the bike's mid-plane)."""
    V, T = geo.load(rrel); W, U = geo.load(lrel)
    S = geo.surf(np.asarray(V, float) * [1, -1, 1], T[:, ::-1], 150000); P = geo.surf(W, U, 3000)
    R, t, d = geo.icp(P, cKDTree(S), S, np.eye(3), np.zeros(3), 60)
    return np.linalg.inv(geo.M4(R, t)), float(np.median(d))
for f in sorted(glob.glob(geo.U + O + 'Legs/MirroredRawSTL/*.stl')):
    mrel = O + 'Legs/MirroredRawSTL/' + os.path.basename(f); o = O + 'Legs/RawSTL/' + os.path.basename(f).replace('-Mirrored', '')
    A, md = mirror_move(mrel, o)
    Mo = np.array(out[o]['M'])           # legs pose in torso coords (original)
    # torso mirrored across its own X (left-right), legs mirrored across bike Y: M_m = MX Mo MY inv(A)
    M = MX @ Mo @ MY @ np.linalg.inv(A)
    out[mrel] = dict(M=M.tolist(), ref='mirror of ' + o, med=md,
                     hips={('Hip R' if k == 'Hip L' else 'Hip L'): (A @ MY @ np.array(H) @ MX).tolist() for k, H in out[o]['hips'].items()})
    print(os.path.basename(f), 'mirror fit %.3f' % md, 'A move', np.round(A[:3, 3], 2))
json.dump(out, open('/home/claude/kits/or/legs_seat.json', 'w'), indent=1)
