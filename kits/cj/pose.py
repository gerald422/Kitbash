"""Chaplain with Jump Pack: each pose (A-D) is exported in its own frame. The torso pose P_X (torso coords -> file)
from the two shoulder discs of the arm pair; then the legs (seated Josh-style, started from P_X) and checks."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, json, numpy as np, os
from scipy.spatial import cKDTree
import legs_match as LM
inv = np.linalg.inv
O = "ChaplainWithJumpPack (1)/ChaplainWithJumpPack/"
D = json.load(open('/home/claude/kits/cj/discs.json'))
J = np.array([5.568, 0.202, 31.949]); NR = np.array([-1, 0, -0.04]); NR /= np.linalg.norm(NR)
JL = J * [-1, 1, 1]; NL = NR * [-1, 1, 1]
def kabsch(A, B, w=None):
    w = np.ones(len(A)) if w is None else w
    ca, cb = (A * w[:, None]).sum(0) / w.sum(), (B * w[:, None]).sum(0) / w.sum()
    H = ((A - ca) * w[:, None]).T @ (B - cb); U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T)); R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return R, cb - R @ ca
ARMS = {'A': ('13-Arm-Right-A', '17-Arm-Left-A'), 'B': ('14-Arm-Right-B', '18-Arm-Left-B'), 'C': ('15-Arm-Right-C', '19-Arm-Left-C'), 'D': ('16-Arm-Right-D', '20-Arm-Left-D')}
LEGS = {'A': '3-Legs-A-ChaplainWithJumppack', 'B': '4-Legs-B-ChaplainWithJumppack', 'C': '5-Legs-C-ChaplainWithJumppack', 'D': '6-Legs-D-ChaplainWithJumppack'}
out = {}
for X, (r, l) in ARMS.items():
    dr = D[O + 'Arms/Arms-Raw-STL/' + r + '.stl'][0]; dl = D[O + 'Arms/Arms-Raw-STL/' + l + '.stl'][0]
    cr, nr = np.array(dr['c']), np.array(dr['n']); cl, nl = np.array(dl['c']), np.array(dl['n'])
    k = 3.0
    A = np.array([J, JL, J + k * NR, JL + k * NL]); B = np.array([cr, cl, cr + k * nr, cl + k * nl])
    R, t = kabsch(A, B); P = geo.M4(R, t)
    res = np.linalg.norm((A @ R.T + t) - B, axis=1)
    # legs: bring into torso coords with inv(P), then the Josh-style seat (AM legs waist regions, a few nudges)
    rel = O + 'Legs/Legs-Raw-STL/' + LEGS[X] + '.stl'
    V, T = geo.load(rel); S = geo.surf(V, T, 300000); St = S @ inv(P)[:3, :3].T + inv(P)[:3, 3]; tree = cKDTree(St)
    best = None
    for rref, (M, Rr, j) in LM.REFS.items():
        # reference region in torso coords (M maps ref legs -> torso)
        Rt = Rr @ M[:3, :3].T + M[:3, 3]
        for dz in (0.0, 1.0, -1.0):
            Rg, tg, d = geo.icp(Rt[::2], tree, St, np.eye(3), np.array([0, 0, dz]), 40)
            md = float(np.median(d))
            if best is None or md < best[0]: best = (md, rref, geo.M4(Rg, tg), M)
    md, rref, G, M = best
    Rg, tg, d = geo.icp(LM.REFS[rref][1] @ M[:3, :3].T + M[:3, 3], tree, St, G[:3, :3], G[:3, 3], 40); G = geo.M4(Rg, tg); md = float(np.median(d))
    # G moves the ref region (torso coords, Josh seat) onto the new legs (torso coords, Mar Fil seat):
    # Josh-style seat of the new legs: legs file -> torso = inv(G) @ inv(P)
    Mj = inv(G) @ inv(P)
    jt = LM.S_WAIST[:3, 3]
    print('%s  disc residuals %s | legs ref %-12s med %.3f | Josh vs Mar Fil: %.1f deg, %.2f mm at the waist' % (
        X, np.round(res, 3), os.path.basename(rref)[:-4], md, geo.ang(G[:3, :3]), np.linalg.norm((G @ np.r_[jt, 1])[:3] - jt)), flush=True)
    LJ = json.load(open('/home/claude/kits/legs_josh.json'))['legs']
    hips = {h: (inv(Mj) @ M @ np.array(v)).tolist() for h, v in LJ[rref]['hips'].items() if h in ('Hip R', 'Hip L')}
    out[X] = dict(P=P.tolist(), legs=rel, M_josh=Mj.tolist(), M_marfil=inv(P).tolist(), ref=rref, med=md, hips=hips, disc_res=res.tolist())
json.dump(out, open('/home/claude/kits/cj/pose.json', 'w'), indent=1)
