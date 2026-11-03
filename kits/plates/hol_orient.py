"""Orientation from shape for parts whose belt fit doesn't hang them right (or have none): the longest axis up
(socket Y), the thinnest out (socket Z) with the flatter side at the back (-Z); a file whose long axis is its
own Z keeps +Z up; otherwise the end with more cross-section is the top (holster mouth / grip).
python hol_orient.py NAMES(comma) PARTS_JSON OUT_JSON"""
import sys, json, numpy as np; sys.path.insert(0, __file__.rsplit("/", 1)[0]); from hol_common import *
names = sys.argv[1].split(","); parts = json.load(open(sys.argv[2])); out = {}
for rel in parts:
    nm = rel.split("\\")[-1][:-4]
    if nm not in names: continue
    V, T = stl(U + rel.replace("\\", "/")); P, _ = surf(V, T, 40000)
    ext = P.max(0) - P.min(0); lo_ax = int(np.argmax(ext)); th_ax = int(np.argmin(ext)); x_ax = 3 - lo_ax - th_ax
    e = np.eye(3); y = e[lo_ax].copy(); z = e[th_ax].copy()
    if lo_ax != 2:
        c = P[:, lo_ax]; m = (c.min() + c.max()) / 2; w = lambda k: np.ptp(P[k][:, x_ax]) * np.ptp(P[k][:, th_ax])
        if w(c < m - 0.25 * ext[lo_ax]) > w(c > m + 0.25 * ext[lo_ax]): y = -y
    t = P[:, th_ax]; near_min = (t < t.min() + 0.25).mean(); near_max = (t > t.max() - 0.25).mean()
    if near_max > near_min: z = -z                              # flatter side is the back: it must face -Z
    x = np.cross(y, z); R = np.array([x, y, z])                 # rows: socket axes in file coordinates
    out[nm] = R.tolist(); print(f"{nm[:50]:50s} up file {'XYZ'[lo_ax]}{'+' if y[lo_ax] > 0 else '-'}, out file {'XYZ'[th_ax]}{'+' if z[th_ax] > 0 else '-'} (flat {near_min:.2f}/{near_max:.2f})")
json.dump(out, open(sys.argv[3], "w"))
