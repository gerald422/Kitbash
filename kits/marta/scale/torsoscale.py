import sys; sys.path.insert(0, '/home/claude/real')
import fitlib as F, numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation as Rot
from fistscale import umeyama
U = "/mnt/user-data/uploads/new cults/"
mt = U + "Marta/51 May 2026-20260612T074408Z-3-001/51 May 2026/torso and back pack/torso_1.stl"
mf = U + "All Mar All the time/VeteranBladeSquad/VeteranBladeSquad/Body/Body-RawSTL/17-Chest-1.stl"
Vb, Tb = F.stl(mf); B = F.surf(Vb, Tb, 30000, 0)
Va, Ta = F.stl(mt); A = F.surf(Va, Ta, 30000, 0)
Rm = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float)     # Marta file -> Mar Fil frame (Y up, Z front, model's right on -X)
A = A @ Rm.T
def run(A, B, region=None):
    if region is not None:
        A = A[region(A)]; B = B[region(B)]
    tree = cKDTree(B); best = None
    for dz in np.linspace(-3, 3, 7):
        for s0 in (0.85, 0.95, 1.05):
            s, R, t = s0, np.eye(3), B.mean(0) - s0 * A.mean(0) + [0, 0, dz]
            for _ in range(60):
                P = s * A @ R.T + t; d, i = tree.query(P); k = d <= np.quantile(d, 0.8)
                s, R, t = umeyama(A[k], B[i[k]])
                # keep the rotation near upright (designs differ): reject big turns
            ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
            d, _ = tree.query(s * A @ R.T + t); d2, _ = cKDTree(s * A @ R.T + t).query(B)
            sc = np.median(d) + np.median(d2)
            if ang < 20 and (best is None or sc < best[0]): best = (sc, s, ang, np.median(d), np.median(d2))
    return best
print('marta bbox', (A.max(0) - A.min(0)).round(2), ' mar fil bbox', (B.max(0) - B.min(0)).round(2))
b = run(A, B); print('whole torso: scale %.3f rot %.1f deg  fit %.3f / %.3f' % (b[1], b[2], b[3], b[4]))
# the top: neck ring and shoulders (top 45% of each)
top = lambda P: P[:, 2] > P[:, 2].min() + 0.55 * (P[:, 2].max() - P[:, 2].min())
b = run(A, B, top); print('upper torso: scale %.3f rot %.1f deg  fit %.3f / %.3f' % (b[1], b[2], b[3], b[4]))
