"""Shoulder disc of each heresy arm in Josh-local coords (HeresyArms_r frame): connected flat patch facing the chest,
circle fit of its outline; compare with Josh's origin (local 0)."""
import sys, json, numpy as np, collections
sys.path.insert(0, "/home/claude/blend/forclaude"); sys.path.insert(0, "/home/claude/kits/cr"); sys.path.insert(0, "/home/claude/kits")
from stl_io import read_stl
U = "/mnt/user-data/uploads/new cults/Springles/"
G = json.load(open("G.json"))
RZ90 = np.array([[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1.0]])
def disc(P, T, nref, near, cos=0.999, rad=6):
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]; fn = np.cross(b - a, c - a); ar = np.linalg.norm(fn, axis=1) / 2
    n = fn / (2 * ar[:, None] + 1e-12); cen = (a + b + c) / 3
    ok = (n @ nref > cos) & (np.linalg.norm(cen - near, axis=1) < rad) & (ar > 0)
    idx = np.where(ok)[0]
    if not len(idx): return None
    # plane groups by offset; take the group with most area; then connected component (shared vertex)
    off = cen[idx] @ nref; best = None
    for o in np.unique(np.round(off / 0.02)):
        sel = idx[np.abs(off / 0.02 - o) < 1.0]
        if best is None or ar[sel].sum() > ar[best].sum(): best = sel
    sel = best
    # components
    vmap = collections.defaultdict(list)
    for f in sel:
        for v in T[f]: vmap[v].append(f)
    seen = set(); comps = []
    for f in sel:
        if f in seen: continue
        st = [f]; comp = []; seen.add(f)
        while st:
            g = st.pop(); comp.append(g)
            for v in T[g]:
                for h2 in vmap[v]:
                    if h2 not in seen: seen.add(h2); st.append(h2)
        comps.append(comp)
    comp = np.array(max(comps, key=lambda c_: ar[c_].sum()))
    A = ar[comp].sum(); C = (cen[comp] * ar[comp, None]).sum(0) / A
    # boundary edges -> circle fit in plane
    E = collections.Counter()
    for f in comp:
        for i in range(3):
            e = tuple(sorted((T[f][i], T[f][(i + 1) % 3]))); E[e] += 1
    bv = np.unique([v for e, k in E.items() if k == 1 for v in e]); Q = P[bv]
    u = np.cross(nref, [0, 0, 1.0]); u /= np.linalg.norm(u); w = np.cross(nref, u)
    x, y = (Q - C) @ u, (Q - C) @ w
    M = np.c_[2 * x, 2 * y, np.ones_like(x)]; s = np.linalg.lstsq(M, x * x + y * y, rcond=None)[0]
    r = np.sqrt(s[2] + s[0] ** 2 + s[1] ** 2); cc = C + s[0] * u + s[1] * w
    spread = np.std(np.hypot(x - s[0], y - s[1])) / r
    return dict(area=A, centroid=C, centre=cc, r=r, spread=spread)
if __name__ == "__main__":
    out = {}
    for name, g in sorted(G.items()):
        v, n, t = read_stl(U + g["rel"]); V = np.asarray(v, float) * g["scale"]; T = np.asarray(t)
        Gm = np.array(g["G"])
        if name.startswith(("patternP", "patternS")) and not g.get("mirrored"): Gm = RZ90 @ Gm
        if np.linalg.det(Gm[:3, :3]) < 0: T = T[:, ::-1]
        P = V @ Gm[:3, :3].T + Gm[:3, 3]
        d = disc(P, T, np.array([0, -1.0, 0]), np.zeros(3))
        if d is None: print(name, "NO DISC"); continue
        out[name] = {k: (v_.tolist() if isinstance(v_, np.ndarray) else float(v_)) for k, v_ in d.items()}
        print("%-32s area %5.1f r %.2f spread %.3f centre %s centroid %s" % (name, d["area"], d["r"], d["spread"], d["centre"].round(2), d["centroid"].round(2)))
    json.dump(out, open("discs_josh.json", "w"), indent=0)
