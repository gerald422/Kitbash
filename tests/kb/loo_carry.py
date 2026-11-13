# Leave-one-out, second version: carry a joint the way the folder's own fitted parts do it.
#   same  = every fitted sibling has one and the same matrix (a kit frame): copy it
#   turn  = the siblings share the turn, only the place differs: move the joint region without turning it
#   rigid = neither: match the region (and the whole shape) with turning
import sys, os, json, time, random, collections
import numpy as np
REPO, LIB = sys.argv[1], sys.argv[2]
NPER, K, CATS = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5].split(",")
sys.path.insert(0, REPO)
from kb import geo
random.seed(11)
DT = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
RADIUS = {"Arms": 6.0, "Legs": float(sys.argv[6]) if len(sys.argv) > 6 else 13.0, "Chests": 7.0}
ROTS = geo.rots24(); cache = {}


def soup(path, scale=1.0): return np.fromfile(path, dtype=DT, offset=84)["v"].astype(float) * scale
def sample(tri, n, seed=0):
    a = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
    rng = np.random.default_rng(seed); i = rng.choice(len(tri), n, p=a / a.sum()); u, w = rng.random(n), rng.random(n)
    m = u + w > 1; u[m], w[m] = 1 - u[m], 1 - w[m]; t = tri[i]
    return t[:, 0] + u[:, None] * (t[:, 1] - t[:, 0]) + w[:, None] * (t[:, 2] - t[:, 0])
def M4(R, t): M = np.eye(4); M[:3, :3] = R; M[:3, 3] = t; return M
def ang(A, B): return geo.ang(A[:3, :3].T @ B[:3, :3])
def point(kind, X): return np.linalg.inv(X)[:3, 3] if kind == "fit" else X[:3, 3]


def joints(cat, sc):
    J = {}
    if cat in ("Arms", "Legs"):
        for k, F in sc.get("fits", {}).items(): J[k] = ("fit", np.array(F).reshape(4, 4))
    else:
        for s in sc.get("sockets", []):
            if s["type"] in ("Shoulder R", "Shoulder L", "Neck", "Back", "Waist", "Flat Waist"): J[s["type"]] = ("sock", np.array(s["matrix"]).reshape(4, 4))
    return J


def regime(kind, Xs):
    if len(Xs) < 2: return "rigid"
    tu = max(ang(Xs[0], X) for X in Xs); P = np.array([point(kind, X) for X in Xs])
    sp = float(np.linalg.norm(P - np.median(P, 0), axis=1).max())
    return "same" if tu < 0.5 and sp < 0.05 else "turn" if tu < 0.5 else "rigid"


def surf_of(rel, sc):
    if rel not in cache:
        tri = soup(os.path.join(LIB, rel[:-13] + ".stl"), sc.get("scale", 1.0)); S = sample(tri, 60000, 1)
        cache[rel] = (S, S[np.random.default_rng(2).choice(len(S), 3000, replace=False)], np.sort(np.ptp(tri.reshape(-1, 3), 0)))
    return cache[rel]


def shift_icp(src, tree, t, iters=30, keep=0.85):
    """move src onto the tree's points without turning it"""
    for _ in range(iters):
        d, i = tree.query(src + t); m = d <= np.quantile(d, keep)
        t = t + (tree.data[i[m]] - (src[m] + t)).mean(0)
    d, _ = tree.query(src + t); return t, d


def carry(cat, mode, Q, tree, S, full, kind, X):
    """the reference's joint X carried onto Q in the given mode: (matrix, region median, whole median)"""
    pt = point(kind, X); reg = S[np.linalg.norm(S - pt, axis=1) < RADIUS[cat]]
    if len(reg) < 150: return None
    if len(reg) > 1500: reg = reg[np.random.default_rng(3).choice(len(reg), 1500, replace=False)]
    I = np.eye(3)
    if mode == "same":
        cands = [(I, np.zeros(3))]
    elif mode == "turn":
        cands = []
        for t0 in (np.zeros(3), Q.mean(0) - full.mean(0)):
            t, _ = shift_icp(full, tree, t0, 20); t, _ = shift_icp(reg, tree, t, 30); cands.append((I, t))
    else:
        sub = full[:400]; coarse = []
        for R0 in ROTS:
            R, t, d = geo.icp(sub, tree, R0, Q.mean(0) - R0 @ full.mean(0), 20); coarse.append((float(np.median(d)), R, t))
        starts = [(R, t) for _, R, t in sorted(coarse, key=lambda c: c[0])[:3]] + [(I, np.zeros(3))]
        cands = []
        for R, t in starts:
            R, t, d = geo.icp(full, tree, R, t, 30); R, t, d = geo.icp(reg, tree, R, t, 30); cands.append((R, t))
    best = None
    for R, t in cands:
        d, _ = tree.query(reg @ R.T + t); m = float(np.median(d)); dw, _ = tree.query(full @ R.T + t); mw = float(np.median(dw))
        if best is None or m + 0.15 * mw < best[0]: best = (m + 0.15 * mw, m, mw, R, t)
    _, m, mw, R, t = best; M = M4(R, t)
    return (X @ np.linalg.inv(M)) if kind == "fit" else (M @ X), m, mw


