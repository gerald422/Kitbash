"""Register every insert onto Josh's reference (HH GEN3 Chest Reinforcement Plate 2) by its back.

The inserts lie face up on one print plate (back on z 16.83, +Y = up on the chest, x across), so each
differs from the reference by a shift only (every file's back is exactly 10.57 wide along x and touches
z 16.826: no turn). Matched by trimmed translation-only ICP of the back-facing surface (normal z < -0.3),
from several starting shifts (a rigid ICP drifted up to 1.25 deg on the decorated backs); writes registrations.json:
rel -> 4x4 A (row-major) taking the insert's file coords into the reference's file coords."""
import json, os, glob, numpy as np
from scipy.spatial import cKDTree
U = "/mnt/user-data/uploads/d/new cults/Inserts/"
REF = "HH GEN3 Chest Reinforcement Plate/2.stl"

def stl(p):
    d = np.fromfile(p, dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]), offset=84)
    return d['v'].astype(float)

def back_points(T, n=6000, seed=0):
    nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); a = np.linalg.norm(nrm, axis=1)
    ok = a > 1e-12; T, nrm, a = T[ok], nrm[ok] / a[ok, None], a[ok]
    b = nrm[:, 2] < -0.3; T, a = T[b], a[b]
    rng = np.random.default_rng(seed); k = rng.choice(len(T), n, p=a / a.sum())
    r1, r2 = rng.random(n), rng.random(n); s = np.sqrt(r1)
    return (1 - s)[:, None] * T[k, 0] + (s * (1 - r2))[:, None] * T[k, 1] + (s * r2)[:, None] * T[k, 2]

def kabsch(P, Q):
    cp, cq = P.mean(0), Q.mean(0); H = (P - cp).T @ (Q - cq); U_, S, Vt = np.linalg.svd(H)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U_.T))]); R = Vt.T @ D @ U_.T
    return R, cq - R @ cp

def icp(P, tree, Q, R, t, iters=60, trim=0.8):
    for _ in range(iters):
        X = P @ R.T + t; d, j = tree.query(X)
        keep = d <= np.quantile(d, trim); t = (Q[j[keep]] - P[keep] @ R.T).mean(0)
    X = P @ R.T + t; d, _ = tree.query(X)
    return R, t, float(np.median(d)), float(np.quantile(d, 0.9))

TR = stl(U + REF); Q = back_points(TR); tree = cKDTree(Q)
lo_r, hi_r = TR.reshape(-1, 3).min(0), TR.reshape(-1, 3).max(0)
out = {}
for p in sorted(glob.glob(U + "**/*.stl", recursive=True)):
    rel = os.path.relpath(p, U); T = stl(p); V = T.reshape(-1, 3); lo, hi = V.min(0), V.max(0)
    P = back_points(T, 3000, 1); best = None
    for dy in np.arange(-1.0, 1.01, 0.25):
        t0 = np.array([(lo_r[0] + hi_r[0]) / 2 - (lo[0] + hi[0]) / 2, (lo_r[1] + hi_r[1]) / 2 - (lo[1] + hi[1]) / 2 + dy, lo_r[2] - lo[2]])
        r = icp(P, tree, Q, np.eye(3), t0)
        if best is None or r[2] < best[2]: best = r
    R, t, med, p90 = best
    ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
    A = np.eye(4); A[:3, :3] = R; A[:3, 3] = t
    out[rel] = {"A": [round(float(x), 6) for x in A.ravel()], "median": round(med, 4), "p90": round(p90, 4), "turn_deg": round(float(ang), 3)}
    print("%-58s med %.3f p90 %.3f turn %.2f" % (rel[:58], med, p90, ang), flush=True)
json.dump(out, open("/home/claude/work/inserts/registrations.json", "w"), indent=1)
