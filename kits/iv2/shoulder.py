"""Where does each Intercessor arm-with-weapon piece have its shoulder? Match the plain arm's shoulder ball
(57-Arm-1-R / -L: inner face on the chest's shoulder axis) onto the piece, from kit position."""
import sys; sys.path.insert(0, '/home/claude/kits')
import geo, numpy as np, json, glob, os
from scipy.spatial import cKDTree
IV = "../Intercessors-V2/Intercessors-V2/Intercessors-Bits/RawSTL/"
J = np.array([5.568, 0.202, 31.949])
def ref(side):
    rel = IV + ("Arms-Raw/57-Arm-1-R.stl" if side == 'R' else "Arms-Raw/Arms-Left/57-Arm-1-L.stl")
    V, T = geo.load(rel); S = geo.surf(V, T, 200000)
    j = J * ([1, 1, 1] if side == 'R' else [-1, 1, 1])
    R_ = S[np.linalg.norm(S - j, axis=1) < 3.2]
    return R_[np.random.default_rng(0).choice(len(R_), 1500, replace=False)], j
REF = {s: ref(s) for s in 'RL'}
def rot(a, ax):
    a = np.radians(a); c, s = np.cos(a), np.sin(a)
    i, k = [(1, 2), (0, 2), (0, 1)][ax]; R = np.eye(3); R[i, i] = c; R[k, k] = c; R[i, k] = -s; R[k, i] = s; return R
def match(rel, side):
    reg, j = REF[side]; V, T = geo.load(rel); Q = geo.surf(V, T, 120000); Q = Q[np.linalg.norm(Q - j, axis=1) < 8]
    tree = cKDTree(Q); best = None
    for dx in (0, 2, -2):
        for ax in range(3):
            for a in (-20, 0, 20):
                if a == 0 and ax > 0: continue
                R0 = rot(a, ax); t0 = j - R0 @ j + [dx * (1 if side == 'R' else -1), 0, 0]
                R, t, d = geo.icp(reg, tree, Q, R0, t0, 30)
                m = float(np.median(d))
                if best is None or m < best[0]: best = (m, geo.M4(R, t))
    return best
if __name__ == '__main__':
    B = IV + "Bolter-Individual-Raw/"; BL = B + "Bolter-Individual-Left/"
    jobs = [(IV + "Arms-Raw/58-Arm-2-R.stl", 'R'), (IV + "Arms-Raw/Arms-Left/58-Arm-2-L.stl", 'L')]
    for f in sorted(glob.glob(geo.U + B + '*.stl')):
        n = int(os.path.basename(f).split('-')[0])
        if 125 <= n <= 143: jobs.append((B + os.path.basename(f), 'R'))
    for f in sorted(glob.glob(geo.U + BL + '*.stl')):
        n = int(os.path.basename(f).split('-')[0])
        if 125 <= n <= 143: jobs.append((BL + os.path.basename(f), 'L'))
    PI = IV + "PlasmaIncinerator-Raw/"; PY = IV + "Pyreblaster-Raw/"; DS = IV + "Desolator-Raw/"
    jobs += [(PI + f, 'R') for f in ("188-PlasmaIncinerator-4-A-R.stl", "189-PlasmaIncinerator-4-B-R.stl", "191-PlasmaIncinerator-5-R.stl", "193-PlasmaIncinerator-6.stl")]
    jobs += [(PY + "201-Pyreblaster-7.stl", 'R'), (PY + "203-Pyreblaster-9-A.stl", 'R'), (DS + "205-Desolator-1.stl", 'R')]
    jobs += [(PI + "PlasmaIncinerator-Left/189-PlasmaIncinerator-4-B-L.stl", 'L'), (PY + "Pyreblaster-Left/201-Pyreblaster-7-L.stl", 'L'), (PY + "202-Pyreblaster-8.stl", 'L'), (PY + "204-Pyreblaster-9-B.stl", 'L')]
    out = {}
    for rel, side in jobs:
        m, G = match(rel, side)
        jj = J * ([1, 1, 1] if side == 'R' else [-1, 1, 1])
        out[rel] = {'G': G.tolist(), 'med': m, 'side': side}
        print('%-44s %s  med %.3f  joint moved %s  rot %.1f deg' % (rel.split('/')[-1], side, m, np.round(G[:3, :3] @ jj + G[:3, 3] - jj, 2), geo.ang(G[:3, :3])), flush=True)
        json.dump(out, open('/home/claude/kits/iv2/shoulder_all.json', 'w'), indent=1)
