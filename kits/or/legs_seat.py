"""Outrider legs (exported on the bike, facing +X): seated like Josh's AM legs. The AM legs' waist regions are first
brought over by a coarse start (turned to face +X, joint under the top of the plug, a few leans), then ICP."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os, glob
from scipy.spatial import cKDTree
import legs_match as LM
MX = np.diag([-1.0, 1, 1, 1])
LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
O = "Outriders (1)/Outriders/"
def rz(a):
    a = np.radians(a); c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
def ry(a):
    a = np.radians(a); c, s = np.cos(a), np.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rx(a):
    a = np.radians(a); c, s = np.cos(a), np.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def match(rel):
    V, T = geo.load(rel); S = geo.surf(V, T, 300000); tree = cKDTree(S)
    top = S[S[:, 2] > S[:, 2].max() - 2.5]; ctop = top.mean(0)
    best = None
    for rref, (M, R, j) in LM.REFS.items():
        jtop = R[:, 2].max()                       # top of the reference region (plug top) vs its joint
        for pitch in (-20, -10, 0, 10, 20):
            for yaw in (-90 - 15, -90, -90 + 15):
                R0 = ry(pitch) @ rz(yaw)
                t0 = ctop - R0 @ np.array([j[0], j[1], jtop]) + R0 @ np.array([j[0], j[1], jtop]) * 0  # placeholder
                # put the region's top centre on the legs' top centre
                rc = R[R[:, 2] > jtop - 2.5].mean(0)
                t0 = ctop - R0 @ rc
                Rg, tg, d = geo.icp(R[::3], tree, S, R0, t0, 25)
                md = float(np.median(d))
                if best is None or md < best[0]: best = (md, rref, geo.M4(Rg, tg), M)
    md, rref, G, M = best
    Rg, tg, d = geo.icp(LM.REFS[rref][1], tree, S, G[:3, :3], G[:3, 3], 40); G = geo.M4(Rg, tg); md = float(np.median(d))
    return md, rref, M @ np.linalg.inv(G), G
out = {}
origs = sorted(O + 'Legs/RawSTL/' + os.path.basename(f) for f in glob.glob(geo.U + O + 'Legs/RawSTL/*.stl'))
for rel in origs:
    md, rref, Mnew, G = match(rel)
    hips = {k: (G @ np.array(v)).tolist() for k, v in LJ[rref]['hips'].items() if k in ('Hip R', 'Hip L')}
    out[rel] = dict(M=Mnew.tolist(), ref=rref, med=md, hips=hips)
    jt = np.linalg.inv(Mnew) @ np.r_[LM.S_WAIST[:3, 3], 1]
    print('%-22s ref %-14s %.3f  waist joint at %s' % (os.path.basename(rel), os.path.basename(rref)[:-4], md, np.round(jt[:3], 2)), flush=True)
json.dump(out, open('/home/claude/kits/or/legs_seat.json', 'w'), indent=1)
