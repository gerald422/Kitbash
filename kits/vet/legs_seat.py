"""Vet / Bladeguard legs seated like Josh's Assault Marine legs (the orange version he picked): best-matching AM legs'
waist (plug + plating) carried onto each original legs piece, with that legs' Hip R/L; mirrored legs = mirror of their original."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob, re
from scipy.spatial import cKDTree
import legs_match as LM                      # REFS (AM legs regions with Josh's seat), match()
MX = np.diag([-1.0, 1, 1, 1])
LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
def mirror_move(lrel, rrel):
    V, T = geo.load(rrel); W, U = geo.load(lrel)
    S = geo.surf(np.asarray(V, float) * [-1, 1, 1], T[:, ::-1], 150000); P = geo.surf(W, U, 3000)
    R, t, d = geo.icp(P, cKDTree(S), S, np.eye(3), np.zeros(3), 60)
    return np.linalg.inv(geo.M4(R, t)), float(np.median(d))
out = {}
VS = 'VeteranSquad/VeteranSquad/Body/'; BG = 'VeteranBladeSquad/VeteranBladeSquad/Body/'
origs = [f[len(geo.RAW):] for f in sorted(glob.glob(geo.RAW + VS + 'Body-RawSTL/*Body*.stl'))] + [f[len(geo.U):] for f in sorted(glob.glob(geo.U + BG + 'Body-RawSTL/*Legs*.stl'))]
for rel in origs:
    md, rref, Mnew, G = LM.match(rel)
    hips = {k: (G @ np.array(v)).tolist() for k, v in LJ[rref]['hips'].items() if k in ('Hip R', 'Hip L')}
    out[rel] = dict(M=Mnew.tolist(), ref=rref, med=md, hips=hips)
    print('%-30s ref %-14s %.3f  hips %s' % (os.path.basename(rel), os.path.basename(rref)[:-4], md, list(hips)), flush=True)
mirs = [f[len(geo.RAW):] for f in sorted(glob.glob(geo.RAW + VS + 'Body-Mirrored/*.stl'))] + [f[len(geo.U):] for f in sorted(glob.glob(geo.U + BG + 'Body-Mirrored/*.stl'))]
for mrel in mirs:
    b = os.path.basename(mrel)
    if b.startswith(tuple('0123456789')) and 'Body' in b: cand = [o for o in origs if os.path.basename(o) == b.replace('-Mirrored', '')]
    else:
        n = re.match(r'(\d+)', b).group(1); cand = [o for o in origs if os.path.basename(o).startswith(n + '-') and 'Corrected' not in o and o.split('/')[0] == mrel.split('/')[0]]
    o = cand[0]; A, md = mirror_move(mrel, o)
    Mo = np.array(out[o]['M'])
    M = MX @ Mo @ MX @ np.linalg.inv(A)
    hips = {('Hip R' if k == 'Hip L' else 'Hip L'): (A @ MX @ np.array(H) @ MX).tolist() for k, H in out[o]['hips'].items()}
    out[mrel] = dict(M=M.tolist(), ref='mirror of ' + o, med=md, hips=hips)
    print('%-30s = mirror of %s (fit %.3f)' % (b, os.path.basename(o), md), flush=True)
json.dump(out, open('/home/claude/kits/vet/legs_seat.json', 'w'), indent=1)