parts = collections.defaultdict(list)
for d, _, fs in os.walk(os.path.join(REPO, "library")):
    for f in fs:
        if not f.endswith(".sockets.json"): continue
        rel = os.path.relpath(os.path.join(d, f), os.path.join(REPO, "library")).replace("\\", "/")
        sc = json.load(open(os.path.join(d, f), encoding="utf-8-sig")); cat = sc.get("category")
        if cat in CATS and joints(cat, sc) and not sc.get("upright"): parts[cat].append((rel, sc))
rows = []
for cat in CATS:
    bym = collections.defaultdict(list)
    for rel, sc in parts[cat]: bym[rel.split("/")[0]].append((rel, sc))
    for maker in sorted(bym, key=lambda m: -len(bym[m]))[:5]:
        for rel, sc in random.sample(bym[maker], min(NPER, len(bym[maker]))):
            t0 = time.time(); J = joints(cat, sc)
            sibs = [(r, s) for r, s in bym[maker] if os.path.dirname(r) == os.path.dirname(rel) and r != rel and set(joints(cat, s)) & set(J)]
            if not sibs: rows.append((cat, maker, rel, "-", None)); continue
            try: tri = soup(os.path.join(LIB, rel[:-13] + ".stl"), sc.get("scale", 1.0))
            except OSError: continue
            Q = sample(tri, 60000, 0); tree = geo.kdtree(Q); ext = np.sort(np.ptp(tri.reshape(-1, 3), 0))
            line = []
            for name, (kind, T) in J.items():
                refs = [(r, s) for r, s in sibs if name in joints(cat, s)]
                if not refs: continue
                mode = regime(kind, [joints(cat, s)[name][1] for r, s in refs])
                def close(x):
                    try: return float(np.abs(surf_of(*x)[2] - ext).sum())
                    except OSError: return 9e9
                use = sorted(random.sample(refs, min(len(refs), 12)), key=close)[:1 if mode == "same" else K]
                best = None
                for r, s in use:
                    try: S, full, _ = surf_of(r, s)
                    except OSError: continue
                    got = carry(cat, mode, Q, tree, S, full, kind, joints(cat, s)[name][1])
                    if got and (best is None or got[1] + 0.15 * got[2] < best[1] + 0.15 * best[2]): best = got
                if best is None: continue
                X, m, mw = best; mm = float(np.linalg.norm(point(kind, X) - point(kind, T))); dg = ang(X, T)
                rows.append((cat, maker, rel, mode, (name, round(mm, 3), round(dg, 2), round(m, 3), round(mw, 3))))
                line.append("%s[%s] %.2fmm %.1fdeg m%.2f" % (name, mode, mm, dg, m))
            print("%-6s %-26s %-42s %s (%.0f s)" % (cat, maker[:26], os.path.basename(rel)[:-13][:42], "  ".join(line), time.time() - t0), flush=True)
print("\n=== carried vs true, by how the folder's fitted parts do it ===")
ok = lambda x: x[1] <= 0.5 and x[2] <= 3
for cat in CATS:
    for mode in ("same", "turn", "rigid"):
        R = [x for c, m, r, md, x in rows if c == cat and md == mode and x]
        if not R: continue
        mm = np.array([x[1] for x in R]); dg = np.array([x[2] for x in R]); md_ = np.array([x[3] for x in R])
        print("%-6s %-5s %3d joints: position median %.2f, 90%% %.2f, max %.2f mm; turn median %.1f, 90%% %.1f deg; within 0.5 mm / 3 deg: %d%%" % (
            cat, mode, len(R), np.median(mm), np.quantile(mm, 0.9), mm.max(), np.median(dg), np.quantile(dg, 0.9), 100 * np.mean([ok(x) for x in R])))
        for g in (0.08, 0.12, 0.20):
            k = md_ <= g
            if 0 < k.sum() < len(R): print("          region match <= %.2f: keeps %d, of those within 0.5 mm / 3 deg: %d%% (worst %.2f mm, %.1f deg)" % (g, k.sum(), 100 * np.mean([ok(x) for x, kk in zip(R, k) if kk]), mm[k].max(), dg[k].max()))
    by = collections.defaultdict(list)
    for c, m, r, md, x in rows:
        if c == cat and x: by[(m, md)].append(x)
    for (m, md), X in sorted(by.items()): print("     %-30s %-5s %3d joints, within 0.5 mm / 3 deg: %3d%%  (position median %.2f, turn median %.1f)" % (m[:30], md, len(X), 100 * np.mean([ok(x) for x in X]), np.median([x[1] for x in X]), np.median([x[2] for x in X])))
    print("     no fitted sibling in the folder: %d of %d parts" % (sum(1 for c, m, r, md, x in rows if c == cat and md == "-"), len({r for c, m, r, md, x in rows if c == cat})))
json.dump(rows, open(sys.argv[7] if len(sys.argv) > 7 else "loo2.json", "w"))
