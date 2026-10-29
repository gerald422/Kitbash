"""How well the add-on's shin finder agrees between Mar Fil's two rigs (pad relative to the frame)."""
import sys, json, numpy as np
sys.path.insert(0, "/home/claude/tiow_blender")
import tiow_inbox as T
from mathutils import Matrix, Vector
def rig(prefix, name):
    Z = np.load(prefix + ".npz"); M = json.load(open(prefix + ".json")); k = M[name]["key"]
    v = Z[k + "_v"].astype(float); t = Z[k + "_t"].astype(np.int64); mw = Z[k + "_mw"]
    V = v @ mw[:3, :3].T + mw[:3, 3]
    if np.linalg.det(mw[:3, :3]) < 0: t = t[:, ::-1]
    return V, t, mw
def merge(V, Tr):
    q = np.round(V, 5); u, inv = np.unique(q, axis=0, return_inverse=True); return u, inv.reshape(-1)[Tr]
def frame(found):
    ea, eb, top, op = found
    pts = [Vector(p) for p in (ea, eb, top)]; n = Vector(op)
    return T._three_point_frame("Shin", pts, [n, n, n])
MXL = np.diag([-1.0, 1, 1, 1])
def ang(R): return np.degrees(np.arccos(np.clip((np.trace(np.asarray(R)[:3, :3]) - 1) / 2, -1, 1)))
rels = {}
for pre, knee, pad, side in (("tech_parts", "Knee-L-Pose", "Intercessor-ShinPad-L", "L"),
                             ("chap_parts", "Knee-A-Pose.L", "ShinPad-L-Chaplain", "L"),
                             ("tech_parts", "Knee-R-Pose", "Intercessor-ShinPad-R", "R"),
                             ("chap_parts", "Knee-A-Pose.R", "ShinPad-R-Chaplain", "R")):
    V, Tr, _ = rig("/home/claude/blend/mf/" + pre, knee); V, Tr = merge(V, Tr)
    f = T.find_shin_points(V, Tr)
    if len(f) != 1: print(pre, knee, "found", len(f)); continue
    S = np.array(frame(f[0]))
    _, _, pmw = rig("/home/claude/blend/mf/" + pre, pad)
    rel = np.linalg.inv(S) @ pmw
    if side == "R":   # compare as the mirror image of a left
        rel = MXL @ rel @ MXL if np.linalg.det(rel[:3,:3]) > 0 else MXL @ rel
    rels[pre + side] = rel
    print(pre, side, "det", round(np.linalg.det(rel[:3,:3]), 3))
ks = list(rels)
for i in range(len(ks)):
    for j in range(i + 1, len(ks)):
        A, B = rels[ks[i]], rels[ks[j]]
        A3 = A[:3,:3] / np.cbrt(abs(np.linalg.det(A[:3,:3]))); B3 = B[:3,:3] / np.cbrt(abs(np.linalg.det(B[:3,:3])))
        print("%-12s %-12s angle %.3f  move %s" % (ks[i], ks[j], ang(A3.T @ B3) if np.linalg.det(A3.T@B3)>0 else -1, np.round(A[:3,3]-B[:3,3], 3)))
