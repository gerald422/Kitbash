"""Neck fit shared by the kits: Josh's AM helmet (its neck ring) matched onto a head, carrying his fit."""
import json, numpy as np
inv = np.linalg.inv
import geo
from scipy.spatial import cKDTree
P_AM = json.load(open('/home/claude/kits/amv2_partial.json'))['side']
AMH = 'AssaultMarines-V2/AssaultMarines-V2/RawSTL/Helmet-Heads/1-Helmet-1.stl'
F_AMH = np.array(P_AM[AMH]['fits']['Neck']).reshape(4, 4)
def neck_fit(helmet_rel):
    V, T = geo.load(AMH); S = geo.surf(V, T, 200000)
    W, U = geo.load(helmet_rel); Q = geo.surf(W, U, 200000); tree = cKDTree(Q)
    full = S[np.random.default_rng(1).choice(len(S), 3000, replace=False)]
    neck = inv(F_AMH)[:3, 3]; reg = S[np.linalg.norm(S - neck, axis=1) < 4.0]
    best = None
    for a in (0, 90, 180, 270):
        c, s_ = np.cos(np.radians(a)), np.sin(np.radians(a)); R0 = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
        R, t, d = geo.icp(full, tree, Q, R0, Q.mean(0) - R0 @ S.mean(0), 40); R, t, d = geo.icp(reg, tree, Q, R, t, 30)
        if best is None or np.median(d) < best[0]: best = (float(np.median(d)), geo.M4(R, t))
    return F_AMH @ inv(best[1]), best[0]
