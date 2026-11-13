"""Fits carried from Josh's reference parts onto a new maker's part, by matching the reference's shape onto it.
Lifted from kits/rw_spr/common.py, heads.py and pads.py (the Nov 9 batch), unchanged in what they compute, without
their container paths: the library root is passed in, and the nearest-point search is kb.geo.kdtree (scipy where
there is one, Blender's own KD tree on the PC).

    from kb import fit
    H = fit.Heads(lib); F, med = H.neck_fit(*fit.load(path, scale))        # Neck fit, median match in mm
    P = fit.Pads(lib);  side, F, s, med = P.pad_fit(*fit.load(path, scale)) # 'Pad R' / 'Pad L', fit, scale vs 62

Heads: Josh's Assault helmet 1 (its whole shape, then its neck ring) matched onto each helmet, carrying his Neck
fit across (12 turns about Z, because makers' files lie at any heading on the plate).
Pads: Josh's pad 62 (Mar Fil Assault Shoulder Pad 1) matched onto each pad (rotation + uniform scale kept within
0.85-1.35, 24 starts: the square turns), carrying 62's Pad R fit across about 62's shell centre, so a bigger pad
grows outward from the shoulder instead of into it. A pad that matches 62 mirrored is a left pad.
"""
import itertools, json, os
import numpy as np
from . import geo

AMH = "Mar Fil - Tacticus/AssaultMarines-V2/Helmet-Heads/Heads/MarFil Assault - Helmet 1"
P62 = "Mar Fil - Tacticus/AssaultMarines-V2/Shoulder Pads/MarFil Assault - Shoulder Pad 1"


def load(path, scale=1.0):
    V, T = geo.stl(path); return np.asarray(V, float) * scale, np.asarray(T, int)
def rz(a):
    c, s = np.cos(a), np.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
def M4(R, t): M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; return M
def flat(M): return [round(float(x), 6) for x in np.asarray(M).reshape(-1)]
def _ref(lib, rel):
    V, T = geo.stl(os.path.join(lib, rel + ".stl"))
    return np.asarray(V, float), T, json.load(open(os.path.join(lib, rel + ".sockets.json"), encoding="utf-8-sig"))


def icp_starts(src_full, src_reg, Q, starts, iters=(40, 30)):
    """best rigid map src -> Q over rotation starts about Z (each start also centres src on Q): a coarse pass on 400
    points from every start, then the best three refined on all points."""
    tree = geo.kdtree(Q); coarse = []
    sub = src_full[np.random.default_rng(3).choice(len(src_full), min(400, len(src_full)), replace=False)]
    for R0 in starts:
        t0 = Q.mean(0) - R0 @ src_full.mean(0)
        R, t, d = geo.icp(sub, tree, R0, t0, 25); coarse.append((float(np.median(d)), R, t))
    best = None
    for _, R, t in sorted(coarse, key=lambda c: c[0])[:3]:
        R, t, d = geo.icp(src_full, tree, R, t, iters[0])
        if src_reg is not None: R, t, d = geo.icp(src_reg, tree, R, t, iters[1])
        m = float(np.median(d))
        if best is None or m < best[0]: best = (m, R, t)
    return best


class Heads:
    def __init__(self, lib):
        Va, Ta, sc = _ref(lib, AMH)
        self.F = np.array(sc["fits"]["Neck"]).reshape(4, 4)
        S = geo.surf(Va, Ta, 200000); rng = np.random.default_rng(1)
        self.full = S[rng.choice(len(S), 3000, replace=False)]
        neck = np.linalg.inv(self.F)[:3, 3]; self.reg = S[np.linalg.norm(S - neck, axis=1) < 4.0]
        self.starts = [rz(np.radians(a)) for a in range(0, 360, 30)]

    def neck_fit(self, V, T):
        Q = geo.surf(V, T, 80000)
        m, R, t = icp_starts(self.full, self.reg, Q, self.starts)
        return self.F @ np.linalg.inv(M4(R, t)), m


def _sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); c, *_ = np.linalg.lstsq(A, b, rcond=None); return c[:3]
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


class Pads:
    def __init__(self, lib):
        V62, T62, sc = _ref(lib, P62)
        self.F = np.array(sc["fits"]["Pad R"]).reshape(4, 4)
        self.S = geo.surf(V62, T62, 60000)[np.random.default_rng(2).choice(60000, 2500, replace=False)]
        self.C = _sphere(self.S)
        self.turns = []
        for perm in itertools.permutations(range(3)):
            for sg in itertools.product((1, -1), repeat=3):
                R = np.zeros((3, 3))
                for i, j in enumerate(perm): R[j, i] = sg[i]
                if np.linalg.det(R) > 0: self.turns.append(R)      # the 24 square turns (either side through mirrorLeft)

    def pad_fit(self, V, T):
        Q = geo.surf(V, T, 60000); tree = geo.kdtree(Q); best = None
        for M0 in self.turns:
            s, R, t, m = sim_icp(self.S, tree, Q, M0)
            if best is None or m < best[3]: best = (s, R, t, m)
        s, R, t, m = best; F62, C62 = self.F, self.C
        if np.linalg.det(R) < 0:    # 62 mirrored matches: x_pad = s R MX x62 + t -> fit on the left socket (conjugated 62 fit)
            Rl = R @ np.diag([-1.0, 1, 1]); MXp = np.diag([-1.0, 1, 1, 1])
            F62L = MXp @ F62 @ MXp; c = np.diag([-1.0, 1, 1]) @ C62
            pc = s * R @ C62 + t    # 62's shell centre on the pad
            return "Pad L", F62L @ M4(np.eye(3), c) @ M4(Rl.T, np.zeros(3)) @ M4(np.eye(3), -pc), s, m
        pc = s * R @ C62 + t
        return "Pad R", F62 @ M4(np.eye(3), C62) @ M4(R.T, np.zeros(3)) @ M4(np.eye(3), -pc), s, m
