"""Pauldrons -> Pad R: Josh's pad 62 (Mar Fil Assault Shoulder Pad 1) matched onto each pad (rotation + uniform scale
kept within 0.85-1.35, 24 starts: the square turns), carrying 62's Pad R fit across about 62's shell centre, so a
bigger pad grows outward from the shoulder instead of into it. Every pad is fitted as a right pad;
the left one is its mirror (mirrorLeft)."""
import sys, json, itertools, numpy as np
sys.path.insert(0, "/home/claude/kitbash/kits/rw_spr"); from common import *
P62 = "Mar Fil - Tacticus/AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 1"
V62, T62 = F.stl(LIBU + P62 + ".stl"); V62 = np.asarray(V62, float)
F62 = np.array(lib_sidecar(P62 + ".sockets.json")["fits"]["Pad R"]).reshape(4, 4)
S62 = geo.surf(V62, T62, 60000)[np.random.default_rng(2).choice(60000, 2500, replace=False)]
def sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); c, *_ = np.linalg.lstsq(A, b, rcond=None); return c[:3]
C62 = sphere(S62)
TURNS = []
for perm in itertools.permutations(range(3)):
    for sg in itertools.product((1, -1), repeat=3):
        R = np.zeros((3, 3))
        for i, j in enumerate(perm): R[j, i] = sg[i]
        if np.linalg.det(R) > 0: TURNS.append(R)      # the 24 square turns (pads go on either side through mirrorLeft)
def umeyama(A, B):
    ma, mb = A.mean(0), B.mean(0); A0, B0 = A - ma, B - mb
    U_, S_, Vt = np.linalg.svd(B0.T @ A0 / len(A)); d = np.ones(3)
    if np.linalg.det(U_ @ Vt) < 0: d[-1] = -1
    R = U_ @ np.diag(d) @ Vt; s = (S_ * d).sum() / (A0 ** 2).sum() * len(A)
    return s, R, mb - s * R @ ma
def sim_icp(src, tree, tgt, M0, iters=40, trim=0.85):
    """src -> tgt with x' = s * M x + t, M a fixed improper/proper turn times a fitted rotation."""
    s = (np.ptp(tgt, 0).prod() / np.ptp(src @ M0.T, 0).prod()) ** (1 / 3); R = M0.copy(); t = tgt.mean(0) - s * (src @ R.T).mean(0)
    for _ in range(iters):
        P = s * src @ R.T + t; d, i = tree.query(P); k = d <= np.quantile(d, trim)
        s2, R2, t2 = umeyama(s * src[k] @ R.T + t, tgt[i[k]])    # incremental
        R = R2 @ R; t = s2 * R2 @ t + t2; s = s * s2
        s_c = min(max(s, 0.85), 1.35)                   # a pauldron is about 62's size: keep ICP from shrinking it onto a stud
        if s_c != s: t = t + (s - s_c) * (src @ R.T).mean(0); s = s_c
    d, _ = tree.query(s * src @ R.T + t); return s, R, t, float(np.median(d))
def pad_fit(V, T):
    Q = geo.surf(V, T, 60000); tree = cKDTree(Q); best = None
    for M0 in TURNS:
        s, R, t, m = sim_icp(S62, tree, Q, M0)
        if best is None or m < best[3]: best = (s, R, t, m)
    s, R, t, m = best; left = np.linalg.det(R) < 0
    if left:                        # 62 mirrored matches: x_pad = s R MX x62 + t -> fit on the left socket (conjugated 62 fit)
        Rl = R @ np.diag([-1.0, 1, 1]); MXp = np.diag([-1.0, 1, 1, 1])
        F62L = MXp @ F62 @ MXp; c = np.diag([-1.0, 1, 1]) @ C62
        pc = s * R @ C62 + t        # 62's shell centre on the pad
        Fit = F62L @ M4(np.eye(3), c) @ M4(Rl.T, np.zeros(3)) @ M4(np.eye(3), -pc)
        return "Pad L", Fit, s, m
    pc = s * R @ C62 + t
    Fit = F62 @ M4(np.eye(3), C62) @ M4(R.T, np.zeros(3)) @ M4(np.eye(3), -pc)
    return "Pad R", Fit, s, m
if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1])); out = {}
    for rel, scale in jobs:
        V, T = load(rel, scale); side, Fit, s, m = pad_fit(V, T)
        out[rel] = dict(side=side, fit=flat(Fit), scale_vs_62=s, med=m, scale=scale)
        print("%-62s %s  x%.2f of 62  match %.3f" % (rel[-62:], side, s, m), flush=True)
    json.dump(out, open(sys.argv[2], "w"), indent=0)
