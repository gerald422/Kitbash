"""Every two-armed piece: find its two inner shoulder faces (as single arms are fitted: the face's centre on
the socket) on the Mar Fil reference torso, and the correction that puts them on Shoulder R and L.
python3 two_discs.py BUILDER [--json out.json]"""
import json, struct, sys, numpy as np
from collections import defaultdict
B = sys.argv[1]
d = json.load(open(B + "/index.json"))
M4 = lambda a: np.array(a, float).reshape(4, 4)
tor = next(p for p in d["parts"] if p["name"] == "MarFil Assault - Torso 3")
S = {s["t"]: M4(s["m"]) for s in tor["sockets"]}
sR, sL = S["Shoulder R"][:3, 3], S["Shoulder L"][:3, 3]
def load(p):
    b = open(B + "/" + p["prev"], "rb").read(); nv, nt = struct.unpack_from("<II", b, 4)
    return (np.frombuffer(b, np.float32, nv * 3, 12).reshape(-1, 3).astype(float),
            np.frombuffer(b, np.uint32, nt * 3, 12 + nv * 12).reshape(-1, 3))
def discs(V, T, direction, near, radius=10.0, tol=0.93, min_area=1.0):
    A, Bv, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(Bv - A, C - A); a = np.linalg.norm(n, axis=1); n = n / np.maximum(a[:, None], 1e-12); a = a / 2
    cen = (A + Bv + C) / 3
    k = ((n @ direction) > tol) & (np.linalg.norm(cen - near, axis=1) < radius)
    if not k.any(): return None
    c, aa, nn = cen[k], a[k], n[k]
    off = c @ direction; used = np.zeros(len(c), bool); best = None
    for i in np.argsort(-aa):
        if used[i]: continue
        g = (~used) & (np.abs(off - off[i]) < 0.15) & (np.linalg.norm(c - c[i], axis=1) < 4.0)
        used |= g; A_ = aa[g].sum()
        if A_ < min_area: continue
        cc = (c[g] * aa[g, None]).sum(0) / A_; nm = (nn[g] * aa[g, None]).sum(0); nm /= np.linalg.norm(nm)
        # the inner face of a shoulder: the biggest, then the one nearest the socket
        score = A_ - 0.3 * np.linalg.norm(cc - near)
        if best is None or score > best[0]: best = (score, cc, A_, nm)
    return best
def rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b); v = np.cross(a, b); c = a @ b
    if np.linalg.norm(v) < 1e-9: return np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))
res = {}; rows = []
for p in d["parts"]:
    if p["type"] not in ("Two-Handed Guns", "Two-Handed Melee", "Heavy Weapons") or not p.get("prev") or "Shoulder R" not in p["fits"]:
        continue
    F = M4(p["fits"]["Shoulder R"]); W = S["Shoulder R"] @ F
    V, T = load(p); w = V @ W[:3, :3].T + W[:3, 3]
    r = discs(w, T, np.array([-1., 0, 0]), sR); l = discs(w, T, np.array([1., 0, 0]), sL)
    if r is None or l is None:
        rows.append((p["maker"], p["kit"], p["name"], "no %s face" % ("right" if r is None else "left"))); continue
    cR, cL = r[1], l[1]
    R = rot_between(cL - cR, sL - sR)
    mid_c, mid_s = (cR + cL) / 2, (sR + sL) / 2
    C = np.eye(4); C[:3, :3] = R; C[:3, 3] = mid_s - R @ mid_c
    ang = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
    span = np.linalg.norm(cL - cR)
    Fn = np.linalg.inv(S["Shoulder R"]) @ C @ W
    res[p["id"]] = {"path": p["path"], "name": p["name"], "fit": Fn.ravel().tolist(), "move": float(np.linalg.norm(C[:3, 3] + R @ mid_c - mid_c)),
                    "rot": float(ang), "span": float(span), "offR": (cR - sR).round(2).tolist(), "offL": (cL - sL).round(2).tolist(),
                    "areas": [round(r[2], 1), round(l[2], 1)], "normals": [r[3].round(2).tolist(), l[3].round(2).tolist()]}
    rows.append((p["maker"], p["kit"], p["name"], "R off %s  L off %s  span %.1f  areas %.1f/%.1f  rot %.1f" % ((cR - sR).round(1), (cL - sL).round(1), span, r[2], l[2], ang)))
for row in sorted(rows): print("%-10s %-14s %-48s %s" % (row[0], row[1][:14], row[2][-48:], row[3]))
if "--json" in sys.argv: json.dump(res, open(sys.argv[sys.argv.index("--json") + 1], "w"))
print(len(res), "with both faces,", len(rows) - len(res), "without")
