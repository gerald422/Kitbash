import sys; sys.path.insert(0,'/home/claude/kits'); sys.path.insert(0,'/home/claude/kits/cr'); sys.path.insert(0,'/home/claude/kits/tn'); sys.path.insert(0,'/home/claude/kits/cr/dev')
import numpy as np, json, stlcache, flats, disc
from topface import merge_flats
from flatface import frame
from belt import surf_n
TN = "/mnt/user-data/uploads/new cults/Turtle Ninja/"
def sphere(P):
    A = np.c_[2 * P, np.ones(len(P))]; b = (P ** 2).sum(1); x = np.linalg.lstsq(A, b, rcond=None)[0]; c = x[:3]; r = np.sqrt(x[3] + c @ c)
    return c, r, float(np.sqrt(np.mean((np.linalg.norm(P - c, axis=1) - r) ** 2)))
def arm_dome(path):
    V, T = stlcache.load(path); M = merge_flats([(A, n, c) for A, n, c, o, s in flats.flats(V, T, min_area=1.0)])
    d = max([m for m in M if abs(m[1][0]) > 0.98 and 6 < m[0] < 30], key=lambda m: m[0]); c0, n = d[2], d[1]
    P, N = surf_n(V, T, 200000)
    out = -n                                                     # away from the torso
    k = ((P - c0) @ out > 0.3) & ((P - c0) @ out < 6) & (P[:, 1] > c0[1] - 0.5) & (np.linalg.norm(P - c0, axis=1) < 6.5) & ((N * (P - c0)).sum(1) > 0)
    c, r, rms = sphere(P[k]); return c, r, rms, c0, n
def pad_inner(path):
    V, T = stlcache.load(path); P, N = surf_n(V, T, 200000)
    c = np.array([(V[:, 0].min() + V[:, 0].max()) / 2, 0.0, (V[:, 2].min() + V[:, 2].max()) / 2])
    for _ in range(6):
        k = ((c - P) * N).sum(1) / (np.linalg.norm(c - P, axis=1) + 1e-9) > 0.6
        c, r, rms = sphere(P[k])
    shell = P.mean(0); return c, r, rms, shell
for a in ["TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Arms/Mk10_2.0_Arm_Right_A_1.stl", "TurtleNinja's Mk4 Tactical Squad/Weapons/Single Arm/Mk4_L_Arm_A_1.stl", "TurtleNinja's Mk6 Addon 1/Arms/Mk6_Arm_A_1.stl"]:
    c, r, rms, c0, n = arm_dome(TN + a); print(a.split('/')[-1], 'dome r %.2f rms %.3f centre-from-disc along out %.2f, up %.2f' % (r, rms, (c - c0) @ -n, c[1] - c0[1]))
for p in ["TurtleNinja's Mk10 Assault Intercessor + Jumppack Addon/Pauldrons/Pauldron_Assault_1.stl", "TurtleNinja's Mk4 Tactical Squad/Pauldron 2.0/Mk4_Pauldron_1.stl"]:
    c, r, rms, shell = pad_inner(TN + p); print(p.split('/')[-1], 'inner r %.2f rms %.3f c %s shell-c %s' % (r, rms, c.round(2), (shell - c).round(2)))
